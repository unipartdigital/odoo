"""
Launcher is a model for starting threads (or possibly other things) when the
server starts.

Models can register functions to be run as threads by calling `register_method`
from their `_register_hook` method.
"""

import logging
import threading

from odoo import models


_logger = logging.getLogger(__name__)


class Launcher(models.TransientModel):
    """A model that starts a thread for each of its records."""

    _description = "Launches threads at server start time."
    _name = "launcher.launcher"

    _registered = []

    @classmethod
    def register_method(cls, method_obj):
        """
        Register methods to be called as threads.

        Subclasses should call this method from their _register_hook method.
        """
        # Ideally we would use __init_subclass__ for this, but it doesn't seem
        # to play well with Odoo's way of initialising subclasses.
        cls._registered.append(method_obj)

    def launch(self):
        """Launches a thread for each registered callable."""
        for i, launchable in enumerate(self._registered):
            t = threading.Thread(target=launchable)
            # FIXME?  Non-daemon threads would be nice here so that we could clean up
            # open database connections etc on shutdown.  However I couldn't
            # get them to join at shutdown time, so have used daemon threads
            # instead.
            # If we can find a way to get threads to join reliably, and without
            # too much complexity, we should implement it.
            t.daemon = True
            t.start()
        # Returning None protects against xmlrpc execute_kw calls launching
        # threads as a DOS.
        return None
