# -*- coding: utf-8 -*-

# Copyright 2018 dhrone. All Rights Reserved.
#
import pytest
import time
from copy import deepcopy

# Imports for v3 validation
from validation import validate_message
import jsonschema
from jsonschema import validate
import json

# pyASH imports
from endpoint import Endpoint
from iot import Iot, IotTest
from user import DemoUser
from pyASH import pyASH
from message import Request
from objects import Header, Channel, CameraStream, Color

from interface import *
from utility import LOGLEVEL

# Setup logger
import logging
logger = logging.getLogger(__name__)
logger.setLevel(LOGLEVEL)

@IotTest.initial('apower', True)
@IotTest.initial('asource', 'CD')
@IotTest.initial('mute', False)
@IotTest.initial('volume', 5)
@IotTest.initial('brightness', 50)
@IotTest.initial('channel', Channel(504, 'NBC4', 'NBC', 'someUrl').json)
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
@Endpoint.addInterface(BrightnessController)
@Endpoint.addInterface(EndpointHealth)
@Endpoint.addInterface(ColorController)
@Endpoint.addInterface(ColorTemperatureController)
@Endpoint.addInterface(InputController)
@Endpoint.addInterface(LockController)
@Endpoint.addInterface(PercentageController)
@Endpoint.addInterface(PowerLevelController, uncertaintyInMilliseconds=200)
@Endpoint.addInterface(StepSpeaker)
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
    def OnWeGo(self, request):
        self.iot['powerState'] = 'ON'

    @Endpoint.addDirective
    def TurnOff(self, request):
        self.iot['powerState'] = 'OFF'

    @Endpoint.addDirective(['AdjustVolume','SetVolume'], interface='Alexa.Speaker')
    def Volume(self, request):
        if request.name == 'AdjustVolume':
            v = self.iot['volume'] + request.payload['volume']
            self.iot['volume'] = 0 if v < 0 else 100 if v > 100 else v
        else:
            self.iot['volume'] = request.payload['volume']

    @Endpoint.addDirective
    def ChangeChannel(self, request):
        self.iot['channel'] = request.payload['channel']

    @Endpoint.addDirective
    def SkipChannels(self, request):
        count = request.payload['channelCount']
        self.iot['channel'] = Channel(str(int(self.iot['channel']['number'])+count), 'NBC4', 'NBC', 'someUrl').json

    @Endpoint.addDirective
    def InitializeCameraStreams(self, request):
        c = CameraStream()
        c.protocol = 'RTSP'
        c.uri = 'rtsp://username:password@link.to.video:443/feed1.mp4'
        c.expirationTime ='2017-09-27T20:30:30.45Z'
        c.idleTimeoutSeconds = 30
        c.resolution = (1920,1080)
        c.authorizationType = 'BASIC'
        c.videoCodec = 'H264'
        c.audioCodec = 'AAC'
        cameraStreams = [c.jsonResponse]
        c = CameraStream()
        c.protocol = 'RTSP'
        c.uri = 'rtsp://username:password@link.to.video:443/feed2.mp4'
        c.expirationTime ='2017-09-27T20:30:30.45Z'
        c.idleTimeoutSeconds = 60
        c.resolution = (1280,720)
        c.authorizationType = 'DIGEST'
        c.videoCodec = 'MPEG2'
        c.audioCodec = 'G711'
        cameraStreams.append(c.jsonResponse)

        payload = {'cameraStreams': cameraStreams, 'imageUri': 'https://username:password@link.to.image/image.jpg' }

        return {
            'context': {},
            'event': {
                'header': Header('Alexa.CameraStreamController', 'Response', request.correlationToken).json,
                'endpoint': {
                    'endpointId': request.endpointId
                },
                'payload': payload
            }
        }

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

def validate_message(request, response):
    with open('alexa_smart_home_message_schema.json') as json_file:
        schema = json.load(json_file)
    validate(response, schema)

def cleanse(r):

    if 'context' in r:
        if 'properties' in r['context']:
            if r['context']['properties'] is not None:
                for p in r['context']['properties']:
                    if 'timeOfSample' in p: p['timeOfSample'] = 'TIMESTAMP'
    if 'event' in r:
        if 'header' in r['event']:
            if 'messageId' in r['event']['header']: r['event']['header']['messageId'] = 'MESSAGEID'
            if 'correlationToken' in r['event']['header']: r['event']['header']['correlationToken'] = 'TOKEN'
        if 'endpoint' in r['event']:
            if 'scope' in r['event']['endpoint']:
                if 'token' in r['event']['endpoint']['scope']: r['event']['endpoint']['scope']['token'] = 'TOKEN'
    return r

