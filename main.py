import os
from core import (
    PluginLoader,
    PluginInstaller,
    PluginSourcer,
)

TMUX_CONFIG_DIR = os.path.expanduser("~/.config/tmux/")
COFFEE_DIR = os.path.expanduser("~/.tmux/coffee")
COFFEE_PLUGINS_LIST_DIR = os.path.join(TMUX_CONFIG_DIR, "coffee/plugins")
COFFEE_INSTALLED_PLUGINS_DIR = os.path.join(COFFEE_DIR, "plugins")
LOCK_FILE_PATH = os.path.join(COFFEE_DIR, "caffeine-lock.json")

os.makedirs(COFFEE_INSTALLED_PLUGINS_DIR, exist_ok=True)
os.makedirs(COFFEE_DIR, exist_ok=True)
os.makedirs(COFFEE_PLUGINS_LIST_DIR, exist_ok=True)

plugin_loader = PluginLoader(COFFEE_PLUGINS_LIST_DIR)
plugins = plugin_loader.load_plugins()

plugin_installer = PluginInstaller(
    plugins,
    COFFEE_INSTALLED_PLUGINS_DIR,
    TMUX_CONFIG_DIR,
)

plugin_installer.install_all_plugins()


plugin_sourcer = PluginSourcer()
plugin_sourcer.source_enabled_plugins()
