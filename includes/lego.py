# -*- coding: utf-8 -*-
"""
 ____        _                    
|  _ \ _   _| |    ___  __ _  ___
| |_) | | | | |   / _ \/ _` |/ _ \
|  __/| |_| | |__|  __/ (_| | (_) |
|_|    \__, |_____\___|\__, |\___/
       |___/           |___/

Easy use of QT in Python
"""
import os
import sys
import time

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.Qt import *
from PyQt4 import uic
from collections import OrderedDict
from random import randint as rnd
from FinanceChart import *
"""ChartDirector module ^^^^ """


################################
# Define classes
###############################


"""
class SystemTrayIcon(QSystemTrayIcon):

    def __init__(self, icon, parent=None):
        QSystemTrayIcon.__init__(self, icon, parent)
        self.menu = QMenu(parent)
        self.setContextMenu(self.menu)
"""


class MainClass(QApplication):
    """
    Empty, but maybe I'll need it later.
    """

    def __init__(self, path):
        super(MainClass, self).__init__(path)


class GUI(QObject):

    def __init__(self, filename, **kwargs):
        QObject.__init__(self, None)
        self.debug = False
        self.printable_fields = OrderedDict({})
        self.actions = []

        """
        Check if we received buttons
        """

        if kwargs.get('buttons'):
            self.buttons = kwargs['buttons']
        else:
            self.buttons = []

        """
        Set up app
        """
        self.show_tray = True  # Trigger to show/hide window
        self.windowdict = {}  # Children windows
        self.filename = filename
        self.app = MainClass(sys.argv)
        self.window = uic.loadUi(self.filename)
        self.window.setAttribute(Qt.WA_TranslucentBackground)
        self.setstyle('cleanlooks')

        """
        Create tray if icon provided
        """
        if kwargs.get('icon'):
            self.set_tray_icon(kwargs['icon'])

        self.link_buttons(buttonlist=self.buttons)

        """
        Get dict of printable objects
        """
        self.update_printable_fields()
        self.window.show()
        self.connect(self, SIGNAL("print"), self.real_print)
        self.connect(self, SIGNAL("set_table"), self.real_set)
        self.connect(self, SIGNAL("anymethod"), self.anymethod)
        self.connect(self, SIGNAL("makechart"), self.makechart)
        self.window.graph.currentChanged.connect(api.redraw_chart)

    #######################################
    #           Window creation           #
    #######################################

    def set_waiting_cursor(self, wait=False):
        if wait:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        else:
            QApplication.restoreOverrideCursor()

    def update_printable_fields(self, *window):
        if not window:
            window = self.window
        for obj in window.__dict__:
            objname = obj.title().lower()
            the_object_itself = window.__dict__[obj]
            acceptable_methods = ['setValue',
                                  'insertHtml', 'insertPlainText', 'setText']
            for method_name in acceptable_methods:
                if hasattr(the_object_itself, method_name):
                    self.printable_fields.update({objname: the_object_itself})

        """
        For debugging, show all fields we can print
        """
        if self.debug:
            print(self.printable_fields)

    def update_exportable_tables(self):
        for widget in qApp.allWidgets():
            if isinstance(widget, QTableView):
                widget.doubleClicked.connect(self.doubleClicked)
                widget.setContextMenuPolicy(Qt.CustomContextMenu)
                widget.customContextMenuRequested.connect(self.showContextMenu)

    def doubleClicked(self, model_index):
        sender = self.sender()
        api.fast_export_to_csv(sender)

    def showContextMenu(self, pos):
        table = self.sender()
        pos = table.viewport().mapToGlobal(pos)  # thx Ekhumoro @ StackOverflow
        menu = QMenu()
        csvAction = menu.addAction(u"Экспорт в CSV...")
        """
        if menu.exec_(pos) is quickAction:
            self.export_quick(self.sender())
        """
        if menu.exec_(pos) is csvAction:
            api.export_to_csv(self.sender())

    def fill_window(self, window, content):
        fields = {}
        assert isinstance(content, dict)
        for obj in window.__dict__:
            objname = obj.title().lower()
            the_object_itself = window.__dict__[obj]
            acceptable_methods = ['setValue',
                                  'insertHtml', 'insertPlainText', 'setText']
            for method_name in acceptable_methods:
                if hasattr(the_object_itself, method_name):
                    fields.update({objname: the_object_itself})
                    if self.debug:
                        print ({objname: the_object_itself})

        for key in content:
            if fields.get(key):
                fields.get(key).setText(content[key])

    def load_window(self, filename, **kwargs):
        """
        Also, to make it non-modal, can do:
        window.setWindowFlags(Qt.Tool)
        """
        window = uic.loadUi(filename)

        # Auto set modality
        if hasattr(window, 'setModal'):
            window.setModal(True)

        if kwargs:
            kwargs.update({'window': window})
            self.link_buttons(**kwargs)

        self.windowdict.update({filename: window})
        self.update_exportable_tables()

        if self.debug:
            print('Load window:')
            print(type(window))
            print(self.windowdict)

        window.show()
        return window

    """
    Get window object instance by its path
    """

    def get_window_object(self, filename):
        if self.windowdict.get(filename):
            if self.debug:
                print(self.windowdict)
            return self.windowdict.get(filename)
        else:
            return None

    def link_buttons(self, **kwargs):
        """
        It's a very tricky method.
        """
        if kwargs.get('window'):
            window = kwargs['window']
        else:
            window = self.window

        if kwargs.get('buttons'):
            buttonlist = kwargs['buttons']
        elif kwargs.get('buttonlist'):
            buttonlist = kwargs['buttonlist']
        else:
            buttonlist = []

        """
        Link buttons to buttons function
        """
        for obj in window.__dict__:
            objname = obj.title().lower()

            for button in buttonlist:
                func_name = button.__name__.lower()
                if objname == func_name:
                    getattr(window, obj).clicked.connect(button)
                    if self.debug:
                        print(('Conn', button, 'to', objname, obj))

    def draw_chart(self, data_dict={}):
        self.emit(SIGNAL("makechart"), data_dict)

    def makechart(self, data_dict={}):
        """
        No, that's not my fault. That's the library. CamelCase, again....
        """
        # Draw chart chart in tab visible only.
        if self.window.graph.currentWidget().objectName() != 'tab_chart':
            return
        # This never happens.
        if not isinstance(data_dict, dict):
            print('%s is not a dict! Type =>%s' % (data_dict, type(data_dict)))
            return
        # Again, never happens.
        if not data_dict:
            return

        size = self.window.chart.size()

        size_x = size.width()
        size_y = size.height() + 83         # This hides yellow ad
        graph_len = size_x * 2
        chart_len = int(graph_len * 4)      # See more

        highData = data_dict.get('high', [])[-chart_len:]
        lowData = data_dict.get('low', [])[-chart_len:]
        openData = data_dict.get('open', [])[-chart_len:]
        closeData = data_dict.get('close', [])[-chart_len:]
        volData = data_dict.get('close', [])[-chart_len:]
        datalen = len(highData)

        rantable = RanTable(9, 6, datalen)
        rantable.setDateCol(0, chartTime(2002, 9, 4), 86400, 1)
        rantable.setHLOCCols(1, 100, -5, 5)
        rantable.setCol(5, 50000000, 250000000)  # VOLDATA

        timeStamps = rantable.getCol(0)
        volData = rantable.getCol(5)

        c = FinanceChart(size_x)  # self.char
        c.setLogScale(True)
        c.setData(timeStamps, highData, lowData,
                  openData, closeData, volData, 1)
        c.addMainChart(size_y - 90)
        c.addCloseLine(0x000000)
        c.addTypicalPrice(0x111111)
        """
        c.addATR(50, 100, 0xff00aa, 0x550077)
        if datalen > 30:
            c.addADX(50, 30, 0xff00aa, 0x550077, 0x9999ff)
        """
        c.addExpMovingAvg(60, 0xee1100)
        c.addExpMovingAvg(300, 0x0022ee)
        c.addBollingerBand(20, 2, 0x9999ff, 0xc06666ff)
        """c.addDonchianChannel(100, 0x9999ff, 0xc06666ff)"""
        """c.addParabolicSAR(0.1, 0.1, 0.05, SolidSphereShape,
                          3, 0x0022ee, 0x0022ee)
        c.addHLOC(0x008000, 0xcc0000)"""

        res = c.makeChart2(BMP)
        myPixmap = QPixmap()
        myPixmap.loadFromData(res)
        self.window.chart.setPixmap(myPixmap)
        self.window.chart.show()


