"""
Remove command implementation
"""

from core import PluginRemover
from ..utils import (
    COFFEE_PLUGINS_DIR,
    print_success,
    print_error,
    print_info,
    confirm_action,
    create_progress,
    console,
    HIGHLIGHT_COLOR,
)


def run(args):
    """Run remove command"""
    try:
        remover = PluginRemover(COFFEE_PLUGINS_DIR)
        installed_plugins = remover.get_installed_plugins()

        # Check if plugin exists
        plugin_to_remove = None
        for plugin in installed_plugins:
            if plugin["name"] == args.plugin:
                plugin_to_remove = plugin
                break

        if not plugin_to_remove:
            print_error(f"Plugin '{args.plugin}' is not installed")
            return 1

        # Confirm removal
        if not args.force and not args.quiet:
            plugin_info = (
                f"{plugin_to_remove['name']} ({plugin_to_remove.get('version', 'N/A')})"
            )
            if not confirm_action(f"Remove plugin {plugin_info}?", False):
                print_info("Removal cancelled")
                return 0

        # Remove plugin
        if not args.quiet:
            print_info(f"Removing {args.plugin}...")

        if args.quiet:
            # Quiet mode - no progress bar
            success = remover.remove_plugin(args.plugin)
        else:
            # Normal mode with progress bar
            with create_progress() as progress:
                task_id = progress.add_task(f"Removing {args.plugin}", total=100)

                # Fixed callback - matches your core method signature
                def callback(plugin_name, percent, task_id=task_id):
                    progress.update(task_id, completed=percent)

                success = remover.remove_plugin(args.plugin, callback)

                if success:
                    progress.update(task_id, completed=100)

        if success:
            if not args.quiet:
                console.print(
                    f"[bold {HIGHLIGHT_COLOR}]SUCCESS[/] Successfully removed {args.plugin}"
                )
            return 0
        else:
            print_error(f"Failed to remove {args.plugin}")
            return 1

    except Exception as e:
        print_error(f"Remove failed: {e}")
        return 1
