import threading
from rich.console import Console

console = Console()


class AppState:
    def __init__(self, plugin_updater, plugin_remover):
        self.scroll_offset = 0
        self.current_selection = 0
        self.current_tab = "Home"
        self.mode = "normal"
        self.update_selected = 0
        self.update_data = []
        self.update_progress = {}
        self.checking_updates = False
        self.remove_selected = 0
        self.marked_for_removal = set()
        self.removing_progress = {}
        self.remove_data = []
        self._app_ref = None
        self.install_selected = 0
        self.install_data = []
        self.installing_progress = {}
        self.plugin_remover = plugin_remover
        self.plugin_updater = plugin_updater

    def refresh_updates(self):
        if not self.checking_updates:
            self.checking_updates = True
            self.update_data = []
            self.update_progress = {}
            thread = threading.Thread(target=self._check_updates_async, daemon=True)
            thread.start()

    def refresh_remove_data(self):
        """Refresh the list of installed plugins for removal tab"""
        self.remove_data = self.plugin_remover.get_installed_plugins()

    def remove_uninstalled_plugins_from_updates(self, uninstalled_plugin_names):
        """Remove uninstalled plugins from the updates list"""
        uninstalled_names_set = set(uninstalled_plugin_names)

        # Filter out uninstalled plugins from update data
        self.update_data = [
            plugin
            for plugin in self.update_data
            if plugin["name"] not in uninstalled_names_set
        ]

        # Clean up update progress for uninstalled plugins
        for name in uninstalled_plugin_names:
            self.update_progress.pop(name, None)

        # Adjust update selection if it's now out of bounds
        if self.update_selected >= len(self.update_data):
            self.update_selected = max(0, len(self.update_data) - 1)

    def _check_updates_async(self):
        try:
            updates = self.plugin_updater.check_for_updates()
            self.update_data = updates
        except Exception as e:
            self.update_data = []
            console.log(f"[ERROR] Error checking updates: {e}")
        finally:
            self.checking_updates = False
            if self._app_ref:
                self._app_ref.call_from_thread(self._app_ref.rich_display.refresh)

    def update_progress_callback(self, plugin_name, progress):
        self.update_progress[plugin_name] = progress
        for plugin in self.update_data:
            if plugin["name"] == plugin_name:
                plugin["progress"] = progress
                break
        if self._app_ref:
            self._app_ref.call_from_thread(self._app_ref.rich_display.refresh)

    def remove_progress_callback(self, plugin_name, progress):
        """Progress callback for plugin removal"""
        self.removing_progress[plugin_name] = progress
        if self._app_ref:
            self._app_ref.call_from_thread(self._app_ref.rich_display.refresh)

    def install_progress_callback(self, plugin_name, progress):
        """Progress callback for plugin installation"""
        self.installing_progress[plugin_name] = progress
        for plugin in self.install_data:
            if plugin["name"] == plugin_name:
                plugin["progress"] = progress
                break
        if self._app_ref:
            self._app_ref.call_from_thread(self._app_ref.rich_display.refresh)

    def bind_app(self, app):
        self._app_ref = app
