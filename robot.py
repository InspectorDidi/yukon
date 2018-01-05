# -*- coding: utf-8 -*-
import os
import sys
import time
import cPickle
import datetime
import tempfile
import random
import threading
import argparse
import dicttoxml
import platform                                                     # For tabulate
import statistics

# from atom.api import *

from includes import api
from includes import async
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import uic
from PyQt4.Qt import *
from PyQt4.QtWebKit import *                                        # for browser tab

from FinanceChart import *

"""
Else nuitka builds won't run on Wine
and Windows 7
"""
import pyexpat
import socket

"""
Important: cElementTree is preferred!
"""
import xml
import xml.etree.cElementTree as ET
try:
    import xml.etree.cElementTree as ET
except ImportError:
    print('Using slower ET')
    from lxml import etree as ET

sys.dont_write_bytecode = True

import requests
import json

def void_main():
    my_api = api.API()
    my_api.start_everything()

    run_code = my_api.gui.app.exec_()
    print('Program finished, exit code %s.' % run_code)
    sys.exit(0)  # For clean exit in Wine

if __name__ == '__main__':
    void_main()