def sk(v):
    return v['name']

def compareResults(r1, r2):
    r1 = deepcopy(r1)
    r2 = deepcopy(r2)
    validateFailed = False
    try:
        validate_message(request, response)
    except:
        validateFailed=True
        print ('Validation Error')

    if r2['event']['header']['name']=='ErrorResponse':
        raise Exception(r2['event']['payload']['type'], r2['event']['payload']['message'])

    # Fix temporal values so that they do not get flagged as different
    r1 = cleanse(r1)
    r2 = cleanse(r2)

    if 'context' in r1:
        if 'properties' in r1['context']:
            r1['context']['properties'] = sorted(r1['context']['properties'], key=sk)
            r2['context']['properties'] = sorted(r2['context']['properties'], key=sk)

    print ('**** R1 ****')
    print(json.dumps(r1, indent=4))
    print ('**** R2 ****')
    print(json.dumps(r2, indent=4))
    assert r1 == r2

@pytest.fixture
def setup():
    user = DemoUser()
    user.addEndpoint(endpointClass=dhroneTV, things='device_1', friendlyName='Sound', description='Sound by dhrone')
    user.addEndpoint(endpointClass=dhroneTVScene, things='device_1', friendlyName='TV', description='TV by dhrone')
    pyash = pyASH(user)

    return pyash



def test_PowerController_TurnOff(setup):
    pyash = setup
    pyash.user.endpoints['dhroneTV:device_1'].iot['powerState']='ON'
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
                "endpointId": "dhroneTV:device_1",
                "cookie": {}
            },
            "payload": {}
        }
    }

    expected_response = {
        "context": {
            "properties": [
                {
                    "namespace": "Alexa.PowerController",
                    "name": "powerState",
                    "value": "OFF",
                    "timeOfSample": "2017-09-27T18:30:30.45Z",
                    "uncertaintyInMilliseconds": 0
                },
                {
                    "namespace": "Alexa.EndpointHealth",
                    "name": "connectivity",
                    "value": {
                        "value": "OK"
                    },
                    "timeOfSample": "2017-09-27T18:30:30.45Z",
                    "uncertaintyInMilliseconds": 0
                }
            ]
        },
        "event": {
            "header": {
                "namespace": "Alexa",
                "name": "Response",
                "payloadVersion": "3",
                "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
                "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-Amazon"
                },
                "endpointId": "dhroneTV:device_1"
            },
            "payload": { }
        }
    }
    response = pyash.lambda_handler(request)
    compareResults(expected_response, response)

def test_PowerController_TurnOn(setup):
    pyash = setup
    pyash.user.endpoints['dhroneTV:device_1'].iot['powerState']='OFF'
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
                "endpointId": "dhroneTV:device_1",
                "cookie": {}
            },
            "payload": {}
        }
    }
    expected_response = {
        "context": {
            "properties": [
                {
                    "namespace": "Alexa.PowerController",
                    "name": "powerState",
                    "value": "ON",
                    "timeOfSample": "2017-09-27T18:30:30.45Z",
                    "uncertaintyInMilliseconds": 0
                },
                {
                    "namespace": "Alexa.EndpointHealth",
                    "name": "connectivity",
                    "value": {
                        "value": "OK"
                    },
                    "timeOfSample": "2017-09-27T18:30:30.45Z",
                    "uncertaintyInMilliseconds": 0
                }
            ]
        },
        "event": {
            "header": {
                "namespace": "Alexa",
                "name": "Response",
                "payloadVersion": "3",
                "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
                "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-Amazon"
                },
                "endpointId": "dhroneTV:device_1"
            },
            "payload": {}
        }
    }
    response = pyash.lambda_handler(request)
    compareResults(expected_response, response)

