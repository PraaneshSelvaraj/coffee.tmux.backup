import os
from core import lock_file_manager as lfm
import shutil
import subprocess


class PluginRemover:
    def __init__(self, plugin_base_dir):
        self.plugin_base_dir = plugin_base_dir

    def get_installed_plugins(self):
        """Get list of installed plugins with details"""
        lock_data = lfm.read_lock_file()
        plugins = lock_data.get("plugins", [])
        installed_plugins = []

        for plugin in plugins:
            plugin_name = plugin.get("name", "")
            plugin_path = os.path.join(self.plugin_base_dir, plugin_name)

            # Get plugin size
            size = "Unknown"
            if os.path.exists(plugin_path):
                try:
                    result = subprocess.run(
                        ["du", "-sh", plugin_path],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    if result.returncode == 0:
                        size = result.stdout.strip().split()[0]
                except Exception:
                    pass

            # Get version info
            git_info = plugin.get("git", {})
            version = git_info.get("tag") or (
                git_info.get("commit_hash", "")[:7]
                if git_info.get("commit_hash")
                else "N/A"
            )

            # Get install time (use last_pull or fallback to "Unknown")
            installed_time = git_info.get("last_pull", "Unknown")
            if installed_time != "Unknown":
                try:
                    from datetime import datetime

                    dt = datetime.fromisoformat(installed_time.replace("Z", "+00:00"))
                    installed_time = dt.strftime("%Y-%m-%d")
                except:
                    installed_time = "Unknown"

            installed_plugins.append(
                {
                    "name": plugin_name,
                    "version": version,
                    "size": size,
                    "installed": installed_time,
                    "dependencies": "None",  # You might want to implement dependency checking
                    "enabled": plugin.get("enabled", False),
                    "env": plugin.get("env", {}),
                }
            )

        return installed_plugins

    def remove_plugin(self, plugin_name, progress_callback=None):
        """Remove a plugin with progress reporting"""

        def send_progress(progress):
            if progress_callback:
                progress_callback(plugin_name, progress)

        try:
            send_progress(10)

            # Step 1: Read lock file and find plugin
            lock_data = lfm.read_lock_file()
            plugins = lock_data.get("plugins", [])
            plugin_entry = next(
                (p for p in plugins if p.get("name") == plugin_name), None
            )

            if not plugin_entry:
                send_progress(0)
                return False

            send_progress(30)

            # Step 2: Remove plugin directory
            plugin_path = os.path.join(self.plugin_base_dir, plugin_name)
            if os.path.exists(plugin_path):
                try:
                    shutil.rmtree(plugin_path)
                except Exception as e:
                    send_progress(0)
                    return False

            send_progress(60)

            # Step 3: Unset environment variables
            env_vars = plugin_entry.get("env", {})
            for key in env_vars.keys():
                try:
                    subprocess.run(["tmux", "set-environment", "-u", key], check=True)
                except Exception as e:
                    print(f"Warning: Failed to unset env var {key}: {e}")

            send_progress(80)

            # Step 4: Remove plugin entry from lock file
            lock_data["plugins"] = [p for p in plugins if p.get("name") != plugin_name]
            lfm.write_lock_file(lock_data)

            send_progress(100)
            return True

        except Exception as e:
            send_progress(0)
            return False
