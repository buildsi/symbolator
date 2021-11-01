# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

"""A smeagle model will load one or more Json corpora, and do a solve.
This is adopted from https://github.com/buildsi/smeagle-demo (db)
"""

import sys
import logging
import os
import re
import json
import subprocess
import jsonschema
import time
import shutil
import clingo

from symbolator.facts import get_facts
from symbolator.asp import AspFunction, AspFunctionBuilder, Result, PyclingoDriver
from symbolator.utils import read_json

from .schema import model_schema


# Smeagle corpus schema

clingo_cffi = hasattr(clingo.Symbol, "_rep")


fn = AspFunctionBuilder()


class SmeagleClingoDriver(PyclingoDriver):
    def solve(
        self,
        setup,
        nmodels=0,
        stats=False,
        logic_programs=None,
        facts_only=False,
    ):
        """
        Run the solver for a model and some number of logic programs
        """
        # logic programs to give to the solver
        logic_programs = logic_programs or []
        if not isinstance(logic_programs, list):
            logic_programs = [logic_programs]

        # Initialize the control object for the solver
        self.control = clingo.Control()
        self.control.configuration.solve.models = nmodels
        self.control.configuration.asp.trans_ext = "all"
        self.control.configuration.asp.eq = "5"
        self.control.configuration.configuration = "tweety"
        self.control.configuration.solve.parallel_mode = "2"
        self.control.configuration.solver.opt_strategy = "usc,one"

        # set up the problem -- this generates facts and rules
        self.assumptions = []
        with self.control.backend() as backend:
            self.backend = backend
            setup.setup(self)

        # If we only want to generate facts, cut out early
        if facts_only:
            return

        # read in provided logic programs
        for logic_program in logic_programs:
            self.control.load(logic_program)

        # Grounding is the first step in the solve -- it turns our facts
        # and first-order logic rules into propositional logic.
        self.control.ground([("base", [])])

        # With a grounded program, we can run the solve.
        result = Result()
        models = []  # stable models if things go well
        cores = []  # unsatisfiable cores if they do not

        def on_model(model):
            models.append((model.cost, model.symbols(shown=True, terms=True)))

        # Won't work after this, need to write files
        solve_kwargs = {
            "assumptions": self.assumptions,
            "on_model": on_model,
            "on_core": cores.append,
        }
        if clingo_cffi:
            solve_kwargs["on_unsat"] = cores.append
        solve_result = self.control.solve(**solve_kwargs)

        # once done, construct the solve result
        result.satisfiable = solve_result.satisfiable

        def stringify(x):
            if clingo_cffi:
                # Clingo w/ CFFI will throw an exception on failure
                try:
                    return x.string
                except RuntimeError:
                    return str(x)
            else:
                return x.string or str(x)

        if result.satisfiable:
            min_cost, best_model = min(models)
            result.answers = {}
            for sym in best_model:
                if sym.name not in result.answers:
                    result.answers[sym.name] = []
                result.answers[sym.name].append([stringify(a) for a in sym.arguments])

        elif cores:
            symbols = dict((a.literal, a.symbol) for a in self.control.symbolic_atoms)
            for core in cores:
                core_symbols = []
                for atom in core:
                    sym = symbols[atom]
                    core_symbols.append(sym)
                result.cores.append(core_symbols)

        if stats:
            print("Statistics:")
            pprint.pprint(self.control.statistics)
        return result


class SolverBase:
    """
    Common base functions for some kind of solver.

    For stability, compatibility, or just fact generation.
    """

    def setup(self, driver):
        """
        Setup to prepare for the solve.
        """
        self.gen = driver

    def print(self, data, title):
        """
        Print a result to the terminal
        """
        if data:
            print("\n" + title)
            print("---------------")
            for entry in data:
                print(" " + " ".join(entry))


class StabilitySolver(SolverBase):
    """
    Class to orchestrate a Stability Solver.
    """

    def __init__(self, lib1, lib2):
        """
        Create a driver to run a compatibility model test for two libraries.
        """
        # The driver will generate facts rules to generate an ASP program.
        self.driver = SmeagleClingoDriver()
        self.setup = StabilitySolverSetup(lib1, lib2)

    def solve(self, logic_programs, detail=False, return_result=False):
        """
        Run the solve
        """
        result = self.driver.solve(self.setup, logic_programs=logic_programs)
        if return_result:
            return result
        missing_imports = result.answers.get("missing_imports", [])
        missing_exports = result.answers.get("missing_exports", [])
        if missing_imports or missing_exports:
            print(
                "Libraries are not stable: %s missing exports, %s missing_imports"
                % (len(missing_exports), len(missing_imports))
            )
            if detail:
                self.print(missing_imports, "Missing Imports")
                self.print(missing_exports, "Missing Exports")


class FactGenerator(SolverBase):
    """
    Class to orchestrate fact generation (uses FactGeneratorSetup)
    """

    def __init__(self, lib):
        """
        Create a driver to run a compatibility model test for two libraries.
        """
        # The driver will generate facts rules to generate an ASP program.
        self.driver = SmeagleClingoDriver(out=sys.stdout)
        self.setup = FactGeneratorSetup(lib)

    def solve(self):
        """
        Generate facts
        """
        return self.driver.solve(self.setup, facts_only=True)


