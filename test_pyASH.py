# -*- coding: utf-8 -*-

# Copyright 2018 dhrone. All Rights Reserved.
#
import pytest
import time

# Imports for v3 validation
from validation import validate_message
import jsonschema

# pyASH imports
from endpoint import Endpoint
from iot import Iot, IotTest
from user import DemoUser
from pyASH import pyASH
from message import Request
from response import HEADER

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

    @Endpoint.addDirective(['AdjustVolume','SetVolume'])
    def Volume(self, request):
        if request.directive == 'AdjustVolume':
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
                'header': HEADER('Alexa.CameraStreamController', 'Response', request.correlationToken),
                'endpoint': {
                    'endpointId': request.endpointId
                },
                'payload': payload
            }
        }

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

def checkProperty(request, response, name, value):
    print (response)
    validateFailed = False
    try:
        validate_message(request, response)
    except:
        validateFailed=True
        print ('Validation Error')

    if validateFailed:
        raise Exception
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
    response = pyash.lambda_handler(request)
    checkProperty(request, response,'powerState','OFF')

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
    response = pyash.lambda_handler(request)
    checkProperty(request, response,'powerState','ON')

def test_Speaker_AdjustVolume(setup):
    pyash = setup
    pyash.user.endpoints['dhroneTV:device_1'].iot['volume']=50
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
    response = pyash.lambda_handler(request)
    checkProperty(request, response,'volume', 30)

def test_Speaker_SetVolume(setup):
    pyash = setup
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
    response = pyash.lambda_handler(request)
    checkProperty(request, response,'volume', 30)

def test_Speaker_SetMute(setup):
    pyash = setup
    pyash.user.endpoints['dhroneTV:device_1'].iot['muted']=False
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
    response = pyash.lambda_handler(request)
    checkProperty(request, response,'muted', True)

    request['directive']['payload']['mute']=False
    response = pyash.lambda_handler(request)
    checkProperty(request, response,'muted', False)

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
    response = pyash.lambda_handler(request)
    checkProperty(request, response,'brightness', 25)

    request['directive']['payload']['brightnessDelta']=35
    response = pyash.lambda_handler(request)
    checkProperty(request, response,'brightness', 60)

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
    response = pyash.lambda_handler(request)
    checkProperty(request, response,'brightness', 70)

    request['directive']['payload']['brightness']=40
    response = pyash.lambda_handler(request)
    checkProperty(request, response,'brightness', 40)

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
    response = pyash.lambda_handler(request)
    checkProperty(request, response,'channel', Channel('505', 'FOX5', 'FOX', 'someUrl').json)

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
    response = pyash.lambda_handler(request)
    checkProperty(request, response,'channel', Channel('504', 'NBC4', 'NBC').json)

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
    raise Exception
