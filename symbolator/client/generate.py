# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from symbolator.corpus import Corpus
from symbolator.asp import PyclingoDriver, ABICompatSolverSetup


# Functions intended to be called by external clients


def generate(args, parser, extra, subparser):
    """
    A single function to print facts for one or more corpora.
    """
    setup = ABICompatSolverSetup()
    driver = PyclingoDriver()
    corpora = [Corpus(args.binary)]
    return driver.solve(setup, corpora, facts_only=True, system_libs=args.system_libs)
