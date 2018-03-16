# -*- coding: utf-8 -*-

# Copyright 2018 dhrone. All Rights Reserved.
#
import pytest
import time

# pyASH imports
from endpoint import Endpoint
from iot import Iot, IotTest
from user import DemoUser
from pyASH import pyASH
from message import Request

from interface import PowerController, Speaker
from utility import LOGLEVEL

# Setup logger
import logging
logger = logging.getLogger(__name__)
logger.setLevel(LOGLEVEL)

@IotTest.initial('apower', True)
@IotTest.initial('asource', 'CD')
@IotTest.initial('mute', False)
@IotTest.initial('volume', 5)
class iotTV(IotTest):

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
@Endpoint.addIot(iotTV)
class dhroneTV(Endpoint):
    manufacturerName = 'dhrone'
    description = 'iotTV controller by dhrone'
    displayCategories = 'OTHER'
    proactivelyReported = False
    retrievable=False
    uncertaintyInMilliseconds=0

    class Iot(iotTV):
        pass

    @Endpoint.addDirective(['TurnOn'])
    def TurnOn(self, request):
        self.iot['powerState'] = 'ON'

    @Endpoint.addDirective
    def TurnOff(self, request):
        self.iot['powerState'] = 'OFF'

    @Endpoint.addDirective(['AdjustVolume','SetVolume'])
    def Volume(self, request):
        if request.directive == 'AdjustVolume':
            v = self.iot['volume'] + request.payload['volume']
            self.iot['volume'] = 0 if v < 0 else 100 if v > 100 else v
        else:
            self.iot['volume'] = request.payload['volume']

#    @Endpoint.addDirective
#    def SetMute(self, request, iot):
#        iot['muted'] = request.payload['mute']

    @Endpoint.addDirective
    def SelectInput(self, request, iot):
        self.iot['asource'] = request.payload['input']

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



@pytest.fixture
def setup():
    user = DemoUser()
    user.addEndpoint(endpointClass=dhroneTV, things='device_1', friendlyName='Sound', description='Sound by dhrone')
    user.addEndpoint(endpointClass=dhroneTVScene, things='device_1', friendlyName='TV', description='TV by dhrone')
    pyash = pyASH(user)

    return pyash

def checkProperty(response, name, value):
    print (response)
    properties = response['context']['properties']
    for p in properties:
        assert 'namespace' in p
        assert 'name' in p
        assert 'value' in p
        assert 'timeOfSample' in p
        assert 'uncertaintyInMilliseconds' in p
        if p['name'] == name:
            assert p['value'] == value

def test_PowerController_TurnOff(setup):
    pyash = setup
    pyash.user.endpoints['dhroneTV|device_1'].iot['powerState']='ON'
    request = {
        "directive": {
            "header": {
                "namespace": "Alexa.PowerController",
                "name": "TurnOff",
                "payloadVersion": "3",
                "messageId": "1bd5d003-31b9-476f-ad03-71d471922820",
                "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-skill"
                },
                "endpointId": "dhroneTV|device_1",
                "cookie": {}
            },
            "payload": {}
        }
    }
    response = pyash.lambda_handler(request)
    checkProperty(response,'powerState','OFF')

def test_PowerController_TurnOn(setup):
    pyash = setup
    pyash.user.endpoints['dhroneTV|device_1'].iot['powerState']='OFF'
    request = {
        "directive": {
            "header": {
                "namespace": "Alexa.PowerController",
                "name": "TurnOn",
                "payloadVersion": "3",
                "messageId": "1bd5d003-31b9-476f-ad03-71d471922820",
                "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-skill"
                },
                "endpointId": "dhroneTV|device_1",
                "cookie": {}
            },
            "payload": {}
        }
    }
    response = pyash.lambda_handler(request)
    checkProperty(response,'powerState','ON')

def test_Speaker_AdjustVolume(setup):
    pyash = setup
    pyash.user.endpoints['dhroneTV|device_1'].iot['volume']=50
    request = {
        "directive": {
            "header": {
                "namespace": "Alexa.Speaker",
                "name": "AdjustVolume",
                "payloadVersion": "3",
                "messageId": "1bd5d003-31b9-476f-ad03-71d471922820",
                "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-skill"
                },
                "endpointId": "dhroneTV|device_1",
                "cookie": {}
            },
            "payload": {
                "volume": -20,
                "volumeDefault": False
            }
        }
    }
    response = pyash.lambda_handler(request)
    checkProperty(response,'volume', 30)

def test_Speaker_SetVolume(setup):
    pyash = setup
    pyash.user.endpoints['dhroneTV|device_1'].iot['volume']=10
    request = {
        "directive": {
            "header": {
                "namespace": "Alexa.Speaker",
                "name": "SetVolume",
                "payloadVersion": "3",
                "messageId": "1bd5d003-31b9-476f-ad03-71d471922820",
                "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-skill"
                },
                "endpointId": "dhroneTV|device_1",
                "cookie": {}
            },
            "payload": {
                "volume": 30,
                "volumeDefault": False
            }
        }
    }
    response = pyash.lambda_handler(request)
    checkProperty(response,'volume', 30)

def test_Speaker_SetMute(setup):
    pyash = setup
    pyash.user.endpoints['dhroneTV|device_1'].iot['muted']=False
    request = {
        "directive": {
            "header": {
                "namespace": "Alexa.Speaker",
                "name": "SetMute",
                "payloadVersion": "3",
                "messageId": "1bd5d003-31b9-476f-ad03-71d471922820",
                "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-skill"
                },
                "endpointId": "dhroneTV|device_1",
                "cookie": {}
            },
            "payload": {
                "mute": True
            }
        }
    }
    response = pyash.lambda_handler(request)
    checkProperty(response,'muted', True)

    request['directive']['payload']['mute']=False
    response = pyash.lambda_handler(request)
    checkProperty(response,'muted', False)
