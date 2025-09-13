import os
import threading
import time
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.layout import Layout
from rich.style import Style
from rich.box import ROUNDED
from rich.console import Console, RenderableType
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Static
from textual import work
from core import lock_file_manager as lfm
from core import PluginSourcer
from core import PluginUpdater

console = Console()
plugin_sourcer = PluginSourcer()

accent_color = "#7aa2f7"
background_color = "#1a1b26"
highlight_color = "#9ece6a"
selection_color = "#bb9af7"
section_color = "#e0af68"

background_style = Style(bgcolor=background_color)

VISIBLE_ROWS = 10
TABS = ["Home", "Install", "Update", "Remove"]

PLUGINS_DIR = os.path.expanduser("~/.tmux/coffee/plugins")
plugin_updater = PluginUpdater(PLUGINS_DIR)

REMOVE_PLUGINS = [
    {
        "name": "tmux-powerline",
        "version": "v4.1.0",
        "size": "2.3 MB",
        "installed": "3 days ago",
        "dependencies": "None",
    },
    {
        "name": "tmux-resurrect",
        "version": "v4.1.0",
        "size": "1.8 MB",
        "installed": "5 days ago",
        "dependencies": "None",
    },
    {
        "name": "battery-status",
        "version": "v1.6.0",
        "size": "0.5 MB",
        "installed": "2 days ago",
        "dependencies": "None",
    },
    {
        "name": "weather-plugin",
        "version": "v0.4.0",
        "size": "1.2 MB",
        "installed": "7 days ago",
        "dependencies": "None",
    },
]


class AppState:
    def __init__(self):
        self.scroll_offset = 0
        self.current_selection = 0
        self.current_tab = "Home"
        self.mode = "normal"
        self.update_selected = 0
        self.update_data = []
        self.update_progress = {}
        self.checking_updates = False
        # Remove tab state
        self.remove_selected = 0
        self.marked_for_removal = set()
        self.removing_progress = {}
        self._app_ref = None

    def refresh_updates(self):
        if not self.checking_updates:
            self.checking_updates = True
            self.update_data = []
            self.update_progress = {}  # Reset progress
            thread = threading.Thread(target=self._check_updates_async, daemon=True)
            thread.start()

    def _check_updates_async(self):
        try:
            updates = plugin_updater.check_for_updates()
            self.update_data = updates
        except Exception as e:
            self.update_data = []
            console.log(f"[ERROR] Error checking updates: {e}")
        finally:
            self.checking_updates = False
            if self._app_ref:
                # Use call_from_thread to safely update UI from background
                self._app_ref.call_from_thread(self._app_ref.rich_display.refresh)

    def update_progress_callback(self, plugin_name, progress):
        self.update_progress[plugin_name] = progress
        for plugin in self.update_data:
            if plugin["name"] == plugin_name:
                plugin["progress"] = progress
                break
        if self._app_ref:
            self._app_ref.call_from_thread(self._app_ref.rich_display.refresh)

    def bind_app(self, app):
        self._app_ref = app


class Tab:
    def __init__(self, name):
        self.name = name

    def create_tab_bar(self, active_tab="Home"):
        tabs = ""
        for tab in TABS:
            if tab == active_tab:
                # highlight active tab
                tabs += f"[reverse bold {highlight_color}] {tab} [/] {' ' }"
            else:
                tabs += f"[bold white] {tab} [/]{' '}"
        return Panel(
            tabs,
            title="Coffee",
            border_style="cyan",
            style=background_style,
            padding=(0, 2),
        )

    def build_layout(self, active_tab="Home"):
        layout = Layout()
        layout.split_column(
            Layout(self.create_tab_bar(active_tab), name="tab_bar", size=3),
            Layout(name="body", ratio=2),
        )
        return layout


