# -*- coding: utf-8 -*-

# Copyright 2018 by dhrone. All Rights Reserved.
#

import logging
import time
import json
import uuid
import os
#from botocore.vendored import requests
#import boto3
import urllib
from datetime import datetime
from datetime import timedelta

from utility import *
from message import Request
from response import HEADER

# Setup logger
logger = logging.getLogger(__name__)
logger.setLevel(LOGLEVEL)

def test_func(val):
    assert False


class pyASH(object):
    def __init__(self, user, version='3'):
        self.user = user
        self.version = version if type(version) is str else str(version)
        if not self.version == '3': raise ValueError('pyAsh currently only supports API version 3')

    @classmethod
    def _errorResponse(cls, request, e):
        json = {
            'event': {
                'header': HEADER('Alexa', 'ErrorResponse', request.correlationToken),
                'payload': e.payload
            }
        }
        if hasattr(request, 'endpointId'):
            json['event']['endpoint'] = {'endpointId': request.endpointId }
            if hasattr(request, 'scope'):
                json['event']['endpoint']['scope'] = request.scope.value

        return json

    def handleAcceptGrant(self, request):
        # Provides tokens to user
        try:
            user.getTokens(request)
            return {
                'event': {
                    'header': HEADER('Alexa.Authorization', 'AcceptGrant.Response'),
                    'payload': {}
                }
            }
        except InterfaceException as e:
            return self._errorResponse(request, e)
        except:
            raise

    def handleDiscovery(self, request):
        # Requires endpoints from user
        try:
            ret = []
            endpoints = self.user.getEndpoints(request)
            for ep in endpoints:
                ret.append(ep.jsonDiscover)
            return {
                'event': {
                    'header': HEADER('Alexa.Discovery', 'Discover.Response'),
                    'payload': {
                        'endpoints': ret
                    }
                }
            }
        except InterfaceException as e:
            return self._errorResponse(request, e)
        except:
            raise


    def handleReportState(seld, request):
        # Requires endpoints from user
        try:
            endpoint = self.user.getEndpoint(request)
            return {
                'context': {
                    'properties': endpoint.jsonResponse
                },
                'event': {
                    'header': HEADER('Alexa', 'StateReport', correlationToken=request.correlationToken),
                    'endpoint': {
                        'scope': {
                            'type': 'BearerToken',
                            'token': request.token
                        },
                        'endpointId' : endpoint.endpointId
                    },
                    'payload': {}
                }
            }
        except InterfaceException as e:
            return self._errorResponse(request, e)
        except:
            raise

    def handleDirective(self, request):

        try:
            endpoint = self.user.getEndpoint(request)
            cls, handler = endpoint.getHandler(request)
            things = self.user._retrieveThings(request.endpointId)
            method = handler.__get__(cls(iots=endpoint.iots), cls)

            healthif = endpoint._interfaces['Alexa.EndpointHealth']['interface'](endpoint.iots[0]) if 'Alexa.EndpointHealth' in endpoint._interfaces else None

            ret = method(request)
            if ret:
                if healthif:
                    if 'context' not in ret: ret['context'] = {}
                    if 'properties' not in ret['context']: ret['context']['properties'] = []
            else:
                waitStarted = time.time()
                waitFor = 5
                while not endpoint.iots[0].updateFinished():
                    if time.time() > waitStarted+waitFor:
                        raise ENDPOINT_UNREACHABLE('Timed out waiting for endpoint to update')

                interface = endpoint._interfaces[request.namespace]['interface'](endpoint.iots[0])
                ret =  {
                    'context': {
                        'properties': interface.jsonResponse
                    },
                    'event': {
                        'header': HEADER('Alexa', 'Response', request.correlationToken),
                        'endpoint': {
                            'endpointId' : endpoint.endpointId
                        },
                        'payload': {}
                    }
                }
            healthif = endpoint._interfaces['Alexa.EndpointHealth']['interface'](endpoint.iots[0]) if 'Alexa.EndpointHealth' in endpoint._interfaces else None
            if healthif: ret['context']['properties'] += healthif.jsonResponse
            if 'scope' in request.raw['directive']['endpoint']: ret['event']['endpoint']['scope'] = request.raw['directive']['endpoint']['scope']
            return ret
        except InterfaceException as e:
            return self._errorResponse(request, e)
        except OAUTH2_EXCEPTION as e:
            raise
        except MISCELLANIOUS_EXCEPTION as e:
            raise
        except:
            raise

    def lambda_handler(self, request, context=None):
        request = Request(request)
        return {
            'Alexa' : self.handleReportState,
            'Alexa.Authorization' : self.handleAcceptGrant,
            'Alexa.Discovery' : self.handleDiscovery,
        }.get(request.namespace, self.handleDirective)(request)

if __name__ == u'__main__':

    ts = get_utc_timestamp()
    u = 0

    p = BrightnessProperty(45, ts, u)
    print (p)

    p = ChannelProperty('6','PBS','KBTC', ts, u)
    print (p)

    p = ColorProperty(350.5, 0.7138, 0.6524, ts, u)
    print (p)

    p = ColorTemperatureInKelvinProperty(7500, ts, u)
    print (p)

    p = CookingModeProperty('TIMECOOK', ts, u)
    print (p)

    p = CookingModeProperty('OFF', ts, u)
    print (p)

    p = EndpointHealthProperty('UNREACHABLE', ts, u)
    print (p)

    p = CookingTimeProperty(datetime(2017,8,30,1,18,21),'cookCompletionTime', ts, u)
    print (p)

    p = CookingTimeControllerTimeProperty(timedelta(minutes=3, seconds=15), ts, u)
    print (p)

    p = CookingTimeControllerPowerProperty('MEDIUM', ts, u)
    print (p)

    fq = WeightFoodQuantity(2.5, 'POUND')
    p = CookingFoodItemProperty('Cooper river salmon', 'FISH', fq, ts, u)
    print(p)

    fq = FoodCountFoodQuantity(1, 'LARGE')
    p = CookingFoodItemProperty('Cooper river salmon', 'FISH', fq, ts, u)
    print (p)

    fq = VolumeFoodQuantity(2, 'LITER')
    p = CookingFoodItemProperty('Salmon Soup', 'FISH', fq, ts, u)
    print (p)

    p = InputProperty('HDMI1', ts, u)
    print (p)

    p = PowerLevelProperty(5, ts, u)
    print (p)

    p = LockProperty('LOCKED', ts, u)
    print (p)

    p = SpeakerMuteProperty(False, ts, u)
    print (p)

    p = PercentageProperty(74, ts, u)
    print (p)

    p = PowerStateProperty('OFF', ts, u)
    print (p)

    p = PowerLevelProperty('MEDIUM', ts, u)
    print (p)

    p = TemperatureProperty(68, 'FAHRENHEIT', ts, u)
    print (p)

    p = ThermostatModeProperty('AUTO','', ts, u)
    print (p)

    p = ThermostatModeProperty('AUTO', 'VENDOR_HEAT_COOL', ts, u)
    print (p)

    p = ThermostatModeProperty('CUSTOM', 'VENDOR_HEAT_COOL', ts, u)
    print (p)
