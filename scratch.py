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

def iso8601(value):
    # split seconds to larger units
    negative= False if value.total_seconds() >= 0 else True
    seconds = -value.total_seconds() if negative else value.total_seconds()
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    days, hours, minutes = map(int, (days, hours, minutes))
    seconds = round(seconds, 6)
    ## build date
    date = ''
    if days:
        date = '%sD' % days if not negative else '-%sD' % days
    ## build time
    time = u'T' if date else u'T' if not negative else u'T-'
    # hours
    bigger_exists = date or hours
    if bigger_exists:
        time += '{:02}H'.format(hours)
    # minutes
    bigger_exists = bigger_exists or minutes
    if bigger_exists:
      time += '{:02}M'.format(minutes)
    # seconds
    print (seconds)
    if seconds.is_integer():
        seconds = '{:02}'.format(int(seconds))
    else:
        # 9 chars long w/leading 0, 6 digits after decimal
        seconds = '%09.6f' % seconds
        # remove trailing zeros
        seconds = seconds.rstrip('0')
    time += '{}S'.format(seconds)
    return u'P' + date + time
