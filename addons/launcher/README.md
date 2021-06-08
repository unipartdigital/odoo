# Launcher Module

This module provides one model, `Launcher`.

`Launcher` will start a thread for each registered function when the HTTP server starts, immediately after the cron thread is spawned.

Functions are registered through `Launcher.register_method`.  Generally, models will perform the registration in their `_register_hook` method.  In any case, functions must be registered before the launch method is called.
