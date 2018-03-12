dAdjustVolumeDown = { "directive": { "header": { "namespace": "Alexa.Speaker", "name": "AdjustVolume", "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4", "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg==", "payloadVersion": "3"},"endpoint": { "scope": { "type": "BearerToken", "token": "access-token-from-skill" }, "endpointId": "avmctrl_den", "cookie": { } }, "payload": { "volume": -10 } } }
dAdjustVolumeUp = { "directive": { "header": { "namespace": "Alexa.Speaker", "name": "AdjustVolume", "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4", "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg==", "payloadVersion": "3"},"endpoint": { "scope": { "type": "BearerToken", "token": "access-token-from-skill" }, "endpointId": "avmctrl_den", "cookie": { } }, "payload": { "volume": 10 } } }
from dhroneTV import dhroneTV, dhroneTVScene, iotTV
from user import DbUser
user = DbUser(endpointClasses=[dhroneTV, dhroneTVScene], iotcls=iotTV)
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


from concept import *
from dhroneTV import iotTV
iot = iotTV('avmctrl_den')
pc = PowerController(iot)

ts = 86404
m, s = divmod(ts, 60)
h, m = divmod(m, 60)
d, h = divmod(h, 24)
print ('{0}D{1}H{2}M{3}S'.format(d,h,m,s))

class c(object):
    pass

def interface(*args, **kwargs):
    print ('Arguments')
    for i in args:
        print(i)
    print ('\nKeyworded Arguments')
    for k, v in kwargs.items():
        print('  {0}:{1}'.format(k,v))
    def decorator(function):
        sp = kwargs.get('directives')
        print ('Setting {0}'.format(sp))
        setattr(function,'_secretproperty', sp)
        def wrapper(*args, **kwargs):
            function(*args, **kwargs)
        return wrapper
    return decorator

def interface(interface=None, directives=None):
    class ClassWrapper:
        def __init__(self, cls):
            self.__baseclass__ = cls
        def __call__(self, *cls_args)
