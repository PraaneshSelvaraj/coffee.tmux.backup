from textual.app import App, ComposeResult
from textual.widgets import Static, Header, Footer
from textual.containers import Container
from textual import events

from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.box import ROUNDED
from rich.style import Style

# ---------------------------
# Theme
# ---------------------------
accent_color = "#7aa2f7"
background_color = "#1a1b26"
highlight_color = "#9ece6a"
selection_color = "#bb9af7"
section_color = "#e0af68"
background_style = Style(bgcolor=background_color)


# ---------------------------
# Fake App State (demo only)
# ---------------------------
class DummyAppState:
    def __init__(self):
        self.checking_updates = False
        self.update_data = [
            {
                "name": "plugin-one",
                "current_version": "1.0.0",
                "new_version": "1.1.0",
                "size": "2MB",
                "released": "2025-09-01",
                "dependencies": ["dep-a", "dep-b"],
                "changelog": ["Fixed bug A", "Added feature B"],
                "progress": 0,
                "_internal": {"update_available": True},
                "marked": False,
            },
            {
                "name": "plugin-two",
                "current_version": "2.3.0",
                "new_version": "2.3.0",
                "size": "1MB",
                "released": "2025-08-20",
                "dependencies": [],
                "changelog": ["No changes"],
                "progress": 0,
                "_internal": {"update_available": False},
                "marked": False,
            },
        ]
        self.update_selected = 0


# ---------------------------
# UpdateTab UI
# ---------------------------
class UpdateTab:
    def build_update_list_panel(self, app_state):
        table = Table.grid(expand=True, padding=(0, 1))
        table.add_column("Plugin", ratio=1)

        if app_state.checking_updates:
            table.add_row(Text("🔄 Checking for updates...", style="bold yellow"))
        elif not app_state.update_data:
            table.add_row(Text("✓ All plugins are up to date", style="bold #9ece6a"))
        else:
            for i, plugin in enumerate(app_state.update_data):
                is_selected = i == app_state.update_selected
                internal_info = plugin.get("_internal", {})
                has_update = internal_info.get("update_available", False)
                mark = "[✓]" if plugin.get("marked", False) else "[ ]"
                progress = plugin.get("progress", 0)
                bar_len = 15
                filled_len = int(progress / 100 * bar_len)
                bar = (
                    ("█" * filled_len + "░" * (bar_len - filled_len))
                    if progress > 0
                    else ""
                )
                progress_text = f"{bar} {progress}%" if bar else ""
                status = "⬆️" if has_update else "✅"

                row_text = f"{status} {plugin['name']} {plugin['current_version']} → {plugin['new_version']}    {mark} {progress_text}"
                style = (
                    f"bold {selection_color}"
                    if is_selected
                    else ("white" if has_update else "dim white")
                )
                table.add_row(Text(row_text, style=style))

        return Panel(
            table,
            title=f"Available Updates ({len(app_state.update_data)})",
            border_style=accent_color,
            box=ROUNDED,
            style=background_style,
        )

    def build_update_details_panel(self, app_state):
        if app_state.checking_updates:
            details = Text("🔄 Checking for updates...", style="yellow")
        elif not app_state.update_data or app_state.update_selected >= len(
            app_state.update_data
        ):
            details = Text(
                "No plugin selected or no update data available.\n\nPress 'c' to check for updates."
            )
        else:
            plugin = app_state.update_data[app_state.update_selected]
            internal_info = plugin.get("_internal", {})
            has_update = internal_info.get("update_available", False)

            details = Text()
            details.append(f"● {plugin['name']}\n\n", style=f"bold {section_color}")
            details.append(
                f"{'Version':<18}: {plugin['current_version']} → {plugin['new_version']}\n",
                style="white",
            )
            details.append(f"{'Size':<18}: {plugin['size']}\n", style="white")
            details.append(f"{'Released':<18}: {plugin['released']}\n\n", style="white")

            if has_update:
                details.append("What's New:\n", style="#5F9EA0")
                for line in plugin.get("changelog", [])[:5]:
                    details.append(f" • {line}\n", style="white")
            else:
                details.append("Status: Up to date\n", style=highlight_color)

            details.append("\nDependencies:\n", style="#5F9EA0")
            details.append(
                " • None\n"
                if not plugin["dependencies"]
                else "".join([f" • {d}\n" for d in plugin["dependencies"]])
            )

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
        controls = Text(
            "[c] Check Updates  [U] Update All  [u] Update Selected  [Space] Mark/Unmark",
            style="#5F9EA0",
        )
        return Panel(
            controls,
            title="Controls",
            border_style=accent_color,
            box=ROUNDED,
            style=background_style,
        )

    def build_panel(self, app_state):
        from rich.layout import Layout

        left = self.build_update_list_panel(app_state)
        right = self.build_update_details_panel(app_state)
        layout = Layout(name="update_layout")
        layout.split_row(Layout(left, ratio=1), Layout(right, ratio=1))
        bottom = self.build_update_status_panel(app_state)
        main_layout = Layout()
        main_layout.split_column(Layout(layout, ratio=3), Layout(bottom, size=3))
        return main_layout


# ---------------------------
# Main TUI App
# ---------------------------
class PluginManagerApp(App):
    CSS_PATH = None

    def __init__(self):
        super().__init__()
        self.state = DummyAppState()
        self.update_tab = UpdateTab()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(Static(self.update_tab.build_panel(self.state)))
        yield Footer()

    async def on_key(self, event: events.Key):
        if event.key == "q":
            await self.action_quit()


if __name__ == "__main__":
    PluginManagerApp().run()
