# -*- coding: utf-8 -*-
"""
My <3 lovely table

Accepts:

- table = Table() / or table = Table(convert_numeric=True) / or table = Table(data=[{'a':'b'}])
- table.add(timestamp='2015/06/01', open='1', high='2', low='0.5', close='1')
- table.add_dict ({'timestamp':'2015/06/03', 'open':'3', 'high':'4', 'low':'0.5', 'close':'2', 'vol' : 0.02})
- f = [ {'timestamp':'2015/06/03', 'open':'3', 'high':'4', 'low':'0.5', 'close':'2', 'vol' : 0.02},
       {'timestamp':'2015/06/03', 'open':'3', 'high':'4', 'low':'0.5', 'close':'2', 'vol' : 0.02}]
  table.merge(f)
- table.get_column('open') --> list as [1,2,3,4]...
- table.loc(0)
- table.drop()
- if table.empty(): ...
- table()
  [{......}, {.......}]
- table
    ------------------------------------------------
    vol   timestamp   mode  high  low  close  open
    ------------------------------------------------
    None  2015/06/01  None  2     0.5  1      1
    0.03  2015/06/02  None  3     0.1  2      2
    0.02  2015/06/03  None  4     0.5  2      3
    0.03  2015/06/02  YESS  3     0.1  2      2
"""
from tabulate import tabulate
from fastnumbers import *


class Table(object):

    def __init__(self, **kwargs):
        __slots__ = ['rows', 'columns']
        """
        Simple structure
        """
        self.rows = []
        self.columns = []

        if 'data' in kwargs:
            """
            Fill on creation?
            """
            values = kwargs['data']
            if type(values) == dict:
                self.add_dict(values)
            else:
                self.merge(values)

    def __call__(self, *args):
        """
        We may ask table's column
        """
        if args:
            res = []
            for col in args:
                res = res + (self.get_column(col))
                return res
        else:
            """
            or, whole table
            """
            return self.rows

    def __repr__(self):
        if not self.empty():
            return self._to_pretty()
        else:
            return []

    def truncate(self, len):
        self.rows = self.rows[-(len):]

    def get_last(self):
        try:
            return self.rows[-1:][0]
        except:
            return {}

    def get_first(self):
        try:
            return self.rows[0]
        except:
            return {}

    def empty(self):
        if len(self.rows) == 0:
            return True

    def record(self, *arg, **kwarg):
        if kwarg != {}:
            self.add_dict(kwarg)
            return 0

        if len(arg) > 0:
            arg = arg[0]

        if type(arg) == list:
            for _dict in arg:
                self.add_dict(_dict)
        elif type(arg) == dict:
            self.add_dict(arg)

    def update_one(self, **values):
        """
        Add columns if not exist
        """
        self.rows[0].update(values)

    def add(self, **values):
        """
        Add columns if not exist
        """
        for key in values:
            if key not in self.columns:
                self.columns.append(key)
                self.rows = self.update()

        """
        Convert numeric if been asked
        if self.convert_numeric:
            for key in values:
                values[key] = self._try_to_float(values[key])

        Finally, append
        """
        self.rows.append(values)

    def drop(self):
        self.rows = []
        self.columns = []

    def merge(self, values):
        if values:
            for row in values:
                self.add_dict(row)

    def add_dict(self, values):
        self.add(**values)

    def add_one(self, values):
        if len(self.rows) > 0:
            self.rows[0].update(values)
        else:
            self.add_dict(values)

    def _get_with_empty(self, row):
        empty = dict.fromkeys(self.columns)
        empty.update(row)
        return empty

    def _try_to_float(self, value):
        if hasattr(value, 'isdigit'):
            if value.isdigit():
                _res = float(value)
                return _res
            else:
                return value
        else:
            return value

    """
    Find by value
    """

    def find(self, search_dict):
        _res = []
        for row in self.rows:
            fail = False
            for key in search_dict:
                """
                Important on searching for empty values
                """
                if key not in row.keys():
                    row[key] = ''
                if row[key] != search_dict[key]:
                    fail = True
            if not fail:
                _res.append(row)
        # return Table(data=_res)
        return _res

    def find_one(self, search_dict):
        _res = []

        for row in self.rows:
            fail = False
            for key in search_dict:
                try:
                    if row[key] != search_dict[key]:
                        fail = True
                except KeyError:
                    #print('Table: Wrong key [%s] in find_one' % key)
                    # ^^^^^^^^^^^^^^^^^^^^^^^^ seccode is wrong key. **********
                    fail = True
                    pass

            if not fail:
                _res = (row)
                return _res
                break
        return None

    """
    Find by value
    """

    def find_table(self, search_dict):
        _res = []
        for row in self.rows:
            fail = False
            for key in search_dict:
                """
                Important on searching for empty values
                """
                if key not in row.keys():
                    row[key] = ''
                if row[key] != search_dict[key]:
                    fail = True
            if not fail:
                _res.append(row)
        return Table(data=_res)

    def update(self):
        res = []
        for row in self.rows:
            if row != {}:  # for deleted rows
                res.append(self._get_with_empty(row))
        return res

    def get_column(self, key):
        _res = []
        for row in list(reversed(self.rows)):
            if key not in row.keys():
                value = ''
            else:
                value = row[key]
            _res.append((value))
        return _res

    def loc(self, row_number):
        return self.rows[row_number]

    def pprint(self):
        print((self._to_pretty()))

    def _to_pretty(self, headers=None):
        return tabulate(self.rows, headers='keys')

    def html(self, headers=None):
        return tabulate(self.rows, headers='keys', tablefmt='html')

    """
    to_table means this:

      vol  timestamp      high    low    close    open  mode
    -----  -----------  ------  -----  -------  ------  ------
           2015/06/01        2   0.5         1       1
           2015/06/02        3   0.15        1       1
     0.03  2015/06/02        3   0.1         2       2
     0.02  2015/06/03        4   0.5         2       3
     0.03  2015/06/3         3   0.1         2       2  YESS
    """

    def to_table(self):
        _res = dict.fromkeys(self.columns, [], reverse=True)
        for row in self.rows:
            for key in _res:
                _res[key].append(row[key])
        return _res

    def to_dict(self):
        """
        We want result:
        _res = {'open': [], 'high': [] ....}
        """
        _res = {}  # dict.fromkeys(self.columns, [])
        for key in self.columns:
            _res[key] = self.get_column(key)
        return _res

