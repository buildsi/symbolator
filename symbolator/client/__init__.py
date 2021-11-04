#!/usr/bin/env python

# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import symbolator
import argparse
import sys


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

    # Splice a binary and find all libraries
    splice = subparsers.add_parser(
        "splice",
        help="Assess the entire space of libs for a binary, optionally splicing in a new library.",
    )

    # Jsonsplice is similar, but from input json instead
    jsonsplice = subparsers.add_parser(
        "jsonsplice",
        help="Do a splice from generate (json) output.",
    )

    for command in [splice, jsonsplice]:
        command.add_argument(
            "binary", help="Single binary to find and assess libs for.", nargs=1
        )

        command.add_argument(
            "--splice", "-s", help="Optional libraries to splice in.", action="append"
        )
        command.add_argument(
            "--dump",
            dest="dump",
            help="Dump asp to stdout instead",
            default=False,
            action="store_true",
        )

    # Stability test using smeagle output
    stability = subparsers.add_parser(
        "stability-test", help="Run a stability test using Smeagle facts."
    )

    stability.add_argument(
        "libs", help="Working and contender library, in that order", nargs=2
    )
    stability.add_argument(
        "--detail", default=False, action="store_true", help="Show detailed results."
    )

    # Compare two library elf symbols
    compare = subparsers.add_parser(
        "compare", help="Compare symbols between two libraries."
    )
    compare.add_argument(
        "libs", help="Two libraries (same but different versions) to compare", nargs=2
    )

    # Assess compatibility
    compat = subparsers.add_parser(
        "compat",
        help="Assess compatibility of a known working binary and library to a contender library",
    )
    compat.add_argument("binary", help="Main binary of interest")
    compat.add_argument(
        "libs", help="Working and contender library, in that order", nargs=2
    )
    compat.add_argument(
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
    generate.add_argument(
        "--globals",
        dest="globals_only",
        help="Only include global symbols",
        default=False,
        action="store_true",
    )

    # Either command can accept json
    for command in [generate, compat, compare, splice, jsonsplice]:
        command.add_argument(
            "--json",
            dest="json",
            help="If generating facts, dump as json instead of ASP.",
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

    if args.command == "compat":
        from .compat import is_compatible as main
    elif args.command == "compare":
        from .compare import compare_libs as main
    elif args.command == "generate":
        from .generate import generate as main
    elif args.command == "jsonsplice":
        from .splice import jsonsplice as main
    elif args.command == "splice":
        from .splice import splice as main
    elif args.command == "stability-test":
        from .smeagle import stability_test as main

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