################################
# Window manipulation
###############################

    def maximize(self):
        self.window.showMaximized()

    def minimize(self):
        self.window.showMinimized()

    def restore(self):
        self.window.showNormal()

    def set_title(self, title):
        self.window.setWindowTitle(title)

    def get_xy(self, window):
        pos = window.pos()
        x = pos.x()
        y = pos.y()
        return (x, y)

    def load_font(self, fontpath):
        if self.debug:
            print('Loading: %s' % fontpath)
        try:
            QFontDatabase.addApplicationFont(fontpath)
        except:
            print('Load %s FAILED!' % fontpath)

    def load_font_dir(self, fontpath):
        if not fontpath.endswith('/'):
            fontpath += '/'
        for font in os.listdir(fontpath):
            if font.endswith('.ttf'):
                fullpath = fontpath + font
                self.load_font(fullpath)

    def setstyle(self, style):
        try:
            self.app.setStyle(QStyleFactory.create(style))
            self.app.setStyleSheet('')
            self.window.hide()
            self.window.show()
        except:
            pass

################################
# Tray manipulation
###############################

    def close_event(self, event):
        """
        Close to tray ***
        Still not finished
        """
        print('CLOSE EVENT')
        self.window.hide()
        event.ignore()

    def add_button_menu(self, button, menu_dict):
        assert isinstance(menu_dict, dict)
        menu = QMenu(u'add_button_menu')
        for key in menu_dict.iterkeys():
            action = menu.addAction(key)
            action.triggered.connect(menu_dict[key])
        button.setMenu(menu)

    def add_tray_menu_dict(self, menu_dict):
        assert isinstance(menu_dict, dict)
        menu = QMenu(u'add_tray_menu')
        for key in menu_dict.iterkeys():
            action = self.tray.menu.addAction(key)
            action.triggered.connect(menu_dict[key])

    def popup(self, title, msg, link=''):
        if not hasattr(self, 'tray'):
            """
            What if we didn't create tray yet?
            """
            self.set_tray_icon('win32/icons/main.ico')

        if self.tray.supportsMessages():
            self.link = link
            if isinstance(title, str):
                title = title.decode('utf-8')
            if isinstance(msg, str):
                msg = msg.decode('utf-8')
            self.tray.showMessage(
                title, msg, icon=QSystemTrayIcon.Warning, msecs=1000)
            if link != '':
                self.tray.messageClicked.connect(self.openlink)

    """
    def openlink(self, link=''):
        if link == '':
            link = self.link
        webbrowser.open(link, new=0, autoraise=True)
    """

    def hide_title(self, *window):
        if not window:
            window = self.window
        if self.debug:
            print(window)
        try:
            window.setWindowFlags(Qt.FramelessWindowHint)
        except:
            if self.debug:
                print('Error! ->', window, type(window))
                pass

    def show_title(self, *window):
        if not window:
            window = self.window
        if self.debug:
            print(window)
        try:
            window.setWindowFlags(Qt.Window)
            """
            Also available:
            Qt.WindowCloseButtonHint |
            Qt.WindowMaximizeButtonHint |
            Qt.WindowMinimizeButtonHint)
            """
        except:
            if self.debug:
                print('Error! ->', window, type(window))
                pass

    def hide_from_taskbar(self):
        self.window.setWindowFlags(Qt.WindowTitleHint)

