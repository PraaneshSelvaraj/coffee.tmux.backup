import os

from core import (
    PluginLoader,
    PluginSourcer,
    PluginUpdater,
    PluginInstaller,
    PluginRemover,
)

TMUX_CONFIG_DIR = os.path.expanduser("~/.config/tmux/")
COFFEE_DIR = os.path.expanduser("~/.tmux/coffee")
COFFEE_PLUGINS_LIST_DIR = os.path.join(TMUX_CONFIG_DIR, "coffee/plugins")
COFFEE_INSTALLED_PLUGINS_DIR = os.path.join(COFFEE_DIR, "plugins")
LOCK_FILE_PATH = os.path.join(COFFEE_DIR, "caffeine-lock.json")

os.makedirs(COFFEE_INSTALLED_PLUGINS_DIR, exist_ok=True)
os.makedirs(COFFEE_DIR, exist_ok=True)
os.makedirs(COFFEE_PLUGINS_LIST_DIR, exist_ok=True)

plugin_loader = PluginLoader(COFFEE_PLUGINS_LIST_DIR)
plugins = plugin_loader.load_plugins()
# print(plugins)

plugin_installer = PluginInstaller(
    plugins, COFFEE_INSTALLED_PLUGINS_DIR, TMUX_CONFIG_DIR
)


plugin_remover = PluginRemover(COFFEE_INSTALLED_PLUGINS_DIR)
# plugin_remover.remove_plugin("spotify.demo")
# plugin_remover.remove_plugin("tmux-resurrect")
plugin_installer.install_all_plugins()
# plugin_sourcer = PluginSourcer()
# plugin_sourcer.source_enabled_plugins()
# plugin_sourcer.activate_plugin("spotify.demo")

plugin_updater = PluginUpdater(COFFEE_INSTALLED_PLUGINS_DIR)
updates = plugin_updater.check_for_updates()
print("UDPATES : ")
print(updates)
plugin_update_info = next(u for u in updates if u["name"] == "spotify.demo")

# plugin_updater.update_plugin(plugin_update_info)

# plugin_updater.auto_update_all()


# plugin_sourcer = PluginSourcer()
# plugin_sourcer.source_enabled_plugins()
# Update the Spotify plugin
# from rich.console import Console

# console = Console()


# def progress_callback(plugin_name, progress):
#     """Progress callback to show update progress"""
#     if progress == 0:
#         console.log(f"[red]❌ Update failed for {plugin_name}[/red]")
#     elif progress == 100:
#         console.log(f"[green]✅ Update completed for {plugin_name}[/green]")
#     else:
#         console.log(f"[blue]🔄 {plugin_name}: {progress}% complete[/blue]")


# # Check if spotify plugin has updates available
# if plugin_update_info and plugin_update_info["_internal"]["update_available"]:
#     current_version = plugin_update_info["current_version"]
#     new_version = plugin_update_info["new_version"]

#     console.log(
#         f"[yellow]🎵 Updating Spotify plugin: {current_version} → {new_version}[/yellow]"
#     )

#     # Perform the update
#     success = plugin_updater.update_plugin(plugin_update_info, progress_callback)

#     if success:
#         console.log("[green]🎉 Spotify plugin updated successfully![/green]")

#         # Optionally re-source plugins after update
#         console.log("[blue]🔄 Re-sourcing plugins...[/blue]")
#         plugin_sourcer = PluginSourcer()
#         plugin_sourcer.source_enabled_plugins()
#         console.log("[green]✅ Plugins re-sourced successfully![/green]")

#     else:
#         console.log("[red]💥 Failed to update Spotify plugin[/red]")

# elif plugin_update_info:
#     console.log(
#         f"[green]✅ Spotify plugin is already up-to-date ({plugin_update_info['current_version']})[/green]"
#     )
# else:
#     console.log("[red]❌ Spotify plugin not found in updates list[/red]")
