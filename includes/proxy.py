# -*- coding: utf-8 -*-
class class_stockdata():

    def __init__(self):
        self.name = None

    def setname(self, name):
        self.name = name

    def getname(self):
        return self.name


class Proxy(object):
    """
    Creates a proxy object of class_default classes
    identified by given id;
    intended to use like:

    self.alltrades = proxy(Table)
    secid = 'SiZ6'
    row = ....
    stock(secid).quotes.update(row)
    """

    def __init__(self, class_default):
        self.class_default = class_default
        self.objects_dict = {}
        self.debug = False
        ownmethods = self.__dict__
        for method in class_default.__dict__:
            if method not in ownmethods:
                if '__' not in method:
                    """ Yes, yes, private methods """
                    self.__dict__.update({method: self.anymethod})
                    if self.debug:
                        print('Adding method %s' % method)

    def __call__(self, id, *args, **kwargs):
        if id in self.objects_dict.keys():
            if self.debug:
                print('Return existing object')
            return self.objects_dict[id]
        else:
            if self.debug:
                print('Create object')
            self.objects_dict[id] = self.class_default(*args, **kwargs)
            return self.objects_dict[id]

    def anymethod(self, id, methodname, *args, **kwargs):
        if id in self.objects_dict.keys():
            current_class = self.objects_dict[id]
            if hasattr(current_class, methodname):
                method = getattr(current_class, methodname)
                return method(*args, **kwargs)
            else:
                print('Error: No method %s for class' % methodname)
        else:
            print('No class id in:')
            print(self.objects_dict.keys())

    def kill(self, id):
        self.objects_dict[id] = None

#################
# Main function #
#################


def void_main():
    stock = Proxy(class_stockdata)
    id = 'first'
    stock(id).setname('myname')
    the_name = stock(id).getname()
    print(the_name)


if __name__ == '__main__':
    void_main()
