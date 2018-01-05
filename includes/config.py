# -*- coding: utf-8 -*-
from saver import *
import cmdline
import os
global api


class ConfigLoader:

    """
    Configuration file and command line
    """

    def __init__(self):
        self.pickler = pickler('/config')
        self.commandline = cmdline.options()
        self.debug = False
        self.good = False

        if self.commandline:
            """ Case when command line is provided """
            self.login, self.password, self.ip, self.port, self.rqdelay = self.commandline
            if self.debug:
                print('Config: Command-line config.')
            self.save(self.commandline)
            self.good = True
        else:
            """ No cmdline, look for saved data """
            if self.debug:
                print('Config: Using saved configuration.')
                print(self.pickler, dir(self.pickler))

            config_data = self.pickler.yukon

            if (not config_data) or (len(config_data) != 5):
                if self.debug:
                    print('Saved config is bad.')

            try:
                (self.login, self.password, self.ip,
                 self.port, self.rqdelay) = config_data
                self.good = True
            except:
                if self.debug:
                    print('Bad config file. (again)')
                pass

    def save(self, config_data):
        self.pickler.save_as(config_data, 'yukon.pick')
