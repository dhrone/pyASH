from dhroneTV import iotTV
from concept import *
iot = iotTV('avmctrl_den')
pc = PowerController(iot)
pc.TurnOff('a')


from pyASH import pyASH
from user import StaticUser
from dhroneTV import dhroneTV
import json
import time
eid = dhroneTV.__name__ + '|' + 'avmctrl_den'
class r:
    def __init__(self, eid, ns, d, pn, v):
        self.endpointId = eid
        self.namespace = ns
        self.directive = d
        self.payload = { pn:v }
        self.correlationToken = '<correlation token>'
        self.token = '<access token>'


user = StaticUser()
user.addEndpoint(dhroneTV, 'avmctrl_den', 'Den TV', 'TV by Me', 'Me', 'OTHER', True, True, 0)
pyash = pyASH(user)

request = r(eid, 'Alexa.Speaker', 'SetVolume', 'volume', 50)
ret = pyash.handleDirective(request)
print(json.dumps(ret, indent=4))
