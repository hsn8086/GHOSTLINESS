import importlib
import json
import logging
import os
import zipfile


class PluginManger:
    def __init__(self, server):
        self.server = server
        self.plugins = {}
        self.logger=logging.getLogger(__name__)

    def load_all(self):
        if not os.path.exists('plugins'):
            os.mkdir('plugins')

        for root, dirs, files in os.walk('plugins'):
            for file in files:
                if file.endswith('.pyz') and root.endswith('plugins'):
                    file_path = os.path.join(root, file)
                    self.load(file_path)



    def reload(self, name):
        # todo:reload
        pass

    def load(self, file_path):

        with zipfile.ZipFile(file_path, 'r') as zf:
            plugin_info = json.load(zf.open('plugin.json', 'r'))
            if 'name' in plugin_info:
                name = plugin_info['name']
                if name in self.plugins:
                    self.logger.error(
                        f'"{file_path}" cannot be loaded. A plugin with the same name already exists.')
                    return False
            else:
                self.logger.error(f'"{file_path}" cannot be loaded. The key named "name" in the configuration file is indeed.')
                return False
            if 'main' in plugin_info:
                module_name = f'plugins.{name}.{".".join(plugin_info["main"].split(".")[:-1])}'
            else:
                self.logger.error(f'"{name}" cannot be loaded. The key named "main" in the configuration file is indeed.')
                return False
            if 'version' in plugin_info:
                ver = plugin_info["version"]
            else:
                self.logger.error(f'"{name}" cannot be loaded. The key named "version" in the configuration file is indeed.')
                return False
            zf.extractall(os.path.join('plugins', name))

        module = importlib.import_module(module_name)
        self.plugins[name] = module
        if plugin_info["main"].split(".")[-1] in dir(module):
            getattr(module, plugin_info["main"].split(".")[-1])(self.server)
        self.logger.info(f'"{name}" is loaded! ver: {ver}.')
        return True

    def unload(self, name):
        # todo:unload plugin
        pass
