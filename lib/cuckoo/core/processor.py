# Copyright (C) 2010-2012 Cuckoo Sandbox Developers.
# This file is part of Cuckoo Sandbox - http://www.cuckoosandbox.org
# See the file 'docs/LICENSE' for copying permission.

import logging
import pkgutil

from lib.cuckoo.common.config import Config
from lib.cuckoo.common.abstracts import Processing, Signature
import modules.processing as processing
import modules.signatures as signatures

log = logging.getLogger(__name__)

class Processor:
    """Analysis processor."""

    def __init__(self, analysis_path):
        """@param analysis_path: analysis folder path."""
        self.analysis_path = analysis_path
        self.__populate(processing)
        self.__populate(signatures)

    def __populate(self, modules):
        """Load modules.
        @param modules: modules.
        """
        prefix = modules.__name__ + "."
        for loader, name, ispkg in pkgutil.iter_modules(modules.__path__, prefix):
            if ispkg:
                continue

            __import__(name, globals(), locals(), ["dummy"], -1)

    def run(self):
        """Run all processors.
        @return: processing results.
        """
        results = {}
        Processing()

        for module in Processing.__subclasses__():
            current = module()
            current.set_path(self.analysis_path)
            current.cfg = Config(current.conf_path)

            try:
                results[current.key] = current.run()
                log.debug("Executed processing module \"%s\"" % current.__class__.__name__)
            except NotImplementedError:
                continue

        Signature()
        sigs = []

        for signature in Signature.__subclasses__():
            current = signature()

            if not current.enabled:
                continue

            try:
                if current.run(results):
                    matched = {"name" : current.name,
                               "description" : current.description,
                               "severity" : current.severity,
                               "references" : current.references,
                               "data" : current.data,
                               "alert" : current.alert}
                    sigs.append(matched)
                    log.debug("Analysis at \"%s\" matched signature \"%s\"" % (self.analysis_path, current.name))
            except NotImplementedError:
                continue

        results["signatures"] = sigs

        return results
