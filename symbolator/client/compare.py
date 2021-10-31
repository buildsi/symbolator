# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from symbolator.corpus import Corpus
from symbolator.asp import PyclingoDriver, ABICompareSolverSetup
from symbolator.facts import get_facts
import json
import os
import sys


def compare_libs(args, parser, extra, subparser):
    """
    Given two libraries (same but different versions) compare across symbols.
    If Smeagle output is provided, we do a more detailed comparison.

    Arguments:
        libraryA (str): path to the first library
        libraryB (str): path to the second library
        json (bool): if the input is smeagle json
    """
    driver = PyclingoDriver()
    if not args.json:
        driver.out = sys.stdout

    # We are required to have three existing libraries
    for path in args.libs:
        if not os.path.exists(path):
            sys.exit("%s does not exist." % path)

    if len(args.libs) != 2:
        sys.exit("You must provide: <first-lib> <second-lib>")

    if not args.json:
        print("% " + "first library : %s" % args.libs[0])
        print("% " + "second library: %s" % args.libs[1])

    corpora = []
    for path in args.libs:
        corpora.append(Corpus(path))
    setup = ABICompareSolverSetup()

    # The order should be binary | working library | contender library
    result = driver.solve(
        setup,
        corpora,
        dump=not args.json,
        logic_programs=get_facts("compare_libs.lp"),
        facts_only=False,
    )

    print(json.dumps(result.answers, indent=4))
