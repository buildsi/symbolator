# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import os

here = os.path.abspath(os.path.dirname(__file__))


def get_facts(name):
    filename = os.path.join(here, name)
    if os.path.exists(filename):
        return filename
