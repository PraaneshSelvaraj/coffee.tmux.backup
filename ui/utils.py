from core import lock_file_manager as lfm, PluginSourcer
from .tabs.home import HomeTab

plugin_sourcer = PluginSourcer()


def toggle_plugin(app_state):
    # read the lockfile fresh, toggle selected plugin, write back
    display_list = HomeTab().get_display_list()
    if app_state.current_selection < len(display_list):
        selected_item = display_list[app_state.current_selection]
        if selected_item["type"] == "plugin":
            plugin = selected_item["data"]
            name = plugin["name"]
            lock_data = lfm.read_lock_file()
            for p in lock_data.get("plugins", []):
                if p["name"] == name:
                    p["enabled"] = not p.get("enabled", False)
                    # persist change
                    lfm.write_lock_file(lock_data)
                    # call plugin source activation / deactivation
                    if p["enabled"]:
                        plugin_sourcer.activate_plugin(name)
                    else:
                        plugin_sourcer.deactivate_plugin(name)
                    break
