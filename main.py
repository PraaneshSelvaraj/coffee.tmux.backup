import os

from core import (
    PluginLoader,
    PluginSourcer,
    PluginUpdater,
    PluginInstaller,
    PluginRemover,
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
print(plugins)

plugin_installer = PluginInstaller(
    plugins, COFFEE_INSTALLED_PLUGINS_DIR, TMUX_CONFIG_DIR
)
plugin_installer.install_all_plugins()

plugin_sourcer = PluginSourcer()
plugin_sourcer.source_enabled_plugins()
# plugin_sourcer.activate_plugin("spotify.demo")

# plugin_updater = PluginUpdater(COFFEE_INSTALLED_PLUGINS_DIR)
# updates = plugin_updater.check_for_updates()
# print("UDPATES : ")
# print(updates)
# plugin_updater.auto_update_all()
# plugin_updater.update_plugin(updates[0])

# plugin_remover = PluginRemover(COFFEE_INSTALLED_PLUGINS_DIR)
# plugin_remover.remove_plugin("spotify.demo")

# plugin_sourcer = PluginSourcer()
# plugin_sourcer.source_enabled_plugins()