class HomeTab(Tab):
    def __init__(self):
        super().__init__("Home")

    def get_display_list(self):
        # Read lockfile fresh each time so state is consistent with disk
        lock_file = lfm.read_lock_file()
        plugins = lock_file.get("plugins", [])
        active = sorted(
            [p for p in plugins if p.get("enabled")], key=lambda x: x["name"].lower()
        )
        inactive = sorted(
            [p for p in plugins if not p.get("enabled")],
            key=lambda x: x["name"].lower(),
        )
        return (
            [{"type": "header", "text": "Active Plugins"}]
            + [{"type": "plugin", "data": p} for p in active]
            + [{"type": "header", "text": "Inactive Plugins"}]
            + [{"type": "plugin", "data": p} for p in inactive]
        )

    def display_installed_plugins(self, app_state):
        display_list = self.get_display_list()
        visible_items = display_list[
            app_state.scroll_offset : app_state.scroll_offset + VISIBLE_ROWS
        ]
        table = Table.grid(expand=True, padding=(0, 1))
        table.add_column("Plugin", ratio=1)
        for i, item in enumerate(visible_items):
            index = app_state.scroll_offset + i
            is_selected = index == app_state.current_selection
            if item["type"] == "header":
                table.add_row(Text(item["text"], style=f"bold {section_color}"))
            else:
                plugin = item["data"]
                circle_style = (
                    selection_color
                    if is_selected
                    else (highlight_color if plugin.get("enabled") else "grey50")
                )
                plugin_name_style = (
                    f"bold {selection_color}"
                    if is_selected
                    else ("white" if plugin.get("enabled") else "dim white")
                )
                table.add_row(
                    Text.assemble(
                        Text(" ● ", style=circle_style),
                        Text(plugin["name"], style=plugin_name_style),
                    )
                )
        return table

    def display_plugin_details(self, app_state):
        display_list = self.get_display_list()
        if not display_list or app_state.current_selection >= len(display_list):
            return Panel(
                Text("No plugin selected"),
                title="Plugin Details",
                border_style=accent_color,
                box=ROUNDED,
                style=background_style,
            )
        selected_item = display_list[app_state.current_selection]
        if selected_item["type"] == "header":
            header_text = selected_item["text"]
            lock_file = lfm.read_lock_file()
            plugins = lock_file.get("plugins", [])
            count = (
                len([p for p in plugins if p.get("enabled")])
                if header_text == "Active Plugins"
                else len([p for p in plugins if not p.get("enabled")])
            )
            info = Text()
            info.append(f"{header_text}\n", style="bold #e0af68")
            info.append("Total: ", style="#5F9EA0")
            info.append(f"{count}\n\n", style="white")
            info.append("Controls:\n", style="#5F9EA0")
            info.append(" j / k    ", style="bold white")
            info.append("- Move up / down\n")
            info.append(" SPACE    ", style="bold white")
            info.append("- Toggle\n")
            info.append(" q        ", style="bold white")
            info.append("- Quit\n")
            return Panel(
                info,
                title="Info",
                border_style=accent_color,
                box=ROUNDED,
                style=background_style,
            )
        else:
            plugin = selected_item["data"]
            version = (
                plugin.get("git", {}).get("tag")
                or (plugin.get("git", {}).get("commit_hash") or "")[:7]
                or "N/A"
            )
            details = Text()
            details.append(f"\n● {plugin['name']}", style=f"bold {section_color}")
            details.append(f"\n\n{'Version':<18}: {version}\n", style="white")
            details.append(
                f"{'Skip Auto Update':<18}: {plugin.get('skip_auto_update', False)}\n",
                style="white",
            )
            if plugin.get("env"):
                details.append(
                    f"{'Env Variables':<18}: {len(plugin['env'])}", style="white"
                )
            return Panel(
                details,
                title="Plugin Details",
                border_style=accent_color,
                box=ROUNDED,
                style=background_style,
            )

    def create_home_panel(self, app_state):
        plugin_list_panel = Panel(
            self.display_installed_plugins(app_state),
            title="Plugin List",
            border_style=accent_color,
            box=ROUNDED,
            style=background_style,
        )
        plugin_details_panel = self.display_plugin_details(app_state)
        layout = Layout(name="home_layout")
        layout.split_row(
            Layout(plugin_list_panel, ratio=1), Layout(plugin_details_panel, ratio=1)
        )
        return layout


class InstallTab(Tab):
    def __init__(self):
        super().__init__("Install")

    def build(self):
        return Panel(
            Text("Install tab coming soon..."),
            border_style="magenta",
            style=background_style,
        )


