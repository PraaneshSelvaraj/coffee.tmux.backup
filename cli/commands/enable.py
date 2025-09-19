"""
Enable command implementation
"""

from core import PluginSourcer
from core import lock_file_manager as lfm
from ..utils import print_success, print_error, print_info


def run(args):
    """Run enable command"""
    try:
        # Check current state first
        lock_data = lfm.read_lock_file()
        plugins = lock_data.get("plugins", [])

        plugin_found = False
        current_state = None

        for plugin in plugins:
            if plugin.get("name") == args.plugin:
                plugin_found = True
                current_state = plugin.get("enabled", True)
                break

        if not plugin_found:
            print_error(f"Plugin '{args.plugin}' is not installed")
            return 1

        if current_state:
            if not args.quiet:
                print_info(f"Plugin '{args.plugin}' is already enabled")
            return 0

        # Enable the plugin
        sourcer = PluginSourcer()

        if not args.quiet:
            print_info(f"Enabling {args.plugin}...")

        sourcer.activate_plugin(args.plugin)

        if not args.quiet:
            print_success(f"Enabled and activated {args.plugin}")

        return 0

    except Exception as e:
        print_error(f"Enable failed: {e}")
        return 1