def test_Speaker_AdjustVolume(setup):
    pyash = setup
    pyash.user.endpoints['dhroneTV:device_1'].iot['volume']=50
    pyash.user.endpoints['dhroneTV:device_1'].iot['muted']=False
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
                "endpointId": "dhroneTV:device_1",
                "cookie": {}
            },
            "payload": {
                "volume": -20,
                "volumeDefault": False
            }
        }
    }
    expected_response = {
        "context": {
            "properties": [
                {
                    "namespace": "Alexa.Speaker",
                    "name": "volume",
                    "value": 30,
                    "timeOfSample": "2017-09-27T18:30:30.45Z",
                    "uncertaintyInMilliseconds": 0
                },
                {
                    "namespace": "Alexa.Speaker",
                    "name": "muted",
                    "value": False,
                    "timeOfSample": "2017-09-27T18:30:30.45Z",
                    "uncertaintyInMilliseconds": 0
                },
                {
                    "namespace": "Alexa.EndpointHealth",
                    "name": "connectivity",
                    "value": {
                        "value": "OK"
                    },
                    "timeOfSample": "2017-09-27T18:30:30.45Z",
                    "uncertaintyInMilliseconds": 0
                }
            ]
        },
        "event": {
            "header": {
                "namespace": "Alexa",
                "name": "Response",
                "payloadVersion": "3",
                "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
                "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-Amazon"
                },
                "endpointId": "dhroneTV:device_1"
            },
            "payload": {}
        }
    }
    response = pyash.lambda_handler(request)
    compareResults(expected_response, response)

def test_Speaker_SetVolume(setup):
    pyash = setup
    pyash.user.endpoints['dhroneTV:device_1'].iot['muted']=False
    pyash.user.endpoints['dhroneTV:device_1'].iot['volume']=10
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
                "endpointId": "dhroneTV:device_1",
                "cookie": {}
            },
            "payload": {
                "volume": 30,
                "volumeDefault": False
            }
        }
    }
    expected_response = {
        "context": {
            "properties": [
                {
                    "namespace": "Alexa.Speaker",
                    "name": "volume",
                    "value": 30,
                    "timeOfSample": "2017-09-27T18:30:30.45Z",
                    "uncertaintyInMilliseconds": 0
                },
                {
                    "namespace": "Alexa.Speaker",
                    "name": "muted",
                    "value": False,
                    "timeOfSample": "2017-09-27T18:30:30.45Z",
                    "uncertaintyInMilliseconds": 0
                },
                {
                    "namespace": "Alexa.EndpointHealth",
                    "name": "connectivity",
                    "value": {
                        "value": "OK"
                    },
                    "timeOfSample": "2017-09-27T18:30:30.45Z",
                    "uncertaintyInMilliseconds": 0
                }
            ]
        },
        "event": {
            "header": {
                "namespace": "Alexa",
                "name": "Response",
                "payloadVersion": "3",
                "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
                "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-Amazon"
                },
                "endpointId": "dhroneTV:device_1"
            },
            "payload": {}
        }
    }
    response = pyash.lambda_handler(request)
    compareResults(expected_response, response)

def test_Speaker_SetMute(setup):
    pyash = setup
    pyash.user.endpoints['dhroneTV:device_1'].iot['muted']=False
    pyash.user.endpoints['dhroneTV:device_1'].iot['volume']=30
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
                "endpointId": "dhroneTV:device_1",
                "cookie": {}
            },
            "payload": {
                "mute": True
            }
        }
    }
    expected_response = {
        "context": {
            "properties": [
                {
                    "namespace": "Alexa.Speaker",
                    "name": "volume",
                    "value": 30,
                    "timeOfSample": "2017-09-27T18:30:30.45Z",
                    "uncertaintyInMilliseconds": 0
                },
                {
                    "namespace": "Alexa.Speaker",
                    "name": "muted",
                    "value": True,
                    "timeOfSample": "2017-09-27T18:30:30.45Z",
                    "uncertaintyInMilliseconds": 0
                },
                {
                    "namespace": "Alexa.EndpointHealth",
                    "name": "connectivity",
                    "value": {
                        "value": "OK"
                    },
                    "timeOfSample": "2017-09-27T18:30:30.45Z",
                    "uncertaintyInMilliseconds": 0
                }
            ]
        },
        "event": {
            "header": {
                "namespace": "Alexa",
                "name": "Response",
                "payloadVersion": "3",
                "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
                "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-Amazon"
                },
                "endpointId": "dhroneTV:device_1"
            },
            "payload": {}
        }
    }
    response = pyash.lambda_handler(request)
    compareResults(expected_response, response)

    request['directive']['payload']['mute']=False
    expected_response['context']['properties'][1]['value']=False
    response = pyash.lambda_handler(request)
    compareResults(expected_response, response)

