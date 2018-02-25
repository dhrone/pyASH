# -*- coding: utf-8 -*-

# Copyright 2018 dhrone. All Rights Reserved.
#

import logging
import time
import json
import uuid
import os
import boto3
import urllib
from datetime import datetime

# Imports for v3 validation
from validation import validate_message
import jsonschema

import pyASH
from endpoint import Endpoint
from iot import Iot

# Setup logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class iotTV(Endpoint):
    class Metadata:
        manufacturerName = 'dhrone'
        description = 'iotTV controller by dhrone'
        displayCategories = 'OTHER'

    @Endpoint.register(['TurnOn'])
    def TurnOn(self, request):
        Iot(request.endpointId)['apower'] = True

    @Endpoint.register
    def TurnOff(self, request):
        Iot(request.endpointId)['apower'] = False

    @Endpoint.register(['AdjustVolume','SetVolume'])
    def Volume(self, request):
        d = Iot(request.endpointId)
        if request.directive == 'AdjustVolume':
            v = d['volume']*10 + request.payload['volume']
            d['volume'] = 0 if v < 0 else 10 if v > 100 else int(v/10)
        else:
            d['volume'] = int(request.payload['volume']/10)

    @Endpoint.register
    def SetMute(self, request):
        d = Iot(request.endpointId)
        d['muted'] = request.payload['mute']

    @Endpoint.register
    def SelectInput(self, request):
        d = Iot(request.endpointId)
        d['asource'] = request.payload['input']

class iotTVScene(Endpoint):
    class Metadata:
        manufacturerName = 'dhrone'
        description = 'iotTV controller by dhrone'
        displayCategories = 'SCENE_TRIGGER'

    @Endpoint.register
    def Activate(self, request):
        (endpointId, sceneId) = request.endpointId.split(':')
        d = Iot(endpointId)
        ds = { 'epower':True, 'esource': 'HDMI1', 'asource': 'SAT' }
        d.batchSet(ds)

    @Endpoint.register
    def Deactivate(self, request):
        (endpointId, sceneId) = request.endpointId.split(':')
        d = Iot(endpointId)
        ds = { 'epower': False, 'asource': 'CD' }
        d.batchSet(ds)


def actions(cls):
    """dict(str, function): All actions the appliance supports and their corresponding (unbound)
    method references. Action names are formatted for the DiscoverAppliancesRequest.
    """
    ret = {}
    for supercls in cls.__mro__:  # This makes inherited Appliances work
        for method in supercls.__dict__.values():
            for action in getattr(method, '_directives', []):
                ret[action] = method
    return ret

dAdjustVolumeUp = {
    "directive": {
        "header": {
            "namespace": "Alexa.Speaker",
            "name": "AdjustVolume",
            "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
            "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg==",
            "payloadVersion": "3"
        },
        "endpoint": {
            "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-skill"
            },
            "endpointId": "avmctrl_den",
            "cookie": { }
        },
        "payload": {
            "volume": 10
        }
    }
}
dAdjustVolumeDown = {
    "directive": {
        "header": {
            "namespace": "Alexa.Speaker",
            "name": "AdjustVolume",
            "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
            "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg==",
            "payloadVersion": "3"
        },
        "endpoint": {
            "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-skill"
            },
            "endpointId": "avmctrl_den",
            "cookie": { }
        },
        "payload": {
            "volume": -10
        }
    }
}
dSetVolume = {
    "directive": {
        "header": {
            "namespace": "Alexa.Speaker",
            "name": "SetVolume",
            "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
            "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg==",
            "payloadVersion": "3"
        },
        "endpoint": {
            "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-skill"
            },
            "endpointId": "avmctrl_den",
            "cookie": { }
        },
        "payload": {
            "volume": 50
        }
    }
}

dTurnOff = {
    "directive": {
        "header": {
            "namespace": "Alexa.PowerController",
            "name": "TurnOff",
            "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
            "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg==",
            "payloadVersion": "3"
        },
        "endpoint": {
            "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-skill"
            },
            "endpointId": "avmctrl_den",
            "cookie": { }
        },
        "payload": {
        }
    }
}

dActivate = {
    "directive": {
        "header": {
            "namespace": "Alexa.SceneController",
            "name": "Activate",
            "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
            "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg==",
            "payloadVersion": "3"
        },
        "endpoint": {
            "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-skill"
            },
            "endpointId": "avmctrl_den:watch",
            "cookie": { }
        },
        "payload": {
        }
    }
}

dDeactivate = {
    "directive": {
        "header": {
            "namespace": "Alexa.SceneController",
            "name": "Deactivate",
            "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
            "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg==",
            "payloadVersion": "3"
        },
        "endpoint": {
            "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-skill"
            },
            "endpointId": "avmctrl_den:watch",
            "cookie": { }
        },
        "payload": {
        }
    }
}

rVolumeUp = pyASH.Request(dAdjustVolumeUp)
rVolumeDown = pyASH.Request(dAdjustVolumeDown)
rSetVolume = pyASH.Request(dSetVolume)
rOff = pyASH.Request(dTurnOff)
rActivate = pyASH.Request(dActivate)
rDeactivate = pyASH.Request(dDeactivate)

#class discover(Discover):

#    @property
#    def endpoints(self):
#        eps = {}
#        eps['avmctrl_den'] = { 'type': iotTV }
#        eps['avmctrl_den:watch']=iotTVScene
#        return eps
