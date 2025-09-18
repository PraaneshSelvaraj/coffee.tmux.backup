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
