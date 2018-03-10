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
