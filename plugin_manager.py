import os
import importlib
import sys
from types import ModuleType


class PluginManger:
    def __init__(self):
        if not os.path.exists('plugins'):
            os.mkdir('plugins')
        self.plugins_list = []
        for root, dirs, files in os.walk('plugins'):
            for file in files:
                if file.endswith(('.py', '.pyc', '.pyd')) and root.endswith(('plugins', 'handlers')):
                    file_path = os.path.join(root, file)
                    module_name = file_path[:file_path.rfind('.')].replace('\\', '.')

                    module = importlib.import_module(module_name)
                    self.plugins_list.append(module_name)
                    if 'init' in dir(module):
                        getattr(module, 'init')(self)

    def run(self, func: str, *args):
        for plugin in self.plugins_list:
            module = sys.modules[plugin]
            if func in dir(module):
                getattr(module, func)(*args)

    def reload(self, name):
        name = 'plugins.' + name
        if name in self.plugins_list:
            importlib.reload(sys.modules[name])

    def load(self, name):
        name = 'plugins.' + name

        module = importlib.import_module(name)
        self.plugins_list.append(name)
        if 'init' in dir(module):
            getattr(module, 'init')(self)

    def unload(self, name):
        name = 'plugins.' + name
        if name in self.plugins_list:
            self.plugins_list.remove(name)
            del sys.modules[name]

    def get_plugin(self, name) -> ModuleType:
        name = 'plugins.' + name
        if name in self.plugins_list:
            return sys.modules[name]
