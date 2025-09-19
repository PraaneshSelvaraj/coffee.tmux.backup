"""
Install command implementation
"""

import os
from core import PluginLoader, PluginInstaller
from ..utils import (
    COFFEE_PLUGINS_DIR,
    COFFEE_CONFIG_DIR,
    print_success,
    print_error,
    print_info,
    create_progress,
    console,
    HIGHLIGHT_COLOR,
    ACCENT_COLOR,
)


def run(args):
    """Run install command"""
    try:
        # Load plugin configurations
        plugin_loader = PluginLoader(COFFEE_CONFIG_DIR)
        plugins = plugin_loader.load_plugins()

        if not plugins:
            if not args.quiet:
                print_info(
                    "No plugins configured. Add YAML files to ~/.config/tmux/coffee/plugins/"
                )
            return 0

        # Filter for specific plugin if requested
        if args.plugin:
            plugins = [p for p in plugins if p["name"] == args.plugin]
            if not plugins:
                print_error(f"Plugin '{args.plugin}' not found in configuration")
                return 1

        # Check which plugins actually need installation
        plugins_to_install = []
        for plugin in plugins:
            plugin_path = os.path.join(COFFEE_PLUGINS_DIR, plugin["name"])
            if not os.path.exists(plugin_path) or args.force:
                plugins_to_install.append(plugin)
            elif not args.quiet:
                console.print(
                    f"[bold {ACCENT_COLOR}]SKIP[/] {plugin['name']} (already installed)"
                )

        if not plugins_to_install:
            if not args.quiet:
                console.print(
                    f"[bold {HIGHLIGHT_COLOR}]All plugins are already installed![/]"
                )
            return 0

        # Install plugins
        installer = PluginInstaller(
            plugins_to_install,
            COFFEE_PLUGINS_DIR,
            os.path.expanduser("~/.config/tmux/"),
        )

        if not args.quiet:
            print_info(f"Installing {len(plugins_to_install)} plugin(s)...")

        if args.quiet:
            # Quiet mode - no progress bars
            for plugin in plugins_to_install:
                success, used_tag = installer._install_git_plugin(plugin)

                if success:
                    installer._update_lock_file(plugin, used_tag)
                else:
                    print_error(f"Failed to install {plugin['name']}")
                    return 1
        else:
            # Normal mode with progress bars
            with create_progress() as progress:
                for plugin in plugins_to_install:
                    task_id = progress.add_task(
                        f"Installing {plugin['name']}", total=100
                    )

                    # Fixed callback - only expects percent argument
                    def callback(percent, task_id=task_id):
                        progress.update(task_id, completed=percent)

                    success, used_tag = installer._install_git_plugin_with_progress(
                        plugin, callback
                    )

                    if success:
                        installer._update_lock_file(plugin, used_tag)
                        progress.update(task_id, completed=100)
                        console.print(
                            f"[bold {HIGHLIGHT_COLOR}]SUCCESS[/] Installed {plugin['name']} @ [bold white]{used_tag or 'latest'}[/]"
                        )
                    else:
                        progress.update(task_id, completed=0)
                        print_error(f"Failed to install {plugin['name']}")

        if not args.quiet:
            console.print(f"[bold {HIGHLIGHT_COLOR}]SUCCESS[/] Installation complete!")

        return 0

    except Exception as e:
        print_error(f"Installation failed: {e}")
        return 1