class GeneratorBase:
    """
    The GeneratorBase is the base for any kind of Setup (fact generator or solve)
    Base functions to set up an ABI Stability and Compatability Solver.
    """

    def add_library(self, lib, identifier=None):
        """
        Given a loaded Smeagle Model, generate facts for it.
        """
        self.gen.h2("Library: %s" % lib.name)

        # Generate a fact for each location
        for loc in lib.data.get("locations", []):

            # Functions
            self.generate_function(lib, loc.get("function"), identifier)

    def generate_function(self, lib, func, identifier=None):
        """
        Generate facts for a function
        """
        if not func:
            return

        libname = os.path.basename(lib.data["library"])
        name = func["name"]
        seen = set()

        for param in func.get("parameters", []):

            # These values assume no underlying type (defaults)
            param_name = param["name"]
            param_type = param["class"]  # param['type'] is compiler specific

            # If the param has fields, continue printing until we are done
            fields = param.get("fields", [])

            # If we have an underlying type, use name, type, from there
            if "underlying_type" in param:
                param_name = param["underlying_type"].get("name") or param_name

                # Use these fields (unless they aren't defined)
                param_type = param["underlying_type"].get("class") or param_type

                # If the param has fields, continue printing until we are done
                fields = param["underlying_type"].get("fields", []) or fields

            # We are skipping locations for now - not correct
            # Location and direction are always with the original parameter
            self.gen.fact(
                fn.abi_typelocation(
                    libname,
                    func["name"],
                    param_name,
                    param_type,
                    param["location"],
                    param["direction"],
                    param.get("indirections", "0"),
                )
            )

            # While we have fields, keep adding them as facts until no more
            while fields:
                field = fields.pop(0)
                self.gen.fact(
                    # The library, function name, direction and location are the same
                    fn.abi_typelocation(
                        libname,
                        func["name"],
                        field.get("name", ""),
                        field.get("class", ""),
                        param["location"],
                        param["direction"],
                        field.get("indirections", "0"),
                    )
                )
                # Fields can have nested fields
                fields += field.get("fields", [])

            # If no identifier, skip the last step
            if not identifier:
                continue

            # This is only needed for the stability model to identify membership
            # of a particular function symbol, etc. with a library set (e.g., a or b)
            # Symbol, Type, Register, Direction, Pointer Indirections
            args = [
                func["name"],
                param["class"],
                param["location"],
                param["direction"],
                param.get("indirections", "0"),
            ]
            fact = AspFunction("is_%s" % identifier, args=args)
            if fact not in seen:
                self.gen.fact(fact)
                seen.add(fact)


class StabilitySolverSetup(GeneratorBase):
    """
    Class to set up and run an ABI Stability and Compatability Solver.
    """

    def __init__(self, lib1, lib2):
        self.lib1 = lib1
        self.lib2 = lib2

    def setup(self, driver):
        """
        Setup to prepare for the solve.

        This function overrides the base setup, which will generate facts only
        for one function.
        """
        self.gen = driver
        self.gen.h1("Library Facts")
        self.add_library(self.lib1, "a")
        self.add_library(self.lib2, "b")


class FactGeneratorSetup(GeneratorBase):
    """
    Class to accept one library and generate facts.
    """

    def __init__(self, lib):
        self.lib = lib

    def setup(self, driver):
        """
        Setup to prepare for the solve.

        This base function provides fact generation for one library.
        """
        self.gen = driver
        self.gen.h1("Library Facts")
        self.add_library(self.lib)


class Model:
    def __init__(self, name, data):
        self.name = name
        if not isinstance(data, dict):
            data = json.loads(data)
        self.data = data

    def __str__(self):
        return self.name

    def __repr__(self):
        return str(self)


class SmeagleRunner:
    def __init__(self):
        """
        Load in Smeagle output files, write to database, and run solver.
        """
        self.stability_lp = get_facts("stability.lp")
        self.records = {}

    def generate_facts(self):
        """
        Generate facts for one entry.
        """
        facts = []
        for name, data in self.records.items():
            setup = FactGenerator(name)
            facts.append(setup.solve())
        return facts

    def stability_test(self, detail=False, out=None, return_result=False):
        """
        Run the stability test for two entries.
        """
        # We must have the stability program!
        if not os.path.exists(self.stability_lp):
            sys.exit("Logic program %s does not exist!" % self.stability_lp)

        # Assumes basename of libs are in database (hashes and package names)
        if len(self.records) != 2:
            sys.exit("Two libraries are required to be loaded for a stability test.")

        setup = StabilitySolver(*list(self.records.values()))
        return setup.solve(
            logic_programs=self.stability_lp, detail=detail, return_result=return_result
        )

    def load(self, path):
        """
        Load results (json) files into Smeagle database
        """
        if not os.path.exists(path):
            sys.exit("%s does not exist." % path)
        self.load_data(path)

    def load_data(self, path):
        """
        Load a json result into the sqlite database
        """
        data = read_json(path)
        name = os.path.basename(path)

        # We can only include valid models
        try:
            jsonschema.validate(data, schema=model_schema)
            self.add(name, data)
        except:
            import IPython

            IPython.embed()

    def add(self, name, data):
        """
        This does a create, only if it does not exist
        """
        if name not in self.records:
            self.records[name] = Model(name, data)
