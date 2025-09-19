"""
Disable command implementation
"""

from core import PluginSourcer
from core import lock_file_manager as lfm
from ..utils import print_success, print_error, print_info


def run(args):
    """Run disable command"""
    try:
        # Check current state first
        lock_data = lfm.read_lock_file()
        plugins = lock_data.get("plugins", [])

        plugin_found = False
        current_state = None

        for plugin in plugins:
            if plugin.get("name") == args.plugin:
                plugin_found = True
                current_state = plugin.get("enabled", True)  # Default to True
                break

        if not plugin_found:
            print_error(f"Plugin '{args.plugin}' is not installed")
            return 1

        if not current_state:
            if not args.quiet:
                print_info(f"Plugin '{args.plugin}' is already disabled")
            return 0

        # Disable the plugin
        sourcer = PluginSourcer()

        if not args.quiet:
            print_info(f"Disabling {args.plugin}...")

        sourcer.deactivate_plugin(args.plugin)

        if not args.quiet:
            print_success(f"Disabled {args.plugin}")

        return 0

    except Exception as e:
        print_error(f"Disable failed: {e}")
        return 1
