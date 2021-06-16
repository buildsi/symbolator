# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import collections
import copy
import hashlib
import itertools
import os
import pprint
import re
import sys
import time
import types

import symbolator.utils as utils
from .corpus import Corpus

# Since we parse the die's directly, we use these pyelftools supporting functions.
from elftools.common.py3compat import bytes2str
from elftools.dwarf.descriptions import describe_attr_value
from elftools.elf.descriptions import (
    describe_symbol_type,
    describe_symbol_bind,
    describe_symbol_visibility,
    describe_symbol_shndx,
)

from six import string_types

# An arbitrary version for this asp.py (libabigail has one, so we are copying)
__version__ = "1.0.0"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import clingo

    # There may be a better way to detect this
    clingo_cffi = hasattr(clingo.Symbol, "_rep")
except ImportError:
    sys.exit("clingo for Python is required.")


if sys.version_info >= (3, 3):
    from collections.abc import Sequence  # novm
else:
    from collections import Sequence


class Timer(object):
    """Simple timer for timing phases of a solve"""

    def __init__(self):
        self.start = time.time()
        self.last = self.start
        self.phases = {}

    def phase(self, name):
        last = self.last
        now = time.time()
        self.phases[name] = now - last
        self.last = now

    def write(self, out=sys.stdout):
        now = time.time()
        out.write("Time:\n")
        for phase, t in self.phases.items():
            out.write("    %-15s%.4f\n" % (phase + ":", t))
        out.write("Total: %.4f\n" % (now - self.start))


def issequence(obj):
    if isinstance(obj, string_types):
        return False
    return isinstance(obj, (Sequence, types.GeneratorType))


def listify(args):
    if len(args) == 1 and issequence(args[0]):
        return list(args[0])
    return list(args)


class AspObject(object):
    """Object representing a piece of ASP code."""


def _id(thing):
    """Quote string if needed for it to be a valid identifier."""
    if isinstance(thing, AspObject):
        return thing
    elif isinstance(thing, bool):
        return '"%s"' % str(thing)
    elif isinstance(thing, int):
        return str(thing)
    else:
        return '"%s"' % str(thing)


class AspFunction(AspObject):
    def __init__(self, name, args=None):
        self.name = name
        self.args = [] if args is None else args

    def __call__(self, *args):
        return AspFunction(self.name, args)

    def symbol(self, positive=True):
        def argify(arg):
            if isinstance(arg, bool):
                return clingo.String(str(arg))
            elif isinstance(arg, int):
                return clingo.Number(arg)
            else:
                return clingo.String(str(arg))

        return clingo.Function(
            self.name, [argify(arg) for arg in self.args], positive=positive
        )

    def __getitem___(self, *args):
        self.args[:] = args
        return self

    def __str__(self):
        return "%s(%s)" % (self.name, ", ".join(str(_id(arg)) for arg in self.args))

    def __repr__(self):
        return str(self)


class AspFunctionBuilder(object):
    def __getattr__(self, name):
        return AspFunction(name)


fn = AspFunctionBuilder()


class Result(object):
    """
    Result of an ASP solve.
    """

    def __init__(self, asp=None):
        self.asp = asp
        self.satisfiable = None
        self.optimal = None
        self.warnings = None
        self.nmodels = 0

        # specs ordered by optimization level
        self.answers = []
        self.cores = []

    def print_cores(self):
        for core in self.cores:
            tty.msg(
                "The following constraints are unsatisfiable:",
                *sorted(str(symbol) for symbol in core)
            )


