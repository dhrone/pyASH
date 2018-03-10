from dhroneTV import iotTV
from concept import *
iot = iotTV('avmctrl_den')
pc = PowerController(iot)
pc.TurnOff('a')
