# -*- coding: utf-8 -*-#
from includes import async

"""   Every plugin has plugin_name   """
plugin_name = u'Краштест'

"""    Imports if needed, go here   """
from random import randint as rnd

"""   Define some classes, functions, globals if needed   """
global api


""" init and trade must be in every plugin """


def init():
    api.pprint(u'Краштест запущен.', 'red')


def trade():
    while True:
        myrand = rnd(0, 10)
        if myrand == 8:
            api.pprint(
                u'Совершаем плановую проверку на ошибки в торговом роботе.', 'red')
            mynull = 0
            res = myrand / mynull
        api.sleep(0.01)