class PyclingoDriver(object):
    def __init__(self, cores=True, asp=None):
        """Driver for the Python clingo interface.

        Arguments:
            cores (bool): whether to generate unsatisfiable cores for better
                error reporting.
            asp (file-like): optional stream to write a text-based ASP program
                for debugging or verification.
        """
        global clingo
        self.out = asp or self.devnull()
        self.cores = cores
        self.assumptions = []

    def devnull(self):
        return open(os.devnull, "w")

    def __exit__(self):
        self.f.close()

    def title(self, name, char):
        self.out.write("\n")
        self.out.write("%" + (char * 76))
        self.out.write("\n")
        self.out.write("%% %s\n" % name)
        self.out.write("%" + (char * 76))
        self.out.write("\n")

    def h1(self, name):
        self.title(name, "=")

    def h2(self, name):
        self.title(name, "-")

    def newline(self):
        self.out.write("\n")

    def fact(self, head):
        """ASP fact (a rule without a body)."""
        symbol = head.symbol() if hasattr(head, "symbol") else head

        self.out.write("%s.\n" % str(symbol))

        atom = self.backend.add_atom(symbol)
        self.backend.add_rule([atom], [], choice=self.cores)
        if self.cores:
            self.assumptions.append(atom)

    def solve(
        self,
        solver_setup,
        corpora,
        dump=None,
        nmodels=0,
        timers=False,
        stats=False,
        logic_programs=None,
        facts_only=False,
        # Only relevant for single library symbol dumps
        system_libs=False,
    ):
        """Given three corpora, generate facts for a solver.

        The order is important:

         [binary, libraryA, libraryB]:
           binary: should be a binary that uses libraryA
           libraryA: should be a known library to work with the binary
           libraryB: should be a second library to test if it will work.

        In the future ideally we would not want to require this working library,
        but for now we are trying to emulate what libabigail does. The first
        working binary serves as a base to subset the symbols to a known set
        that are needed. We could possibly remove it if we can load all symbols
        provided by other needed files, and then eliminate them from the set.
        """
        # logic programs to give to the solver
        logic_programs = logic_programs or []
        if not isinstance(logic_programs, list):
            logic_programs = [logic_programs]

        timer = Timer()
        self.control = clingo.Control()

        # set up the problem -- this generates facts and rules
        with self.control.backend() as backend:
            self.backend = backend

            # one corpus we can only generate facts
            if len(corpora) == 1:
                solver_setup.single_setup(self, corpora[0], system_libs)
            else:
                solver_setup.compat_setup(self, corpora)
        timer.phase("setup")

        # If we only want to generate facts, cut out early
        if facts_only:
            return

        for logic_program in logic_programs:
            self.control.load(logic_program)
        timer.phase("load")
        self.control.ground([("base", [])])

        # With a grounded program, we can run the solve.
        result = Result()
        models = []  # stable models if things go well
        cores = []  # unsatisfiable cores if they do not

        def on_model(model):
            models.append((model.cost, model.symbols(shown=True, terms=True)))

        solve_kwargs = {
            "assumptions": self.assumptions,
            "on_model": on_model,
            "on_core": cores.append,
        }

        if clingo_cffi:
            solve_kwargs["on_unsat"] = cores.append

        # Get the result object
        solve_result = self.control.solve(**solve_kwargs)
        timer.phase("solve")

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
            result.answers = {
                sym.name: [stringify(a) for a in sym.arguments] for sym in best_model
            }

        elif cores:
            symbols = dict((a.literal, a.symbol) for a in self.control.symbolic_atoms)
            for core in cores:
                core_symbols = []
                for atom in core:
                    sym = symbols[atom]
                    if sym.name == "missing_symbol":
                        sym = sym.arguments[0].string
                    core_symbols.append(sym)
                result.cores.append(core_symbols)

        if timers:
            timer.write()
            print()

        # statistics
        # pprint.pprint(self.control.statistics)

        return result