def test_BrightnessController_AdjustBrightness(setup):
    pyash = setup
    pyash.user.endpoints['dhroneTV:device_1'].iot['brightness']=50
    request = {
        "directive": {
            "header": {
                "namespace": "Alexa.BrightnessController",
                "name": "AdjustBrightness",
                "payloadVersion": "3",
                "messageId": "1bd5d003-31b9-476f-ad03-71d471922820",
                "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-skill"
                },
                "endpointId": "dhroneTV:device_1",
                "cookie": {}
            },
            "payload": {
                "brightnessDelta": -25
            }
        }
    }
    expected_response = {
        "context": {
            "properties": [
                {
                    "namespace": "Alexa.BrightnessController",
                    "name": "brightness",
                    "value": 25,
                    "timeOfSample": "2017-02-03T16:20:50.52Z",
                    "uncertaintyInMilliseconds": 0
                },
                {
                    "namespace": "Alexa.EndpointHealth",
                    "name": "connectivity",
                    "value": {
                        "value": "OK"
                    },
                    "timeOfSample": "2017-09-27T18:30:30.45Z",
                    "uncertaintyInMilliseconds": 0
                }
            ]
        },
        "event": {
            "header": {
                "namespace": "Alexa",
                "name": "Response",
                "payloadVersion": "3",
                "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
                "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-Amazon"
                },
                "endpointId": "dhroneTV:device_1"
            },
            "payload": {}
        }
    }
    response = pyash.lambda_handler(request)
    compareResults(expected_response, response)

    request['directive']['payload']['brightnessDelta']=35
    expected_response['context']['properties'][0]['value']=60
    response = pyash.lambda_handler(request)
    compareResults(expected_response, response)


def test_BrightnessController_SetBrightness(setup):
    pyash = setup
    pyash.user.endpoints['dhroneTV:device_1'].iot['brightness']=50
    request = {
        "directive": {
            "header": {
                "namespace": "Alexa.BrightnessController",
                "name": "SetBrightness",
                "payloadVersion": "3",
                "messageId": "1bd5d003-31b9-476f-ad03-71d471922820",
                "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-skill"
                },
                "endpointId": "dhroneTV:device_1",
                "cookie": {}
            },
            "payload": {
                "brightness": 70
            }
        }
    }
    expected_response = {
        "context": {
            "properties": [
                {
                    "namespace": "Alexa.BrightnessController",
                    "name": "brightness",
                    "value": 70,
                    "timeOfSample": "2017-09-27T18:30:30.45Z",
                    "uncertaintyInMilliseconds": 0
                },
                {
                    "namespace": "Alexa.EndpointHealth",
                    "name": "connectivity",
                    "value": {
                        "value": "OK"
                    },
                    "timeOfSample": "2017-09-27T18:30:30.45Z",
                    "uncertaintyInMilliseconds": 0
                }
            ]
        },
        "event": {
            "header": {
                "namespace": "Alexa",
                "name": "Response",
                "payloadVersion": "3",
                "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
                "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-Amazon"
                },
                "endpointId": "dhroneTV:device_1"
            },
            "payload": {}
        }
    }
    response = pyash.lambda_handler(request)
    compareResults(expected_response, response)

    request['directive']['payload']['brightness']=40
    expected_response['context']['properties'][0]['value']=40
    response = pyash.lambda_handler(request)
    compareResults(expected_response, response)

def test_ChannelController_ChangeChannel(setup):
    pyash = setup
    pyash.user.endpoints['dhroneTV:device_1'].iot['channel']= Channel(number='504', callSign='NBC4', affiliateCallSign='NBC', uri='someUrl').json
    request = {
        "directive": {
            "header": {
                "namespace": "Alexa.ChannelController",
                "name": "ChangeChannel",
                "payloadVersion": "3",
                "messageId": "1bd5d003-31b9-476f-ad03-71d471922820",
                "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-skill"
                },
                "endpointId": "dhroneTV:device_1",
                "cookie": {}
            },
            "payload": {
                "channel": {
                    "number": "505",
                    "callSign": "FOX5",
                    "affiliateCallSign": "FOX",
                    "uri": "someUrl"
                },
                "channelMetadata": {
                    "name": "Alternate Channel Name",
                    "image": "urlToImage"
                }
            }
        }
    }
    expected_response = {
        "context": {
            "properties": [
                {
                    "namespace": "Alexa.ChannelController",
                    "name": "channel",
                    "value": {
                        "number": "505",
                        "callSign": "FOX5",
                        "affiliateCallSign": "FOX"
                    },
                    "timeOfSample": "2017-09-27T18:30:30.45Z",
                    "uncertaintyInMilliseconds": 0
                },
                {
                    "namespace": "Alexa.EndpointHealth",
                    "name": "connectivity",
                    "value": {
                        "value": "OK"
                    },
                    "timeOfSample": "2017-09-27T18:30:30.45Z",
                    "uncertaintyInMilliseconds": 0
                }
            ]
        },
        "event": {
            "header": {
                "namespace": "Alexa",
                "name": "Response",
                "payloadVersion": "3",
                "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
                "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-Amazon"
                },
                "endpointId": "dhroneTV:device_1"
            },
            "payload": {}
        }
    }
    response = pyash.lambda_handler(request)
    compareResults(expected_response, response)

