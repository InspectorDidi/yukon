# -*- coding: utf-8 -*-
from functools import wraps
from PyQt4 import QtCore


class Runner(QtCore.QThread):

    def __init__(self, target, *args, **kwargs):
        #super(Runner, self).__init__()
        QtCore.QThread.__init__(self)
        self._target = target
        self._args = args
        self._kwargs = kwargs

    def run(self):
        self._target(*self._args, **self._kwargs)


def run_qt(func):
    @wraps(func)
    def async_func(*args, **kwargs):
        runner = Runner(func, *args, **kwargs)
        # Keep the runner somewhere or it will be destroyed
        func.__runner = runner
        runner.start()
    return async_func


# Async is a simple set of decorators I found somwhere over the net
from threading import Thread
from functools import wraps


def run(func):
    @wraps(func)
    def async_func(*args, **kwargs):
        func_hl = Thread(target=func, args=args, kwargs=kwargs)
        func_hl.daemon = False
        func_hl.start()
        return func_hl
    return async_func
