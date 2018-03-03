# -*- coding: utf-8 -*-

# Copyright 2018 dhrone. All Rights Reserved.
#

from endpoint import Endpoint
from iot import Iot
from message import Request

from utility import *
from db import *

# Setup logger
import logging
logger = logging.getLogger(__name__)
logger.setLevel(LOGLEVEL)

class iotTV(Iot):
    @Iot.transformFromProperty('powerState', 'apower')
    def fromPowerState(self, value):
        return value

    @Iot.transformToProperty('powerState', 'apower')
    def toPowerState(self, value):
        return value

    @Iot.transformFromProperty('input', 'asource')
    def fromInput(self, value):
        return value

    @Iot.transformToProperty('input', 'asource')
    def toInput(self, value):
        return value

    @Iot.transformFromProperty('muted', 'mute')
    def fromMuted(self, value):
        return value

    @Iot.transformToProperty('muted', 'mute')
    def toMuted(self, value):
        return value

    @Iot.transformFromProperty('volume')
    def fromVolume(self, value):
        return int(value / 10)

    @Iot.transformToProperty('volume')
    def toVolume(self, value):
        return value * 10

class dhroneTV(Endpoint):
    manufacturerName = 'dhrone'
    description = 'iotTV controller by dhrone'
    displayCategories = 'OTHER'

    @Endpoint.register(['TurnOn'])
    def TurnOn(self, request):
        iotTV(request.endpointId)['powerState'] = True

    @Endpoint.register
    def TurnOff(self, request):
        iotTV(request.endpointId)['powerState'] = False

    @Endpoint.register(['AdjustVolume','SetVolume'])
    def Volume(self, request):
        d = iotTV(request.endpointId)
        if request.directive == 'AdjustVolume':
            v = d['volume'] + request.payload['volume']
            d['volume'] = 0 if v < 0 else 100 if v > 100 else v
        else:
            d['volume'] = request.payload['volume']

#    def SetMute(self, request):
#        d = iotTV(request.endpointId)
#        d['muted'] = request.payload['mute']

    @Endpoint.register
    def SelectInput(self, request):
        d = iotTV(request.endpointId)
        d['asource'] = request.payload['input']

class dhroneTVScene(Endpoint):
    manufacturerName = 'dhrone'
    description = 'iotTV controller by dhrone'
    displayCategories = 'SCENE_TRIGGER'

    @Endpoint.register
    def Activate(self, request):
        (endpointId, sceneId) = request.endpointId.split(':')
        d = iotTV(endpointId)
        ds = { 'epower':True, 'esource': 'HDMI1', 'input': 'SAT', 'powerState':True }
        d.batchSet(ds)

    @Endpoint.register
    def Deactivate(self, request):
        (endpointId, sceneId) = request.endpointId.split(':')
        d = Iot(endpointId)
        ds = { 'epower': False, 'input': 'CD' }
        d.batchSet(ds)


#user = StaticUser(dhroneTV('avmctrl_den'), dhroneTVScene('avmctrl_den:scene1'))
#user = DbUser(dhroneTV, dhroneTVScene)
#ash = pyASH(user, dhroneTV, dhroneTVScene)
#lambda_handler = ash.lambda_handler

if __name__ == u'__main__':
from user import DbUser

DbUser.createTables()