#########################################################################
if __name__ == '__main__':
    print('It starts somewhere else.')

    """
    sec = Table()
    for n in range(3):
        sec.add(timestamp='2015/06/01', open='1',
                high='2', low='0.5', close='1')
        sec.add(timestamp='2015/06/02', open='1',
                high='3', low='0.15', close='1')
        sec.add(timestamp='2015/06/02', open='2',
                high='3', low='0.1', close='2', vol=0.03)
        d = {'timestamp': '2015/06/03', 'open': '3',
             'high': '4', 'low': '0.5', 'close': '2', 'vol': 0.02}
        sec.add_dict(d)
    sec.add(timestamp='2015/06/3', open='2', high='3',
            low='0.1', close='2', vol=0.03, mode='YESS')

    print('Table rows:')
    print(sec.rows)
    print('Table:')
    print(sec)
    print('-' * 30)
    # print('to_table:')
    # print sec.to_table()
    print('to_dict')
    print(sec.to_dict())
    print('-' * 30)
    print('Search results')
    search = sec.find({'open': '1', 'close': '1'})
    print(search)
    print((search()))
    print('get first:')
    print(sec.get_first())
    print('get last')
    print(sec.get_last())
    one = Table(data={'a': '1', 'b': '2'})
    two = {'a': '3', 'b': '4'}
    one.add_dict(two)
    print one
    """
