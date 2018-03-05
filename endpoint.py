# -*- coding: utf-8 -*-

# Copyright 2018 dhrone. All Rights Reserved.
#

import json

# pyASH imports
from utility import *
from message import EndpointResponse, Capability

# Setup logger
import logging
logger = logging.getLogger(__name__)
logger.setLevel(LOGLEVEL)

class _classproperty(property):
    """Utility class for @property fields on the class."""
    def __init__(self, func):
        self.func = func
        self.__doc__ = func.__doc__

    def __get__(self, instance, owner):
        # This makes docstrings work
        if owner is Endpoint:
            return self
        return self.func(owner)

class Endpoint(object):
    friendlyName = 'pyASH device'
    manufacturerName = 'pyASH'
    description = 'Generic device by pyASH'
    displayCategories = 'OTHER'
    proactivelyReported = None
    retrievable = None
    supportsDeactivation = None
    cookie = None
    endpointIdPattern = None

    def __init__(self, endpointId=None, friendlyName = None, description = None, manufacturerName=None, displayCategories=None, proactivelyReported=None, retrievable=None, supportsDeactivation=None, cookie=None, json=None):

        if json:
            self.endpointId = json.get('endpointId') if 'endpointId' in json else None
            self.friendlyName = json.get('friendlyName') if 'friendlyName' in json else None
            self.manufacturerName = json.get('manufacturerName') if 'manufacturerName' in json else None
            self.description = json.get('description') if 'description' in json else None
            self.displayCategories = json.get('displayCategories') if 'displayCategories' in json else None
            self.proactivelyReported = json.get('proactivelyReported') if 'proactivelyReported' in json else None
            self.retrievable = json.get('retrievable') if 'retrievable' in json else None
            self.supportsDeactivation = json.get('supportsDeactivation') if 'supportsDeactivation' in json else None
            self.cookie = json.get('cookie') if 'cookie' in json else None
        else:
            self.endpointId = endpointId
            self.friendlyName = friendlyName if friendlyName else Endpoint.friendlyName
            self.manufacturerName = manufacturerName if manufacturerName else Endpoint.manufacturerName
            self.description = description if description else Endpoint.description
            self.displayCategories = displayCategories if displayCategories else Endpoint.displayCategories
            self.proactivelyReported = proactivelyReported if proactivelyReported else Endpoint.proactivelyReported
            self.retrievable = retrievable if retrievable else Endpoint.retrievable
            self.supportsDeactivation = supportsDeactivation if supportsDeactivation else Endpoint.supportsDeactivation
            self.cookie = cookie if cookie else Endpoint.cookie

    @property
    def json(self):
        return {
            'endpointId': self.endpointId,
            'className': self.__class__.__name__,
            'friendlyName': self.friendlyName,
            'manufacturerName': self.manufacturerName,
            'description': self.description,
            'displayCategories': self.displayCategories,
            'proactivelyReported': self.proactivelyReported,
            'retrievable': self.retrievable,
            'supportsDeactivation': self.supportsDeactivation,
            'cookie': self.cookie
        }

    @classmethod
    def register(cls, *args, **kwargs):
        _interface = kwargs['interface'] if 'interface' in kwargs else ''
        _properties = kwargs['properties'] if 'properties' in kwargs else '__all__'
        if _interface:
            Endpoint.lookupInterface(_interface)

        def decoratelist(func):
            d = args[0] if type(args[0]) is list else [args[0]]
            for item in d:
                directives = getattr(func, '_directives', [])
                interface = _interface if _interface else Endpoint.lookupInterfaceFromDirective(item)
                func._directives = directives + [(interface, Endpoint.lookupDirective(item,interface), _properties)]
            return func
        def decorateinterface(func):
            directives = getattr(func, '_directives', [])
            interface = _interface if _interface else Endpoint.lookupInterfaceFromDirective(func.__name__)
            func._directives = directives + [(interface, Endpoint.lookupDirective(func.__name__, interface), _properties)]
            return func

        if args:
            if callable(args[0]):
                directives = getattr(args[0], '_directives', [])
                interface = _interface if _interface else Endpoint.lookupInterfaceFromDirective(args[0].__name__)
                args[0]._directives = directives + [(interface, Endpoint.lookupDirective(args[0].__name__,interface), _properties)]
                return args[0]
            else:
                return decoratelist
        else:
            return decorateinterface

    @property
    def _getCapabilities(self):
        ### Need to go through all of the potential capabilities per interface to make sure I am handling all of the special cases

        ip_list = self._properties
        cps = [Capability('Alexa')] # All endpoints should report this generic capability
        for interface in ip_list:
            if len(ip_list[interface]):
                for property in ip_list[interface]:
                    # Main use case.  Handles most of the capabilities
                    cps.append( Capability(interface, property, self.proactivelyReported, self.retrievable) )
            else:
                # Handles all of the special cases
                if interface == 'Alexa.SceneController':
                    cps.append( Capability(interface, proactivelyReported=self.proactivelyReported, supportsDeactivation = self.supportsDeactivation) )
                elif interface == 'Alexa.CameraStreamController':
                    pass
                else:
                    # Handles all of the normal non-property use-cases
                    cps.append( Capability(interface, self.proactivelyReported, self.retrievable) )
        return cps

    def endpointResponse(self):
        # endpointId, manufacturerName='', friendlyName='', description='', displayCategories=[], cookie='', capabilities=[], token={}
        return EndpointResponse(self.endpointId, self.manufacturerName, self.friendlyName, self.description, self.displayCategories, self.cookie, self._getCapabilities, self.__class__.__name__)

    @staticmethod
    def lookupInterface(interface):
        for item in VALID_DIRECTIVES:
            if interface == item:
                return interface
        raise ValueError('{0} is not a valid interface'.format(interface))

    @staticmethod
    def lookupInterfaceFromDirective(directive):
        for interface in VALID_DIRECTIVES:
            for item in VALID_DIRECTIVES[interface]:
                if directive == item:
                    return interface
        raise ValueError('{0} is not a valid directive'.format(directive))

    @staticmethod
    def lookupDirective(directive, interface=''):
        if interface:
            for item in VALID_DIRECTIVES[interface]:
                if directive == item:
                    return directive
        else:
            for interface in VALID_DIRECTIVES:
                for item in VALID_DIRECTIVES[interface]:
                    if directive == item:
                        return interface
        if interface:
            raise ValueError('{0} is not a valid directive for interface {1}'.format(directive,interface))
        raise ValueError('{0} is not a valid directive'.format(directive))

    @staticmethod
    def getEndpointId(thingName):
        return self.__name__ + ':' + thingName

    @_classproperty
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

    @property
    def _properties(self):

        ret = self.actions
        idp_list = ret.keys()
        ret = {}
        for i in idp_list:
            if i[2] == '__all__':
                ret[i[0]] = VALID_PROPERTIES[i[0]]
            else:
                if i[0] in ret:
                    if type(i[2]) is tuple:
                        for j in i[2]:
                            if j not in ret[i[0]]:
                                ret[i[0]].append(j)
                    else:
                        if i[2] not in ret[i[0]]:
                            ret[i[0]].append(i[2])
                else:
                    ret[i[0]] = list(i[2]) if type(i[2]) is tuple else [i[2]]
        return ret

    def getHandler(self, request):
        ret = self.actions
        for i in ret:
            if i[0] == request.namespace and i[1] == request.directive:
                return ret[i]

    @_classproperty
    def request_handlers(cls):
        """dict(str, function): All requests the appliance supports (methods marked as actions)
        and their corresponding (unbound) method references. For example action turn_on would be
        formatted as TurnOnRequest.
        """
        ret = {}
        for supercls in cls.__mro__:  # This makes inherited Appliances work
            for method in supercls.__dict__.values():
                for action in getattr(method, '_directives', []):
                    ret[action] = method

        return ret
