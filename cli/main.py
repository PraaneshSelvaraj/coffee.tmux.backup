#!/usr/bin/env python3
"""
Coffee CLI - Main entry point
"""
import argparse
import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, current_dir)

from core import PluginSourcer
from cli.commands import (
    install,
    update,
    upgrade,
    remove,
    list_plugins,
    info,
    enable,
    disable,
)
from cli.utils import setup_directories, print_version


def create_parser():
    """Create the main argument parser"""
    parser = argparse.ArgumentParser(
        prog="coffee",
        description="☕ Coffee - Modern tmux plugin manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  coffee install              Install all configured plugins
  coffee update               Check for plugin updates
  coffee upgrade              Upgrade all plugins with updates
  coffee upgrade tmux-sensible  Upgrade specific plugin
  coffee remove tmux-sensible   Remove plugin
  coffee list                 List installed plugins
  coffee info tmux-sensible   Show plugin information
  coffee enable tmux-sensible Enable plugin
  coffee disable tmux-sensible Disable plugin
        """,
    )

    # Global flags
    parser.add_argument("--version", action="store_true", help="Show version")
    parser.add_argument(
        "--source-plugins",
        action="store_true",
        help="Source enabled plugins (internal use)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-q", "--quiet", action="store_true", help="Quiet output")

    # Create subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Install command
    install_parser = subparsers.add_parser("install", help="Install plugins")
    install_parser.add_argument("plugin", nargs="?", help="Specific plugin to install")
    install_parser.add_argument("--force", action="store_true", help="Force reinstall")
    install_parser.set_defaults(func=install.run)

    # Update command
    update_parser = subparsers.add_parser("update", help="Check for plugin updates")
    update_parser.set_defaults(func=update.run)

    # Upgrade command
    upgrade_parser = subparsers.add_parser("upgrade", help="Upgrade plugins")
    upgrade_parser.add_argument("plugin", nargs="?", help="Specific plugin to upgrade")
    upgrade_parser.add_argument(
        "--all", action="store_true", help="Upgrade all plugins"
    )
    upgrade_parser.set_defaults(func=upgrade.run)

    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove plugin")
    remove_parser.add_argument("plugin", help="Plugin to remove")
    remove_parser.add_argument(
        "--force", action="store_true", help="Force removal without confirmation"
    )
    remove_parser.set_defaults(func=remove.run)

    # List command
    list_parser = subparsers.add_parser("list", help="List installed plugins")
    list_parser.add_argument("--table", action="store_true", help="Display as table")
    list_parser.add_argument("-q", "--quiet", action="store_true", help="Quiet output")
    list_parser.set_defaults(func=lambda args: list_plugins.run(args))

    # Info command
    info_parser = subparsers.add_parser("info", help="Show plugin information")
    info_parser.add_argument("plugin", help="Plugin name")
    info_parser.set_defaults(func=info.run)

    # Enable command
    enable_parser = subparsers.add_parser("enable", help="Enable a plugin")
    enable_parser.add_argument("plugin", help="Plugin name to enable")
    enable_parser.add_argument(
        "-q", "--quiet", action="store_true", help="Quiet output"
    )
    enable_parser.set_defaults(func=enable.run)

    # Disable command
    disable_parser = subparsers.add_parser("disable", help="Disable a plugin")
    disable_parser.add_argument("plugin", help="Plugin name to disable")
    disable_parser.add_argument(
        "-q", "--quiet", action="store_true", help="Quiet output"
    )
    disable_parser.set_defaults(func=disable.run)

    return parser


def main():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()

    # Handle global flags
    if args.version:
        print_version()
        return 0

    if args.source_plugins:

        sourcer = PluginSourcer()
        sourcer.source_enabled_plugins()
        return 0

    # Setup directories
    setup_directories()

    # Handle commands
    if hasattr(args, "func"):
        try:
            return args.func(args)
        except KeyboardInterrupt:
            print("\n❌ Operation cancelled by user")
            return 1
        except Exception as e:
            if args.verbose:
                import traceback

                traceback.print_exc()
            else:
                print(f"❌ Error: {e}")
            return 1
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
