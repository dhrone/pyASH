# -*- coding: utf-8 -*-

# Copyright 2018 by dhrone. All Rights Reserved.
#

import logging
import time

from utility import *
#from message import Request
from objects import Header

# Setup logger
logger = logging.getLogger(__name__)
logger.setLevel(LOGLEVEL)

class Request(dict):
    """Simplifies retrieval of values from a request.

    Request takes a json object and exposes its contents as dynamically generated
    attributes.  It will search, depth-first to find a key within the json object
    that matches the requested attribute and will raise a KeyError if no key
    within the json object matches the requested attribute.  If you need to ensure
    that the key you are requesting comes from a specific path within the json
    object, you can string together attributes to specify the path that you want
    Request to follow to find the key.

    Note:

        Request will only return the first value that matches the requested attribute

    Example:

        json = {
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
    	            "endpointId": "endpoint-001",
    	            "cookie": {}
    	        },
    	        "payload": {
    	            "brightnessDelta": -25
    	        }
    	    }
    	}
        request = Request(json)
        >>> request.endpointId
        "endpoint-001"
        >>> request.endpoint.endpointId
        "endpoint-001"
        >>> request.payload
        { 'brightnessDelta': -25 }
        >>> request.brightnessDelta
        -25
        >>> request.payload.brightnessDelta
        -25
    """
    def __init__(self, rawRequest):
        super(Request, self).__init__(rawRequest)
        self.raw = rawRequest

    def __getattr__(self, name):
        res = self.findkey(name, self.raw)
        if isinstance(res, dict):
            return Request(res)
        if res:
            return res
        raise KeyError(name)

    def findkey(self, key, dictionary):
        for k,v in dictionary.items():
            if k==key:
                return v
            elif isinstance(v, dict):
                res = self.findkey(key,v)
                if res: return res
            else:
                continue
        return None

class pyASH(object):
    def __init__(self, user, version='3'):
        self.user = user
        self.version = version if type(version) is str else str(version)
        if not self.version == '3': raise ValueError('pyAsh currently only supports API version 3')

    @classmethod
    def _errorResponse(cls, request, e):
        json = {
            'event': {
                'header': Header(namespace='Alexa', name='ErrorResponse', correlationToken=request.correlationToken).json,
                'payload': e.payload
            }
        }
        if hasattr(request, 'endpointId'):
            json['event']['endpoint'] = {'endpointId': request.endpointId }
            if hasattr(request, 'scope'):
                json['event']['endpoint']['scope'] = request.scope

        return json

    def handleAcceptGrant(self, request):
        # Provides tokens to user
        try:
            user.getTokens(request)
            return {
                'event': {
                    'header': Header(namespace='Alexa.Authorization', name='AcceptGrant.Response').json,
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
                    'header': Header(namespace='Alexa.Discovery', name='Discover.Response').json,
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
                    'header': Header(namespace='Alexa', name='StateReport', correlationToken=request.correlationToken).json,
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

            ret = method(request)

            # If the handler did not produce it's own response message then compute a default one
            if not ret:
                waitStarted = time.time()
                waitFor = 5
                while not endpoint.iots[0].updateFinished():
                    if time.time() > waitStarted+waitFor:
                        raise ENDPOINT_UNREACHABLE('Timed out waiting for endpoint to update')

                interface = endpoint.generateInterfaces(endpoint.iots[0])[request.namespace]
                ret =  {
                    'context': {
                        'properties': interface.jsonResponse
                    },
                    'event': {
                        'header': Header(namespace='Alexa', name='Response', correlationToken=request.correlationToken).json,
                        'endpoint': {
                            'endpointId' : endpoint.endpointId
                        },
                        'payload': {}
                    }
                }

            # Check if Endpoint Health is enabled and if yes, add the appropriate context information to the response
            healthif = endpoint.generateInterfaces(endpoint.iots[0])['Alexa.EndpointHealth'] if 'Alexa.EndpointHealth' in endpoint._interfaces else None
            if healthif:
                if 'context' not in ret: ret['context'] = {}
                if 'properties' not in ret['context'] or ret['context']['properties'] is None: ret['context']['properties'] = []
                ret['context']['properties'] += healthif.jsonResponse
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