def test_ChannelController_ChangeChannel(setup):
    pyash = setup
    pyash.user.endpoints['dhroneTV:device_1'].iot['channel']= Channel(number='509', callSign='ABC9', affiliateCallSign='ABC', uri='someUrl').json
    request = {
        "directive": {
            "header": {
                "namespace": "Alexa.ChannelController",
                "name": "SkipChannels",
                "payloadVersion": "3",
                "messageId": "1bd5d003-31b9-476f-ad03-71d471922820",
                "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-skill"
                },
                "endpointId": "dhroneTV:device_1",
                "cookie": {}
            },
            "payload": {
                "channelCount": -5
            }
        }
    }
    expected_response = {
        "context": {
            "properties": [
                {
                    "namespace": "Alexa.ChannelController",
                    "name": "channel",
                    "value": {
                        "number": "504",
                        "callSign": "NBC4",
                        "affiliateCallSign": "NBC"
                    },
                    "timeOfSample": "2017-09-27T18:30:30.45Z",
                    "uncertaintyInMilliseconds": 0
                },
                {
                    "namespace": "Alexa.EndpointHealth",
                    "name": "connectivity",
                    "value": {
                        "value": "OK"
                    },
                    "timeOfSample": "2017-09-27T18:30:30.45Z",
                    "uncertaintyInMilliseconds": 0
                }
            ]
        },
        "event": {
            "header": {
                "namespace": "Alexa",
                "name": "Response",
                "payloadVersion": "3",
                "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
                "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-Amazon"
                },
                "endpointId": "dhroneTV:device_1"
            },
            "payload": {}
        }
    }
    response = pyash.lambda_handler(request)
    compareResults(expected_response, response)

def test_ColorController_SetColor(setup):
    pyash = setup
    pyash.user.endpoints['dhroneTV:device_1'].iot['color']= Color(hue=320.4, saturation=0.6138, brightness=0.7524).json
    request = {
        "directive": {
            "header": {
                "namespace": "Alexa.ColorController",
                "name": "SetColor",
                "payloadVersion": "3",
                "messageId": "1bd5d003-31b9-476f-ad03-71d471922820",
                "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-skill"
                },
                "endpointId": "dhroneTV:device_1",
                "cookie": {}
            },
            "payload": {
                "color": {
                    "hue": 350.5,
                    "saturation": 0.7138,
                    "brightness": 0.6524
                }
            }
        }
    }
    expected_response = {
        "context": {
            "properties": [
                {
                    "namespace": "Alexa.ColorController",
                    "name": "color",
                    "value": {
                        "hue": 350.5,
                        "saturation": 0.7138,
                        "brightness": 0.6524
                    },
                    "timeOfSample": "2017-09-27T18:30:30.45Z",
                    "uncertaintyInMilliseconds": 0
                },
                {
                    "namespace": "Alexa.EndpointHealth",
                    "name": "connectivity",
                    "value": {
                        "value": "OK"
                    },
                    "timeOfSample": "2017-09-27T18:30:30.45Z",
                    "uncertaintyInMilliseconds": 0
                }
            ]
        },
        "event": {
            "header": {
                "namespace": "Alexa",
                "name": "Response",
                "payloadVersion": "3",
                "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
                "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-Amazon"
                },
                "endpointId": "dhroneTV:device_1"
            },
            "payload": {}
        }
    }
    response = pyash.lambda_handler(request)
    compareResults(expected_response, response)