################################
# Window output
###############################
    def call_method(self, **kwargs):
        self.any_args = kwargs
        self.emit(SIGNAL("anymethod"))

    def anymethod(self):
        try:
            gui_object = self.any_args['field']
            method_name = self.any_args['method']
            what = self.any_args['what']
            method = getattr(gui_object, method_name)
            method(what)
        except:
            pass
            if self.debug:
                print('Lego: anymethod: Error in method: %s' % method_name)

    def set_table(self, table, data):
        self.emit(SIGNAL('set_table'), table, data)

    def real_set(self, table, data):
        """
        Check type of given table field
        """
        if type(table) == QTableWidget:
            # *** Was: False for placebo speedup
            # table.setSortingEnabled(False) <- This gives no speedup!
            """
            Get first key and get len of contents
            """
            rows = 0
            for key in data:
                rows = len(data[key])
                table.setRowCount(rows)
                break

            """
            Set number of columns too
            """
            mykeys = sorted(data.keys(), reverse=True)
            """
            Add translation here! ****
            """
            table.setColumnCount(len(data))
            table.setHorizontalHeaderLabels(mykeys)

            """
            Detect special case for stakan
            """
            if len(mykeys) == 3:
                stakan = True
            else:
                stakan = False
            """
            Now fill data
            """
            for n, key in enumerate(mykeys):
                for m, item in enumerate(data[key]):
                    if item:
                        try:
                            newitem = QTableWidgetItem(item)
                            table.setItem(m, n, newitem)

                        except:
                            print('Fill data error!')
                            pass

        elif type(table) == QTableView:
            """
            Forbid resizing(speeds up)
            """
            table.horizontalHeader().setResizeMode(QHeaderView.Fixed)
            table.verticalHeader().setResizeMode(QHeaderView.Fixed)
            table.horizontalHeader().setStretchLastSection(False)
            table.verticalHeader().setStretchLastSection(False)
            table.setSortingEnabled(True)
            model = QStandardItemModel(table)

            """
            Was:
            ------------------
            for colnumber, column in enumerate(data.values()):
                items = []
                for value in column:
                    items.append(QStandardItem(value))
                model.insertColumn(colnumber, items)
            ------------------
            Now, with lambdas:
            """
            for colnumber, column in enumerate(data.values()):
                items = map(lambda x: QStandardItem(x), column)
                model.insertColumn(colnumber, items)
            """
            Don't forget about memory leak here!!! ****
            """
            table.setModel(model)

    def real_print(self, myargs):
        if myargs.get('window'):
            target_window = myargs['window']
        else:
            target_window = self.window
        gui_object = target_window.outbox
        text = myargs['text']
        kwargs = myargs['kwargs']
        if not kwargs.get('field'):
            gui_object = target_window.outbox
        else:
            field = kwargs['field']

            if field in self.printable_fields.keys():
                gui_object = self.printable_fields[field]
            else:
                if self.debug:
                    print("%s is not printable!" % field)

        if kwargs.get('method'):
            method_name = kwargs['method']
        else:
            method_name = 'insertHtml'

        try:
            method = getattr(gui_object, method_name)
            method(text)
        except:
            if self.debug:
                print((gui_object, method_name))
            sys.exit(0)

        if method_name == 'insertHtml':
            method('<br>')
            gui_object.moveCursor(QTextCursor.End)

    def pprint(self, text, **kwargs):
        self.emit(SIGNAL("print"), {'text': text, 'kwargs': kwargs})

    def select_file(self, **kwargs):
        if kwargs.get('mask'):
            mask = kwargs['mask']
        else:
            mask = ''
        if mask == 'dir':
            self.fileDialog = QFileDialog.getExistingDirectory(
                None, 'Select dir')
        else:
            self.fileDialog = QFileDialog.getSaveFileName(filter=mask)
        return self.fileDialog

    def save_file(self, **kwargs):
        if kwargs.get('mask'):
            mask = kwargs['mask']
        else:
            mask = ''
            self.fileDialog = QFileDialog.getSaveFileName(selectedFilter=mask)
        return self.fileDialog

    def set_tray_icon(self, filename, **kwargs):
        self.widget = QWidget()
        self.tray = SystemTrayIcon(QIcon(filename), self.widget)
        self.tray.activated.connect(self.tray_clicked)
        self.tray.show()

    def set_tray_tooltip(self, tooltip):
        if hasattr(self, 'tray'):
            if isinstance(tooltip, str):
                tooltip = tooltip.decode('utf-8')
            try:
                self.tray.setToolTip(tooltip)
            except:
                if self.debug:
                    print('Error setting tooltip!')

    def tray_clicked(self):
        if self.debug:
            print('Tray click reason: -> %s' % self.tray.ActivationReason())

        if self.show_tray:
            self.show_tray = False
            self.window.hide()
            for window in self.windowdict.values():
                window.hide()
        else:
            self.show_tray = True
            self.window.showNormal()
            for window in self.windowdict.values():
                window.show()

    def restore_window(self, window):
        """
        Восстановление окна из свернутого состояния
        """
        if self.windowState() == Qt.WindowMinimized:
            window.setWindowState(Qt.WindowNoState)
        window.showNormal()

    def msgbox(self, message_text, title=None, buttons=None, icon=None):
        """
        Show modal message box
        a = msgbox('Choose yes or no', title= 'Hello',
         buttons={'yes': self.yes_answer, 'no': self.no_answer})
        """
        mymessage = QMessageBox(self.window)
        mymessage.setWindowModality(Qt.WindowModal)

        if title:
            mymessage.setWindowTitle(title)
        mymessage.setText(message_text)

        if buttons:
            # self.pprint('Buttons')
            for key in buttons.keys():
                _btn = mymessage.addButton(key, QMessageBox.ActionRole)
                _btn.clicked.connect(buttons[key])

        mymessage.exec_()
        clicked = mymessage.clickedButton()
        return clicked.text()

    def button_set_state(self, **kwargs):
        button = kwargs['button']
        state = kwargs['state']
        if state == 'enabled':
            target = True
        else:
            target = False
        self.pprint(target, method='setEnabled', field=button)

    def scroll_table_down(self, table):
        table.scrollToBottom()

    def scroll_table_up(self, table):
        table.scrollToTop()

    def add_text_tab(self, tab_widget, tab_title):
        newtab = QWidget(parent=None)
        tab_widget.addTab(newtab, tab_title)
        textbrowser = QTextBrowser()
        textbrowser.setFontFamily("Courier")
        textbrowser.setFontPointSize(10)
        layout = QHBoxLayout()
        layout.addWidget(textbrowser)
        newtab.setLayout(layout)
        return textbrowser


