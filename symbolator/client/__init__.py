#!/usr/bin/env python

# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import symbolator
import argparse
import sys
import os


def get_parser():
    parser = argparse.ArgumentParser(
        description="Symbolator: assess compatibility based on symbols.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "--version",
        dest="version",
        help="suppress additional output.",
        default=False,
        action="store_true",
    )

    description = "actions for symbolator"
    subparsers = parser.add_subparsers(
        help="symbolator actions",
        title="actions",
        description=description,
        dest="command",
    )

    # print version and exit
    subparsers.add_parser("version", help="show software version")

    compare = subparsers.add_parser(
        "compare",
        help="Compare a known working binary and library to a contender library",
    )
    compare.add_argument("binary", help="Main binary of interest")
    compare.add_argument(
        "libs", help="Working and contender library, in that order", nargs=2
    )
    compare.add_argument(
        "--dump",
        dest="dump",
        help="Dump asp to stdout instead",
        default=False,
        action="store_true",
    )

    # Just generate facts to the screen
    generate = subparsers.add_parser(
        "generate", help="Dump symbols as facts to the terminal."
    )
    generate.add_argument("binary", help="Main binary of interest")
    generate.add_argument(
        "--system-libs",
        dest="system_libs",
        help="Include facts for linked system libs",
        default=False,
        action="store_true",
    )

    return parser


def run():
    parser = get_parser()

    def help(return_code=0):
        """print help, including the software version and active client
        and exit with return code.
        """
        version = symbolator.__version__

        print("\nSymbolator v%s" % version)
        parser.print_help()
        sys.exit(return_code)

    # If the user didn't provide any arguments, show the full help
    if len(sys.argv) == 1:
        help()

    # If an error occurs while parsing the arguments, the interpreter will exit with value 2
    args, extra = parser.parse_known_args()

    # Show the version and exit
    if args.command == "version" or args.version:
        print(symbolator.__version__)
        sys.exit(0)

    # retrieve subparser (with help) from parser
    helper = None
    subparsers_actions = [
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    ]
    for subparsers_action in subparsers_actions:
        for choice, subparser in subparsers_action.choices.items():
            if choice == args.command:
                helper = subparser
                break

    if args.command == "compare":
        from .compare import is_compatible as main
    elif args.command == "generate":
        from .generate import generate as main

    # Pass on to the correct parser
    return_code = 0
    try:
        main(args=args, parser=parser, extra=extra, subparser=helper)
        sys.exit(return_code)
    except UnboundLocalError:
        return_code = 1

    help(return_code)


if __name__ == "__main__":
    run()
