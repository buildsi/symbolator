# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

# from symbolator.corpus import Corpus
# from symbolator.asp import PyclingoDriver, ABICompatSolverSetup
# from symbolator.facts import get_facts

from symbolator.smeagle import SmeagleRunner
import json
import os
import sys


def stability_test(args, parser, extra, subparser):
    """
    Run a stability test with Smeagle.
    """
    smeagle = SmeagleRunner()

    # Load the libraries
    for lib in args.libs:
        smeagle.load(lib)

    # Stability test between two libraries
    smeagle.stability_test(detail=args.detail)
