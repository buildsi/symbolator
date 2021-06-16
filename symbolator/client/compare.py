# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from symbolator.corpus import Corpus
from symbolator.asp import PyclingoDriver, ABICompatSolverSetup
from symbolator.facts import get_facts
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
        dump=args.dump,
        logic_programs=get_facts("is_compatible.lp"),
        facts_only=args.dump,
    )

    # Don't print any more if we are just dumping
    if args.dump:
        return

    print("Missing Symbol Count: %s" % result.answers["count_missing_symbols"][0])
    print("Missing Symbols:\n%s" % result.answers["missing_symbols"])
