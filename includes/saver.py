# -*- coding: utf-8 -*-#
import cPickle
import sys
import os

"""
Pickler class
-------------
list of /data:

a.pick
b.pick
--------------
Usage:

mydata = pickler('/data')

a = mydata.a
b = mydata.b

if there is no file '/data/b.pick', then mydata.b equals to None
"""


class pickler(object):

    def __init__(self, lookupdir):
        """
        Get dir and add to system path
        (if not exist, create dir)
        """
        lookupdir = lookupdir.strip('/')
        self.__pickle_dir__ = lookupdir
        self.__full_dir__ = '%s/%s' % (os.getcwd(), lookupdir)
        sys.path.append(self.__pickle_dir__)
        self.check_dir()
        """
        okay, dir exists
        """
        try:
            self.__pickle_files__ = os.listdir(self.__pickle_dir__)
        except:
            self.__pickle_files__ = []

        for filename in self.__pickle_files__:
            if filename.endswith('.pick'):
                self.process_import(filename)

    def check_dir(self):
        """
        If no dir, we create it
        """
        if os.path.isdir(self.__full_dir__):
            pass
        else:
            create_dir = self.__full_dir__
            try:
                os.mkdir(create_dir)
            except:
                print('Cannot create %s directory, exiting...' %
                      self.__full_dir__)
                os._exit(1)

    def process_import(self, filename):
        _res = False
        try:
            fullpath = '%s/%s/%s' % (os.getcwd(),
                                     self.__pickle_dir__, filename)
            _res = cPickle.load(file(fullpath))
        except:
            """
            Maybe, kill file?
            """
            pass

        if _res:
            _name = filename.strip('.pick')
            setattr(self, _name, _res)

    def save_all(self):
        for attr in self.__dict__:
            if '__' not in attr:
                _name = attr.title().lower() + '.pick'
                self.save_as(attr, _name)

    def save_as(self, attr, filename):
        """
        Save attr to file
        """
        self.check_dir()
        fullpath = '%s/%s/%s' % (os.getcwd(), self.__pickle_dir__, filename)
        cPickle.dump(attr, file(fullpath, 'w'))

    def __getattr__(self, attr):
        if attr is self.__dict__:
            return self.__dict__[attr]
        else:
            return None

# code in case of standalone usage
if __name__ == "__main__":
    pick = pickler('/data')

    a = pick.a or 'Data for a'
    pick.save_as(a, 'a.pick')

    b = xrange(0, 10)
    pick.save_as(b, 'b.pick')

    fl = 0.0000000001
    pick.save_as(fl, 'fl.pick')

    pi = 3.1415927
    pick.save_as(pi, 'pi.pick')

    mydict = {'name': 'John'}
    pick.save_as(mydict, 'mydict.pick')

    d = [a, b, fl, pi]
    pick.save_as(d, 'd.pick')

    print pick.a
    print pick.b
    print pick.fl
    print pick.pi
    print pick.mydict
    print pick.d
