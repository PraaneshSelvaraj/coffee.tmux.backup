import os
import yaml


class PluginLoader:
    def __init__(self, path):
        self.COFFEE_PLUGINS_LIST_DIR = path

    def load_plugins(self):
        plugin_configs = []

        if not os.path.exists(self.COFFEE_PLUGINS_LIST_DIR):
            raise FileNotFoundError(
                f"The plugin directory '{self.COFFEE_PLUGINS_LIST_DIR}' doesn't exist."
            )

        for file in os.listdir(self.COFFEE_PLUGINS_LIST_DIR):
            if file.endswith(".yaml") or file.endswith(".yml"):
                file_path = os.path.join(self.COFFEE_PLUGINS_LIST_DIR, file)

                try:
                    with open(file_path, "r") as f:
                        data = yaml.safe_load(f)
                        if data:
                            plugin_data = {
                                "name": data.get("name", ""),
                                "url": data.get("url", ""),
                                "local": data.get("local", False),
                                "source": data.get("source", []),
                                "tag": data.get("tag", None),
                                "skip_auto_update": data.get("skip_auto_update", False),
                                "env": data.get("env", {}),
                            }

                            if plugin_data["name"] and plugin_data["url"]:
                                plugin_configs.append(plugin_data)

                except Exception as e:
                    print(f"Error Reading {file_path}:{e}")

        return plugin_configs
