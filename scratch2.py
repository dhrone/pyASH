from dhroneTV import iotTV
from concept import *
iot = iotTV('avmctrl_den')
pc = PowerController(iot)
sc = Speaker(iot)

class c():
	def __init__(self, val, val2):
		self.payload = { 'volume': val, 'mute': val2 }


request = c(10, False)
sc.AdjustVolume(request)
