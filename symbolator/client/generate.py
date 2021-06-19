# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from symbolator.corpus import Corpus
from symbolator.asp import PyclingoDriver, ABICompatSolverSetup
import json
import io

# Functions intended to be called by external clients


def generate(args, parser, extra, subparser):
    """
    A single function to print facts for one or more corpora.
    """
    setup = ABICompatSolverSetup()
    corpus = Corpus(args.binary)

    # Json output
    if args.json:
        result = setup.get_json(corpus, system_libs=args.system_libs)
        print(json.dumps(result, indent=4))

    # Asp output
    else:
        # Get output via StringIO
        out = io.StringIO()
        driver = PyclingoDriver(asp=out)
        driver.solve(setup, [corpus], facts_only=True, system_libs=args.system_libs)
        asp = out.getvalue()
        out.close()
        print(asp)
