"""
Info command implementation
"""

from core import PluginRemover, lock_file_manager as lfm
from ..utils import (
    COFFEE_PLUGINS_DIR,
    print_error,
    console,
    ACCENT_COLOR,
    HIGHLIGHT_COLOR,
    ERROR_COLOR,
    SECTION_COLOR,
)
from rich.panel import Panel
from rich.text import Text


def run(args):
    """Run info command"""
    try:
        remover = PluginRemover(COFFEE_PLUGINS_DIR)
        installed_plugins = remover.get_installed_plugins()

        # Find the plugin
        plugin_info = None
        for plugin in installed_plugins:
            if plugin["name"] == args.plugin:
                plugin_info = plugin
                break

        if not plugin_info:
            print_error(f"Plugin '{args.plugin}' is not installed")
            return 1

        # Get additional info from lock file
        lock_data = lfm.read_lock_file()
        lock_plugin = None
        for p in lock_data.get("plugins", []):
            if p["name"] == args.plugin:
                lock_plugin = p
                break

        # Create info display
        info_text = Text()
        info_text.append(f"Name: {plugin_info['name']}\n", style="bold white")
        info_text.append(
            f"Version: {plugin_info.get('version', 'N/A')}\n", style=ACCENT_COLOR
        )
        info_text.append(
            f"Size: {plugin_info.get('size', 'N/A')}\n", style=SECTION_COLOR
        )
        info_text.append(f"Installed: {plugin_info.get('installed', 'N/A')}\n")

        status = "Enabled" if plugin_info.get("enabled", True) else "Disabled"
        status_style = (
            HIGHLIGHT_COLOR if plugin_info.get("enabled", True) else ERROR_COLOR
        )
        info_text.append(f"Status: {status}\n", style=f"bold {status_style}")

        if lock_plugin:
            git_info = lock_plugin.get("git", {})
            if git_info.get("repo"):
                info_text.append(f"Repository: {git_info['repo']}\n", style="dim white")
            if git_info.get("commit_hash"):
                info_text.append(
                    f"Commit: {git_info['commit_hash'][:7]}\n", style="dim white"
                )
            if git_info.get("last_pull"):
                info_text.append(
                    f"Last Updated: {git_info['last_pull']}\n", style="dim white"
                )

            env_vars = lock_plugin.get("env", {})
            if env_vars:
                info_text.append("\nEnvironment Variables:\n", style="bold white")
                for key in env_vars.keys():
                    info_text.append(f"  {key}\n", style=ACCENT_COLOR)

            sources = lock_plugin.get("sources", [])
            if sources:
                info_text.append("\nSource Files:\n", style="bold white")
                for source in sources:
                    info_text.append(f"  {source}\n", style=ACCENT_COLOR)

        panel = Panel(
            info_text,
            title=f"[bold {ACCENT_COLOR}]Coffee - {plugin_info['name']}[/]",
            border_style=ACCENT_COLOR,
        )
        console.print(panel)

        return 0

    except Exception as e:
        print_error(f"Info failed: {e}")
        return 1
