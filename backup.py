from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Static
from rich.box import ROUNDED
from rich.console import Console, RenderableType
from rich.layout import Layout
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, BarColumn, TextColumn
from core import PluginSourcer
from core import lock_file_manager as lfm

console = Console()
plugin_sourcer = PluginSourcer()

# Theme Colors
accent_color = "#7aa2f7"
background_color = "#1a1b26"
highlight_color = "#9ece6a"
selection_color = "#bb9af7"
section_color = "#e0af68"

background_style = Style(bgcolor=background_color)

VISIBLE_ROWS = 6
TABS = ["Home", "Install", "Update", "Remove"]
lock_file = lfm.read_lock_file()


# --- Mock Data for Updates ---
mock_updates = [
    {
        "name": "tmux-powerline",
        "current_version": "v2.1.0",
        "new_version": "v2.2.0",
        "size": "2.3 MB",
        "released": "3 days ago",
        "changelog": [
            "Fixed tmux 3.4 compatibility",
            "Added new powerline segments",
            "Performance improvements",
            "Bug fixes for status bar",
        ],
        "dependencies": [],
        "breaking": None,
        "marked": True,
        "progress": 75,  # percent
    },
    {
        "name": "tmux-resurrect",
        "current_version": "v4.0.0",
        "new_version": "v4.1.0",
        "size": "1.8 MB",
        "released": "1 week ago",
        "changelog": ["Restore layouts faster", "Bug fixes"],
        "dependencies": [],
        "breaking": None,
        "marked": False,
        "progress": 0,
    },
    {
        "name": "battery-status",
        "current_version": "v1.5.2",
        "new_version": "v1.6.0",
        "size": "512 KB",
        "released": "5 days ago",
        "changelog": ["Improved battery detection", "UI tweaks"],
        "dependencies": [],
        "breaking": None,
        "marked": False,
        "progress": 0,
    },
    {
        "name": "weather-plugin",
        "current_version": "v0.3.1",
        "new_version": "v0.4.0",
        "size": "1.2 MB",
        "released": "2 weeks ago",
        "changelog": ["Updated API support", "Fixed display bug"],
        "dependencies": [],
        "breaking": None,
        "marked": False,
        "progress": 0,
    },
]

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
        self.mode = "normal"  # "normal" | "search"
        self.update_selected = 0  # for Update tab


class Tab:
    def __init__(self, name):
        self.name = name

    def create_tab_bar(self, active_tab="Home"):
        tabs = ""
        for tab in TABS:
            if tab == active_tab:
                tabs += f"[bold reverse #1D8E5E bold white] {tab} [/]{'  '}"
            else:
                tabs += f"[bold white] {tab} [/]{'  '}"
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


