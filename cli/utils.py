"""
CLI utility functions
"""

import os
import sys
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
)
from rich.table import Table
from rich.panel import Panel

console = Console()

ACCENT_COLOR = "#7aa2f7"
BACKGROUND_COLOR = "#1a1b26"
HIGHLIGHT_COLOR = "#9ece6a"
SELECTION_COLOR = "#bb9af7"
SECTION_COLOR = "#e0af68"
ERROR_COLOR = "#f7768e"

# Directories
COFFEE_BASE_DIR = os.path.expanduser("~/.tmux/coffee")
COFFEE_SOURCE_DIR = os.path.expanduser("~/.local/share/coffee")
COFFEE_PLUGINS_DIR = os.path.join(COFFEE_BASE_DIR, "plugins")
COFFEE_CONFIG_DIR = os.path.expanduser("~/.config/tmux/coffee/plugins")
LOCK_FILE_PATH = os.path.join(COFFEE_BASE_DIR, "caffeine-lock.json")


def setup_directories():
    """Create necessary directories"""
    os.makedirs(COFFEE_PLUGINS_DIR, exist_ok=True)
    os.makedirs(COFFEE_BASE_DIR, exist_ok=True)
    os.makedirs(COFFEE_CONFIG_DIR, exist_ok=True)


def print_version():
    """Print Coffee version"""
    console.print("Coffee v1.0.0", style=f"bold {ACCENT_COLOR}", highlight=False)
    console.print("Modern tmux plugin manager", highlight=False)


def print_success(message):
    """Print success message"""
    console.print(f"[bold {HIGHLIGHT_COLOR}]SUCCESS[/] {message}", highlight=False)


def print_error(message):
    """Print error message"""
    console.print(f"[bold {ERROR_COLOR}]ERROR[/] {message}", highlight=False)


def print_warning(message):
    """Print warning message"""
    console.print(f"[bold {SECTION_COLOR}]WARNING[/] {message}", highlight=False)


def print_info(message):
    """Print info message"""
    console.print(f"[bold {ACCENT_COLOR}]INFO[/] {message}", highlight=False)


def confirm_action(message, default=False):
    """Ask for user confirmation"""
    suffix = " [Y/n]" if default else " [y/N]"
    try:
        response = input(f"{message}{suffix}: ").strip().lower()
        if not response:
            return default
        return response in ["y", "yes"]
    except KeyboardInterrupt:
        return False


def create_progress():
    """Create a rich progress bar"""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(
            bar_width=40,
            style="grey70",
            complete_style=SELECTION_COLOR,
            finished_style=SELECTION_COLOR,
        ),
        TextColumn(
            f"[{SELECTION_COLOR}][progress.percentage]{{task.percentage:>3.0f}}%[/]"
        ),
        console=console,
    )


def format_plugin_table(plugins, title="Plugins"):
    """Format plugins as a rich table"""
    table = Table(title=f"[bold {ACCENT_COLOR}]{title}[/]", border_style=ACCENT_COLOR)
    table.add_column("Name", style="bold white")
    table.add_column("Version", style=ACCENT_COLOR)
    table.add_column("Size", style=SECTION_COLOR)
    table.add_column("Status", style="white")

    for plugin in plugins:
        status = (
            f"[bold {HIGHLIGHT_COLOR}]Enabled[/]"
            if plugin.get("enabled", True)
            else f"[bold {ERROR_COLOR}]Disabled[/]"
        )
        table.add_row(
            plugin["name"],
            plugin.get("version", "N/A"),
            plugin.get("size", "N/A"),
            status,
        )

    return table