def test_ColorTemperatureController_SetColorTemperature(setup):
    pyash = setup
    pyash.user.endpoints['dhroneTV:device_1'].iot['colorTemperatureInKelvin']= 4000
    request = {
        "directive": {
            "header": {
                "namespace": "Alexa.ColorTemperatureController",
                "name": "SetColorTemperature",
                "payloadVersion": "3",
                "messageId": "1bd5d003-31b9-476f-ad03-71d471922820",
                "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-skill"
                },
                "endpointId": "dhroneTV:device_1",
                "cookie": {}
            },
            "payload": {
                "colorTemperatureInKelvin": 5000
            }
        }
    }
    expected_response = {
        "context": {
            "properties": [
                {
                    "namespace": "Alexa.ColorTemperatureController",
                    "name": "colorTemperatureInKelvin",
                    "value": 5000,
                    "timeOfSample": "2017-09-27T18:30:30.45Z",
                    "uncertaintyInMilliseconds": 0
                },
                {
                    "namespace": "Alexa.EndpointHealth",
                    "name": "connectivity",
                    "value": {
                        "value": "OK"
                    },
                    "timeOfSample": "2017-09-27T18:30:30.45Z",
                    "uncertaintyInMilliseconds": 0
                }
            ]
        },
        "event": {
            "header": {
                "namespace": "Alexa",
                "name": "Response",
                "payloadVersion": "3",
                "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
                "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-Amazon"
                },
                "endpointId": "dhroneTV:device_1"
            },
            "payload": {}
        }
    }
    response = pyash.lambda_handler(request)
    compareResults(expected_response, response)

def test_ColorTemperatureController_Increase_DecreaseColorTemperature(setup):
    pyash = setup
    pyash.user.endpoints['dhroneTV:device_1'].iot['colorTemperatureInKelvin']= 4000
    request = {
        "directive": {
            "header": {
                "namespace": "Alexa.ColorTemperatureController",
                "name": "IncreaseColorTemperature",
                "payloadVersion": "3",
                "messageId": "1bd5d003-31b9-476f-ad03-71d471922820",
                "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-skill"
                },
                "endpointId": "dhroneTV:device_1",
                "cookie": {}
            },
            "payload": {}
        }
    }
    expected_response = {
        "context": {
            "properties": [
                {
                    "namespace": "Alexa.ColorTemperatureController",
                    "name": "colorTemperatureInKelvin",
                    "value": 5500,
                    "timeOfSample": "2017-09-27T18:30:30.45Z",
                    "uncertaintyInMilliseconds": 0
                },
                {
                    "namespace": "Alexa.EndpointHealth",
                    "name": "connectivity",
                    "value": {
                        "value": "OK"
                    },
                    "timeOfSample": "2017-09-27T18:30:30.45Z",
                    "uncertaintyInMilliseconds": 0
                }
            ]
        },
        "event": {
            "header": {
                "namespace": "Alexa",
                "name": "Response",
                "payloadVersion": "3",
                "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
                "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-Amazon"
                },
                "endpointId": "dhroneTV:device_1"
            },
            "payload": {}
        }
    }
    response = pyash.lambda_handler(request)
    compareResults(expected_response, response)

    request['directive']['header']['name'] = 'DecreaseColorTemperature'
    expected_response['context']['properties'][0]['value']=4000
    response = pyash.lambda_handler(request)
    compareResults(expected_response, response)

def test_InputController_SelectInput(setup):
    pyash = setup
    pyash.user.endpoints['dhroneTV:device_1'].iot['input']= 'CD'
    request = {
        "directive": {
            "header": {
                "namespace": "Alexa.InputController",
                "name": "SelectInput",
                "payloadVersion": "3",
                "messageId": "1bd5d003-31b9-476f-ad03-71d471922820",
                "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-skill"
                },
                "endpointId": "dhroneTV:device_1",
                "cookie": {}
            },
            "payload": {
                "input": "HDMI1"
            }
        }
    }
    expected_response = {
        "context": {
            "properties": [
                {
                    "namespace": "Alexa.InputController",
                    "name": "input",
                    "value": "HDMI1",
                    "timeOfSample": "2017-09-27T18:30:30.45Z",
                    "uncertaintyInMilliseconds": 0
                },
                {
                    "namespace": "Alexa.EndpointHealth",
                    "name": "connectivity",
                    "value": {
                        "value": "OK"
                    },
                    "timeOfSample": "2017-09-27T18:30:30.45Z",
                    "uncertaintyInMilliseconds": 0
                }
            ]
        },
        "event": {
            "header": {
                "namespace": "Alexa",
                "name": "Response",
                "payloadVersion": "3",
                "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
                "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-Amazon"
                },
                "endpointId": "dhroneTV:device_1"
            },
            "payload": {}
        }
    }
    response = pyash.lambda_handler(request)
    compareResults(expected_response, response)

