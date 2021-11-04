# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

"""A Corpus object is used to extract Dwarf and ELF symbols from a library.
We exclude most of the Dwarf Information Entries to expose a reduced set.
Entries can be added as they are needed.
"""

from symbolator.utils import read_json
import sys
import os


class CorpusBase:
    def __init__(self, filename, name=None, uid=None, **kwargs):

        must_exist = kwargs.get("must_exist", True)
        if not os.path.exists(filename) and must_exist:
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
        self.kwargs = kwargs
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


class JsonCorpusLoader:
    def __init__(self):
        self.seen = set()
        self.corpora = []

    def get_lookup(self, key="name"):
        """
        Return a corpus lookup (by key)
        """
        # Create a lookup we can easily sub a library in for
        lookup = {}
        for corpus in self.corpora:
            field = getattr(corpus, key)
            if field in lookup:
                print("Warning: %s is seen more than once in lookup." % field)
            lookup[field] = corpus
        return lookup

    def load(self, content):
        """
        Given a json dump of a corpus (and system libraries) load into corpora
        """
        # If it isn't already loaded!
        if not isinstance(content, list):
            if not os.path.exists(content):
                sys.exit("%s for loading corpora does not exist." % content)
            content = read_json(content)

        for entry in content:
            if "corpus" not in entry:
                sys.exit("corpus key missing at top level!")
            corpus = entry["corpus"]
            filename = corpus["metadata"]["path"]
            name = corpus["metadata"]["corpus_name"]

            # It's reasonable we could have a corpus seen twice
            if filename not in self.seen:
                self.corpora.append(
                    JsonCorpus(filename, name, loaded=entry["corpus"], must_exist=False)
                )
                self.seen.add(filename)


class JsonCorpus(CorpusBase):
    """
    Generate an ABI corpus from Json input
    """

    def read_corpus(self):
        """
        Read the entire json corpus
        """
        loaded = self.kwargs.get("loaded")
        if not loaded:
            sys.exit("Cannot create a json corpus without loaded content.")

        self.metadata = loaded.get("metadata", {})
        self.symbols = loaded.get("symbols", {})
        self.elfheader = loaded.get("header", {})
        self.dynamic_tags = loaded.get("dynamic_tags", {})
        self.architecture = self.metadata.get("corpus_elf_machine")
        self.elfclass = self.metadata.get("corpus_elf_class")
