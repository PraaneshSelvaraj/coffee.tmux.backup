import os
import shutil
import subprocess
from core import lock_file_manager as lfm


class PluginRemover:
    def __init__(self, plugin_base_dir):
        self.plugin_base_dir = plugin_base_dir

    def remove_plugin(self, plugin_name):
        lock_data = lfm.read_lock_file()
        plugins = lock_data.get("plugins", [])

        plugin_entry = next((p for p in plugins if p.get("name") == plugin_name), None)

        if not plugin_entry:
            print(f"🤷 Plugin '{plugin_name}' not found in lock file.")
            return

        plugin_path = os.path.join(self.plugin_base_dir, plugin_name)

        # Step 2: Remove plugin directory
        if os.path.exists(plugin_path):
            try:
                shutil.rmtree(plugin_path)
                print(f"🧹 Removed plugin directory: {plugin_path}")
            except Exception as e:
                print(f"💥 Error removing plugin directory: {plugin_path} - {e}")

        else:
            print(f"⚠️ Plugin directory not found: {plugin_path}")

        # Step 3: Unset environment variables
        env_vars = plugin_entry.get("env", {})
        for key in env_vars.keys():
            subprocess.run(["tmux", "set-environment", "-u", key])
            print(f"❌ Unset env var: {key}")

        # Step 4: Remove plugin entry from lock file
        lock_data["plugins"] = [p for p in plugins if p.get("name") != plugin_name]
        lfm.write_lock_file(lock_data)

        # Step 5: Finish him
        print(f"💥 Plugin '{plugin_name}' has been removed successfully.")