def test_LockController_LockUnlock(setup):
    pyash = setup
    pyash.user.endpoints['dhroneTV:device_1'].iot['lockState']= 'UNLOCKED'
    request = {
        "directive": {
            "header": {
                "namespace": "Alexa.LockController",
                "name": "Lock",
                "payloadVersion": "3",
                "messageId": "1bd5d003-31b9-476f-ad03-71d471922820",
                "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-skill"
                },
                "endpointId": "dhroneTV:device_1",
                "cookie": {}
            },
            "payload": {}
        }
    }
    expected_response = {
        "context": {
            "properties": [
                {
                    "namespace": "Alexa.LockController",
                    "name": "lockState",
                    "value": "LOCKED",
                    "timeOfSample": "2017-09-27T18:30:30.45Z",
                    "uncertaintyInMilliseconds": 0
                },
                {
                    "namespace": "Alexa.EndpointHealth",
                    "name": "connectivity",
                    "value": {
                        "value": "OK"
                    },
                    "timeOfSample": "2017-09-27T18:30:30.45Z",
                    "uncertaintyInMilliseconds": 0
                }
            ]
        },
        "event": {
            "header": {
                "namespace": "Alexa",
                "name": "Response",
                "payloadVersion": "3",
                "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
                "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-Amazon"
                },
                "endpointId": "dhroneTV:device_1"
            },
            "payload": {}
        }
    }
    response = pyash.lambda_handler(request)
    compareResults(expected_response, response)

    request['directive']['header']['name']='Unlock'
    expected_response['context']['properties'][0]['value']='UNLOCKED'
    response = pyash.lambda_handler(request)
    compareResults(expected_response, response)

def test_PercentageController_SetAdjust(setup):
    pyash = setup
    pyash.user.endpoints['dhroneTV:device_1'].iot['percentage']= 50
    request = {
        "directive": {
            "header": {
                "namespace": "Alexa.PercentageController",
                "name": "SetPercentage",
                "payloadVersion": "3",
                "messageId": "1bd5d003-31b9-476f-ad03-71d471922820",
                "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-skill"
                },
                "endpointId": "dhroneTV:device_1",
                "cookie": {}
            },
            "payload": {
                "percentage": 74
            }
        }
    }
    expected_response = {
        "context": {
            "properties": [
                {
                    "namespace": "Alexa.PercentageController",
                    "name": "percentage",
                    "value": 74,
                    "timeOfSample": "2017-09-27T18:30:30.45Z",
                    "uncertaintyInMilliseconds": 0
                },
                {
                    "namespace": "Alexa.EndpointHealth",
                    "name": "connectivity",
                    "value": {
                        "value": "OK"
                    },
                    "timeOfSample": "2017-09-27T18:30:30.45Z",
                    "uncertaintyInMilliseconds": 0
                }
            ]
        },
        "event": {
            "header": {
                "namespace": "Alexa",
                "name": "Response",
                "payloadVersion": "3",
                "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
                "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-Amazon"
                },
                "endpointId": "dhroneTV:device_1"
            },
            "payload": {}
        }
    }

    response = pyash.lambda_handler(request)
    compareResults(expected_response, response)

    request['directive']['header']['name']='AdjustPercentage'
    request['directive']['payload']['percentageDelta']=-20
    expected_response['context']['properties'][0]['value']=54
    response = pyash.lambda_handler(request)
    compareResults(expected_response, response)

def test_PowerLevelController_SetAdjust(setup):
    pyash = setup
    pyash.user.endpoints['dhroneTV:device_1'].iot['powerLevel']= 50
    request = {
        "directive": {
            "header": {
                "namespace": "Alexa.PowerLevelController",
                "name": "SetPowerLevel",
                "payloadVersion": "3",
                "messageId": "1bd5d003-31b9-476f-ad03-71d471922820",
                "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-skill"
                },
                "endpointId": "dhroneTV:device_1",
                "cookie": {}
            },
            "payload": {
                "powerLevel": 42
            }
        }
    }
    expected_response = {
        "context": {
            "properties": [
                {
                    "namespace": "Alexa.PowerLevelController",
                    "name": "powerLevel",
                    "value": 42,
                    "timeOfSample": "2017-09-27T18:30:30.45Z",
                    "uncertaintyInMilliseconds": 200
                },
                {
                    "namespace": "Alexa.EndpointHealth",
                    "name": "connectivity",
                    "value": {
                        "value": "OK"
                    },
                    "timeOfSample": "2017-09-27T18:30:30.45Z",
                    "uncertaintyInMilliseconds": 0
                }
            ]
        },
        "event": {
            "header": {
                "namespace": "Alexa",
                "name": "Response",
                "payloadVersion": "3",
                "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
                "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-Amazon"
                },
                "endpointId": "dhroneTV:device_1"
            },
            "payload": {}
        }
    }

    response = pyash.lambda_handler(request)
    compareResults(expected_response, response)

    request['directive']['header']['name']='AdjustPowerLevel'
    request['directive']['payload']['powerLevelDelta']=3
    expected_response['context']['properties'][0]['value']=45
    response = pyash.lambda_handler(request)
    compareResults(expected_response, response)

