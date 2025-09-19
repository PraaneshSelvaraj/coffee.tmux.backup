#!/usr/bin/env python3
"""
Coffee TUI entry point for tmux popup
"""
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from ui.app import PluginManagerApp
from ui.constants import PLUGINS_DIR
from core import PluginRemover, PluginUpdater


def main():
    plugin_remover = PluginRemover(PLUGINS_DIR)
    plugin_updater = PluginUpdater(PLUGINS_DIR)
    app = PluginManagerApp(plugin_updater, plugin_remover)
    app.run()


if __name__ == "__main__":
    main()
