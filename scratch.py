dAdjustVolumeDown = { "directive": { "header": { "namespace": "Alexa.Speaker", "name": "AdjustVolume", "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4", "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg==", "payloadVersion": "3"},"endpoint": { "scope": { "type": "BearerToken", "token": "access-token-from-skill" }, "endpointId": "avmctrl_den", "cookie": { } }, "payload": { "volume": -10 } } }
dAdjustVolumeUp = { "directive": { "header": { "namespace": "Alexa.Speaker", "name": "AdjustVolume", "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4", "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg==", "payloadVersion": "3"},"endpoint": { "scope": { "type": "BearerToken", "token": "access-token-from-skill" }, "endpointId": "avmctrl_den", "cookie": { } }, "payload": { "volume": 10 } } }
from dhroneTV import dhroneTV, dhroneTVScene, iotTV
from user import DbUser
user = DbUser(endpointClasses=[dhroneTV, dhroneTVScene])
from message import Request
reqDown = Request(dAdjustVolumeDown)
reqUp   = Request(dAdjustVolumeUp)
user.getUser(userEmail='ron@ritchey.org')
response = user.handleDirective(reqUp)
import json
print (json.dumps(response.json,indent=4))

class C(object):
   class iotTV(Iot):
     def __init__(self):
       super(C.iotTV, self).__init__('avmctrl_den')
       print ('Loading iotTV')
   def __init__(self):
     x = self.iotTV()
     print ('Yeah')

method_list = [func for func in dir(dhroneTV) if isinstance(getattr(dhroneTV, func),Iot)]

from dhroneTV import dhroneTV, dhroneTVScene, iotTV
a = dhroneTV('avmctrl_den', 'b')
a.iot['volume']


def addinterface(interface):
    def wrapper(*args, **kwargs):
        for i in args:
            print('addinterface arg: {0}'.format(args))
        for k, v in kwargs.items():
            print('addinterface kwargs {0}:{1}'.format(k,v))
        if hasattr(func, _secret):
            func._secret.append(interface)
        else:
            func._secret = [ interface ]
        return func
    if hasattr(addinterface, '_secret'):
        wrapper._secret = addinterface._secret
    return wrapper()

def interface(interface):
    class ClassWrapper:
        def __init__(self, cls):
            self.other_class = cls
            if hasattr(self.other_class, '_secret_property'):
                self.other_class._secret_property.append(interface)
            else:
                self.other_class._secret_property = [ interface ]
            print ('__init__')
        def __call__(self,*cls_ars):
            other = self.other_class(*cls_ars)
            other.__interface_to_handle__ = interface
            print ('__call__')
            return other
    return ClassWrapper

@addinterface('Alexa.PowerController')
@addinterface('Alexa.InputController')
class c(object):
    def __init__(self):
        self.val = 0
    def m(self):
        if hasattr(self, '__interface_to_handle__'):
            print (self.__interface_to_handle__)

@decorator(" is now decorated.")
class NormalClass:
    def __init__(self, name):
        self.field = name

    def __repr__(self):
        return str(self.field)
