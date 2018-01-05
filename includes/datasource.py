# -*- coding: utf-8 -*-
global api
import async
import time
import os
import sys
import table
import dicttoxml
import xmltodict
from ctypes import *
from os import getcwd, _exit


class Connector:
    """
  _____                            _
 / ____|                          | |
| |     ___  _ __  _ __   ___  ___| |_ ___  _ __
| |    / _ \| '_ \| '_ \ / _ \/ __| __/ _ \| '__|
| |___| (_) | | | | | | |  __/ (__| || (_) | |
 \_____\___/|_| |_|_| |_|\___|\___|\__\___/|_|
    Class for low-level connection to Transaq host
    """

    def __init__(self, api):
        self.txml = None  # Undefined lib type
        self.rqdelay = None
        self.session_timeout = 10
        self.request_timeout = 5
        self.loglevel = 3
        self.speed = 0
        self.debug = False

    def init_lib(self):
        if api.config.good:
            self.ip, self.port, self.login, self.password, self.rqdelay = (api.ip,
                               api.port, api.login, api.password, int(api.rqdelay))

        self.dir = getcwd()

        """
        Handle logs directory
        """
        logsdir = api.cwd() + '\logs'
        api.mkdir(logsdir)

        self.logsdir = logsdir + '\\\x00'
        api.pprint('Connector: Storing logs at: %s' % self.logsdir[0:-1])

        if not self.rqdelay:
            api.pprint('No settings yet.')

        """
        Choose proper dll
        (also check HFT or not)
        """
        if self.rqdelay >= 100:
            self.hft = False
            """
            So, simple?
            """
            if api.get_architecture() == 64:
                self.txml = WinDLL(
                    self.dir + "/win32/dll/finam-simple/txmlconnector64.dll")
                api.pprint('Connector: simple 64-bit mode.')

                """
                If demo, use old
                """

                if self.ip == "78.41.194.46":
                    self.txml = WinDLL(
                        self.dir + "/win32/dll/finam-demo/txml64old.dll")
                    api.pprint('Using old 64-bit version for demo server')

                if self.ip == "89.202.47.149":
                    self.txml = WinDLL(
                        self.dir + "/win32/dll/j2t-demo/txmlconnector64.dll")
                    api.pprint(
                        'Using *special* 64-bit version for Just2Trade demo server')
            else:
                """
                Simple, but x86?
                """
                self.txml = WinDLL(
                    self.dir + "/win32/dll/finam-simple/txmlconnector.dll")
                api.pprint('Connector: simple 32-bit mode.')

                if self.ip == "78.41.194.46":
                    self.txml = WinDLL(
                        self.dir + "/win32/dll/finam-demo/txml32old.dll")
                    api.pprint('Using old 32-bit version for demo server')

                if self.ip == "89.202.47.149":
                    self.txml = WinDLL(
                        self.dir + "/win32/dll/j2t-demo/txmlconnector.dll")
                    api.pprint(
                        'Using *special* 32-bit version for Just2Trade demo server')

        else:
            """
            Yes, it's HFT
            """
            self.hft = True
            if api.get_architecture() == 64:
                self.txml = WinDLL(
                    self.dir + "/win32/dll/finam-hft/txcn64.dll")
                api.pprint('Connector: HFT 64-bit mode.')
            else:
                self.txml = WinDLL(self.dir + "/win32/dll/finam-hft/txcn.dll")
                api.pprint('Connector: HFT 32-bit mode.')

        """
        C-like CamelCase is not my fault
        Also the code below is to be as nice as possible
        """
        _res = None
        try:
            _res = self.txml.Initialize(self.logsdir, self.loglevel)
        except:
            api.pprint('Connector: Error initializing DLL.', 'red')
            _exit(0)

        if _res == None:
            print('Connector: Error initializing DLL (result = %s), exiting.' % _res)
            os._exit(0)

        proto_callback = WINFUNCTYPE(c_bool, POINTER(c_byte))
        self.callback = proto_callback(self.rx2)
        _res = self.txml.SetCallback(self.callback)

        if _res != 1:
            """
            This NEVER happens, but...
            """
            api.pprint('Connector: Error setting callback.', 'red')
            _exit(0)

    def ask_queue(self):
        """
        REFACTOR THIS ****
        It returns:
        {u'queue_size': u'0', u'version': u'5.1.0.2.10.10', u'queue_mem_used': u'0'}
        api.pprint('Connector: Asking for queue...')
        """
        request = '<request><value>queue_size</value><value>queue_mem_used</value><value>version</value></request>' + '\\\x00'

        mem = POINTER(c_ubyte)(create_string_buffer('\000' * 1))

        if self.txml:
            """
            Only if library is initialized
            """
            try:
                errcode = self.txml.GetServiceInfo(request, byref(mem))
            except:
                errcode = None
            raw_data = cast(mem, c_char_p).value

        else:
            raw_data = None

        """
        Okay, then try to to parse if we have data
        """
        if raw_data:
            _res = self.xml_to_dict(raw_data)
            api.stock.dict_connector.update(_res)
        else:
            raw_data = None

        """
        Don't ever try to avoid memory leak here.
        It never happens.
        """
        mem = None
        return raw_data

    def rx2(self, rxdata):
        to_cast = rxdata
        received = cast(rxdata, c_char_p).value.decode('utf-8')
        self.txml.FreeMemory(rxdata)
        api.parser.parse(received)
        self.speed += 1

    def get_speed(self):
        _res = self.speed
        self.speed = 0
        return _res

    def connect(self):
        self.init_lib()
        api.pprint('Connector: Connecting to server...')
        api.server_button_change(state='connecting')
        self.send_command({'id': 'connect', 'login': self.login,
                           'password': self.password, 'host': self.ip,
                           'port': self.port, 'rqdelay': self.rqdelay,
                           'autopos': 'True',
                           'session_timeout': self.session_timeout, 'request_timeout': self.request_timeout})

    def disconnect(self):
        api.pprint('Connector: Disconnecting from TRANSAQ.', color='red')
        """
        If connector exists
        """
        if self.txml:
            _res = self.send_command({'id': 'disconnect'})
            self.txml.UnInitialize()
        self.txml = None

    def xml_to_dict(self, xmltext):
        try:
            doc = xmltodict.parse(xmltext)
        except:
            print('Error parsing: %s' % xmltext)
            return None

        _res = {}

        for key, value in doc.iteritems():
            if isinstance(value, dict):
                stripped_dict = {}
                for subkey in value.keys():
                    stripped_key = subkey.strip('@')
                    stripped_dict[stripped_key] = value[subkey]
                _res.update(stripped_dict)
            else:
                _res[key] = value
        return _res

    def send_command(self, args):
        id = args.pop('id')
        xml = dicttoxml.dicttoxml(
            args, custom_root='command', root=False, attr_type=False)
        cmd = "<command id='%s'>" % id + xml + "</command>"
        self.update_table({'dir': 'transmit', 'data': cmd})
        if self.debug:
            print('Sending: %s' % cmd)
        _res = self.send(cmd)
        self.update_table({'dir': 'receive', 'data': _res})
        return self.xml_to_dict(_res)

    def send(self, xml_command):
        res = self.tx(xml_command).decode('utf-8')

        if 'true' in res:
            return res
        else:
            api.pprint('Connector: [%s] ' % res, 'red')
            """
            For exceptional cases, to be rock-solid
            """
            if u'уже установлено' in res:
                api.datasource.server_status['connected'] = 'true'
                self.tx("<command id='server_status'/>")
            return res

    def tx(self, txdata):
        if txdata:
            senddata = txdata.encode('utf-8')
            try:
                reply = self.txml.SendCommand(senddata)
                _res = cast(reply, c_char_p).value
            except:
                _res = 'Error'
                print('Connector: tx: error in casting: %s' % repr(reply))
                print('-' * 80)
                print(reply)
                print('-' * 80)
                print type(reply)
            return _res

    def update_table(self, data):
        api.stock.commands.add_dict(data)


