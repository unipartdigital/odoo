"""
Launcher is a model for starting threads (or possibly other things) when the
server starts.

Models can register functions to be run as threads by calling `register_method`
from their `_register_hook` method.
"""

import functools
import logging
import threading

from odoo import models


_logger = logging.getLogger(__name__)

# This object is used to notify launched threads of a pending system shutdown
_sentinel = threading.Event()


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
            t = threading.Thread(target=functools.partial(launchable, _sentinel))
            # Ensure db name is output in logs.
            t.dbname = getattr(threading.currentThread(), "dbname", "?")
            t.start()
        # Returning None protects against xmlrpc execute_kw calls launching
        # threads as a DOS.
        return None

    def notify_shutdown(self):
        """
        Notify threads of system shutdown.

        Notified threads should act to make themselves joinable.
        """
        _sentinel.set()
        return
