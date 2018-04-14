# -*- coding: utf-8 -*-

# Copyright 2018 dhrone. All Rights Reserved.
#


# pyASH imports
from pyASH.endpoint import Endpoint
from pyASH.iot import Iot

from pyASH.interface import PowerController, Speaker
from pyASH.utility import LOGLEVEL

# Setup logger
import logging
logger = logging.getLogger(__name__)
logger.setLevel(LOGLEVEL)

class iotTV(Iot):

    @Iot.transformFromProperty('powerState', 'apower')
    def fromPowerState(self, value):
        return { 'ON': True, 'OFF': False }.get(value, value)

    @Iot.transformToProperty('powerState', 'apower')
    def toPowerState(self, value):
        return { True: 'ON', False: 'OFF'}.get(value, value)

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

@Endpoint.addInterface(PowerController, proactivelyReported=True, retrievable=True, uncertaintyInMilliseconds=0) ### Need to think through how to specify uncertainty for a property
@Endpoint.addInterface(Speaker)
class dhroneTV(Endpoint):
    manufacturerName = 'dhrone'
    description = 'iotTV controller by dhrone'
    displayCategories = 'OTHER'
    proactivelyReported = False
    retrievable=False
    uncertaintyInMilliseconds=0

    @Endpoint.addDirective(['TurnOn'])
    def TurnOn(self, request):
        self.iot['powerState'] = True

    @Endpoint.addDirective
    def TurnOff(self, request):
        self.iot['powerState'] = False

    @Endpoint.addDirective(['AdjustVolume','SetVolume'])
    def Volume(self, request):
        if request.name == 'AdjustVolume':
            v = self.iot['volume'] + request.payload['volume']
            self.iot['volume'] = 0 if v < 0 else 100 if v > 100 else v
        else:
            self.iot['volume'] = request.payload['volume']

class dhroneTVScene(Endpoint):
    manufacturerName = 'dhrone'
    description = 'iotTV controller by dhrone'
    displayCategories = 'SCENE_TRIGGER'

    class Iot(iotTV):
        def getThingName(self):
            return self.endpointId.split(':')[0]

    @Endpoint.addDirective
    def Activate(self, request):
        (endpointId, sceneId) = request.endpointId.split(':')
        ds = { 'epower':True, 'esource': 'HDMI1', 'input': 'SAT', 'powerState':True }
        self.iot.batchSet(ds)

    @Endpoint.addDirective
    def Deactivate(self, request):
        (endpointId, sceneId) = request.endpointId.split(':')
        ds = { 'epower': False, 'input': 'CD' }
        self.iot.batchSet(ds)

#user = StaticUser()
#user.addEndpoint(endpointClass=dhroneTV, things='avmctrl_den', friendlyName='Sound', description='Sound by dhrone')
#user.addEndpoint(endpointClass=dhroneTVScene, things='avmctrl_den', friendlyName='TV', description='TV by dhrone'))
#ash = pyASH(user)
#lambda_handler = ash.lambda_handler

if __name__ == u'lambda_function':
    user = StaticUser()
    user.addEndpoint(endpointClass=dhroneTV, things='avmctrl_den', friendlyName='Sound', description='Sound by dhrone')
    user.addEndpoint(endpointClass=dhroneTVScene, things='avmctrl_den', friendlyName='TV', description='TV by dhrone')

    pyash = pyASH(user)

if __name__ == u'__main__':
    from user import DbUser


    user = DbUser()
    user.createTables()

    user.createUser('ron@ritchey.org')

    user.addEndpoint(endpointClass=dhroneTV, things='avmctrl_den', friendlyName='Sound', description='Sound by dhrone')
    user.addEndpoint(endpointClass=dhroneTVScene, things='avmctrl_den', friendlyName='TV', description='TV by dhrone')
    user.commit()
