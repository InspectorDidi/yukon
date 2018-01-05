# -*- coding: utf-8 -*-
import async
import time
import datetime
from table import Table
from stakan import Stakan
from proxy import Proxy
from fastnumbers import *
from collections import defaultdict

global api

"""
Fixme: res['success'] is wrong, do res.get() ******
"""


class Stock():

    """
       _____ _             _
      / ____| |           | |
     | (___ | |_ ___   ___| | __
      \___ \| __/ _ \ / __| |/ /
      ____) | |_ (_) | (__|   \
     |_____/ \__\___/ \___|_|\_\


    Stock - main class for stock data, has Markets, Security records etc...
    """

    def __init__(self):
        __builtins__['stock'] = self
        api.pprint('Stock: Started.')
        self.shares_dict, self.futures_dict, self.options_dict = None, None, None
        self.orders_count = 0
        """
        Non-nullable tables here:
        """
        self.dict_connector = dict.fromkeys(
            ['queue_size', 'version', 'queue_mem_used'])

        """
        Constant (non-nullable tables are here)
        """
        self.server_status = Table()
        self.commands = Table()

        """
        Market-related tables here:
        """
        self.null_tables()
        self.subscribed = []

        self.mapping = {
            u'orders_table': self.orders,
            u'trades_table': self.trades,
            u'commands_table': self.commands,
            u'securities_table': self.securities
        }

    def null_stakan(self):
        """
        Empty stakan on disconnect
        """
        self.quotes = Stakan()

    def null_tables(self):
        """
        Create tables when started
        """
        self.quotes = Stakan()
        self.alltrades = Table()
        self.markets = Table()
        self.boards = Table()
        self.candlekinds = Table()
        self.securities = Table()
        self.positions = Table()
        self.result = Table()
        self.quotations = Table()
        self.client = Table()
        self.orders = Table()
        self.news = Table()
        self.pits = Table()
        self.sec_info_upd = Table()
        self.messages = Table()
        self.trades = Table()

    def on_connect(self):
        api.pprint('Stock: on_connect: ready.', 'green')
        self.shares_dict = self.securities.find_table(
            {'sectype': 'SHARE', 'active': 'true'}).to_dict()
        self.options_dict = self.securities.find_table(
            {'sectype': 'OPT', 'active': 'true'}).to_dict()
        self.futures_dict = self.securities.find_table(
            {'sectype': 'FUT', 'active': 'true'}).to_dict()

    """    Returns secid (0001) for a given seccode ('LKOH')
    """

    def get_secid(self, seccode):
        val = None
        retries = 0

        while val is None and retries < 10:
            try:
                _res = self.securities.find_one({'seccode': seccode})
                val = _res['secid']
            except:
                retries += 1
                time.sleep(0.1)

        if retries == 10 and val is None:
            api.pprint('Stock: Failed to find SECID for code %s' %
                       seccode, 'red')
        else:
            #api.pprint('Stock: found [%s]' % seccode)
            pass
        return val

    """
    Returns board (0001) for a given seccode ('LKOH')
    """

    def get_board(self, seccode):
        val = None
        retries = 0

        while val is None and retries < 10:
            try:
                _res = self.securities.find_one({'seccode': seccode})
                val = _res['board']
            except:
                retries += 1
                time.sleep(0.1)

        if retries == 10 and val is None:
            api.pprint('Stock: Failed to find board for %s' % seccode, 'red')
            val = None
        return val

    """
    Subscribe by seccode, i.e: api.subscribe ('SiZ6')
    """
    @async.run
    def subscribe(self, seccode):
        #api.pprint('Stock: Subscribing [%s]' % seccode)
        secid = self.get_secid(seccode)

        if secid:
            api.datasource.connector.send_command({'id': 'subscribe',
                                                   'quotations': {'secid': secid}, 'quotes': {'secid': secid},
                                                   'alltrades': {'secid': secid}})

            """
            api.datasource.connector.send_command({'id': 'subscribe_ticks',
               'filter': 'false', 'security': {'secid': secid, 'tradeno': '1'}})
            """
            if seccode not in self.subscribed:
                self.subscribed.append(seccode)
                if api.debug:
                    api.pprint('Stock: Append self.subscribed')
                    api.pprint(self.subscribed)
        else:
            api.pprint('Stock: Error - no secid for %s' % (seccode), 'red')

    """
    Returns client
    """

    def get_client(self):
        _res = self.client.get_last()
        if 'id' in _res.keys():
            id = _res['id']
        else:
            id = None
        return id

    """
    Re-Subscribe after disconnect
    """

    def resubscribe(self):
        self.null_stakan()  # Else stakan shows unused rows
        if api.debug:
            api.pprint('Stock: Connection restored, resubscribing', 'green')
            api.pprint(self.subscribed)

        for seccode in self.subscribed:
            self.subscribe(seccode)

    def get_offer(self):
        return self.get_float('offer')

    def get_bid(self):
        return self.get_float('bid')

    def close_position(self, seccode):
        api.pprint('API: close position', 'green')

        lots = self.get_forts_position(seccode)
        if lots > 0:
            self.sell_market(seccode, lots)
        else:
            self.buy_market(seccode, abs(lots))

    def buy_market(self, seccode, lots=1, brokerref=''):
        lots = fast_int(lots)
        board = self.get_board(seccode)
        client = self.get_client()

        if client and board:
            self.orders_count += 1
            res = api.datasource.connector.send_command({
                'id': 'neworder',
                'security': {'seccode': seccode, 'board': board},
                'brokerref': brokerref, 'quantity': lots, 'buysell': 'B',
                'bymarket': True, 'client': client
            })

            if res['success'] == 'true':
                id = res['transactionid']
                api.pprint('<b>BUY ACCEPTED</b>, id=[%s]' % id, 'green')
                return id
            else:
                return False
        else:
            api.pprint(
                '<b>Stock: buy_market: No client or board (No connection?)</b>', 'red')
            return False

    def sell_market(self, seccode, lots=1, brokerref=''):
        lots = fast_int(lots)
        board = self.get_board(seccode)
        client = self.get_client()

        if client and board:
            self.orders_count += 1
            res = api.datasource.connector.send_command({
                'id': 'neworder',
                'security': {'seccode': seccode, 'board': board},
                'brokerref': brokerref, 'quantity': lots, 'buysell': 'S',
                'bymarket': True, 'client': client
            })

            if res['success'] == 'true':
                id = res['transactionid']
                api.pprint('<b>SELL ACCEPTED</b>, id=[%s]' % id, 'red')
                return id
            else:
                return False
        else:
            api.pprint(
                '<b>Stock: sell_market: No client or board (No connection?)</b>', 'red')
            return False

    ################################
    #      Needed functions
    ###############################

    def get_current_contract(self, prefix='Si', day=None, month=None, year=None):
        if not day:
            today = datetime.datetime.now()
            year = int(today.year)
            month = int(today.month)
            day = int(today.day)

        codes = ['H', 'M', 'U', 'Z', 'H']
        # H expires on month 3
        # M expires on month 6
        # U on month 9
        # Z on month 12
        quartal = int(month // 3)
        monthcode = codes[quartal]
        if month in [3, 6, 9, 12] and day < 15:
            monthcode = codes[quartal - 1]

        if (month == 12) & (monthcode == 'H'):
            yearcode = str(year + 1)[-1]
            # SiH7 for end of '2016
        else:
            yearcode = str(year)[-1]
        result = prefix + monthcode + yearcode
        # was for debugging print('Code: [%s]' % result)
        return result

    def get_forts_all_money(self):
        _res = 0.0
        for pos_dict in self.positions():
            for k, v in pos_dict.iteritems():
                if k == 'current' and v:
                    _res = float(v)
        return _res

    def get_forts_free_money(self):
        _res = 0.0
        for pos_dict in self.positions():
            for k, v in pos_dict.iteritems():
                if k == 'free' and v:
                    _res = float(v)
        return fast_int(_res)

    def get_varmargin(self, seccode):
        dict_positions = self.get_forts_position_dict(seccode)
        varmargin = dict_positions.get('varmargin') or 0
        return fast_float(varmargin)

    def get_forts_position_dict(self, seccode):
        """    ^^^^^^^^^^^^^^^^^^^^^^^^ This returns:
        {'optmargin': '0.0', 'blocked': None, 'secid': '16060', 'expirationpos': '0',
        'union': None, 'todaysell': '1', 'opensells': '0', 'current': None,
        'openbuys': '0', 'shortname': None, 'seccode': 'SiZ6', 'varmargin': '208.0',
        'free': None, 'todaybuy': '1', 'totalnet': '-1', 'startnet': '-1',
        'markets': None, 'client': '7618xz0'}
        """
        res_dict = self.positions.find_one({'seccode': seccode}) or {}
        return res_dict

    def get_forts_position(self, seccode):
        """
        Returns:
        1, 0 or whatever lots you bought/sold
        """
        res_dict = self.get_forts_position_dict(seccode)
        _res = res_dict.get('totalnet', 0)
        return fast_int(_res)

    def get_trades_dict(self, seccode):
        """    ^^^^^^^^^^^^^^^^^^^^^^^^ This returns:
        {'optmargin': '0.0', 'blocked': None, 'secid': '16060', 'expirationpos': '0',
        'union': None, 'todaysell': '1', 'opensells': '0', 'current': None,
        'openbuys': '0', 'shortname': None, 'seccode': 'SiZ6', 'varmargin': '208.0',
        'free': None, 'todaybuy': '1', 'totalnet': '-1', 'startnet': '-1',
        'markets': None, 'client': '7618xz0'}
        """
        res_dict = self.trades.find({'seccode': seccode}) or {}
        api.pprint(res_dict)
        return res_dict
        """
        [
        {'value': '0', 'buysell': 'S', 'comission': '0.0', 'quantity': '1', 'union': None,
        'items': '1', 'price': '64282', 'yield': '0.0', 'settlecode': None, 'accruedint': '0.0',
        'client': '7618xz0', 'tradetype': 'T', 'board': 'FUT', 'time': '07.11.2016 17:02:37',
        'tradeno': '1633123339', 'orderno': '23559230679', 'brokerref': None, 'currentpos': '0',
        'seccode': 'SiZ6', 'secid': '16060'},

        {'value': '0', 'buysell': 'B', 'comission': '0.0', 
        'quantity': '1', 'union': None, 'items': '1', 'price': '64175', 'yield':'0.0', 
        'settlecode': None, 'accruedint': '0.0', 'client': '7618xz0', 'tradetype': 'T', 
        'board': 'FUT', 'time': '07.11.2016 21:56:02', 'tradeno': '1633406879', 
        'orderno': '23564475956', 'brokerref': None,'currentpos': '0', 'seccode': 'SiZ6', 
        'secid': '16060'}
        ]
        """

    def get_float(self, key):
        _res = fast_float(self.quotations.get_last().get(key, 0.0))
        return _res

    def get_current_price(self):
        return self.get_float('marketpricetoday')

    def get_last_price(self):
        return self.get_float('marketpricetoday')

    def get_waprice(self):
        return self.get_float('waprice')

"""
3.8 neworder 
Подать новую заявку на биржу 
<command id="neworder"> 
<security> 
<board> идентификатор режима торгов </board> 
<seccode> код инструмента </seccode> 
</security> 
<client>клиент</client> 
<union>union code</union> 
<price>цена</price> 
<hidden>скрытое количество в лотах</hidden> 
<lots>количество в лотах</lots> 
<buysell>B</buysell> 
("В" - покупка, или "S" – продажа) 
<bymarket/> 
<brokerref>примечание</brokerref>   
(будет возвращено в составе структур order и trade) 
<unfilled>PutInQueue</unfilled>   
(другие возможные значения: CancelBalance, ImmOrCancel) 
<usecredit/> 
<nosplit/> 
<expdate>дата экспирации (только для ФОРТС)</expdate> 
(задается в формате 23.07.2012 00:00:00 (не обязательно) 
</command> 
Для идентификации инструмента необходимо задать элемент <security>.
"""
