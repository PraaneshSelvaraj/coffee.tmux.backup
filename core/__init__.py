"""
coffee.tmux
Author: Praanesh S

Modules:
- pluginInstaller: Handles the installation of plugins.
- pluginLoader: Manages loading of plugins.
- pluginSourcer: Handles sourcing and configuration.
- pluginUpdater: Manages plugin updates.
- pluginRemover: Manages plugin removals.
"""

from .pluginSourcer import PluginSourcer
from .pluginInstaller import PluginInstaller
from .pluginRemover import PluginRemover
from .pluginUpdater import PluginUpdater
from .pluginLoader import PluginLoader
from . import lock_file_manager

__all__ = [
    "PluginSourcer",
    "PluginInstaller",
    "PluginRemover",
    "PluginUpdater",
    "PluginLoader",
    "lock_file_manager",
]