class ABICompatSolverSetup:
    """
    Class to set up and run an ABI Compatability Solver.
    """

    def generate_elf_symbols(self, corpora, prefix=""):
        """For each corpus, write out elf symbols as facts. Note that we are
        trying a more detailed approach with facts/atoms being named (e.g.,
        symbol_type instead of symbol_attr). We could also try a simpler
        approach:

        symbol_type("_ZN11MathLibrary10Arithmetic8MultiplyEdd", "STT_FUNC").
        symbol_binding("_ZN11MathLibrary10Arithmetic8MultiplyEdd", "STB_FUNC").
        symbol_attr("_ZN11MathLibrary10Arithmetic8MultiplyEdd", "STV_default").

        """
        # If we have a prefix, add a spacer
        prefix = "%s_" % prefix if prefix else ""

        for corpus in corpora:
            self.gen.h2("Corpus symbols: %s" % corpus.path)

            for symbol, meta in corpus.elfsymbols.items():

                # It begins with a NULL symbol, not sure it's useful
                if not symbol:
                    continue

                self.gen.fact(AspFunction(prefix + "symbol", args=[symbol]))
                self.gen.fact(
                    AspFunction(
                        prefix + "symbol_type", args=[corpus.path, symbol, meta["type"]]
                    )
                )
                self.gen.fact(
                    AspFunction(
                        prefix + "symbol_version",
                        args=[corpus.path, symbol, meta["version_info"]],
                    )
                )
                self.gen.fact(
                    AspFunction(
                        prefix + "symbol_binding",
                        args=[corpus.path, symbol, meta["binding"]],
                    )
                )
                self.gen.fact(
                    AspFunction(
                        prefix + "symbol_visibility",
                        args=[corpus.path, symbol, meta["visibility"]],
                    )
                )
                self.gen.fact(
                    AspFunction(
                        prefix + "symbol_definition",
                        args=[corpus.path, symbol, meta["defined"]],
                    )
                )

                # Might be redundant
                has = "has_%s" % prefix if prefix else "has_"
                self.gen.fact(AspFunction(has + "symbol", args=[corpus.path, symbol]))
                self.gen.fact(fn.has_symbol(corpus.path, symbol))

    def generate_needed(self, corpora):
        """
        Given a list of corpora, add needed libraries from dynamic tags.
        """
        for corpus in corpora:
            for needed in corpus.dynamic_tags.get("needed", []):
                self.gen.fact(fn.corpus_needs_library(corpus.path, needed))

    def generate_corpus_metadata(self, corpora, prefix=""):
        """Given a list of corpora, create a fact for each one. If we need them,
        we can add elfheaders here.
        """
        prefix = "%s_" % prefix if prefix else ""

        # Use the corpus path as a unique id (ok if binaries exist)
        # This would need to be changed if we don't have the binary handy
        for corpus in corpora:
            hdr = corpus.elfheader

            self.gen.h2("Corpus facts: %s" % corpus.path)

            self.gen.fact(fn.corpus(corpus.path))
            self.gen.fact(AspFunction(prefix + "corpus", args=[corpus.path]))
            self.gen.fact(
                AspFunction(
                    prefix + "corpus_name",
                    args=[corpus.path, os.path.basename(corpus.path)],
                )
            )

            # e_ident is ELF identification
            # https://docs.oracle.com/cd/E19683-01/816-1386/chapter6-35342/index.html
            # Note that we could update these to just be corpus_attr, but I'm
            # starting with testing a more detailed approach for now.

            # If the corpus has a soname:
            if corpus.soname:
                self.gen.fact(
                    AspFunction(
                        prefix + "corpus_soname", args=[corpus.path, corpus.soname]
                    )
                )

            # File class (also at elffile.elfclass or corpus.elfclass
            self.gen.fact(
                AspFunction(
                    prefix + "corpus_elf_class",
                    args=[corpus.path, hdr["e_ident"]["EI_CLASS"]],
                )
            )

            # Data encoding
            self.gen.fact(
                AspFunction(
                    prefix + "corpus_data_encoding",
                    args=[corpus.path, hdr["e_ident"]["EI_DATA"]],
                )
            )

            # File version
            self.gen.fact(
                AspFunction(
                    prefix + "corpus_file_version",
                    args=[corpus.path, hdr["e_ident"]["EI_VERSION"]],
                )
            )

            # Operating system / ABI Information
            self.gen.fact(
                AspFunction(
                    prefix + "corpus_elf_osabi",
                    args=[corpus.path, hdr["e_ident"]["EI_OSABI"]],
                )
            )

            # Abi Version
            self.gen.fact(
                AspFunction(
                    prefix + "corpus_abiversion",
                    args=[corpus.path, hdr["e_ident"]["EI_ABIVERSION"]],
                )
            )

            # e_type is the object file type
            self.gen.fact(
                AspFunction(
                    prefix + "corpus_elf_type", args=[corpus.path, hdr["e_type"]]
                )
            )

            # e_machine is the required architecture for the file
            self.gen.fact(
                AspFunction(
                    prefix + "corpus_elf_machine", args=[corpus.path, hdr["e_machine"]]
                )
            )

            # object file version
            self.gen.fact(
                AspFunction(
                    prefix + "corpus_elf_version", args=[corpus.path, hdr["e_version"]]
                )
            )

            # Not included (and we could add?)
            # virtual address where system transfers control, if no entry, will find 0
            # 'e_entry': 4160, <-- this is likely important

            # program header table's file offset (bytes), 0 if none
            # 'e_phoff': 64,

            # section header table's offset, also in bytes (0 if none)
            # 'e_shoff': 15672,

            # processor-specific flags associated with the file (0 if none)
            # 'e_flags': 0,

            # elf header size in bytes
            # 'e_ehsize': 64,

            # size in bytes of one entry in file's program header
            # 'e_phentsize': 56,

            # number of entries in program header table
            # 'e_phnum': 11,

            # section header's size in bytes
            # 'e_shentsize': 64,

            # number of entries in section header table
            # 'e_shnum': 30,

            # section header table index of entry associated with section name string table
            # 'e_shstrndx': 29

    def get_system_corpora(self, corpora):
        """
        Get a list of corpora for system corpora
        """
        ldd = utils.which("ldd").get("message")
        if not ldd:
            print("Cannot find ldd to detect system libraries, skipping.")
            return

        # Ensure we don't add a library twice
        seen = set([x.path for x in corpora])
        syscorpora = []
        for corpus in corpora:
            output = utils.run_command([ldd, corpus.path]).get("message", "")

            for line in output.split("\n"):
                if "=>" in line:
                    lib, path = line.split("=>")
                    lib = lib.strip()
                    path = path.strip().split(" ")[0]

                    # Don't add redundant entries
                    if path in seen:
                        continue
                    if os.path.exists(path) and lib in corpus.needed:
                        syscorpora.append(Corpus(path, name=lib))
                    seen.add(path)
        return syscorpora

    def single_setup(self, driver, corpus, system_libs=False):
        """
        Generate facts for a single library.
        """
        assert corpus.exists()

        # driver is used by all the functions below to add facts and
        # rules to generate an ASP program.
        self.gen = driver

        self.gen.h1("Corpus Facts")

        # Generate high level corpus metadata facts (e.g., header)
        self.generate_corpus_metadata([corpus])

        # Dynamic libraries that are needed
        self.generate_needed([corpus])

        # generate all elf symbols (might be able to make this smaller set)
        self.generate_elf_symbols([corpus])

        # Add system corpora to elf symbols
        if system_libs:
            self.generate_elf_symbols(self.get_system_corpora([corpus]))

    def compat_setup(self, driver, corpora):
        """
        Generate an ASP program with relevant constraints for a binary
        and a library, for which we have been provided their corpora.

        This calls methods on the solve driver to set up the problem with
        facts and rules from both corpora, and rules that determine ABI
        compatibility.

        Arguments:
            corpora: [corpusA, corpusB, corpusC]
            corpusA (corpus.Corpus): the first corpus for the binary
            corpusB (corpus.Corpus): the corpus for the library that works
            corpusB (corpus.Corpus): the corpus for the library that we test

        """
        # preliminary checks
        for corpus in corpora:
            assert corpus.exists()

        binary, working, contender = corpora
        corpora = [binary, contender]

        # driver is used by all the functions below to add facts and
        # rules to generate an ASP program.
        self.gen = driver

        self.gen.h1("Corpus Facts")

        self.gen.fact(fn.is_main(binary.path))
        self.gen.fact(fn.is_library(contender.path))
        self.gen.fact(fn.is_needed(working.path))

        # Generate high level corpus metadata facts (e.g., header)
        self.generate_corpus_metadata(corpora)
        self.generate_corpus_metadata([working], prefix="needed")

        # Dynamic libraries that are needed
        self.generate_needed(corpora)

        # generate all elf symbols (might be able to make this smaller set)
        self.generate_elf_symbols(corpora)

        # Generate the same for the known working library, but with a prefix
        self.generate_elf_symbols([working], prefix="needed")

        # Add system corpora to elf symbols
        self.generate_elf_symbols(self.get_system_corpora(corpora))