class UpdateTab(Tab):
    def __init__(self):
        super().__init__("Update")

    def _get_updates_with_updates(self, app_state):
        return [
            p
            for p in app_state.update_data
            if p.get("_internal", {}).get("update_available", False)
        ]

    def build_update_list_panel(self, app_state):
        table = Table.grid(expand=True, padding=(0, 1))
        table.add_column("Plugin", ratio=1)

        updates_with_updates = self._get_updates_with_updates(app_state)

        if app_state.checking_updates:
            table.add_row(Text("🔄 Checking for updates...", style="bold yellow"))
        elif not updates_with_updates:
            table.add_row(Text("✓ All plugins are up to date", style="bold #9ece6a"))
        else:
            for i, plugin in enumerate(updates_with_updates):
                is_selected = i == app_state.update_selected
                marked = plugin.get("marked", False)

                # Mark checkbox
                mark_text = Text(
                    "[✓] " if marked else "[ ] ",
                    style=f"bold {selection_color}" if marked else "dim white",
                )

                # Plugin name and version
                version_text = f" → {plugin['new_version']}"
                name_text = Text(
                    f"{plugin['name']}{version_text}",
                    style=f"bold {selection_color}" if is_selected else "white",
                )

                # Progress bar
                progress = plugin.get("progress", 0)
                progress_text_obj = Text()
                if progress > 0 and progress < 100:
                    bar_len = 15
                    filled_len = int(progress / 100 * bar_len)
                    bar = "█" * filled_len + "░" * (bar_len - filled_len)
                    progress_text_obj = Text(f" {bar} {progress}%", style="yellow")
                elif progress == 100:
                    progress_text_obj = Text(" ✔ Done", style="green")

                row_text_obj = Text.assemble(mark_text, name_text, progress_text_obj)
                table.add_row(row_text_obj)

        title = f"Available Updates ({len(updates_with_updates)})"
        return Panel(
            table,
            title=title,
            border_style=accent_color,
            box=ROUNDED,
            style=background_style,
        )

    def build_update_details_panel(self, app_state):
        updates_with_updates = self._get_updates_with_updates(app_state)

        if app_state.checking_updates:
            details = Text("🔄 Checking for updates...", style="yellow")
        elif not updates_with_updates or app_state.update_selected >= len(
            updates_with_updates
        ):
            details = Text(
                "No plugin selected or no update data available.\n\nPress 'c' to check for updates."
            )
        else:
            plugin = updates_with_updates[app_state.update_selected]
            internal_info = plugin.get("_internal", {})
            details = Text()
            details.append(f"● {plugin['name']}\n\n", style=f"bold {section_color}")
            details.append(
                f"{'Version':<18}: {plugin['current_version']} → {plugin['new_version']}\n",
                style="white",
            )
            details.append(f"{'Size':<18}: {plugin['size']}\n", style="white")
            details.append(f"{'Released':<18}: {plugin['released']}\n\n", style="white")

            if internal_info.get("update_available", False):
                details.append("What's New:\n", style="#5F9EA0")
                for line in plugin["changelog"][:5]:
                    details.append(f" • {line}\n", style="white")
            else:
                details.append("Status: Up to date\n", style=highlight_color)

            progress = plugin.get("progress", 0)
            if progress > 0:
                bar_len = 20
                filled_len = int(progress / 100 * bar_len)
                bar = "█" * filled_len + "░" * (bar_len - filled_len)
                details.append(
                    f"\nUpdating... {bar} {progress}%\n", style=highlight_color
                )

        return Panel(
            details,
            title="Update Details",
            border_style=accent_color,
            box=ROUNDED,
            style=background_style,
        )

    def build_update_status_panel(self, app_state):
        controls = Text()
        controls.append("[c] Check Updates ", style="#5F9EA0")
        controls.append("[Space] Mark/Unmark ", style="#5F9EA0")
        controls.append(f"[u] Update Marked ", style="#5F9EA0")
        controls.append(f"[Ctrl+u] Update All", style="#5F9EA0")

        return Panel(
            controls,
            title="Controls",
            border_style=accent_color,
            box=ROUNDED,
            style=background_style,
        )

    def build_panel(self, app_state):
        left = self.build_update_list_panel(app_state)
        right = self.build_update_details_panel(app_state)
        layout = Layout(name="update_layout")
        layout.split_row(Layout(left, ratio=1), Layout(right, ratio=1))
        bottom = self.build_update_status_panel(app_state)
        main_layout = Layout()
        main_layout.split_column(Layout(layout, ratio=3), Layout(bottom, size=3))
        return main_layout


