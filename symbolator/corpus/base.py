# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

"""A Corpus object is used to extract Dwarf and ELF symbols from a library.
We exclude most of the Dwarf Information Entries to expose a reduced set.
Entries can be added as they are needed.
"""

import sys
import os


class CorpusBase:
    def __init__(self, filename, name=None, uid=None):

        if not os.path.exists(filename):
            sys.exit("%s does not exist." % filename)

        self.elfheader = {}
        self.basename = os.path.basename(filename)

        self.name = name
        self.uid = uid
        self.symbols = {}
        self.path = filename
        self.basename = None
        self.dynamic_tags = {}
        self.architecture = None
        self._soname = None
        self.read_corpus()

    def read_corpus(self):
        raise NotImplementedError

    def __str__(self):
        return "[Corpus:%s]" % self.path

    def __repr__(self):
        return str(self)

    def exists(self):
        return self.path is not None and os.path.exists(self.path)

    @property
    def soname(self):
        return self.dynamic_tags.get("soname")

    @property
    def needed(self):
        return self.dynamic_tags.get("needed", [])

    @property
    def runpath(self):
        return self.dynamic_tags.get("runpath")

    @property
    def rpath(self):
        return self.dynamic_tags.get("rpath")
