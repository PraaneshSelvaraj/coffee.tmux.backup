import os
import subprocess
from datetime import datetime
from core import lock_file_manager as lfm


class PluginUpdater:
    def __init__(self, plugins_dir):
        self.plugins_dir = plugins_dir

    def _get_latest_tag(self, plugin_path):
        try:
            tags = (
                subprocess.check_output(["git", "tag"], cwd=plugin_path, text=True)
                .strip()
                .splitlines()
            )

            return tags[-1] if tags else None
        except Exception as e:
            print(f"Could not fetch tags in {plugin_path}: {e}")
            return None

    def _get_commit_hash(self, plugin_path):
        try:
            # This gets the latest remote commit
            return subprocess.check_output(
                ["git", "rev-parse", "origin/HEAD"], cwd=plugin_path, text=True
            ).strip()
        except Exception as e:
            print(f"⚠️ Could not get remote commit hash in {plugin_path}: {e}")
            return None

    def check_for_updates(self):
        updates = []
        lock_data = lfm.read_lock_file()

        for plugin in lock_data.get("plugins", []):
            name = plugin["name"]
            plugin_path = os.path.join(self.plugins_dir, name)

            if not os.path.exists(plugin_path):
                print(f"⛔ Skipping {name} (not installed)")
                continue

            try:
                subprocess.run(["git", "fetch", "--tags"], cwd=plugin_path, check=True)
                subprocess.run(["git", "fetch"], cwd=plugin_path, check=True)

                locked_git = plugin.get("git", {})
                current_tag = locked_git.get("tag")
                current_hash = locked_git.get("commit_hash")

                latest_tag = self._get_latest_tag(plugin_path)
                latest_commit_hash = self._get_commit_hash(plugin_path)

                print(f"Current TAG : {current_tag}")
                print(f"LATEST TAG : {latest_tag}")
                print(f"Current HASH : {current_hash}")
                print(f"LATEST HASH : {latest_commit_hash}")
                if current_tag:
                    if latest_tag and latest_tag != current_tag:
                        updates.append(
                            {
                                "name": name,
                                "type": "tag",
                                "old_tag": current_tag,
                                "new_tag": latest_tag,
                                "commit_hash": latest_commit_hash,
                                "last_pull": str(datetime.utcnow()),
                            }
                        )
                else:
                    if latest_tag:
                        updates.append(
                            {
                                "name": name,
                                "type": "tag-added",
                                "new_tag": latest_tag,
                                "commit_hash": latest_commit_hash,
                                "last_pull": str(datetime.utcnow()),
                            }
                        )
                    elif latest_commit_hash != current_hash:
                        updates.append(
                            {
                                "name": name,
                                "type": "commit",
                                "old_commit": current_hash,
                                "new_commit": latest_commit_hash,
                                "last_pull": str(datetime.utcnow()),
                            }
                        )

            except Exception as e:
                print(f"💥 Failed to check update for {name}: {e}")

        return updates

    def update_plugin(self, update_info):
        name = update_info["name"]
        plugin_path = os.path.join(self.plugins_dir, name)

        try:
            if update_info["type"] in ["tag", "tag-added"]:
                tag = update_info["new_tag"]
                subprocess.run(
                    ["git", "checkout", f"tags/{tag}"], cwd=plugin_path, check=True
                )
                print(f"✅ Updated {name} to tag {tag}")
            elif update_info["type"] == "commit":
                new_commit = update_info["new_commit"]
                subprocess.run(
                    ["git", "checkout", new_commit], cwd=plugin_path, check=True
                )
                print(f"✅ Updated {name} to commit {new_commit}")
            else:
                print(f"⚠️ Unknown update type for {name}")
                return

            lock_data = lfm.read_lock_file()
            for plugin in lock_data.get("plugins", []):
                if plugin["name"] == name:
                    plugin["git"]["commit_hash"] = update_info.get(
                        "commit_hash"
                    ) or update_info.get("new_commit")
                    plugin["git"]["tag"] = (
                        update_info.get("new_tag") if "new_tag" in update_info else None
                    )
                    plugin["git"]["last_pull"] = update_info["last_pull"]
                    break

            lfm.write_lock_file(lock_data)

        except Exception as e:
            print(f"💥 Failed to update {name}: {e}")

    def auto_update_all(self):
        updates = self.check_for_updates()
        lock_data = lfm.read_lock_file()

        if not updates:
            print("🎉 all plugins are up-to-date!")
            return

        for update in updates:
            name = update["name"]

            # find skip_auto_update flag from lock file
            plugin_info = next(
                (p for p in lock_data.get("plugins", []) if p["name"] == name), None
            )
            if plugin_info and plugin_info.get("skip_auto_update", False):
                print(f"⏭️ Skipping auto-update for {name} (skip_auto_update = true)")
                continue

            print(f"⬆️ Auto-updating {name} ...")
            self.update_plugin(update)