class RemoveTab(Tab):
    def __init__(self):
        super().__init__("Remove")

    def build_remove_list_panel(self, app_state):
        table = Table.grid(expand=True, padding=(0, 1))
        table.add_column("Plugin", ratio=1)

        if not REMOVE_PLUGINS:
            table.add_row(Text("No plugins installed", style="bold #9ece6a"))
        else:
            for i, plugin in enumerate(REMOVE_PLUGINS):
                is_selected = i == app_state.remove_selected
                marked = plugin["name"] in app_state.marked_for_removal

                # Mark checkbox
                mark_text = Text(
                    "[✓] " if marked else "[ ] ",
                    style=f"bold {selection_color}" if marked else "dim white",
                )

                # Plugin name and version
                version_text = f" (v{plugin['version']})"
                name_text = Text(
                    f"{plugin['name']}{version_text}",
                    style=f"bold {selection_color}" if is_selected else "white",
                )

                # Progress bar
                progress = app_state.removing_progress.get(plugin["name"], 0)
                progress_text_obj = Text()
                if progress > 0 and progress < 100:
                    bar_len = 15
                    filled_len = int(progress / 100 * bar_len)
                    bar = "█" * filled_len + "░" * (bar_len - filled_len)
                    progress_text_obj = Text(f" {bar} {progress}%", style="yellow")
                elif progress == 100:
                    progress_text_obj = Text(" ✔ Removed", style="green")

                row_text_obj = Text.assemble(mark_text, name_text, progress_text_obj)
                table.add_row(row_text_obj)

        title = f"Installed Plugins ({len(REMOVE_PLUGINS)})"
        return Panel(
            table,
            title=title,
            border_style=accent_color,
            box=ROUNDED,
            style=background_style,
        )

    def build_remove_details_panel(self, app_state):
        if not REMOVE_PLUGINS or app_state.remove_selected >= len(REMOVE_PLUGINS):
            details = Text(
                "No plugin selected or no plugins installed.\n\nPress 'j/k' to navigate through plugins."
            )
        else:
            plugin = REMOVE_PLUGINS[app_state.remove_selected]
            details = Text()
            details.append(f"● {plugin['name']}\n\n", style=f"bold {section_color}")
            details.append(f"{'Version':<18}: {plugin['version']}\n", style="white")
            details.append(f"{'Size':<18}: {plugin['size']}\n", style="white")
            details.append(f"{'Installed':<18}: {plugin['installed']}\n", style="white")
            details.append(
                f"{'Dependencies':<18}: {plugin['dependencies']}\n\n", style="white"
            )

            # Show removal status
            progress = app_state.removing_progress.get(plugin["name"], 0)
            if progress > 0 and progress < 100:
                bar_len = 20
                filled_len = int(progress / 100 * bar_len)
                bar = "█" * filled_len + "░" * (bar_len - filled_len)
                details.append(f"Removing... {bar} {progress}%\n", style="yellow")
            elif progress == 100:
                details.append("✔ Successfully removed\n", style="green")
            elif plugin["name"] in app_state.marked_for_removal:
                details.append("Status: Marked for removal\n", style="yellow")
            else:
                details.append("Status: Installed\n", style=highlight_color)

        return Panel(
            details,
            title="Plugin Details",
            border_style=accent_color,
            box=ROUNDED,
            style=background_style,
        )

    def build_remove_controls_panel(self, app_state):
        controls = Text()
        controls.append("[Space] Mark/Unmark ", style="#5F9EA0")
        controls.append("[r] Remove Selected ", style="#5F9EA0")
        controls.append(f"[A] Remove All Marked ", style="#5F9EA0")

        # Show count of marked plugins
        marked_count = len(app_state.marked_for_removal)
        if marked_count > 0:
            controls.append(f"({marked_count} marked)", style="yellow")

        return Panel(
            controls,
            title="Controls",
            border_style=accent_color,
            box=ROUNDED,
            style=background_style,
        )

    def build_panel(self, app_state):
        left = self.build_remove_list_panel(app_state)
        right = self.build_remove_details_panel(app_state)
        layout = Layout(name="remove_layout")
        layout.split_row(Layout(left, ratio=1), Layout(right, ratio=1))
        bottom = self.build_remove_controls_panel(app_state)
        main_layout = Layout()
        main_layout.split_column(Layout(layout, ratio=3), Layout(bottom, size=3))
        return main_layout

    # -------- Remove Actions (Dynamic) --------
    def remove_selected(self, app_state, refresh_callback):
        # Use the current selected index from app_state to find plugin
        if app_state.remove_selected >= len(REMOVE_PLUGINS):
            return
        plugin_name = REMOVE_PLUGINS[app_state.remove_selected]["name"]
        app_state.removing_progress[plugin_name] = 0
        for pct in range(0, 101, 10):
            app_state.removing_progress[plugin_name] = pct
            refresh_callback()
            time.sleep(0.05)
        # Remove from marked list after completion
        if plugin_name in app_state.marked_for_removal:
            app_state.marked_for_removal.remove(plugin_name)

    def remove_all_marked(self, app_state, refresh_callback):
        marked_plugins = list(app_state.marked_for_removal)  # Create a copy
        for plugin_name in marked_plugins:
            app_state.removing_progress[plugin_name] = 0
            for pct in range(0, 101, 10):
                app_state.removing_progress[plugin_name] = pct
                refresh_callback()
                time.sleep(0.02)  # Faster for multiple plugins
        app_state.marked_for_removal.clear()


