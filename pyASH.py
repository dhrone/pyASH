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
from message import Header

# Setup logger
logger = logging.getLogger(__name__)
logger.setLevel(LOGLEVEL)


class pyASH(object):
    def __init__(self, user, version='3'):
        self.user = user
        self.version = version if type(version) is str else str(version)
        if not self.version == '3': raise ValueError('pyAsh currently only supports API version 3')

    def handleAcceptGrant(self, request):
        # Provides tokens to user
        try:
            response = getAccessTokenFromCode(request['payload']['grant']['code'])
            user.storeTokens(response['access_token'], response['refresh_token'], response['expires_in'])
            return {
                'event': {
                    'header': Header('Alexa.Authorization', 'AcceptGrant.Response', payloadVersion=self.version).json,
                    'payload': {}
                }
            }
        except:
            # Generate Error Response
            pass

    def handleDiscovery(self, request):
        # Requires endpoints from user
        try:
            ret = []
            endpoints = self.user.getEndpoints(request)
            for ep in endpoints:
                ret.append(ep.jsonDiscover)
            return {
                'event': {
                    'header': Header('Alexa.Discovery', 'Discover.Response', payloadVersion=self.version).json,
                    'payload': {
                        'endpoints': ret
                    }
                }
            }
        except:
            # Generate Error Response
            pass

    def handleReportState(seld, request):
        # Requires endpoints from user
        try:
            endpoint = self.user.getEndpoint(request)
            return {
                'context': {
                    'properties': endpoint.jsonResponse
                },
                'event': {
                    'header': Header('Alexa', 'StateReport', correlationToken=request.correlationToken, payloadVersion=self.version).json,
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
        except:
            # Deal with failure
            pass

    def handleDirective(self, request):

        try:
            endpoint = self.user.getEndpoint(request)
            cls, handler = endpoint.getHandler(request)
            things = self.user._retrieveThings(request.endpointId)
            method = handler.__get__(cls(things=things), cls)

            ret = method(request)
            if ret:
                return ret

            time.sleep(1) # Allow time for update to be processed

            endpoint.iots[0].refresh()
            interface = endpoint._interfaces[request.namespace]['interface'](endpoint.iots[0])
            return {
                'context': {
                    'properties': interface.jsonResponse
                },
                'event': {
                    'header': Header('Alexa', 'Response', correlationToken=request.correlationToken, payloadVersion=self.version).json,
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
        except Exception as e:
            print (e)
            # Deal with failure




    def lambda_handler(self, request, context=None):

        if not request.namespace in VALID_DIRECTIVES:
            raise INVALID_INTERFACE('{0}:{1} is not a valid directive'.format(request.namespace, request.directive))
        if request.directive not in VALID_DIRECTIVES[request.namespace]:
            raise INVALID_DIRECTIVE('{0}:{1} is not a valid directive'.format(request.namespace, request.directive))
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