def test_StepSpeaker_SetAdjust(setup):
    pyash = setup
    pyash.user.endpoints['dhroneTV:device_1'].iot['muted']= False
    pyash.user.endpoints['dhroneTV:device_1'].iot['volume']= 50

    request = {
        "directive": {
            "header": {
                "namespace": "Alexa.StepSpeaker",
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
                "endpointId": "dhroneTV:device_1",
                "cookie": {}
            },
            "payload": {
                "volumeSteps": -20
            }
        }
    }
    expected_response = {
        "context": {
            "properties": [
                {
                    "namespace": "Alexa.EndpointHealth",
                    "name": "connectivity",
                    "value": {
                        "value": "OK"
                    },
                    "timeOfSample": "2017-09-27T18:30:30.45Z",
                    "uncertaintyInMilliseconds": 0
                }
            ]
        },
        "event": {
            "header": {
                "namespace": "Alexa",
                "name": "Response",
                "payloadVersion": "3",
                "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
                "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-Amazon"
                },
                "endpointId": "dhroneTV:device_1"
            },
            "payload": {}
        }
    }

    response = pyash.lambda_handler(request)
    compareResults(expected_response, response)

    request['directive']['header']['name']='SetMute'
    request['directive']['payload']['mute']= True
    response = pyash.lambda_handler(request)
    compareResults(expected_response, response)

def test_CameraStreamController_InitializeCameraStreams(setup):
    pyash = setup

    request = {
        "directive": {
            "header": {
                "namespace": "Alexa.CameraStreamController",
                "name": "InitializeCameraStreams",
                "payloadVersion": "3",
                "messageId": "1bd5d003-31b9-476f-ad03-71d471922820",
                "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-skill"
                },
                "endpointId": "dhroneTV:device_1",
                "cookie": {}
            },
            "payload": {
                "cameraStreams": [
                    {
                        "protocol": "RTSP",
                        "resolution": {
                            "width": 1920,
                            "height": 1080
                        },
                        "authorizationType": "BEARER",
                        "videoCodec": "H264",
                        "audioCodec": "AAC"
                    },
                    {
                        "protocol": "RTSP",
                        "resolution": {
                            "width": 1280,
                            "height": 720
                        },
                        "authorizationType": "BEARER",
                        "videoCodec": "MPEG2",
                        "audioCodec": "G711"
                    }
                ]
            }
        }
    }
    expected_response = {
        "context": {
            "properties": [
                {
                    "namespace": "Alexa.EndpointHealth",
                    "name": "connectivity",
                    "value": {
                        "value": "OK"
                    },
                    "timeOfSample": "2017-09-27T18:30:30.45Z",
                    "uncertaintyInMilliseconds": 0
                }
            ]
        },
        "event": {
            "header": {
                "namespace": "Alexa.CameraStreamController",
                "name": "Response",
                "payloadVersion": "3",
                "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
                "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-Amazon"
                },
                "endpointId": "dhroneTV:device_1"
            },
            "payload": {
                "cameraStreams": [
                    {
                        "uri": "rtsp://username:password@link.to.video:443/feed1.mp4",
                        "expirationTime": "2017-09-27T20:30:30.45Z",
                        "idleTimeoutSeconds": 30,
                        "protocol": "RTSP",
                        "resolution": {
                            "width": 1920,
                            "height": 1080
                        },
                        "authorizationType": "BASIC",
                        "videoCodec": "H264",
                        "audioCodec": "AAC"
                    },
                    {
                        "uri": "rtsp://username:password@link.to.video:443/feed2.mp4",
                        "expirationTime": "2017-09-27T20:30:30.45Z",
                        "idleTimeoutSeconds": 60,
                        "protocol": "RTSP",
                        "resolution": {
                            "width": 1280,
                            "height": 720
                        },
                        "authorizationType": "DIGEST",
                        "videoCodec": "MPEG2",
                        "audioCodec": "G711"
                    }
                ],
                "imageUri": "https://username:password@link.to.image/image.jpg"
            }
        }
    }

    response = pyash.lambda_handler(request)
    print (response)
    validateFailed = False
    try:
        validate_message(request, response)
    except:
        validateFailed=True
        print ('Validation Error')
    if validateFailed:
        raise Exception

    compareResults(expected_response, response)
