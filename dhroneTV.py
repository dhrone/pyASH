# -*- coding: utf-8 -*-

# Copyright 2018 dhrone. All Rights Reserved.
#


# pyASH imports
from endpoint import Endpoint
from iot import Iot
from message import Request

from utility import LOGLEVEL

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
    def TurnOn(self, request, iot):
        iot['powerState'] = True

    @Endpoint.register
    def TurnOff(self, request, iot):
        iot['powerState'] = False

    @Endpoint.register(['AdjustVolume','SetVolume'], properties='volume')
    def Volume(self, request, iot):
        if request.directive == 'AdjustVolume':
            v = iot['volume'] + request.payload['volume']
            iot['volume'] = 0 if v < 0 else 100 if v > 100 else v
        else:
            iot['volume'] = request.payload['volume']

#    @Endpoint.register
#    def SetMute(self, request, iot):
#        iot['muted'] = request.payload['mute']

    @Endpoint.register
    def SelectInput(self, request, iot):
        iot['asource'] = request.payload['input']

class dhroneTVScene(Endpoint):
    manufacturerName = 'dhrone'
    description = 'iotTV controller by dhrone'
    displayCategories = 'SCENE_TRIGGER'
    endpointIdPattern = '^[^:]+'

    @Endpoint.register
    def Activate(self, request, iot):
        (endpointId, sceneId) = request.endpointId.split(':')
        ds = { 'epower':True, 'esource': 'HDMI1', 'input': 'SAT', 'powerState':True }
        iot.batchSet(ds)

    @Endpoint.register
    def Deactivate(self, request, iot):
        (endpointId, sceneId) = request.endpointId.split(':')
        ds = { 'epower': False, 'input': 'CD' }
        iot.batchSet(ds)


#user = StaticUser(dhroneTV('avmctrl_den'), dhroneTVScene('avmctrl_den:scene1'))
#user = DbUser(endpointClasses=[dhroneTV, dhroneTVScene])
#ash = pyASH(user)
#lambda_handler = ash.lambda_handler

if __name__ == u'__main__':
    from user import DbUser


    user = DbUser()
    user.createTables()

    user.createUser('ron@ritchey.org')

    user.addEndpoint(dhroneTV('avmctrl_den','Sound', 'Sound by dhrone'))
    user.addEndpoint(dhroneTVScene('avmctrl_den:scene-1', 'TV', 'TV by dhrone'))
    user.commit()
