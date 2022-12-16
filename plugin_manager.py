import json
import os
import importlib
import sys
import zipfile
from types import ModuleType


class PluginManger:
    def __init__(self, server):
        self.server = server
        self.plugins = {}

    def load_all(self):
        if not os.path.exists('plugins'):
            os.mkdir('plugins')

        for root, dirs, files in os.walk('plugins'):
            for file in files:
                if file.endswith('.pyz') and root.endswith('plugins'):
                    file_path = os.path.join(root, file)
                    self.load(file_path)

    def reload(self, name):
        #todo:reload
        pass

    def load(self, file_path):

        with zipfile.ZipFile(file_path, 'r') as zf:
            plugin_info = json.load(zf.open('plugin.json', 'r'))
            if 'name' in plugin_info:
                name = plugin_info['name']
            else:
                # todo:日志输出:无法加载插件
                return
            if 'main' in plugin_info:
                ""
                module_name = f'plugins.{name}.{".".join(plugin_info["main"].split(".")[:-1])}'
            else:
                # todo:日志输出:无法加载插件
                return
            zf.extractall(os.path.join('plugins', name))

        module = importlib.import_module(module_name)
        self.plugins[name] = module
        if plugin_info["main"].split(".")[-1] in dir(module):
            getattr(module, plugin_info["main"].split(".")[-1])(self.server)

    def unload(self, name):
        # todo:unload plugin
        pass