def toggle_plugin(app_state):
    # read the lockfile fresh, toggle selected plugin, write back
    display_list = HomeTab().get_display_list()
    if app_state.current_selection < len(display_list):
        selected_item = display_list[app_state.current_selection]
        if selected_item["type"] == "plugin":
            plugin = selected_item["data"]
            name = plugin["name"]
            lock_data = lfm.read_lock_file()
            for p in lock_data.get("plugins", []):
                if p["name"] == name:
                    p["enabled"] = not p.get("enabled", False)
                    # persist change
                    lfm.write_lock_file(lock_data)
                    # call plugin source activation / deactivation
                    if p["enabled"]:
                        plugin_sourcer.activate_plugin(name)
                    else:
                        plugin_sourcer.deactivate_plugin(name)
                    break


class RichDisplay(Static):
    def __init__(self, app_state: AppState):
        super().__init__()
        self.app_state = app_state

    def render(self) -> RenderableType:
        tab = self.app_state.current_tab
        layout = Tab("dummy").build_layout(tab)
        if tab == "Home":
            layout["body"].update(HomeTab().create_home_panel(self.app_state))
        elif tab == "Install":
            layout["body"].update(InstallTab().build())
        elif tab == "Update":
            layout["body"].update(UpdateTab().build_panel(self.app_state))
        elif tab == "Remove":
            layout["body"].update(RemoveTab().build_panel(self.app_state))
        layout["tab_bar"].update(Tab("dummy").create_tab_bar(tab))
        return layout


