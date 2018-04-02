# -*- coding: utf-8 -*-

# Copyright 2018 by dhrone. All Rights Reserved.
#

import logging
import time

#from .utility import *
from .utility import LOGLEVEL, get_uuid, get_utc_timestamp
from .exceptions import InterfaceException, OAUTH2_EXCEPTION, MISCELLANIOUS_EXCEPTION
from .objects import ASHO, Request

# Setup logger
logger = logging.getLogger(__name__)
logger.setLevel(LOGLEVEL)



class pyASH(object):
    """ pyASH is the message handler for the system processing all Alexa requests """

    def __init__(self, user, version='3'):
        """
        Args:
            user (user object): The user object contains the list of endpoints that belong to a user
            version (enum = ['3']): Currently pyASH only supports the version 3 Alexa Smart Home API.
        """
        self.user = user
        self.version = version if type(version) is str else str(version)
        if not self.version == '3': raise ValueError('pyAsh currently only supports API version 3')

    @classmethod
    def _errorResponse(cls, request, e):
        json = {
            'event': {
                'header': ASHO.Header(namespace='Alexa', name='ErrorResponse', correlationToken=request.correlationToken, messageId=get_uuid(), payloadVersion='3').as_dict(),
                'payload': e.payload
            }
        }
        if hasattr(request, 'endpointId'):
            json['event']['endpoint'] = {'endpointId': request.endpointId }
            if hasattr(request, 'scope'):
                json['event']['endpoint']['scope'] = request.scope

        return json

    def handleAcceptGrant(self, request):
        """ Handles the receipt of a user's OAUTH2 code.

        When installing a new skill, during the enable process, the skill is linked to the customer's account through OAUTH2 authentication. If the user successfully authenticates, an AcceptGrant message is sent to your Lambda function.  This message includes a OAUTH2 Code which can be exchanged for an OAUTH2 refresh token and an OAUTH2 access token.

        Note:  You only need to persist the refresh token if you need to initiate a message (e.g. async communications) with the Alexa Smart Home Service.  If you will only be synchronously replying, you can use the access token provided in the Alexa request and therefore do not need to manage requesting your own access token for the user.
        """
        try:
            self.user.getTokens(request)
            return {
                'event': {
                    'header': ASHO.Header(namespace='Alexa.Authorization', name='AcceptGrant.Response', messageId=get_uuid(), payloadVersion='3').as_dict(),
                    'payload': {}
                }
            }
        except InterfaceException as e:
            return self._errorResponse(request, e)
        except:
            raise

    def handleDiscovery(self, request):
        """ Sends a list of all of the endpoints a user has installed and what they are capable of to Alexa Smart Home

        Before Alexa Smart Home can control a device, it needs to be told about each endpoint that your skill will handle for a user and what interfaces that endpoint supports.
        """

        try:
            ret = []
            endpoints = self.user.getEndpoints(request)
            for ep in endpoints:
                ret.append(ep.jsonDiscover)
            return {
                'event': {
                    'header': ASHO.Header(namespace='Alexa.Discovery', name='Discover.Response',messageId=get_uuid(), payloadVersion='3').as_dict(),
                    'payload': {
                        'endpoints': ret
                    }
                }
            }
        except InterfaceException as e:
            return self._errorResponse(request, e)
        except:
            raise


    def handleReportState(self, request):
        """ Sends the current property values for the requested endpoint to Alexa Smart Home """
        try:
            endpoint = self.user.getEndpoint(request)
            return {
                'context': {
                    'properties': endpoint.jsonResponse
                },
                'event': {
                    'header': ASHO.Header(namespace='Alexa', name='StateReport', correlationToken=request.correlationToken,messageId=get_uuid(), payloadVersion='3').as_dict(),
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
        """ Based upon the request from Alexa Smart Home, invokes the appropriate method to handle the request """

        def _getResponseJson(request):
            if request.namespace != 'Alexa.SceneController':
                return {
                    'context': {
                         'properties': []
                    },
                     'event': {
                        'header': ASHO.Header(namespace='Alexa', name='Response', correlationToken=request.correlationToken,messageId=get_uuid(), payloadVersion='3').as_dict(),
                        'endpoint': ASHO.Endpoint(endpointId=endpoint.endpointId).as_dict(),
                        'payload': {}
                    }
                }

            scene_type = 'ActivationStarted' if request.name == 'Activate' else 'DeactivationStarted' if request.name == 'Deactivate' else None
            return {
                "context": {
                    "properties": []
                },
                "event": {
                    'header': ASHO.Header(namespace='Alexa.SceneController', name=scene_type, correlationToken=request.correlationToken,messageId=get_uuid(), payloadVersion='3').as_dict(),
                    'endpoint': ASHO.Endpoint(endpointId=endpoint.endpointId, scope=ASHO.Scope(type='BearerToken', token=request.token)).as_dict(),
                    "payload": {
                        "cause": {
                            "type": "VOICE_INTERACTION"
                        },
                        "timestamp": get_utc_timestamp()
                    }
                }
            }

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
                interfaceJsonResponse = interface.jsonResponse
                ret = _getResponseJson(request)
                if interfaceJsonResponse and type(interfaceJsonResponse) is list:
                    ret['context']['properties'] += interfaceJsonResponse

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
        """ Routes the Alexa Smart Home request to the appropriate handler

        This is the method that you should point your Lambda function toself.
        """
        request = Request(request)
        return {
            'Alexa' : self.handleReportState,
            'Alexa.Authorization' : self.handleAcceptGrant,
            'Alexa.Discovery' : self.handleDiscovery,
        }.get(request.namespace, self.handleDirective)(request)
