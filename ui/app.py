from textual.app import App, ComposeResult
from textual.binding import Binding
from textual import work
from .state import AppState
from .widgets.rich_display import RichDisplay
from .utils import toggle_plugin
from .tabs.install import InstallTab
from .tabs.update import UpdateTab
from .tabs.home import HomeTab
from core import PluginInstaller
from rich.console import Console
from .constants import *

console = Console()


class PluginManagerApp(App):
    CSS = """RichDisplay { background: #1a1b26; width:100%; height:100%; }"""
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("H", "switch_to_home", "Home", show=False),
        Binding("I", "switch_to_install", "Install", show=False),
        Binding("U", "switch_to_update", "Updates", show=False),
        Binding("R", "switch_to_remove", "Remove", show=False),
        # Movement
        Binding("j", "move_down", "Down", show=False),
        Binding("k", "move_up", "Up", show=False),
        Binding("down", "move_down", "Down", show=False),
        Binding("up", "move_up", "Up", show=False),
        # Actions
        Binding("space", "toggle_plugin_or_mark", "Toggle/Mark", show=False),
        Binding("/", "enter_search_mode", "Search", show=False),
        Binding("escape", "exit_search_mode", "Exit Search", show=False),
        # Updates
        Binding("c", "check_updates", "Check Updates", show=False),
        Binding("ctrl+u", "update_all", "Update All", show=False),
        Binding("u", "update_marked", "Update Marked", show=False),
        # Removal
        Binding("r", "remove_marked", "Remove Marked", show=False),
        Binding("ctrl+r", "refresh_remove_list", "Refresh Remove List", show=False),
        # Installation
        Binding("i", "install_marked", "Install Marked", show=False),
        Binding("ctrl+a", "install_all", "Install All", show=False),
    ]

    def __init__(self, plugin_updater, plugin_remover):
        super().__init__()
        self.plugin_updater = plugin_updater
        self.plugin_remover = plugin_remover
        self.app_state = AppState(plugin_updater, plugin_remover)
        self.app_state.bind_app(self)
        self.rich_display = None

    def compose(self) -> ComposeResult:
        self.rich_display = RichDisplay(self.app_state)
        yield self.rich_display

    def action_switch_to_home(self):
        self.app_state.current_tab = "Home"
        self.rich_display.refresh()

    def action_switch_to_install(self):
        self.app_state.current_tab = "Install"
        # Reset selection when switching tabs
        self.app_state.install_selected = 0
        # Populate install data when switching to tab
        install_tab = InstallTab()
        self.app_state.install_data = install_tab._get_installable_plugins(
            self.app_state
        )
        self.rich_display.refresh()

    def action_switch_to_update(self):
        self.app_state.current_tab = "Update"
        if not self.app_state.update_data:
            self.app_state.refresh_updates()
        self.rich_display.refresh()

    def action_switch_to_remove(self):
        self.app_state.current_tab = "Remove"
        # Refresh remove data when switching to remove tab
        if not self.app_state.remove_data:
            self.app_state.refresh_remove_data()
        self.rich_display.refresh()

    def action_refresh_remove_list(self):
        """Refresh the list of installed plugins in remove tab"""
        if self.app_state.current_tab == "Remove":
            self.app_state.refresh_remove_data()
            self.app_state.remove_selected = 0  # Reset selection
            self.app_state.marked_for_removal.clear()  # Clear marked plugins
            self.notify("Plugin list refreshed")
        self.rich_display.refresh()

    def action_move_down(self):
        if self.app_state.current_tab == "Home" and self.app_state.mode == "normal":
            display_list = HomeTab().get_display_list()
            if self.app_state.current_selection < len(display_list) - 1:
                self.app_state.current_selection += 1
                self._update_scroll_offset(display_list)
        elif self.app_state.current_tab == "Install":
            installable_plugins = getattr(self.app_state, "install_data", [])
            if (
                installable_plugins
                and self.app_state.install_selected < len(installable_plugins) - 1
            ):
                self.app_state.install_selected += 1
        elif self.app_state.current_tab == "Update":
            updates_with_updates = UpdateTab()._get_updates_with_updates(self.app_state)
            if (
                updates_with_updates
                and self.app_state.update_selected < len(updates_with_updates) - 1
            ):
                self.app_state.update_selected += 1
        elif self.app_state.current_tab == "Remove":
            if self.app_state.remove_selected < len(self.app_state.remove_data) - 1:
                self.app_state.remove_selected += 1
        self.rich_display.refresh()

    def action_move_up(self):
        if self.app_state.current_tab == "Home" and self.app_state.mode == "normal":
            if self.app_state.current_selection > 0:
                self.app_state.current_selection -= 1
                self._update_scroll_offset(HomeTab().get_display_list())
        elif self.app_state.current_tab == "Install":
            if self.app_state.install_selected > 0:
                self.app_state.install_selected -= 1
        elif self.app_state.current_tab == "Update":
            if self.app_state.update_selected > 0:
                self.app_state.update_selected -= 1
        elif self.app_state.current_tab == "Remove":
            if self.app_state.remove_selected > 0:
                self.app_state.remove_selected -= 1
        self.rich_display.refresh()

    def action_toggle_plugin_or_mark(self):
        if self.app_state.current_tab == "Home":
            toggle_plugin(self.app_state)
        elif self.app_state.current_tab == "Install":
            installable_plugins = getattr(self.app_state, "install_data", [])
            if installable_plugins and 0 <= self.app_state.install_selected < len(
                installable_plugins
            ):
                plugin = installable_plugins[self.app_state.install_selected]
                plugin["marked"] = not plugin.get("marked", False)
        elif self.app_state.current_tab == "Update":
            updates_with_updates = UpdateTab()._get_updates_with_updates(self.app_state)
            if updates_with_updates and 0 <= self.app_state.update_selected < len(
                updates_with_updates
            ):
                plugin = updates_with_updates[self.app_state.update_selected]
                plugin["marked"] = not plugin.get("marked", False)
        elif self.app_state.current_tab == "Remove":
            if 0 <= self.app_state.remove_selected < len(self.app_state.remove_data):
                plugin_name = self.app_state.remove_data[
                    self.app_state.remove_selected
                ]["name"]
                if plugin_name in self.app_state.marked_for_removal:
                    self.app_state.marked_for_removal.remove(plugin_name)
                else:
                    self.app_state.marked_for_removal.add(plugin_name)
        self.rich_display.refresh()

    def action_check_updates(self):
        if self.app_state.current_tab == "Update":
            if not self.app_state.checking_updates:
                self.app_state.refresh_updates()
            self.rich_display.refresh()

    @work(exclusive=True, thread=True)
    def install_plugins_in_background(self, plugins_to_install):
        """Worker to install plugins and report progress."""
        try:
            console.log(
                f"[blue]Background installation started for plugins: {[p['name'] for p in plugins_to_install]}[/blue]"
            )

            installer = PluginInstaller(
                [p["_config"] for p in plugins_to_install],
                PLUGINS_DIR,
                os.path.expanduser("~/.config/tmux/"),
            )

            installed_plugins = []
            for plugin_data in plugins_to_install:
                plugin_name = plugin_data["name"]
                config = plugin_data["_config"]
                console.log(f"[blue]Starting installation for {plugin_name}[/blue]")

                # Create a progress callback for this specific plugin
                def progress_callback(progress):
                    self.app_state.install_progress_callback(plugin_name, progress)

                success, used_tag = installer._install_git_plugin_with_progress(
                    config, progress_callback
                )

                if success:
                    # Update lock file
                    installer._update_lock_file(config, used_tag)

                    # Complete
                    self.app_state.install_progress_callback(plugin_name, 100)
                    console.log(f"[green]Successfully installed {plugin_name}[/green]")
                    installed_plugins.append(plugin_name)
                else:
                    console.log(f"[red]Failed to install {plugin_name}[/red]")
                    self.app_state.install_progress_callback(plugin_name, 0)
                    self.call_from_thread(
                        lambda name=plugin_name: self.notify(
                            f"Failed to install {name}", severity="error"
                        )
                    )

            # Remove successfully installed plugins from install_data
            if installed_plugins:
                console.log(
                    f"[green]Removing installed plugins from install list: {installed_plugins}[/green]"
                )
                # Filter out installed plugins
                self.app_state.install_data = [
                    p
                    for p in self.app_state.install_data
                    if p["name"] not in installed_plugins
                ]

                # Reset selection if needed
                if self.app_state.install_selected >= len(self.app_state.install_data):
                    self.app_state.install_selected = max(
                        0, len(self.app_state.install_data) - 1
                    )

            # Final UI refresh
            self.call_from_thread(self.rich_display.refresh)
            console.log("[blue]Background installation worker completed[/blue]")

        except Exception as e:
            console.log(f"[red]Error in background installation: {e}[/red]")
            import traceback

            console.log(f"[red]Traceback: {traceback.format_exc()}[/red]")
            self.call_from_thread(
                lambda: self.notify(f"Installation failed: {str(e)}", severity="error")
            )

    def action_install_marked(self):
        """Install all plugins marked for installation."""
        self.console.log("✅ Ctrl+I pressed, installing all plugins...")
        if self.app_state.current_tab == "Install":
            installable_plugins = getattr(self.app_state, "install_data", [])
            marked_plugins = [p for p in installable_plugins if p.get("marked", False)]

            if marked_plugins:
                # Reset progress for marked plugins
                for plugin in marked_plugins:
                    plugin["progress"] = 0
                    self.app_state.installing_progress[plugin["name"]] = 0

                self.install_plugins_in_background(marked_plugins)
                self.notify(f"Installing {len(marked_plugins)} marked plugin(s)...")
            else:
                self.notify(
                    "No plugins marked for installation. Use Space to mark plugins first."
                )
        self.rich_display.refresh()

    def action_install_all(self) -> None:
        if self.app_state.current_tab == "Install":
            installable_plugins = getattr(self.app_state, "install_data", [])
            if installable_plugins:
                # Reset progress for all plugins
                for plugin in installable_plugins:
                    plugin["progress"] = 0
                    self.app_state.installing_progress[plugin["name"]] = 0

                self.install_plugins_in_background(installable_plugins)
                self.notify(f"Installing all {len(installable_plugins)} plugin(s)...")

        self.rich_display.refresh()

    @work(exclusive=True, thread=True)
    def update_plugins_in_background(self, plugins_to_update):
        """Worker to update plugins and report progress."""
        try:
            # Update plugins synchronously to avoid race conditions
            for plugin in plugins_to_update:
                plugin_name = plugin["name"]
                console.log(f"Starting update for {plugin_name}")

                # Update using the plugin updater
                success = self.plugin_updater.update_plugin(
                    plugin, progress_callback=self.app_state.update_progress_callback
                )

                if success:
                    console.log(f"Successfully updated {plugin_name}")
                    # Mark as no longer needing update
                    plugin["_internal"]["update_available"] = False
                    plugin["current_version"] = plugin["new_version"]
                else:
                    console.log(f"Failed to update {plugin_name}")
                    # Reset progress on failure
                    self.app_state.update_progress_callback(plugin_name, 0)

            # Final UI refresh
            self.call_from_thread(self.rich_display.refresh)

        except Exception as e:
            console.log(f"Error in background update: {e}")
            self.call_from_thread(
                lambda: self.notify(f"Update failed: {str(e)}", severity="error")
            )

    def action_update_marked(self):
        """Updates all marked plugins."""
        if self.app_state.current_tab == "Update":
            marked_plugins = [
                p
                for p in self.app_state.update_data
                if p.get("marked", False)
                and p.get("_internal", {}).get("update_available", False)
            ]

            if marked_plugins:
                # Reset progress for marked plugins
                for plugin in marked_plugins:
                    plugin["progress"] = 0
                    self.app_state.update_progress[plugin["name"]] = 0

                # Start background update
                self.update_plugins_in_background(marked_plugins)
                self.notify(f"Updating {len(marked_plugins)} marked plugin(s)...")
            else:
                self.notify("No plugins marked for update.")

            self.rich_display.refresh()

    def action_update_all(self):
        """Updates all plugins with available updates."""
        if self.app_state.current_tab == "Update":
            updates_with_updates = UpdateTab()._get_updates_with_updates(self.app_state)

            if updates_with_updates:
                # Reset progress for all plugins
                for plugin in updates_with_updates:
                    plugin["progress"] = 0
                    self.app_state.update_progress[plugin["name"]] = 0
                    plugin["marked"] = True  # Mark all for visual feedback

                # Start background update
                self.update_plugins_in_background(updates_with_updates)
                self.notify(f"Updating all {len(updates_with_updates)} plugin(s)...")
            else:
                self.notify("No updates available.")

            self.rich_display.refresh()

    def _update_scroll_offset(self, display_list):
        if (
            self.app_state.current_selection
            >= self.app_state.scroll_offset + VISIBLE_ROWS
        ):
            self.app_state.scroll_offset = (
                self.app_state.current_selection - VISIBLE_ROWS + 1
            )
        elif self.app_state.current_selection < self.app_state.scroll_offset:
            self.app_state.scroll_offset = self.app_state.current_selection

    @work(exclusive=True, thread=True)
    def remove_plugins_in_background(self, plugins_to_remove):
        """Worker to remove plugins and report progress."""
        try:
            console.log(
                f"[blue]Background removal started for plugins: {plugins_to_remove}[/blue]"
            )
            removed_plugins = []

            for plugin_name in plugins_to_remove:
                console.log(f"[blue]Starting removal for {plugin_name}[/blue]")

                # Remove using the plugin remover
                success = self.plugin_remover.remove_plugin(
                    plugin_name,
                    progress_callback=self.app_state.remove_progress_callback,
                )

                if success:
                    console.log(f"[green]Successfully removed {plugin_name}[/green]")
                    removed_plugins.append(plugin_name)
                else:
                    console.log(f"[red]Failed to remove {plugin_name}[/red]")
                    # Reset progress on failure
                    self.app_state.remove_progress_callback(plugin_name, 0)
                    self.call_from_thread(
                        lambda: self.notify(
                            f"Failed to remove {plugin_name}", severity="error"
                        )
                    )

            # Refresh the remove data after successful removals
            if removed_plugins:
                console.log(
                    f"[green]Refreshing remove data after successful removals: {removed_plugins}[/green]"
                )

                # Remove uninstalled plugins from updates list
                self.call_from_thread(
                    lambda: self.app_state.remove_uninstalled_plugins_from_updates(
                        removed_plugins
                    )
                )

                self.call_from_thread(self.app_state.refresh_remove_data)

                # Clear marked plugins that were successfully removed
                for plugin_name in removed_plugins:
                    self.app_state.marked_for_removal.discard(plugin_name)

                # Reset selection if we removed the currently selected plugin
                if (
                    self.app_state.remove_selected >= len(self.app_state.remove_data)
                    and len(self.app_state.remove_data) > 0
                ):
                    self.app_state.remove_selected = len(self.app_state.remove_data) - 1
                elif len(self.app_state.remove_data) == 0:
                    self.app_state.remove_selected = 0

            # Final UI refresh
            self.call_from_thread(self.rich_display.refresh)
            console.log("[blue]Background removal worker completed[/blue]")

        except Exception as e:
            console.log(f"[red]Error in background removal: {e}[/red]")
            import traceback

            console.log(f"[red]Traceback: {traceback.format_exc()}[/red]")
            self.call_from_thread(
                lambda: self.notify(f"Removal failed: {str(e)}", severity="error")
            )

    def action_remove_marked(self):
        """Remove all plugins marked for removal."""
        if self.app_state.current_tab == "Remove":
            if self.app_state.marked_for_removal:
                marked_plugins = list(self.app_state.marked_for_removal)
                # Reset progress for marked plugins
                for plugin_name in marked_plugins:
                    self.app_state.removing_progress[plugin_name] = 0

                self.remove_plugins_in_background(marked_plugins)
                self.notify(f"Removing {len(marked_plugins)} marked plugin(s)...")
            else:
                self.notify(
                    "No plugins marked for removal. Use Space to mark plugins first."
                )
        self.rich_display.refresh()