class PluginManagerApp(App):
    CSS = """RichDisplay { background: #1a1b26; width:100%; height:100%; }"""
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("H", "switch_to_home", "Home", show=False),
        Binding("I", "switch_to_install", "Install", show=False),
        Binding("U", "switch_to_update", "Updates", show=False),
        Binding("R", "switch_to_remove", "Remove", show=False),
        Binding("j", "move_down", "Down", show=False),
        Binding("k", "move_up", "Up", show=False),
        Binding("space", "toggle_plugin_or_mark", "Toggle/Mark", show=False),
        Binding("/", "enter_search_mode", "Search", show=False),
        Binding("escape", "exit_search_mode", "Exit Search", show=False),
        Binding("c", "check_updates", "Check Updates", show=False),
        Binding("ctrl+u", "update_all", "Update All", show=False),
        Binding("u", "update_marked", "Update Marked", show=False),
        Binding("r", "remove_selected", "Remove Selected", show=False),
        Binding("A", "remove_all_marked", "Remove All Marked", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.app_state = AppState()
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
        self.rich_display.refresh()

    def action_switch_to_update(self):
        self.app_state.current_tab = "Update"
        if not self.app_state.update_data:
            self.app_state.refresh_updates()
        self.rich_display.refresh()

    def action_switch_to_remove(self):
        self.app_state.current_tab = "Remove"
        self.rich_display.refresh()

    def action_move_down(self):
        if self.app_state.current_tab == "Home" and self.app_state.mode == "normal":
            display_list = HomeTab().get_display_list()
            if self.app_state.current_selection < len(display_list) - 1:
                self.app_state.current_selection += 1
                self._update_scroll_offset(display_list)
        elif self.app_state.current_tab == "Update":
            updates_with_updates = UpdateTab()._get_updates_with_updates(self.app_state)
            if (
                updates_with_updates
                and self.app_state.update_selected < len(updates_with_updates) - 1
            ):
                self.app_state.update_selected += 1
        elif self.app_state.current_tab == "Remove":
            if self.app_state.remove_selected < len(REMOVE_PLUGINS) - 1:
                self.app_state.remove_selected += 1
        self.rich_display.refresh()

    def action_move_up(self):
        if self.app_state.current_tab == "Home" and self.app_state.mode == "normal":
            if self.app_state.current_selection > 0:
                self.app_state.current_selection -= 1
                self._update_scroll_offset(HomeTab().get_display_list())
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
        elif self.app_state.current_tab == "Update":
            updates_with_updates = UpdateTab()._get_updates_with_updates(self.app_state)
            if updates_with_updates and 0 <= self.app_state.update_selected < len(
                updates_with_updates
            ):
                plugin = updates_with_updates[self.app_state.update_selected]
                plugin["marked"] = not plugin.get("marked", False)
        elif self.app_state.current_tab == "Remove":
            if 0 <= self.app_state.remove_selected < len(REMOVE_PLUGINS):
                plugin_name = REMOVE_PLUGINS[self.app_state.remove_selected]["name"]
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
    def update_plugins_in_background(self, plugins_to_update):
        """Worker to update plugins and report progress."""
        try:
            # Update plugins synchronously to avoid race conditions
            for plugin in plugins_to_update:
                plugin_name = plugin["name"]
                console.log(f"Starting update for {plugin_name}")

                # Update using the plugin updater
                success = plugin_updater.update_plugin(
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

    def action_remove_selected(self):
        """Trigger removal of the currently selected plugin in the Remove tab."""
        if self.app_state.current_tab == "Remove":
            if 0 <= self.app_state.remove_selected < len(REMOVE_PLUGINS):
                self.remove_selected_worker()
                pname = REMOVE_PLUGINS[self.app_state.remove_selected]["name"]
                self.notify(f"Removing {pname}...")
            else:
                self.notify("No plugin selected to remove.")

    @work(thread=True)
    def remove_selected_worker(self):
        try:
            RemoveTab().remove_selected(
                self.app_state, lambda: self.call_from_thread(self.rich_display.refresh)
            )
            self.call_from_thread(self.rich_display.refresh)
            self.call_from_thread(lambda: self.notify("Removal complete."))
        except Exception as e:
            console.log(f"Error removing selected plugin: {e}")
            self.call_from_thread(
                lambda: self.notify(f"Removal failed: {e}", severity="error")
            )

    def action_remove_all_marked(self):
        """Trigger removal of all plugins marked for removal."""
        if self.app_state.current_tab == "Remove":
            if self.app_state.marked_for_removal:
                self.remove_all_marked_worker()
                self.notify(
                    f"Removing {len(self.app_state.marked_for_removal)} plugin(s)..."
                )
            else:
                self.notify("No plugins marked for removal.")

    @work(thread=True)
    def remove_all_marked_worker(self):
        try:
            RemoveTab().remove_all_marked(
                self.app_state, lambda: self.call_from_thread(self.rich_display.refresh)
            )
            self.call_from_thread(self.rich_display.refresh)
            self.call_from_thread(lambda: self.notify("All removals complete."))
        except Exception as e:
            console.log(f"Error removing all marked plugins: {e}")
            self.call_from_thread(
                lambda: self.notify(f"Removal failed: {e}", severity="error")
            )


def main():
    app = PluginManagerApp()
    app.run()


if __name__ == "__main__":
    main()