# ---------------- HOME TAB ----------------
class HomeTab(Tab):
    def __init__(self):
        super().__init__("Home")

    def get_display_list(self):
        plugins = lock_file.get("plugins", [])
        active = sorted(
            [p for p in plugins if p["enabled"]], key=lambda x: x["name"].lower()
        )
        inactive = sorted(
            [p for p in plugins if not p["enabled"]], key=lambda x: x["name"].lower()
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
                header = Text(item["text"], style=f"bold {section_color}")
                table.add_row(header)
            elif item["type"] == "plugin":
                plugin = item["data"]
                circle_style = (
                    selection_color
                    if is_selected
                    else (highlight_color if plugin["enabled"] else "grey50")
                )
                plugin_name_style = (
                    f"bold {selection_color}"
                    if is_selected
                    else ("white" if plugin["enabled"] else "dim white")
                )
                circle_text = Text("  ● ", style=circle_style)
                plugin_name = Text(plugin["name"], style=plugin_name_style)
                table.add_row(Text.assemble(circle_text, plugin_name))

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
            plugins = lock_file.get("plugins", [])
            count = (
                len([p for p in plugins if p["enabled"]])
                if header_text == "Active Plugins"
                else len([p for p in plugins if not p["enabled"]])
            )

            info = Text()
            info.append(f"{header_text}\n", style="bold #e0af68")
            info.append("Total: ", style="#5F9EA0")
            info.append(f"{count}\n\n", style="white")
            info.append("Controls:\n", style="#5F9EA0")
            info.append("  j / k   ", style="bold white")
            info.append("- Move up / down\n")
            info.append("  SPACE   ", style="bold white")
            info.append("- Toggle\n")
            info.append("  q       ", style="bold white")
            info.append("- Quit\n")

            return Panel(
                info,
                title="Info",
                border_style=accent_color,
                box=ROUNDED,
                style=background_style,
            )

        elif selected_item["type"] == "plugin":
            plugin = selected_item["data"]
            version = (
                plugin.get("git", {}).get("tag")
                or plugin.get("git", {}).get("commit_hash", "")[:7]
                or "N/A"
            )

            details = Text()
            details.append(f"\n● {plugin['name']}", style=f"bold {section_color}")
            details.append("\n\n")
            details.append(f"{'Version':<18}: {version}\n", style="white")
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

        return Panel(
            Text("No plugin selected"),
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


# ---------------- INSTALL / REMOVE TABS ----------------
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
    """Update tab with full layout, mock data, and progress bar."""

    def __init__(self):
        super().__init__("Update")

    def build_update_list_panel(self, app_state):
        table = Table.grid(expand=True, padding=(0, 1))
        table.add_column("Plugin", ratio=1)

        any_updates = False
        for i, plugin in enumerate(mock_updates):
            is_selected = i == app_state.update_selected
            mark = "[✓]" if plugin["marked"] else "[ ]"
            if plugin["progress"] > 0:
                bar_len = 20
                filled_len = int(plugin["progress"] / 100 * bar_len)
                bar = "█" * filled_len + "░" * (bar_len - filled_len)
                progress_text = f"{bar} {plugin['progress']}%"
            else:
                progress_text = ""

            row_text = f"● {plugin['name']} {plugin['current_version']} → {plugin['new_version']}    {mark} {progress_text}"
            style = (
                f"bold {selection_color}"
                if is_selected
                else (
                    "white"
                    if plugin["current_version"] != plugin["new_version"]
                    else "dim white"
                )
            )
            table.add_row(Text(row_text, style=style))
            if plugin["current_version"] != plugin["new_version"]:
                any_updates = True

        if not any_updates:
            table.add_row(Text("✓ All plugins are up to date", style="bold #9ece6a"))

        return Panel(
            table,
            title=f"Available Updates ({len(mock_updates)})",
            border_style=accent_color,
            box=ROUNDED,
            style=background_style,
        )

    def build_update_details_panel(self, app_state):
        plugin = mock_updates[app_state.update_selected]

        details = Text()
        details.append(f"● {plugin['name']}\n\n", style=f"bold {section_color}")
        details.append(
            f"{'Version':<18}: {plugin['current_version']} → {plugin['new_version']}\n",
            style="white",
        )
        details.append(f"{'Size':<18}: {plugin['size']}\n", style="white")
        details.append(f"{'Released':<18}: {plugin['released']}\n\n", style="white")
        details.append("What's New:\n", style="#5F9EA0")
        for line in plugin["changelog"]:
            details.append(f" • {line}\n", style="white")
        details.append("\nDependencies:\n", style="#5F9EA0")
        details.append(
            " • None\n"
            if not plugin["dependencies"]
            else "".join([f" • {d}\n" for d in plugin["dependencies"]])
        )
        details.append("\nBreaking Changes:\n", style="#5F9EA0")
        details.append(
            " • None\n" if not plugin["breaking"] else "\n".join(plugin["breaking"])
        )

        if plugin["progress"] > 0:
            # Add a mini progress bar under details
            bar_len = 20
            filled_len = int(plugin["progress"] / 100 * bar_len)
            bar = "█" * filled_len + "░" * (bar_len - filled_len)
            details.append(
                f"\nUpdating... {bar} {plugin['progress']}%\n", style=highlight_color
            )

        return Panel(
            details,
            title="Update Details",
            border_style=accent_color,
            box=ROUNDED,
            style=background_style,
        )

    def build_update_status_panel(self, app_state):
        controls = Text(
            "[U] Update All  [u] Update Selected  [Space] Mark/Unmark", style="#5F9EA0"
        )
        return Panel(
            controls,
            title="Update Status",
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

    def build(self):
        return Panel(
            Text("Remove tab coming soon..."),
            border_style="magenta",
            style=background_style,
        )


# ---------------- TOGGLE PLUGIN ----------------
def toggle_plugin(app_state):
    display_list = HomeTab().get_display_list()
    if app_state.current_selection < len(display_list):
        selected_item = display_list[app_state.current_selection]
        if selected_item["type"] == "plugin":
            plugin = selected_item["data"]
            plugin["enabled"] = not plugin["enabled"]
            if plugin["enabled"]:
                plugin_sourcer.activate_plugin(plugin["name"])
            else:
                plugin_sourcer.deactivate_plugin(plugin["name"])
            lfm.write_lock_file(lock_file)


# ---------------- RICH DISPLAY ----------------
class RichDisplay(Static):
    """Widget that renders Rich content directly."""

    def __init__(self, app_state: AppState):
        super().__init__()
        self.app_state = app_state

    def render(self) -> RenderableType:
        """Rebuild layout every render for fresh state."""
        tab = self.app_state.current_tab
        layout = Tab("dummy").build_layout(tab)

        if tab == "Home":
            layout["body"].update(HomeTab().create_home_panel(self.app_state))
        elif tab == "Install":
            layout["body"].update(InstallTab().build())
        elif tab == "Update":
            layout["body"].update(UpdateTab().build_panel(self.app_state))
        elif tab == "Remove":
            layout["body"].update(RemoveTab().build())

        layout["tab_bar"].update(Tab("dummy").create_tab_bar(tab))
        return layout


# ---------------- PLUGIN MANAGER APP ----------------
class PluginManagerApp(App):
    """Textual app that renders Rich content directly."""

    CSS = """
    RichDisplay {
        background: #1a1b26;
        width: 100%;
        height: 100%;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("H", "switch_to_home", "Home", show=False),
        Binding("I", "switch_to_install", "Install", show=False),
        Binding("U", "switch_to_update", "Update", show=False),
        Binding("R", "switch_to_remove", "Remove", show=False),
        Binding("j", "move_down", "Down", show=False),
        Binding("k", "move_up", "Up", show=False),
        Binding("space", "toggle_plugin_or_mark", "Toggle/Mark", show=False),
        Binding("/", "enter_search_mode", "Search", show=False),
        Binding("esc", "exit_search_mode", "Exit Search", show=False),
        Binding("enter", "view_update_details", "View Details", show=False),
        Binding("U", "update_all", "Update All", show=False),
        Binding("u", "update_selected", "Update Selected", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.app_state = AppState()
        self.rich_display = None

    def compose(self) -> ComposeResult:
        self.rich_display = RichDisplay(self.app_state)
        yield self.rich_display

    # -------- Tab Switching --------
    def action_switch_to_home(self) -> None:
        self.app_state.current_tab = "Home"
        self.rich_display.refresh()

    def action_switch_to_install(self) -> None:
        self.app_state.current_tab = "Install"
        self.rich_display.refresh()

    def action_switch_to_update(self) -> None:
        self.app_state.current_tab = "Update"
        self.rich_display.refresh()

    def action_switch_to_remove(self) -> None:
        self.app_state.current_tab = "Remove"
        self.rich_display.refresh()

    # -------- Navigation --------
    def action_move_down(self) -> None:
        if self.app_state.current_tab == "Home" and self.app_state.mode == "normal":
            display_list = HomeTab().get_display_list()
            if self.app_state.current_selection < len(display_list) - 1:
                self.app_state.current_selection += 1
                self._update_scroll_offset(display_list)
                self.rich_display.refresh()
        elif self.app_state.current_tab == "Update":
            if self.app_state.update_selected < len(mock_updates) - 1:
                self.app_state.update_selected += 1
                self.rich_display.refresh()

    def action_move_up(self) -> None:
        if self.app_state.current_tab == "Home" and self.app_state.mode == "normal":
            if self.app_state.current_selection > 0:
                self.app_state.current_selection -= 1
                display_list = HomeTab().get_display_list()
                self._update_scroll_offset(display_list)
                self.rich_display.refresh()
        elif self.app_state.current_tab == "Update":
            if self.app_state.update_selected > 0:
                self.app_state.update_selected -= 1
                self.rich_display.refresh()

    # -------- Toggle / Mark --------
    def action_toggle_plugin_or_mark(self) -> None:
        if self.app_state.current_tab == "Home" and self.app_state.mode == "normal":
            toggle_plugin(self.app_state)
        elif self.app_state.current_tab == "Update":
            plugin = mock_updates[self.app_state.update_selected]
            plugin["marked"] = not plugin["marked"]
        self.rich_display.refresh()

    # -------- Search Mode (Home only) --------
    def action_enter_search_mode(self) -> None:
        self.app_state.mode = "search"

    def action_exit_search_mode(self) -> None:
        self.app_state.mode = "normal"

    # -------- Update Actions --------
    def action_view_update_details(self) -> None:
        self.rich_display.refresh()

    def action_update_all(self) -> None:
        for plugin in mock_updates:
            plugin["progress"] = 100
        self.rich_display.refresh()

    def action_update_selected(self) -> None:
        plugin = mock_updates[self.app_state.update_selected]
        plugin["progress"] = 100
        self.rich_display.refresh()

    # -------- Scroll offset for Home tab --------
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


def main():
    app = PluginManagerApp()
    app.run()


if __name__ == "__main__":
    main()
