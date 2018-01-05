# -*- coding: utf-8 -*-#
from collections import OrderedDict
"""
CSV recorder class
"""


class csv_writer(object):

    def __init__(self, **kwargs):
        self.headers = OrderedDict()
        self.eol = ('\n')
        self.delimiter = kwargs.get('delimiter', ';')
        self.filename = kwargs.get('filename', 'export.csv')
        self.file = open(self.filename, 'w+')
        self.header_written = False

    def fwrite(self, string):
        """
        Simply write given string
        """
        if isinstance(string, unicode):
            string = string.decode('utf-8').encode('cp1251')
        _res = True
        try:
            _res = self.file.write(string)
        except:
            _res = False
            pass
        return _res

    def record_dict(self, somedict):
        if not somedict.keys():
            return False

        to_write = ''

        """
        Check for safety
        """

        if not self.header_written:
            """
            Write headers
            """
            self.headers = OrderedDict.fromkeys(sorted(somedict.keys()))
            for key in self.headers.keys():
                to_write += '%s%s' % (key, self.delimiter)
            to_write = to_write[:- len(self.delimiter)] + self.eol
            self.fwrite(to_write)
            self.header_written = True

        """
        Headers okay, so write data
        """
        to_write = ''
        for key in self.headers:
            to_write += '%s%s' % (somedict.get(key, ''), self.delimiter)
        to_write += self.eol

        if self.fwrite(to_write):
            return True
        else:
            return False

    def record_list(self, somelist):
        for somedict in somelist:
            if isinstance(somedict, dict):
                self.record_dict(somedict)
            else:
                print('csv_writer: fixme! Not a dict...')
                print type(somedict), somedict

if __name__ == '__main__':
    csv = csv_writer(delimiter=';', filename='test.csv')
    test = [{'a': 1, 'b': 2, 'c': 'not 3'}, {'a': 2, 'b': 3, 'c': '4'}]
    csv.record_list(test)
