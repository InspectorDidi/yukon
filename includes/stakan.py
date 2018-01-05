# -*- coding: utf-8 -*-
from table import Table
from tabulate import tabulate
from collections import OrderedDict


class Stakan(object):

    def __init__(self, **kwargs):
        self.rows = {}
        self.columns = ['sell', 'price', 'buy']
        self.changed = False

    def __repr__(self):
        if not self.empty():
            return self._to_pretty()
        else:
            return 'Empty table.'

    def get_column(self, col_name):
        _res = []
        allrows = sorted(self.rows.keys(), reverse=True)
        for row in allrows:
            try:
                """ ^^^ Case if row was deleted """
                stakan_row = self.rows[row]
                item = stakan_row[col_name]
                if item == None:
                    # <- commonly abbreviated ZWSP (was u'···')
                    item = u"\u200B"
                _res.append(item)
            except:
                pass
        return _res

    def to_dict(self):
        self.changed = False
        _res = OrderedDict.fromkeys(self.columns)
        for column in _res.keys():
            _res[column] = self.get_column(column)
        return _res

    def update(self, stakan_dict):
        self.changed = True
        workdict = dict.fromkeys(self.columns)
        for key in stakan_dict:
            if key in ['buy', 'sell', 'price']:
                workdict[key] = stakan_dict[key]

        price = workdict['price']
        buy = workdict['buy']
        sell = workdict['sell']

        del_list = (-1, '-1')

        if buy in del_list or sell in del_list:
            try:
                #self.rows[price] = {}
                self.rows.pop(price)
            except:
                """
                print(('Pop from stakan, price = %s' % price))
                print(('Self.rows are', self.rows))
                """
                pass

        else:
            self.rows[workdict['price']] = workdict

    def empty(self):
        if len(self.rows) == 0:
            return True

    def to_list(self):
        _res = []
        if not self.empty():
            try:
                for s in sorted(iter(list(self.rows.items())), key=lambda x_y: x_y[1]['price'], reverse=True):
                    dict_to_add = s[1]
                    for key in dict_to_add:
                        if dict_to_add[key] is None:
                            dict_to_add[key] = ''
                    _res.append(dict_to_add)
            except:
                pass
        self.changed = False
        return _res

    def _to_pretty(self, headers=None):
        return tabulate(self.to_list())

    """
    def as_dict(self):
        newdict = dict.fromkeys(self.columns, [])
        for row in self.rows.values():
            for key, value in row.items():
                if value == None:
                    value = []
                print('row item is `%s`: %s' % (key, value))
                print ('content of newdict[`%s`] is %s ' % (key, newdict[key]))
                newdict[key].append(value)
                print('newdict[%s] append %s' % (key, value))
        return newdict
    """

if __name__ == '__main__':
    stakan = Stakan()
    stakan.update({'buy': 10, 'price': 98000, 'sell': None})
    stakan.update({'buy': 20, 'price': 98100, 'sell': None})
    stakan.update({'buy': 30, 'price': 98200, 'sell': None})
    stakan.update({'buy': 40, 'price': 98300, 'sell': None})
    stakan.update({'buy': None, 'price': 98400, 'sell': 40})
    stakan.update({'buy': None, 'price': 98500, 'sell': 30})
    stakan.update({'buy': None, 'price': 98600, 'sell': 20})
    stakan.update({'buy': None, 'price': 98700, 'sell': 10})
    """
    print('Table df')
    print df
   
    for row in (df()):
        stakan.update(row)
    """
    print('to_pretty')
    print((stakan._to_pretty()))
    print('-' * 40)
    print(stakan.get_column('sell'))
    print(stakan.to_dict())
