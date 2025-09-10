import os
import subprocess
import threading
from datetime import datetime, timezone
from core import lock_file_manager as lfm
from rich.console import Console

console = Console()


class PluginUpdater:
    def __init__(self, plugins_dir):
        self.plugins_dir = plugins_dir
        self._update_threads = {}

    def _safe_check_output(self, cmd, cwd=None, default=None):
        """Safely execute git commands with error handling"""
        try:
            return subprocess.check_output(cmd, cwd=cwd, text=True).strip()
        except subprocess.CalledProcessError as e:
            console.log(f"[red]Git command failed:[/red] {' '.join(cmd)} -> {e}")
            return default
        except FileNotFoundError:
            console.log("[red]Git not found on PATH[/red]")
            return default

    def _get_local_head_commit(self, plugin_path, short=False):
        """Get the current local HEAD commit hash"""
        out = self._safe_check_output(["git", "rev-parse", "HEAD"], cwd=plugin_path)
        if out and short:
            return out[:7]
        return out

    def _get_repo_size(self, plugin_path):
        """Get repository size on disk"""
        try:
            result = subprocess.run(
                ["du", "-sh", ".git"], cwd=plugin_path, capture_output=True, text=True
            )
            if result.returncode == 0:
                return result.stdout.strip().split()[0]
        except Exception:
            pass
        return "Unknown"

    def _get_time_since_tag(self, plugin_path, tag):
        """Get human-readable time since a tag was created"""
        if not tag:
            return "Unknown"
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--format=%cr", f"tags/{tag}"],
                cwd=plugin_path,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return "Unknown"

    def _get_remote_tags(self, repo_url):
        """Fetch all remote tags for a repository"""
        try:
            result = subprocess.run(
                ["git", "ls-remote", "--tags", repo_url],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                console.log(f"[yellow]Failed to fetch tags for {repo_url}[/yellow]")
                return []

            tags = []
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) == 2 and "refs/tags/" in parts[1]:
                    tag = parts[1].split("/")[-1]
                    # Strip trailing ^{} if present (annotated tags)
                    if tag.endswith("^{}"):
                        tag = tag[:-3]
                    tags.append(tag)

            # Sort tags by version if possible, otherwise alphabetically
            return sorted(set(tags), reverse=True)

        except Exception as e:
            console.log(f"[red]Failed to fetch remote tags for {repo_url}:[/red] {e}")
            return []

    def _get_latest_commit(self, repo_url, branch="HEAD"):
        """Get the latest commit hash from remote repository"""
        try:
            result = subprocess.run(
                ["git", "ls-remote", repo_url, branch],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout.split()[0]
        except Exception as e:
            console.log(f"[red]Failed to fetch latest commit for {repo_url}:[/red] {e}")
        return None

    def _get_tag_commit_hash(self, repo_url, tag):
        """Get commit hash for a specific remote tag"""
        try:
            result = subprocess.run(
                ["git", "ls-remote", repo_url, f"refs/tags/{tag}"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout.split()[0]
        except Exception as e:
            console.log(f"[red]Failed to fetch commit hash for tag {tag}:[/red] {e}")
        return None

    def _write_lockfile_update(self, name, new_tag=None, new_commit=None):
        """Update the lock file with new plugin information"""
        try:
            lock_data = lfm.read_lock_file()
            for plugin in lock_data.get("plugins", []):
                if plugin["name"] == name:
                    git_info = plugin.setdefault("git", {})
                    if new_commit:
                        git_info["commit_hash"] = new_commit
                    if new_tag is not None:
                        git_info["tag"] = new_tag
                    git_info["last_pull"] = datetime.utcnow().isoformat()
                    break
            lfm.write_lock_file(lock_data)
            return True
        except Exception as e:
            console.log(f"[red]Failed to update lockfile for {name}:[/red] {e}")
            return False

    def check_for_updates(self):
        """Check for updates without downloading plugin code"""
        updates = []
        lock_data = lfm.read_lock_file()

        for plugin in lock_data.get("plugins", []):
            name = plugin["name"]
            plugin_path = os.path.join(self.plugins_dir, name)
            git_info = plugin.get("git", {})
            repo = git_info.get("repo")
            repo_url = f"https://github.com/{repo}" if repo else None

            # Handle missing plugin or repository
            if not os.path.exists(plugin_path) or not repo_url:
                updates.append(
                    {
                        "name": name,
                        "current_version": "Not installed",
                        "new_version": "Not installed",
                        "size": "N/A",
                        "released": "N/A",
                        "changelog": ["Plugin not installed or missing URL"],
                        "marked": False,
                        "progress": 0,
                        "_internal": {"update_available": False},
                    }
                )
                continue

            current_tag = git_info.get("tag")
            current_commit = git_info.get("commit_hash")

            update_available = False
            new_tag = None
            new_commit = None
            update_type = "commit"

            if current_tag:
                # TAG-BASED PLUGIN: Check for newer tags
                console.log(
                    f"[blue]Checking tag-based plugin: {name} (current: {current_tag})[/blue]"
                )

                remote_tags = self._get_remote_tags(repo_url)
                if remote_tags:
                    latest_tag = remote_tags[0]  # First tag after sorting
                    new_tag = latest_tag
                    update_type = "tag"

                    # Check if we have a newer tag
                    if current_tag != latest_tag:
                        # Get commit hash for the new tag
                        new_commit = self._get_tag_commit_hash(repo_url, latest_tag)
                        update_available = True
                    else:
                        new_tag = current_tag
                        new_commit = current_commit
                else:
                    # No remote tags found, fallback to current
                    new_tag = current_tag
                    new_commit = current_commit
            else:
                # COMMIT-BASED PLUGIN: Check for newer commits
                console.log(
                    f"[blue]Checking commit-based plugin: {name} (current: {current_commit[:7] if current_commit else 'unknown'})[/blue]"
                )

                latest_commit = self._get_latest_commit(repo_url)
                if latest_commit:
                    new_commit = latest_commit
                    update_available = current_commit != latest_commit
                else:
                    new_commit = current_commit

            # Determine display versions
            current_version = current_tag or (
                current_commit[:7] if current_commit else "Unknown"
            )
            new_version = new_tag or (new_commit[:7] if new_commit else "Unknown")

            updates.append(
                {
                    "name": name,
                    "current_version": current_version,
                    "new_version": new_version,
                    "size": self._get_repo_size(plugin_path),
                    "released": self._get_time_since_tag(
                        plugin_path, new_tag or current_tag
                    ),
                    "changelog": (
                        [f"Update available: {current_version} → {new_version}"]
                        if update_available
                        else ["Up-to-date"]
                    ),
                    "marked": False,
                    "progress": 0,
                    "_internal": {
                        "type": update_type,
                        "old_tag": current_tag,
                        "new_tag": new_tag,
                        "old_commit": current_commit,
                        "new_commit": new_commit,
                        "plugin_path": plugin_path,
                        "repo_url": repo_url,
                        "update_available": update_available,
                    },
                }
            )

        return updates

    def update_plugin(self, update_info, progress_callback=None):
        """Update a single plugin by fetching the appropriate tag or commit"""
        name = update_info["name"]
        internal = update_info["_internal"]
        plugin_path = internal["plugin_path"]
        repo_url = internal["repo_url"]

        if not internal.get("update_available", False):
            console.log(f"[yellow]No update available for {name}[/yellow]")
            return False

        def send_progress(progress):
            if progress_callback:
                progress_callback(name, progress)

        try:
            send_progress(10)
            console.log(f"[blue]Updating {name}...[/blue]")

            if internal["type"] == "tag":
                # TAG-BASED UPDATE
                tag = internal["new_tag"]
                console.log(f"[blue]Fetching tag {tag} for {name}[/blue]")

                # Fetch the specific tag
                result = subprocess.run(
                    [
                        "git",
                        "fetch",
                        "--depth=1",
                        "origin",
                        f"refs/tags/{tag}:refs/tags/{tag}",
                    ],
                    cwd=plugin_path,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                send_progress(50)

                # Checkout the tag
                subprocess.run(
                    ["git", "checkout", f"tags/{tag}"],
                    cwd=plugin_path,
                    check=True,
                    capture_output=True,
                    text=True,
                )
            else:
                # COMMIT-BASED UPDATE
                commit = internal["new_commit"]
                console.log(f"[blue]Fetching commit {commit[:7]} for {name}[/blue]")

                # Fetch the specific commit
                subprocess.run(
                    ["git", "fetch", "origin", commit],
                    cwd=plugin_path,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                send_progress(50)

                # Checkout the commit
                subprocess.run(
                    ["git", "checkout", commit],
                    cwd=plugin_path,
                    check=True,
                    capture_output=True,
                    text=True,
                )

            send_progress(90)

            # Get the actual commit hash after checkout
            actual_commit = self._get_local_head_commit(plugin_path)

            # Update lock file with new information
            success = self._write_lockfile_update(
                name,
                new_tag=internal.get("new_tag"),
                new_commit=actual_commit,
            )

            if success:
                send_progress(100)
                console.log(f"[green]✓ Updated {name} successfully[/green]")
                return True
            else:
                console.log(f"[red]✗ Failed to update lockfile for {name}[/red]")
                return False

        except subprocess.CalledProcessError as e:
            console.log(f"[red]✗ Update failed for {name}:[/red] {e}")
            if hasattr(e, "stderr") and e.stderr:
                console.log(f"[red]Error details:[/red] {e.stderr}")
            send_progress(0)
            return False
        except Exception as e:
            console.log(f"[red]✗ Unexpected error updating {name}:[/red] {e}")
            send_progress(0)
            return False

    # --- Async helpers ---
    def update_plugin_async(self, update_info, progress_callback=None):
        """Update a plugin asynchronously"""
        name = update_info["name"]

        def thread_fn():
            try:
                success = self.update_plugin(update_info, progress_callback)
                if not success and progress_callback:
                    progress_callback(name, 0)
            except Exception as e:
                console.log(f"[red]Async update failed for {name}:[/red] {e}")
                if progress_callback:
                    progress_callback(name, 0)
            finally:
                # Clean up thread reference
                self._update_threads.pop(name, None)

        thread = threading.Thread(target=thread_fn, daemon=True)
        self._update_threads[name] = thread
        thread.start()
        return thread

    def update_marked_plugins(self, updates, progress_callback=None):
        """Update all plugins marked for update"""
        threads = []
        for update in updates:
            if update.get("marked", False):
                thread = self.update_plugin_async(update, progress_callback)
                threads.append(thread)
        return threads

    def update_all_plugins(self, updates, progress_callback=None):
        """Update all plugins that have available updates"""
        threads = []
        for update in updates:
            if update.get("_internal", {}).get("update_available", False):
                thread = self.update_plugin_async(update, progress_callback)
                threads.append(thread)
        return threads

    def auto_update_all(self):
        """Automatically update all plugins that have updates available"""
        console.log("[blue]Checking for plugin updates...[/blue]")
        updates = self.check_for_updates()
        lock_data = lfm.read_lock_file()

        available_updates = [
            u for u in updates if u.get("_internal", {}).get("update_available", False)
        ]

        if not available_updates:
            console.log("[green]🎉 All plugins are up-to-date![/green]")
            return

        console.log(
            f"[blue]Found {len(available_updates)} plugin(s) with updates[/blue]"
        )

        for update in available_updates:
            name = update["name"]
            plugin_info = next(
                (p for p in lock_data.get("plugins", []) if p["name"] == name), None
            )

            if plugin_info and plugin_info.get("skip_auto_update", False):
                console.log(
                    f"[yellow]⏭️ Skipping auto-update for {name} (skip_auto_update = true)[/yellow]"
                )
                continue

            console.log(
                f"[blue]⬆️ Auto-updating {name}: {update['current_version']} → {update['new_version']}[/blue]"
            )
            success = self.update_plugin(update)

            if success:
                console.log(f"[green]✓ {name} updated successfully[/green]")
            else:
                console.log(f"[red]✗ Failed to update {name}[/red]")

    def get_update_status(self, plugin_name):
        """Get the current update status of a specific plugin"""
        return self._update_threads.get(plugin_name)

    def cancel_update(self, plugin_name):
        """Cancel an ongoing update (if possible)"""
        thread = self._update_threads.get(plugin_name)
        if thread and thread.is_alive():
            console.log(
                f"[yellow]Cannot cancel ongoing update for {plugin_name} (thread already running)[/yellow]"
            )
            return False
        return True
