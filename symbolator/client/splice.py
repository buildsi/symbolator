# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from symbolator.corpus import Corpus, JsonCorpusLoader
from symbolator.asp import PyclingoDriver, ABIGlobalSolverSetup
from symbolator.facts import get_facts
import json
import os
import sys


def splice(args, parser, extra, subparser):
    """

    Arguments:
        binary (str): path to a binary to assess for compataibility
        splice ([str]): list of libs to splice in.
    """
    driver = PyclingoDriver()
    if args.dump and not args.json:
        driver.out = sys.stdout

    args.splice = args.splice or []

    # Prepare splices
    lookup = {}
    for sp in args.splice:
        if "=" in sp:
            src, dest = sp.split("=")
        else:
            src, dest = sp, sp

        # The dst (the library to splice) must exist
        if not os.path.exists(dest):
            sys.exit("Splice target %s does not exist." % dest)
        lookup[src] = dest

    # We are required to have three existing libraries
    paths = args.binary + list(lookup.values())

    # Whether doing a splice or regular, we are looking for missing symbols
    logic_program = "missing_symbols.lp"

    for path in paths:
        if not os.path.exists(path):
            sys.exit("%s does not exist." % path)

    if len(paths) == 0:
        sys.exit("You must provide: <binary> [splice1]...[spliceN]")

    # No pretty printing if we are exporting json
    if not args.json:
        print("% " + "binary : %s" % args.binary[0])
        for src, dest in lookup.items():
            print("% " + "splice : %s->%s" % (src, dest))

    # Spliced libraries will be added as corpora here
    corpora = []
    for path in paths:
        corpora.append(Corpus(path))

    setup = ABIGlobalSolverSetup()

    # The order should be binary | working library | contender library
    result = driver.solve(
        setup,
        corpora,
        dump=args.dump,
        logic_programs=get_facts(logic_program),
        facts_only=False,
        splices=lookup,
    )

    missing_symbols = result.answers.get("missing_symbols")

    if missing_symbols:
        if not args.json:
            print("\nMissing Symbols:")

        # Generate lookup by library
        missing = {}
        for item in missing_symbols:
            if item[0] not in missing:
                missing[item[0]] = set()
            missing[item[0]].add(item[1])

        # Needs to be list to dump
        for lib, symbols in missing.items():
            missing[lib] = list(symbols)

        if not args.json:
            for lib, symbols in missing.items():
                print("\n=> %s" % lib)
                for symbol in symbols:
                    print("   %s" % symbol)
        else:
            print(json.dumps(missing, indent=4))
    else:
        if args.json:
            print("{}")
        else:
            print("\nThere are no missing symbols.")


def jsonsplice(args, parser, extra, subparser):
    driver = PyclingoDriver()
    if args.dump and not args.json:
        driver.out = sys.stdout

    args.splice = args.splice or []

    # Prepare splices
    lookup = {}
    for sp in args.splice:
        if "=" in sp:
            src, dest = sp.split("=")
        else:
            src, dest = sp, sp

        # The dst (the library to splice) must exist
        if not os.path.exists(dest):
            sys.exit("Splice target %s does not exist." % dest)
        lookup[src] = dest

    # We are required to have three existing libraries
    paths = args.binary + list(lookup.values())

    # Whether doing a splice or regular, we are looking for missing symbols
    logic_program = "missing_symbols.lp"

    for path in paths:
        if not os.path.exists(path):
            sys.exit("%s does not exist." % path)

    if len(paths) == 0:
        sys.exit("You must provide: <binary> [splice1]...[spliceN]")

    # No pretty printing if we are exporting json
    if not args.json:
        print("% " + "binary : %s" % args.binary[0])
        for src, dest in lookup.items():
            print("% " + "splice : %s->%s" % (src, dest))

    # Spliced libraries will be added as corpora here
    loader = JsonCorpusLoader()
    loader.load(args.binary[0])
    corpora = loader.get_lookup()

    # Now load the splices separately, and select what we need
    for lib, jsonfile in lookup.items():
        splice_loader = JsonCorpusLoader()
        splice_loader.load(jsonfile)
        splices = splice_loader.get_lookup()

        # If we have the library in corpora, delete it, add spliced libraries
        if lib in corpora:
            del corpora[lib]
            for newlib, newcorp in splices.items():
                corpora[newlib] = newcorp

    setup = ABIGlobalSolverSetup()

    # The order should be binary | working library | contender library
    result = driver.solve(
        setup,
        list(corpora.values()),
        dump=args.dump,
        logic_programs=get_facts(logic_program),
        facts_only=False,
        # Loading from json already includes system libs
        system_libs=False,
    )

    missing_symbols = result.answers.get("missing_symbols")

    if missing_symbols:
        if not args.json:
            print("\nMissing Symbols:")

        # Generate lookup by library
        missing = {}
        for item in missing_symbols:
            if item[0] not in missing:
                missing[item[0]] = set()
            missing[item[0]].add(item[1])

        # Needs to be list to dump
        for lib, symbols in missing.items():
            missing[lib] = list(symbols)

        if not args.json:
            for lib, symbols in missing.items():
                print("\n=> %s" % lib)
                for symbol in symbols:
                    print("   %s" % symbol)
        else:
            print(json.dumps(missing, indent=4))
    else:
        if args.json:
            print("{}")
        else:
            print("\nThere are no missing symbols.")
