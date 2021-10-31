# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from symbolator.corpus import Corpus
from symbolator.asp import PyclingoDriver, ABICompatSolverSetup
from symbolator.facts import get_facts
import json
import os
import sys


def is_compatible(args, parser, extra, subparser):
    """
    Given three libraries (we call one a main binary and the other a library
    that works, and the second one that we want to link with it), determine
    if the second library is compatible with the binary. This wrapper function,
    in requiring the three named arguments for binary, libraryA and libraryB,
    enforces that all three are provided (and in the correct order).
    If the functions for the solver are used outside this context, make sure
    that you provide them in the correct order.

    Arguments:
        binary (str): path to a binary to assess for compataibility
        libraryA (str): path to a library that is known to work
        libraryB (str): a second library to assess for compatability.
        dump (tuple): what to dump
        models (int): number of models to search (default: 0)
    """
    driver = PyclingoDriver()
    if args.dump:
        driver.out = sys.stdout

    # We are required to have three existing libraries
    paths = [args.binary] + args.libs
    for path in paths:
        if not os.path.exists(path):
            sys.exit("%s does not exist." % path)

    if len(paths) != 3:
        sys.exit("You must provide: <binary> <working-lib> <contender-lib>")

    # No pretty printing if we are exporting json
    if not args.json:
        print("% " + "binary           : %s" % args.binary)
        print("% " + "working library  : %s" % args.libs[0])
        print("% " + "contender library: %s" % args.libs[1])

    corpora = []
    for path in paths:
        corpora.append(Corpus(path))
    setup = ABICompatSolverSetup()

    # The order should be binary | working library | contender library
    result = driver.solve(
        setup,
        corpora,
        dump=args.dump or not args.json,
        logic_programs=get_facts("is_compatible.lp"),
        facts_only=args.dump,
    )

    # Don't print any more if we are just dumping
    if args.dump:
        return

    if args.json:

        missing_symbols = 0
        if (
            "count_missing_symbols" in result.answers
            and result.answers["count_missing_symbols"]
        ):
            missing_symbols = result.answers["count_missing_symbols"][0]
        data = {
            "binary": corpora[0].path,
            "library_working": corpora[1].path,
            "library_contender": corpora[2].path,
            "missing_symbols": result.answers.get("missing_symbols", []),
            "count_missing_symbols": missing_symbols,
        }
        print(json.dumps(data, indent=4))
    else:
        print("Missing Symbol Count: %s" % result.answers["count_missing_symbols"][0])
        print("Missing Symbols:\n%s" % result.answers["missing_symbols"])
