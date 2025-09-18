import os
import subprocess
import datetime
from core import lock_file_manager as lfm


class PluginInstaller:
    def __init__(self, plugins_config, plugins_dir, tmux_conf_path):
        self.plugins_config = plugins_config
        self.plugins_dir = plugins_dir
        self.tmux_conf_path = tmux_conf_path

    def install_all_plugins(self):
        for plugin in self.plugins_config:
            print(f"Installing {plugin.get('name')}...")
            success, used_tag = self._install_git_plugin(plugin)
            if success:
                print(f"✅ Successfully installed {plugin.get('name')} @ {used_tag}")
                self._update_lock_file(plugin, used_tag)
            else:
                print(f"❌ Failed to install {plugin.get('name')}")

    def _install_git_plugin(self, plugin):
        plugin_path = os.path.join(self.plugins_dir, plugin["name"])

        if os.path.exists(plugin_path):
            return True, plugin.get("tag", None)

        repo_url = f"https://github.com/{plugin['url']}"
        used_tag = plugin.get("tag")

        try:
            subprocess.run(
                ["git", "clone", repo_url, plugin_path],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            subprocess.run(
                ["git", "fetch", "--tags"],
                cwd=plugin_path,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            if used_tag:
                subprocess.run(
                    ["git", "checkout", used_tag],
                    cwd=plugin_path,
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                latest_tag = self._get_latest_tag(plugin_path)
                if latest_tag:
                    subprocess.run(
                        ["git", "checkout", f"tags/{latest_tag}"],
                        cwd=plugin_path,
                        check=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    used_tag = latest_tag

        except Exception as e:
            return False, None

        return True, used_tag or None

    def _install_git_plugin_with_progress(self, plugin, progress_callback=None):
        """Install git plugin with progress reporting"""
        plugin_path = os.path.join(self.plugins_dir, plugin["name"])

        if os.path.exists(plugin_path):
            if progress_callback:
                progress_callback(100)
            return True, plugin.get("tag", None)

        repo_url = f"https://github.com/{plugin['url']}"
        used_tag = plugin.get("tag")

        try:
            # Starting installation
            if progress_callback:
                progress_callback(5)

            # Clone repository
            subprocess.run(
                ["git", "clone", repo_url, plugin_path],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            if progress_callback:
                progress_callback(40)

            # Fetch tags
            subprocess.run(
                ["git", "fetch", "--tags"],
                cwd=plugin_path,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            if progress_callback:
                progress_callback(60)

            if used_tag:
                subprocess.run(
                    ["git", "checkout", used_tag],
                    cwd=plugin_path,
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                if progress_callback:
                    progress_callback(90)
            else:
                latest_tag = self._get_latest_tag(plugin_path)
                if progress_callback:
                    progress_callback(70)

                if latest_tag:
                    subprocess.run(
                        ["git", "checkout", f"tags/{latest_tag}"],
                        cwd=plugin_path,
                        check=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    used_tag = latest_tag

                if progress_callback:
                    progress_callback(90)

        except Exception as e:
            if progress_callback:
                progress_callback(0)
            return False, None

        return True, used_tag or None

    def _get_latest_tag(self, plugin_path):
        try:
            result = subprocess.run(
                ["git", "tag", "--sort=-creatordate"],
                cwd=plugin_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=True,
                text=True,
            )
            tags = result.stdout.strip().split("\n")
            if tags and tags[0]:
                return tags[0]
            else:
                return None
        except subprocess.CalledProcessError:
            return None

    def _update_lock_file(self, plugin, used_tag):
        sources = []
        plugin_path = os.path.join(self.plugins_dir, plugin["name"])

        for source in plugin["source"]:
            sources.append(os.path.join(plugin_path, source))

        plugin_data = {
            "name": plugin["name"],
            "sources": sources,
            "enabled": plugin.get("enabled", True),
            "env": plugin.get("env", {}),
            "skip_auto_update": plugin.get("skip_auto_update", False),
            "git": {
                "repo": plugin["url"],
                "tag": used_tag,
                "commit_hash": self._get_commit_hash(plugin),
                "last_pull": self._get_current_timestamp(),
            },
        }

        lock_data = lfm.read_lock_file()

        existing_plugin = next(
            (p for p in lock_data["plugins"] if p["name"] == plugin["name"]), None
        )

        if not existing_plugin:
            lock_data["plugins"].append(plugin_data)

        lfm.write_lock_file(lock_data)

    def _get_commit_hash(self, plugin):
        plugin_path = os.path.join(self.plugins_dir, plugin["name"])
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=plugin_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    def _get_current_timestamp(self):
        return str(datetime.datetime.utcnow())
