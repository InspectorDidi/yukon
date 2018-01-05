# -*- coding: utf-8 -*-
"""
User functions for API actually are here
"""
import binascii

################################
# Most of API classes here:
# Strategies, coders, graph tools, storage
###############################


class Coder(object):
    """
    Just an example, made a class to be stateful
    if needed, also great for PEP20
    """

    def __init__(self):
        pass

    def hexlify(self, str_to_encode):
        return binascii.hexlify(str_to_encode)
