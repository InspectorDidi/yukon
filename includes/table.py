# -*- coding: utf-8 -*-
"""
Version: 0.31
==============
My <3 lovely table

Accepts:

- table = Table()
- table = Table(convert_numeric=True)
- table = Table(data=[{'a':'b'}])
- table.add(timestamp='2015/06/01', open='1', high='2', low='0.5', close='1')
- table.add_dict ({'timestamp':'2015/06/03', 'open':'3', 'high':'4', 'low':'0.5', 'close':'2')
- f = [ {'timestamp':'2015/06/03', 'open':'3', 'high':'4', 'low':'0.5', 'close':'2'},
       {'timestamp':'2015/06/03', 'open':'3', 'high':'4', 'low':'0.5', 'close':'2'}]
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
class Table(object):
    def __init__(self, **kwargs):
        __slots__ = ['rows', 'columns']
        self.rows = []
        self.keys = []

        if 'data' in kwargs:                                        # Fill on creation?
            values = kwargs['data']
            if type(values) == dict:
                self.add_dict(values)
            else:
                self.merge(values)

    def __call__(self, *args):
        """
        We may ask table's column:
        ==========================
        print(table('column1')
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
        """
        String representation
        """
        return str(self.rows)


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
            if key not in self.keys:
                self.keys.append(key)
                self.rows = self.update()

        """
        Convert numeric if been asked
        if self.convert_numeric:
            for key in values:
                values[key] = self.__fast_float__(values[key])

        Finally, append
        """
        self.rows.append(values)

    def drop(self):
        self.rows = []
        self.keys = []

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
        empty = dict.fromkeys(self.keys)
        empty.update(row)
        return empty


    def __fast_float__(self, value):
        """ This runs only if convert_numeric was set """
        if value.isdigit():                                      #   !isdigit only for str
            res = float(value)
        else:
            res = value
        return res

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
                if key not in self.keys:
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
                if key not in self.keys:
                    row[key] = ''
                    break                       # v.0.75 check if ok

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
        """
        ROWS is a [] or {}
        """
        _res = [row.get(key, '') for row in reversed(self.rows)]
        return _res


    """
    Old code
    def get_column(self, key):
        _res = []
        for row in list(reversed(self.rows)):
            if key not in self.keys:
                value = ''
            else:
                try:
                    value = row[key]
                except:
                    print('Table: Error looking for key: %s' % key)
                    print('Columns are: %s' % self.keys)
                    print('Keys available: %s' % row.keys())
                    value = ''
                    pass
            _res.append((value))
        return _res
    """

    def loc(self, row_number):
        return self.rows[row_number]

    def to_dict(self):
        """
        We want result:
        _res = {'open': [], 'high': [] ....}

        This is HEAVILY used for PySide / PyQt
        """
        _res = {}
        for key in self.keys:
            _res[key] = self.get_column(key)
        return _res

##############################
# Now, tests...              #
##############################
if __name__ == '__main__':
    sec = Table()

    from functions import fn_timer

    @fn_timer
    def test_speed():
        """
        One million inserts
        """
        sec = Table()
        runs = 1000

        for n in range(runs):
            sec.add(timestamp='2015/06/01', open='1',
                high='2', low='0.5', close='1')
        for n in range(runs):
            res = sec.to_dict()


    def test_add(sec):
        sec.add(timestamp='2015/06/01', open='1',
                high='2', low='0.5', close='1')
        sec.add(timestamp='2015/06/02', open='1',
                high='3', low='0.15', close='1')
        sec.add(timestamp='2015/06/02', open='2',
                high='3', low='0.1', close='2', vol=0.03)
        sec.add_dict({'timestamp': '2015/06/03', 'open': '3',
             'high': '4', 'low': '0.5', 'close': '2', 'vol': 0.02})
        sec.add(timestamp='2015/06/3', open='2', high='3',
                low='0.1', close='2', vol=0.03, mode='YESS')
        print('-' * 30)
        print('sec.rows:')
        print(sec.rows)
        print('-' * 30)

        print('__call__():')
        print(sec())
        print('-' * 30)

        print('__call__("timestamp"):')
        print(sec('timestamp'))
        print('-' * 30)

        print('__repr__():')
        print(sec)
        print('-' * 30)

        print('to_dict')
        print(sec.to_dict())
        print('-' * 30)
    

    test_add(sec)
    print(' ' * 20440)
    print('=' * 60)
    print(sec.to_dict())
    print('.' * 60)
    print(sec.get_column('high'))
    
    test_speed()
    

    """
    import os
    os._exit(0)
    print('Search results')
    search = sec.find({'open': '1', 'close': '1'})
    print(search)
    print('get first:')
    print(sec.get_first())
    print('get last')
    print(sec.get_last())
    one = Table(data={'a': '1', 'b': '2'})
    two = {'a': '3', 'b': '4'}
    one.add_dict(two)
    print(one)
    print('to_table:')
    print(sec.to_table())
    print('=' * 79)
    c = Table(name=Vasya, age=20)
    print(c(name))
    """