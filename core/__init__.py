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

from .pluginInstaller import PluginInstaller
from .pluginLoader import PluginLoader
from .pluginSourcer import PluginSourcer
from .pluginUpdater import PluginUpdater
from .pluginRemover import PluginRemover
