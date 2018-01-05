# -*- coding: utf-8 -*-
def options():
    import argparse

    m = argparse.ArgumentParser(description="Yukon options")

    m.add_argument("-login", type=str, default=False)
    m.add_argument("-password", type=str, default=False)
    m.add_argument("-host", type=str, default=False)
    m.add_argument("-port", type=str, default=False)
    m.add_argument("-rqdelay", type=str, default=100)

    opts = m.parse_args()
    options = vars(opts)

    if 'False' in repr(vars(opts)):
        return False
    else:
        return options['login'], options['password'], options['host'], options['port'], options['rqdelay']
