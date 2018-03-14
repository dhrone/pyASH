def addinterface(interface):
    def wrapper(func):
        if hasattr(func, '__interface__'):
            func.__interface__.append(interface)
        else:
            func.__interface__ = [ interface ]
        return func
    return wrapper

@addinterface('Alexa.PowerController')
@addinterface('Alexa.InputController')
class c(object):
    def __init__(self, val):
        self.val = val
    def m(self):
        if hasattr(self, '__interface__'):
            print (self.__interface__)
