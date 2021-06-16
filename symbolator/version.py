# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

__version__ = "0.0.1"
AUTHOR = "Vanessa Sochat"
AUTHOR_EMAIL = "vsoch@users.noreply.github.com"
NAME = "symbolator-python"
PACKAGE_URL = "https://github.com/buildsi/symbolator"
KEYWORDS = "abi, compatibility, symbols"
DESCRIPTION = "Assess compatibility of two binaries based on symbols."
LICENSE = "LICENSE"

################################################################################
# Global requirements

INSTALL_REQUIRES = (
    ("pyelftools", {"min_version": None}),
    ("clingo", {"min_version": None}),
    ("six", {"min_version": None}),
)

TESTS_REQUIRES = (("pytest", {"min_version": "4.6.2"}),)

################################################################################
# Submodule Requirements (versions that include database)

INSTALL_REQUIRES_ALL = INSTALL_REQUIRES + TESTS_REQUIRES