class DataSource():

    """
      _____        _         _____
     |  __ \      | |       / ____|
     | |  | | __ _| |_ __ _| (___   ___  _   _ _ __ ___ ___
     | |  | |/ _` | __/ _` |\___ \ / _ \| | | | '__/ __/ _ \
     | |__| | (_| | || (_| |____) | (_) | |_| | | | (_|  __/
     |_____/ \__,_|\__\__,_|_____/ \___/ \__,_|_|  \___\___|
    High-Level class to handle transaq exchange
    Accepts: ip, port, login, password
    Runs: connect(), disconnect() only
    """

    def __init__(self):
        api.pprint('DataSource: Creating new datasource.')
        self.target_status = 'offline'
        self.server_status = {'id': None,
                              'connected': 'false', 'recover': 'false'}
        self.connector = Connector(api)

    def connect(self):
        self.target_status = 'online'
        self.manage_connection()

    def disconnect(self):
        api.pprint('DataSource: Disconnecting from server.')
        self.target_status = 'offline'
        """ If wasn't connected, it doesn't exist """
        if hasattr(self.connector, 'txml'):
            self.connector.disconnect()

    @async.run_qt
    def manage_connection(self):
        """
        Affirm there is connection
        """
        if not api.config.good:
            api.pprint(
                '<b>Datasource: manage_connection: no txml, fill settings.</b>')
            self.disconnect()
            api.server_button_change(state='offine')

        """
        We start connection and manage it.
        """
        while self.target_status == 'online':
            if 'true' not in self.server_status['connected']:
                api.pprint('DataSource: Try to connect...')

                if hasattr(self.server_status, 'recover'):
                    if 'true' in self.server_status['recover']:
                        api.pprint(
                            'Datasource: Recovering connection...', 'red')

                if self.target_status == 'online':
                    api.server_button_change(state='connecting')
                    self.connector.connect()
                    connector_time = self.connector.session_timeout
                    api.sleep(connector_time)
