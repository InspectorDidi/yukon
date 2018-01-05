# -*- coding: utf-8 -*-
from fastnumbers import *

global api


class Trader():

    """
    Trader - класс, который знает о текущих позициях
    """

    def __init__(self):
        api.pprint('Trader: Started.')