class SystemTrayIcon(QSystemTrayIcon):

    def __init__(self, icon, parent=None):
        QSystemTrayIcon.__init__(self, icon, parent)
        self.menu = QMenu(parent)
        self.setContextMenu(self.menu)

""" Now, simple demo of this module """
if __name__ == '__main__':
    import time
    import random
    import async
    play = True

    def play_button():
        global play

        playIcon = QIcon(QPixmap("icons/toggle-on.png"))
        stopIcon = QIcon(QPixmap("icons/toggle-off.png"))

        if play == True:
            # gui.window.play_button.setIcon(QIcon(stopIcon))
            gui.call_method(field=gui.window.play_button,
                            method='setIcon', what=playIcon)
            play = False
        else:
            # gui.window.play_button.setIcon(QIcon(playIcon))
            gui.call_method(field=gui.window.play_button,
                            method='setIcon', what=stopIcon)
            play = True

    @async.run_qt
    def print_in_first_thead():
        for x in xrange(300):
            gui.pprint(u'Thread1: Hello %s' % x)
            v = random.randint(1, 99)
            gui.pprint(v, field='percent', method='setValue')
            time.sleep(3)

    @async.run_qt
    def print_in_second_thead():
        for x in xrange(300):
            gui.pprint((u'Thread 2: Hello %s' % x))
            v = random.randint(1, 99)
            gui.pprint(v, field='percent', method='setValue')
            time.sleep(2)

    @async.run_qt
    def update_table():
        import random
        a = ['1', '2', '3', '4', '5']
        b = ['6', '7', '8', '9', '0']
        c = ['A', 'B', 'C', 'D', 'E']
        all = [a, b, c]

        while True:
            alldata = {'a': random.choice(all), 'b': random.choice(
                all), 'c': random.choice(all)}
            gui.set_table(gui.window.mytable, alldata)
            time.sleep(0.5)

    """ Example of buttons linked to GuiFile class """

    def show_dialog():
        a = gui.msgbox(u'Medved?', title=u'Preved', buttons={
            'Yes Preved': yes_answer, 'No preved': no_answer})
        gui.pprint('Chosen button: %s' % str(a))

    def quit_button():
        sys.exit(0)

    def select_dir():
        _file = gui.select_file(mask='dir')
        gui.pprint('Selected dir: %s' % _file)

    def select_file():
        _file = gui.select_file(mask='*.py')
        gui.pprint('Selected file: %s' % _file)

    def yes_answer():
        gui.pprint('Aswer yes')

    def no_answer():
        gui.pprint('Aswer no')

    def mytable(index):
        pressed = ('Table pressed at (%s,%s) => %s value' %
                   (index.row(), index.column(), index.data().toString()))
        gui.pprint(pressed)

""" Example use """
if __name__ == '__main__':
    gui = GUI('demo.ui', buttons=[quit_button, select_dir, select_file,
                                  show_dialog, play_button, mytable], icon='icons/lego.png')
    gui.window.hide()
    gui.load_font_dir('fonts')
    gui.setstyle('plastique')
    gui.window.show()
    gui.set_title('PyLego demo program')
    print_in_first_thead()
    print_in_second_thead()
    update_table()
    sys.exit(gui.app.exec_())
