# -*- coding: utf-8 -*-
ver = u'РТС Робот v.1.00'
compiler = 'nuitka'                                                 # 'nuitka' or 'other'

"""
Actually, this is the main class in Yukon.
The class. The one. The root of everything.
"""

import datetime
import os
import sys
import tempfile
import winsound
import time
import threading
import async
import statistics
import _winreg
from collections import OrderedDict
from struct import calcsize
from fastnumbers import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from stock import Stock
from dataparser import Parser
from datasource import DataSource
from config import ConfigLoader
from lego import *
from plugins import PluginLoader
from csvrec import csv_writer
from bottle import app, route, get
from rocket import Rocket

####################################
# Main class for almost everything #
####################################

class API:

    def __init__(self):
        """
        Prepare commons
        """
        self.debug = False
        __builtins__['api'] = self
        self.platform = 'windows'
        self.logsdir = self.cwd() + '\logs'
        self.prepare()
        """
        Prepare GUI
        """
        self.buttonlist = [self.button_quit, self.button_server,
                           self.finam_defaults, self.finam_hft,
                           self.finam_demo, self.finam_mma, self.saveconfig,
                           self.button_futures,
                           self.button_shares, self.button_option,
                           self.button_settings,
                           self.button_sell, self.button_buy,
                           self.button_cancel, self.button_alltrades,
                           self.button_ask_queue, self.button_maximize,
                           self.button_close_position]

        self.windowmax = False
        self.gui = GUI('win32/window2.ui', buttons=self.buttonlist)
        fontpath = 'win32/fonts/'
        for font in os.listdir(fontpath):
            if font.endswith('.ttf'):
                fullpath = fontpath + font
                self.gui.load_font(fullpath)

        self.onIcon = QIcon(QPixmap("win32/icons/plug-on.png"))
        self.midIcon = QIcon(QPixmap("win32/icons/plug-mid.png"))
        self.offIcon = QIcon(QPixmap("win32/icons/plug-off.png"))
        self.gui.window.setWindowTitle(ver)
        self.gui.window.show()
        self.pprint(u'%s запущен.' % ver)

        """
        Init stock and start everything
        """
        self.run = True
        self.hft = False
        self.stock = Stock()

        """
        Serve right-clicks for table export to CSV
        """
        self.gui.update_exportable_tables()
        """
        RT Thread starts immediately
        """
        self.main_realtime_thread()
        self.mysec = self.stock.get_current_contract('Si')
        self.start_everything()
        os._exit(self.gui.app.exec_())

    ##############################
    #   Handle Qt context menus  #
    ##############################
    def export_to_csv(self, sender):
        tablename = unicode(sender.objectName().toUtf8(), encoding="UTF-8")

        if tablename == 'stakan':
            data = self.stock.quotes.to_dict()
        elif tablename == 'positions_table':
            data = self.stock.positions()
        elif tablename == 'client_table':
            data = self.stock.client()
        else:
            data = self.stock.mapping[tablename]()
        filename = self.gui.select_file(mask='*.csv')

        if not filename:
            return
        else:
            csv = csv_writer(delimiter=';', filename=filename)
            csv.record_list(data)

    def fast_export_to_csv(self, sender):
        """
        We can do also: api.fast_export_to_csv('positions_table')
        instead of double-clicking table!
        """
        if isinstance(sender, basestring):
            tablename = sender
        else:
            tablename = unicode(sender.objectName().toUtf8(), encoding="UTF-8")
        """
        Decide what to export.
        """
        if tablename == 'stakan':
            data = self.stock.quotes.to_dict()
        elif tablename == 'positions_table':
            data = self.stock.positions()
        elif tablename == 'client_table':
            data = self.stock.client()
        else:
            data = self.stock.mapping[tablename]()
        self.mkdir('export')
        filename = '%s/export/%s(%s).csv' % (self.cwd(),
                                             tablename, self.humantime_fs())
        csv = csv_writer(delimiter=';', filename=filename)
        csv.record_list(data)
        self.play('win32\sounds\photo.wav')

    def start_everything(self):
        """
        API variables and functions:
        api.pprint(), api.stock, api.config
        """
        self.pprint('API: Starting everything')
        """
        Create config, source, parser
        """
        self.readconfig()

        if not self.config.good:
            self.warn_no_config()

        self.datasource = DataSource()
        self.parser = Parser()
        self.plugins = PluginLoader('plugins')

        if hasattr(self.datasource.connector, 'hft'):
            self.hft = True
        """
        Start other threads last of everything
        """
        self.main_ui_thread()
        self.main_slow_thread()

    def on_connect(self):
        self.pprint('<b>API: on_Connect: Server connected.</b>', 'green')

    def humantime(self):
        return str(datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S.%f")[0:-7])

    def humantime_fs(self):
        return str(datetime.datetime.now().strftime("%d-%m-%Y-%H-%M-%S-%f")[0:-7])

    def warn_no_config(self):
        """
        Switch to settings tab
        """
        self.pprint('API: No config found')
        self.gui.msgbox(
            u'Конфигурация не найдена.<br>Заполните настройки.', title=u'Инфо')
        self.button_settings()

    def prepare(self):
        self.mkdir('config')

        """
        Clean up logs directory
        """
        for file in self.logsdir:
            if file.endswith('.log'):
                fullpath = '%s\%s' % (self.logsdir, file)
                print('os.remove(fullpath %s)' % fullpath)
                try:
                    pass
                    # os.remove(fullpath)
                except:
                    pass
        """
        Clean up pyinstaller folders which occasionally occur in tempdir
        """
        self.tempdir = tempfile.gettempdir()

        if compiler != 'nuitka':
            for file in os.listdir(self.tempdir):
                if file.startswith('_MEI'):
                    fullpath = '%s\%s' % (self.tempdir, file)
                    try:
                        os.remove(fullpath)
                    except:
                        pass

        """
        Clean dump files here
        """
        for file in os.listdir(os.getcwd()):
            if file.endswith('.mdmp'):
                fullpath = '%s\%s' % (os.getcwd(), file)
                try:
                    os.remove(fullpath)
                except:
                    pass

    def readconfig(self):
        self.config = ConfigLoader()
        if self.config.good:
            self.ip = self.config.ip
            self.port = self.config.port
            self.login = self.config.login
            self.password = self.config.password
            self.rqdelay = self.config.rqdelay
        else:
            self.ip, self.port, self.login, \
                self.password, self.rqdelay = '0.0.0.0', '3900', 'User', '', 10

    def saveconfig(self):
        self.config.save((self.login, self.password, self.ip,
                          self.port, (self.rqdelay or 100)))
        self.readconfig()
        self.start_everything()

    def pprint(self, text, *color, **kwargs):

        if hasattr(kwargs, 'color'):
            color = kwargs['color']
            text = '%s' % text

        if type(text) in [int, float, bool]:
            self.gui.pprint(text, **kwargs)
            return

        if type(text) == 'unicode':
            try:
                text = text.decode('utf-8')
            except:
                text = text.decode('unicode_escape')

        if color:
            _prefix = '<font color="%s">' % color
            _postfix = '</font>'
        else:
            _prefix, _postfix = '', ''

        self.gui.pprint('%s%s%s' % (_prefix, text, _postfix), **kwargs)

    """
    For special cases - straight to method!
    Used to setData in stakan
    """

    def set(self, **kwargs):
        self.gui.pprint(**kwargs)

################################
# Different API functions will be here...
###############################
    def cwd(self):
        return os.getcwd()

    def sleep(self, sec):
        if self.hft:
            min_sleep = 0.01
        else:
            min_sleep = 0.05
        if(sec < min_sleep):
            sec = min_sleep
        time.sleep(sec)

    def get_architecture(self):
        if calcsize("P") == 8:
            return 64
        else:
            return 32

    def numeric_time(self):
        t = (datetime.datetime.now().strftime("%H%M%S"))
        d = (datetime.datetime.now().strftime("%d%m%Y"))
        return int(t)

    def numeric_date(self):
        t = (datetime.datetime.now().strftime("%H%M%S"))
        d = (datetime.datetime.now().strftime("%d%m%Y"))
        return int(d)

    def mkdir(self, dirname):
        if not (os.path.isdir(dirname)):
            try:
                if self.debug:
                    print('API: Making dir: %s' % dirname)
                os.mkdir(dirname)
            except:
                print('API: Making dir: %s FAILED' % dirname)
                pass

################################
# Special 'Server' button behavior
###############################
    def button_close_position(self):
        self.stock.close_position(self.mysec)

    def server_button_change(self, **kwargs):
        """
        It's a special button with special behaviour!
        """
        state = kwargs.get('state')
        icon = self.offIcon
        style = ''

        if state == 'online':
            icon = self.onIcon
            style = ('QPushButton {background-color: green;}')

        elif state == 'offine' or state == 'debug':
            icon = self.offIcon
            style = ('QPushButton {background-color: red;}')

        elif state == 'connecting':
            icon = self.onIcon
            style = ('QPushButton {background-color: orange;}')

        """
        Set chosen icon and style
        """

        self.gui.call_method(
            field=self.gui.window.button_server, method='setIcon', what=icon)
        self.gui.call_method(
            field=self.gui.window.button_server, method='setStyleSheet', what=style)

################################
# Serve main UI buttons
###############################
    def button_maximize(self):
        if not self.windowmax:
            self.gui.hide_title()
            self.gui.maximize()
            self.windowmax = True
        else:
            self.gui.show_title()
            self.gui.maximize()
            self.windowmax = False

    def button_ask_queue(self):
        self.datasource.connector.ask_queue()

    def button_alltrades(self):
        """
        Show alltrades table
        """
        sec_data = self.stock.alltrades.to_dict()
        dialog = self.gui.load_window('win32/securities.ui')
        self.gui.set_table(dialog.securities_table, sec_data)

    def button_server(self):
        """
        Here it changes to orange state (i.e. 'connecting')
        """
        if 'true' not in self.datasource.server_status['connected']:
            """
            Not connected
            """
            if self.datasource.target_status != 'online':
                """
                And was not going to...
                """
                self.server_button_change(state='connecting')
                self.datasource.connect()
        else:
            self.plugins.stop_plugins()
            self.datasource.disconnect()
            self.server_button_change(state='offine')

    # For settings
    def finam_defaults(self):
        self.ip = '78.41.197.18'
        self.port = '3900'
        self.rqdelay = 100
        self.fill_settings_tab()

    def finam_mma(self):
        self.ip = '89.202.47.149'
        self.port = '13900'
        self.rqdelay = 100
        self.fill_settings_tab()

    def finam_hft(self):
        self.ip = '78.41.199.32'
        self.port = '13900'
        self.rqdelay = 10
        self.fill_settings_tab()

    def finam_demo(self):
        self.ip = '78.41.194.46'
        self.port = '3950'
        self.rqdelay = 100
        self.fill_settings_tab()

    def fill_settings_tab(self):
        self.gui.fill_window(self.setwnd, {
            'ip': self.ip, 'port': self.port, 'login': self.login,
            'password': self.password, 'rqdelay': str(self.rqdelay)})

    def button_settings(self):
        def button_save_settings():
            self.pprint('API: Saving config')
            self.login = str(self.setwnd.login.text())
            self.password = str(self.setwnd.password.text())
            self.ip = str(self.setwnd.ip.text())
            self.port = str(self.setwnd.port.text())
            self.rqdelay = int(self.setwnd.rqdelay.text())
            self.saveconfig()
            self.config.good = True
            self.setwnd.close()

        def ok_button():
            self.setwnd.close()

        self.setwnd = self.gui.load_window('win32/settings.ui')
        self.fill_settings_tab()

        self.gui.link_buttons(buttons=[
            ok_button, button_save_settings,
            self.finam_demo, self.finam_hft,
            self.finam_mma, self.finam_defaults], window=self.setwnd)

    def dummy(self, dummy):
        pass

    def button_quit(self):
        ask = self.gui.msgbox(u'Закрыть программу?', title=u'Выход',
                              buttons=OrderedDict({u'Да': self.dummy, u'Нет': self.dummy}))
        if ask == u'Да':
            print('API: Exit requested, disconnecting...')
            self.plugins.stop_plugins()
            self.run = False
            """
            This is made the way it's made. Just because.
            """
            self.gui.app.quit()
            os._exit(0)

    def button_shares(self, arg):
        """
        Show every trading asset
        """
        if self.stock.shares_dict:
            dialog = self.gui.load_window('win32/securities.ui')
            self.gui.set_table(dialog.securities_table, self.stock.shares_dict)

    def button_option(self, arg):
        """
        Show every trading asset
        """
        if self.stock.options_dict:
            dialog = self.gui.load_window('win32/securities.ui')
            self.gui.set_table(dialog.securities_table,
                               self.stock.options_dict)

    def button_futures(self, arg):
        """
        Show every trading asset
        """
        if self.stock.futures_dict:
            dialog = self.gui.load_window('win32/securities.ui')
            self.gui.set_table(dialog.securities_table,
                               self.stock.futures_dict)

    def get_lotsize(self):
        """
        Get 'lotsize' spinbox text value
        """
        return str(self.gui.window.lotsize.text())

    def button_sell(self):
        lots = self.get_lotsize()
        self.stock.sell_market(self.mysec, lots)

    def button_buy(self):
        lots = self.get_lotsize()
        self.stock.buy_market(self.mysec, lots)

    def button_cancel(self):
        pass

    def stakan_click(self, index):
        """
        Not a button, but stakan.
        """
        self.pprint('x=%s, y=%s, value = [%s]' % (index.column(),
                                                  index.row(), index.data().toString()))

###################
# UI functions
###################

    @async.run
    def play(self, sound):
        """
        Use: play ('audio.mp3')
        """
        try:
            winsound.PlaySound(sound, winsound.SND_FILENAME)
        except:
            pass

    def threads_number(self):
        return threading.active_count()

    @async.run
    def execfile(self, command):
        try:
            os.system(command)
        except:
            pass

    def get(self, key):
        return self.stock.quotations.get_last().get(key, '')

    def get_float(self, key):
        return fast_float(self.stock.quotations.get_last().get(key, 0.0))

    def get_int(self, key):
        return fast_forceint(self.stock.quotations.get_last().get(key, 0))

################################
# Main ui thread for drawing interface
###############################

    @async.run_qt
    def main_ui_thread(self):
        """
        Wait for connection
        """
        while 'true' not in self.datasource.server_status['connected']:
            self.sleep(0.5)
        self.pprint("Plugin: Subscibing %s" % self.mysec, 'green')

        """
        For testing and debugging -- v.61
        """
        if self.datasource.connector.ip == '78.41.194.46':
            self.mysec = 'GAZP'

        """
        Then wait for subscription
        """
        while self.mysec not in self.stock.subscribed and 'true' in self.datasource.server_status['connected']:
            self.stock.subscribe(self.mysec)
            self.sleep(0.1)

        """
        Then prepare some vars for main loop
        """
        self.ex_delta = 0
        self.all_deltas = [(self.get_float('deltapositions'))]
        delta_color = 'black'

        self.gui.window.stakan.clicked.connect(self.stakan_click)  # Здесь ****
        self.lastperc = 0
        """
        Here goes THE LOOP
        """
        while self.run:
            """
            Draw main parameters
            """
            self.point_cost = self.get('point_cost')
            self.waprice = self.get('waprice')   # FFFFFIIIIIXXX!!!***
            self.time = self.get('time')
            self.marketpricetoday = self.get('marketpricetoday')
            self.bid = self.get('bid')
            self.offer = self.get('offer')
            self.seccode = self.get('seccode')
            self.openprice = self.get_float('open')
            self.lastprice = self.get_float('last')

            if self.openprice:
                self.change = self.lastprice - self.openprice
                self.perc_change = (
                    self.lastprice / self.openprice * 100) - 100
                if self.change < 0:
                    color = 'red'
                    self.change = '%s (%s)%%' % (
                        self.change, str(self.perc_change)[:4])
                else:
                    color = 'green'
                    self.change = '+%s (%s)%%' % (self.change,
                                                  str(self.perc_change)[:4])
            else:
                self.change = ''
                color = 'black'

            self.biddeptht = self.get_float('biddeptht')
            self.offerdeptht = self.get_float('offerdeptht')
            self.totaldeptht = (self.biddeptht + self.offerdeptht)

            """
            Some manipulation with percent bar and stakan
            """
            if self.totaldeptht > 0:
                self.perc = fast_forceint(
                    self.biddeptht / self.totaldeptht * 100) - 50  # Percent from -50 to +50
            else:
                self.perc = 0

            if self.perc > 0 and self.lastperc <= 0:
                self.gui.scroll_table_up(self.gui.window.stakan)
                self.lastperc = self.perc
                #print('[%s] SELL %s' % (self.numeric_time(), self.bid))

            if self.perc < 0 and self.lastperc >= 0:
                self.gui.scroll_table_down(self.gui.window.stakan)
                self.lastperc = self.perc
                #print('[%s] BUY %s' % (self.numeric_time(), self.offer))

            """
            Draw colorful delta field
            """
            self.buydeposit = str(self.get_float('buydeposit'))
            #                 ^^^ Important!
            self.deltapositions = self.get_int('deltapositions')

            if self.ex_delta != self.deltapositions:
                self.all_deltas.append(self.deltapositions)
                self.all_deltas = self.all_deltas[-100:]

            self.avg_delta = statistics.mean(self.all_deltas)
            self.avg_pstdev = statistics.pstdev(self.all_deltas)

            """
            Choose color for deltapositions, add '+' if needed
            """
            delta_color = 'black'
            if self.deltapositions >= 0:
                delta_color = 'green'
            else:
                delta_color = 'red'

            if self.avg_delta + self.avg_pstdev:
                delta_postfix = u'▼'
            else:
                delta_postfix = u'▲'

            if self.deltapositions > 0:
                str_deltapositions = '+%s' % self.deltapositions
            else:
                str_deltapositions = str(self.deltapositions)
            self.ex_delta = self.deltapositions
            self.pprint('<font color="%s">%s%s</font>' % (delta_color, str_deltapositions, delta_postfix),
                        method='setHtml', field='deltapositions')

            marketpricetoday_color = 'gray'
            if self.marketpricetoday == self.offer:
                marketpricetoday_color = 'red'
            elif self.marketpricetoday == self.bid:
                marketpricetoday_color = 'green'
            """
            Now print all the data
            """
            self.pprint('%s' % self.stock.get_forts_position(self.mysec),
                        method='setPlainText', field='position')
            self.pprint('<font color="%s">%s</font>' % (marketpricetoday_color, self.marketpricetoday),
                        method='setHtml', field='marketpricetoday')
            self.pprint(self.deltapositions, method='setValue', field='delta')
            self.pprint(self.perc, method='setValue', field='percent')
            self.pprint(self.bid, method='setPlainText', field='bid')
            self.pprint(self.offer, method='setPlainText', field='offer')
            self.pprint(self.seccode, method='setPlainText', field='seccode')
            self.pprint(self.point_cost, method='setPlainText',
                        field='point_cost')
            self.pprint(self.waprice, method='setPlainText', field='waprice')
            self.pprint(self.time, method='setText', field='last_trade_time')
            self.pprint(self.buydeposit, method='setPlainText',
                        field='buydeposit')
            self.pprint(self.get('biddeptht'),
                        method='setPlainText', field='text_bid')
            self.pprint(self.get('offerdeptht'),
                        method='setPlainText', field='text_offer')
            self.pprint('<font color="%s">%s</font>' % (color, self.change), method='setHtml',
                        color='green', field='change')

            """
            Show positions
            """
            self.gui.set_table(self.gui.window.positions_table,
                               self.stock.positions.to_dict())
            """
            Show orders
            """
            self.gui.set_table(self.gui.window.orders_table,
                               self.stock.orders.to_dict())
            """
            Show trades
            """
            self.gui.set_table(self.gui.window.trades_table,
                               self.stock.trades.to_dict())
            self.gui.set_table(self.gui.window.client_table,
                               self.stock.client.to_dict())
            self.sleep(0.5)

    @async.run_qt
    def main_realtime_thread(self):
        """
        It's realtime, so be careful.
        """
        while self.run:
            self.redraw_chart()
            """
            Print changes as fast as possible
            """
            if self.stock.quotes.changed:
                self.gui.set_table(self.gui.window.stakan,
                                   self.stock.quotes.to_dict())
            """
            Show threads in realtime, too
            """
            self.pprint(str(self.threads_number()),
                        field='threads', method='setText')
            self.sleep(0)

    def float_list(self, somelist):
        return map(float, reversed(somelist))
        # return [float(i) for i in somelist] *****

    def redraw_chart(self):
        alltrades = self.stock.alltrades.to_dict()

        if len(alltrades.get('price', '')) > 0:
            prices = self.float_list(alltrades['price'])
            data_dict = {'open': prices, 'high': prices,
                         'low': prices, 'close': prices,
                         'time': alltrades['time']}
            self.gui.draw_chart(data_dict=data_dict)
        else:
            if self.debug:
                print('Alltrades are 0 len')

    @async.run_qt
    def main_slow_thread(self):
        while self.run:
            """
            Tell connector state
            """
            self.datasource.connector.ask_queue()
            self.pprint('%s' % (self.stock.dict_connector['queue_size']),
                        method='setText', field='queue_size')
            self.pprint('%s' % (self.stock.dict_connector['queue_mem_used']),
                        method='setText', field='queue_mem_used')
            self.pprint('%s' % (self.stock.dict_connector['version']),
                        method='setText', field='version')
            self.pprint('%s' % (self.stock.get_forts_free_money()),
                        method='setText', field='free_money')
            self.pprint('%s' % (self.stock.get_forts_all_money()),
                        method='setText', field='all_money')
            self.pprint('%s' % (self.datasource.connector.get_speed()),
                        method='setText', field='speed')
            self.pprint('%s' % (self.stock.get_varmargin(self.mysec)),
                        method='setText', field='varmargin')

            self.gui.set_table(self.gui.window.commands_table,
                               self.stock.commands.to_dict())
            self.sleep(1)

if __name__ == '__self.gui.__':
    api = API()
    self.pprint('API test ok', 'green')
    api.exit()
