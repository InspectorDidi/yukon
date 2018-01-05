# -*- coding: utf-8 -*-
"""
Try to use the fastest xml library
"""
try:
    import xml.etree.cElementTree as ET
    print('Using cElementTree')
except ImportError:
    print('Using slower ET')
    from lxml import etree as ET

from table import Table
import time
from includes import async

"""
It's very important for parsing!
Really.

Just leave me alone, I know what I'm doing.
"""
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
global api


class Parser (object):

    """
      _____
     |  __ \
     | |__) |_ _ _ __ ___  ___ _ __
     |  ___/ _` | '__/ __|/ _ \ '__|
     | |  | (_| | |  \__ \  __/ |
     |_|   \__,_|_|  |___/\___|_|

    Class for interpreting XML data provided by Transaq XML connector
    It builds data for given market
    """

    def __init__(self):
        self.debug = False
        """
        First map keys to functions
        """
        self.parse_options = {
            'result': self.result,
            'server_status': self.server_status,
            'securities': self.securities,
            'sec_info_upd': self.sec_info_upd,
            'quotes': self.quotes,
            'alltrades': self.alltrades,
            'client': self.client,
            'connector_version': self.connector_version,
            'markets': self.markets,
            'boards': self.boards,
            'pits': self.pits,
            'candlekinds': self.candlekinds,
            'orders': self.orders,
            'trades': self.trades,
            'positions': self.positions,
            'overnight': self.overnight,
            'news_header': self.news_header,
            'messages': self.messages,
            'quotations': self.quotations,
            'error': self.error
        }

        self.df = None
        self.api = api
        self.datasource = api.datasource
        self.stock = api.stock
        self.run = False
        self.banned_keys = ['union', 'settlecode',
                            'sec_tz', 'comission', 'accruedint']
        self.api.pprint('Parser: Started.')

        """ DEBUG: Start plugins (only when debug is enabled) """
        if self.api.debug:
            self.debug_start_plugins()
            self.api.server_button_change(state='debug')

    @async.run_qt
    def debug_start_plugins(self):
        self.api.pprint(
            'DataParser: Debug mode, starting plugins NOW...', 'red')
        """
        Do a very small delay
        """
        while not hasattr(self.api, 'plugins'):
            self.api.pprint('Dataparser: Waiting plugins to load.')
            self.api.sleep(0.3)
        self.api.plugins.init()
        self.api.plugins.start()
        self.api.plugins.trade()
        api.pprint('Dataparser: Plugins started', 'green')

    def xml_parse(self, xmltext):
        """
        I know it's your favourite part.
        But no, you CAN'T do it any faster.
        """
        tree = ET.fromstring(xmltext)
        self.xmltag = tree.tag
        mylist = []

        if tree.keys():
            _res = {}
            for key, value in tree.items():
                _res.update({key: value})
            mylist.append(_res)
        else:
            _res = {}
            for child in tree.getchildren():
                _res = {}
                if child.attrib:
                    _res.update(child.attrib)
                for more in child.getchildren():
                    if more.attrib:
                        _res.update(more.attrib)
                    else:
                        _res.update({more.tag: more.text})
                mylist.append(_res)
        """
        Clean
        """
        for _dict in mylist:
            for _key in self.banned_keys:
                if _key in _dict.keys():
                    _dict.pop(_key)
        return mylist

    def alltrades(self):
        self.stock.alltrades.merge(self.df())
        self.stock.alltrades.truncate(20000)

    def quotes(self):
        """
        Stakan
        """
        for row in self.df.rows:
            self.stock.quotes.update(row)  # special case for Stakan

    def quotations(self):
        """
        Base parameters
        """
        self.stock.quotations.add_one(self.df.rows[0])

    def connector_version(self):
        pass

    def client(self):
        self.stock.client = self.df

    def positions(self):
        self.stock.positions = self.df

    def orders(self):
        self.stock.orders.merge(self.df())

    def trades(self):
        self.stock.trades.merge(self.df())

    def overnight(self):
        pass

    def news_header(self):
        pass

    def pits(self):
        pass
        # self.stock.pits.merge(self.df()) - v.61

    def sec_info_upd(self):
        pass
        # self.stock.sec_info_upd.merge(self.df()) - v.61

    def boards(self):
        self.stock.boards = self.df

    def markets(self):
        # self.stock.markets = self.df - v.61
        pass

    def candlekinds(self):
        # self.stock.candlekinds = self.df - v.61
        pass

    def securities(self):
        self.stock.securities.merge(self.df())

    def result(self):
        self.stock.result = self.df

    def messages(self):
        # self.stock.messages.merge(self.df())
        pass

    def server_status(self):
        self.datasource.server_status = self.df.get_last()
        """
        When we receive that info, button is already disabled from API
        """
        if self.datasource.server_status['connected'] != 'true':
            self.api.server_button_change(state='offline')
            self.stock.null_tables()    # v.75 - didnt null on recover

        if self.datasource.server_status['connected'] == 'error':
            if hasattr(self.datasource.server_status, 'server_status'):
                errmsg = self.datasource.server_status['server_status']
            else:
                errmsg = 'Unknown connection problem: <b>%s</b>' % self.datasource.server_status
            self.api.pprint('DataParser: Connection error: %s' % errmsg, 'red')
            self.api.play('win32\sounds\disconnected.wav')
            self.stock.null_tables()
            """
            Later, add alert with disconnetion message for every plugin
            self.api.plugins.alert(message=errmsg)
            """

        if self.datasource.server_status['connected'] == 'true':
            """
            Process some callbacks.
            """
            self.api.stock.on_connect()
            self.api.on_connect()
            self.api.server_button_change(state='online')
            self.api.plugins.trade()

            if hasattr(self.datasource.server_status, 'recover'):
                if self.datasource.server_status['recover']:
                    self.api.pprint(
                        'DataParser: Recovering connection.', 'red')
                    self.stock.null_tables()
            else:
                if not self.stock.positions.empty():
                    self.api.pprint('DataParser: Connected OK.', 'green')
                    self.api.play('win32\sounds\start.wav')
                    self.stock.resubscribe()
                    """
                    Note from v.57:
                    This causes plugin to re-init causing more threads
                    (if any plugin is multithreaded)
                    that's 'by design', not a bug.
                    """
                    self.api.plugins.start()

    def error(self):
        self.api.pprint('DataParser: Error - %s' %
                        self.xmltext.decode('utf-8'))

    def parse(self, xmltext):
        self.xmltext = xmltext
        if self.debug:
            print(xmltext)

        res = self.xml_parse(xmltext)
        self.df = Table(data=res)
        self.parse_options[self.xmltag]()
