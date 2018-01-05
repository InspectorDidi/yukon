# -*- coding: utf-8 -*-
import sys
import time
import async
import codecs
import platform
from os import getcwd, listdir
"""
It's very important for import!
"""
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

global api


class PluginLoader():

    def __init__(self, lookupdir):
        """
        Never ever change this:
        """
        self.catch_errors = True
        """
        get dir and add to system path
        """
        self.pluginsdir = '%s/%s' % (getcwd(), lookupdir)
        sys.path.append(self.pluginsdir)

        """
        populate list of files to be loaded
        """
        self.found_plugins = []
        self.all_plugins = []
        self.trade_plugins = []

        try:
            pluginfiles = listdir(self.pluginsdir)
        except:
            pluginfiles = None

        if pluginfiles:
            for file in pluginfiles:
                """
                Check it's a good one
                """
                if file.endswith('.py') and '__init__' not in file:
                    self.found_plugins.append(file[:-3])
        else:
            api.pprint('No plugins dir found')

        """
        load and init plugins
        """
        for filename in self.found_plugins:
            if self.catch_errors:
                try:
                    self.process_import(filename)
                except Exception as inst:
                    api.pprint('Plugins: __init__: error in %s' % filename)
                    self.show_exception(inst, None)
                    pass
            else:
                self.process_import(filename)
        self.init()

    def process_import(self, filename):
        newplugin = self.loadplugin(filename)
        """ If import error, then: """
        if not newplugin:
            return False

        newplugin.is_running = False
        api.pprint('PluginLoader: Module [%s] loaded.' % (
            filename.upper()), 'green')
        """
        Check if it is good and tradeable
        """

        if hasattr(newplugin, 'plugin_name'):
            self.all_plugins.append(newplugin)
            """
            To make references like 'api.plugins.plugin...'
            """
            setattr(self, newplugin.plugin_name, newplugin)
            """
            So we can have:
            api.plugins.anyplugin.property
            """
            setattr(self, newplugin.plugin_name, newplugin)

    def loadplugin(self, filename):
        """
        That's okay!
        """
        try:
            mod = __import__(filename)
        except Exception as inst:
            api.pprint('Plugins: loadplugin: Error loading file: %s' %
                       filename, 'red')
            self.show_exception(inst, None)
            mod = False
        return mod

    """
    This is to notify plugins on disconnect etc...
    def alert(self, *args, **kwargs):
        for plugin in self.all_plugins:
            if hasattr(plugin, 'alert'):
                plugin.alert(api, *args, **kwargs)
    """

    @async.run
    def init(self):
        for plugin in self.all_plugins:
            if hasattr(plugin, 'init'):
                try:
                    plugin.init()
                except:
                    try:
                        self.stop_and_remove(plugin)
                    except:
                        pass

    @async.run
    def stop_plugins(self):
        for plugin in self.all_plugins:
            api.play('win32\sounds\whistle.wav')
            if hasattr(plugin, 'stop'):
                plugin.stop()
                plugin.is_running = False

    def stop_and_remove(self, plugin):
        """ Try to stop plugin """
        api.pprint('Plugins: stop_and_remove: Removing plugin %s ' %
                   plugin.plugin_name, 'red')
        if hasattr(plugin, 'stop'):
            try:
                plugin.stop()
            except:
                api.pprint(
                    'Plugins: stop_and_remove: Stop is bad too, I kill it now.')
            finally:
                self.all_plugins.remove(plugin)

    @async.run
    def start(self):
        for plugin in self.all_plugins:
            if hasattr(plugin, 'start'):
                try:
                    plugin.start()
                    api.play('win32\sounds\whistle.wav')
                except:
                    try:
                        self.stop_and_remove(plugin)
                    except:
                        pass

    def trade(self):
        for plugin in self.all_plugins:
            """
            Prevent from running it multiple times
            """
            if not plugin.is_running:
                plugin.is_running = True
                if hasattr(plugin, 'trade'):
                    self.do_trade(plugin)

    @async.run
    def do_trade(self, plugin):
        api.pprint('Starting %s.trade()' % plugin.plugin_name, 'green')
        if self.catch_errors:
            try:
                plugin.trade()
            except Exception as inst:
                self.show_exception(inst, plugin)
                """ This is HARD ERROR, so we try to stop and unload plugin """
                self.stop_and_remove(plugin)
        else:
            plugin.trade()

    def show_exception(self, inst, plugin):
        api.pprint(inst.args, 'red')
        """
            arguments stored in .args
            __str__ allows args to be printed directly
            """
        api.pprint('Error text: %s ' % (repr(inst)), 'red')
        api.pprint('Instance: %s' % (inst))
        if plugin:
            api.pprint('Plugins: Error in plugin: %s' %
                       plugin.plugin_name, 'red')

if __name__ == 'main':
    print('It starts somewhere else.')
