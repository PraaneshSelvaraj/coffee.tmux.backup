from typing import Any, Dict, List

from rich.box import ROUNDED
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from core import lock_file_manager as lfm

from ..constants import (
    ACCENT_COLOR,
    BACKGROUND_STYLE,
    HIGHLIGHT_COLOR,
    SECTION_COLOR,
    SELECTION_COLOR,
    VISIBLE_ROWS,
)
from .base import Tab


class HomeTab(Tab):
    def __init__(self) -> None:
        super().__init__("Home")

    def get_display_list(self) -> List[Dict[str, Any]]:
        lock_file = lfm.read_lock_file()
        plugins = lock_file.get("plugins", [])
        active = sorted(
            [p for p in plugins if p.get("enabled")], key=lambda x: x["name"].lower()
        )
        inactive = sorted(
            [p for p in plugins if not p.get("enabled")],
            key=lambda x: x["name"].lower(),
        )
        display_list: List[Dict[str, Any]] = []
        if active:
            display_list.append({"type": "header", "text": "Active Plugins"})
            display_list.extend([{"type": "plugin", "data": p} for p in active])
        if inactive:
            display_list.append({"type": "header", "text": "Inactive Plugins"})
            display_list.extend([{"type": "plugin", "data": p} for p in inactive])
        return display_list

    def display_installed_plugins(self, app_state: Any) -> Table:
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
                table.add_row(Text(item["text"], style=f"bold {SECTION_COLOR}"))
            else:
                plugin = item["data"]
                circle_style = (
                    SECTION_COLOR
                    if is_selected
                    else (HIGHLIGHT_COLOR if plugin.get("enabled") else "grey50")
                )
                plugin_name_style = (
                    f"bold {SELECTION_COLOR}"
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

    def display_plugin_details(self, app_state: Any) -> Panel:
        display_list = self.get_display_list()
        if not display_list or app_state.current_selection >= len(display_list):
            return Panel(
                Text("No plugin selected"),
                title="Plugin Details",
                border_style=ACCENT_COLOR,
                box=ROUNDED,
                style=BACKGROUND_STYLE,
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
                border_style=ACCENT_COLOR,
                box=ROUNDED,
                style=BACKGROUND_STYLE,
            )
        else:
            plugin = selected_item["data"]
            version = (
                plugin.get("git", {}).get("tag")
                or (plugin.get("git", {}).get("commit_hash") or "")[:7]
                or "N/A"
            )
            details = Text()
            details.append(f"\n● {plugin['name']}", style=f"bold {SECTION_COLOR}")
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
                border_style=ACCENT_COLOR,
                box=ROUNDED,
                style=BACKGROUND_STYLE,
            )

    def create_home_panel(self, app_state: Any) -> Layout:
        plugin_list_panel = Panel(
            self.display_installed_plugins(app_state),
            title="Plugin List",
            border_style=ACCENT_COLOR,
            box=ROUNDED,
            style=BACKGROUND_STYLE,
        )
        plugin_details_panel = self.display_plugin_details(app_state)
        layout = Layout(name="home_layout")
        layout.split_row(
            Layout(plugin_list_panel, ratio=1), Layout(plugin_details_panel, ratio=1)
        )
        return layout
