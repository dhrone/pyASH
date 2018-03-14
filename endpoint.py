# -*- coding: utf-8 -*-

# Copyright 2018 dhrone. All Rights Reserved.
#

import json

# pyASH imports
from iot import Iot
from message import EndpointResponse, Capability
from exceptions import *
from utility import *
from interface import getInterfaceClass

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
    proactivelyReported = False
    retrievable = False
    uncertaintyInMilliseconds = 0
    supportsDeactivation = False
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

        # Find and instantiate an Iot object if possible
        self.iotClass = self._findIot()
        self.iot = self.iotClass(self.endpointId) if self.iotClass and self.endpointId else None

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

    @staticmethod
    def addInterface(interface, proactivelyReported=None, retrievable=None, uncertaintyInMilliseconds=None, supportsDeactivation = None):
        if type(interface) is str:
            interface = getInterfaceClass(interface)
        name = 'Alexa.'+ interface.__name__
        Endpoint.lookupInterface(name)
        _proactivelyReported = proactivelyReported if proactivelyReported is not None else None
        _retrievable = retrievable if retrievable is not None else None
        _uncertaintyInMilliseconds = uncertaintyInMilliseconds if uncertaintyInMilliseconds is not None else None
        _supportsDeactivation = supportsDeactivation if supportsDeactivation is not None else None

        def wrapper(func):
            item = { 'interface': interface, 'proactivelyReported': _proactivelyReported, 'retrievable': _retrievable, 'uncertaintyInMilliseconds': _uncertaintyInMilliseconds, 'supportsDeactivation': _supportsDeactivation }
            if hasattr(func, '__interfaces__'):
                func.__interfaces__.append( item )
            else:
                func.__interfaces__ = [ item ]
            return func

        return wrapper

    @staticmethod
    def addProperty(propertyName, proactivelyReported=None, retrievable=None, uncertaintyInMilliseconds=None):
        _proactivelyReported = proactivelyReported if proactivelyReported else None
        _retrievable = retrievable if retrievable else None
        _uncertaintyInMilliseconds = uncertaintyInMilliseconds if uncertaintyInMilliseconds else None

        def wrapper(func):
            item = { 'property': propertyName, 'proactivelyReported': _proactivelyReported, 'retrievable': _retrievable, 'uncertaintyInMilliseconds': _uncertaintyInMilliseconds }
            if hasattr(func, '__properties__'):
                func.__properties__.append( item )
            else:
                func.__properties__ = [ item ]
            return func
        return wrapper

    @staticmethod
    def addIot(iotcls):
        def wrapper(func):
            if hasattr(func, '__iot__'):
                raise OnlyOneIOTallowedPerEndpoint('You can only specify a single IOT for an endpoint')
            else:
                func.__iot__ = iotcls
            return func
        return wrapper

    @classmethod
    def addDirective(cls, *args, **kwargs):
        _interface = kwargs['interface'] if 'interface' in kwargs else ''
        if _interface:
            Endpoint.lookupInterface(_interface)

        def decoratelist(func):
            d = args[0] if type(args[0]) is list else [args[0]]
            for item in d:
                directives = getattr(func, '__directives__', [])
                interface = _interface if _interface else Endpoint.lookupInterfaceFromDirective(item)
                func.__directives__ = directives + [(interface, Endpoint.lookupDirective(item,interface))]
            return func
        def decorateinterface(func):
            directives = getattr(func, '__directives__', [])
            interface = _interface if _interface else Endpoint.lookupInterfaceFromDirective(func.__name__)
            func.__directives__ = directives + [(interface, Endpoint.lookupDirective(func.__name__, interface))]
            return func

        if args:
            if callable(args[0]):
                directives = getattr(args[0], '__directives__', [])
                interface = _interface if _interface else Endpoint.lookupInterfaceFromDirective(args[0].__name__)
                args[0].__directives__ = directives + [(interface, Endpoint.lookupDirective(args[0].__name__,interface))]
                return args[0]
            else:
                return decoratelist
        else:
            return decorateinterface

    @property
    def _getCapabilities(self):
        ### Need to go through all of the potential capabilities per interface to make sure I am handling all of the special cases
        ### Now that __interfaces__ and __directives__ are available this method needs to be rewritten.  Interfaces should generate capabilities.


        interfaces = self._interfaces
        capabilities = []
        # Fix interface defaults
        for k, interface in interfaces.items():
            interface['proactivelyReported'] = interface['proactivelyReported'] if interface['proactivelyReported'] else self.proactivelyReported
            interface['retrievable'] = interface['retrievable'] if interface['retrievable'] else self.retrievable
            interface['uncertaintyInMilliseconds'] = interface['uncertaintyInMilliseconds'] if interface['uncertaintyInMilliseconds'] else self.uncertaintyInMilliseconds

            # For each interface, add capabilities
            interface['supportsDeactivation'] = interface['supportsDeactivation'] if interface['supportsDeactivation'] else self.supportsDeactivation
            object = interface['interface'] \
                ( \
                    proactivelyReported=interface['proactivelyReported'], \
                    retrievable = interface['retrievable'], \
                    uncertaintyInMilliseconds = interface['uncertaintyInMilliseconds'], \
                    supportsDeactivation = interface['supportsDeactivation']
                )
            capabilities.append(object.jsonDiscover)
        return capabilities

        '''
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
        '''

    def endpointResponse(self):
        # endpointId, manufacturerName='', friendlyName='', description='', displayCategories=[], cookie='', capabilities=[], token={}
        return EndpointResponse(self.endpointId, self.manufacturerName, self.friendlyName, self.description, self.displayCategories, self.cookie, self._getCapabilities, None, self.__class__.__name__)

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
                        return directive
        if interface:
            raise ValueError('{0} is not a valid directive for interface {1}'.format(directive,interface))
        raise ValueError('{0} is not a valid directive'.format(directive))

    @staticmethod
    def getEndpointId(thingName):
        return self.__name__ + ':' + thingName

    @_classproperty
    def _directives(cls):
        """dict(str, function): All directives the appliance supports
        """
        ret = {}
        # Add in default handlers from interface
        for supercls in cls.__mro__:  # This makes inherited Appliances work
            for interface in getattr(supercls, '__interfaces__', []):
                for d in VALID_DIRECTIVES['Alexa.'+interface['interface'].__name__]:
                    if hasattr(interface['interface'], d):
                        ret[('Alexa.'+interface['interface'].__name__, d)] = (interface['interface'], getattr(interface['interface'], d))

        # Override those with any locally defined ones
        for supercls in cls.__mro__:
            for method in supercls.__dict__.values():
                for directive in getattr(method, '__directives__', []):
                    ret[directive] = (supercls, method)
        return ret

    @_classproperty
    def _interfaces(cls):
        """dict(str, function): All interfaces the appliance supports.
        """
        ret = {}
        # Start with the list of declared interfaces
        for supercls in cls.__mro__:
            for interface in getattr(supercls, '__interfaces__', []):
                ret['Alexa.'+interface['interface'].__name__] = interface

        # Add any inferred interfaces based upon any Directives implemented within the endpoint
        for supercls in cls.__mro__:
            for method in supercls.__dict__.values():
                for directive in getattr(method, '__directives__', []):
                    interface, d = directive
                    if interface not in ret:
                        ret[interface] = {
                            'interface': getInterfaceClass(interface),
                            'proactivelyReported': None,
                            'retrievable': None,
                            'uncertaintyInMilliseconds': None,
                            'supportsDeactivation': None
                        }

        return ret

    @property
    def _properties(self):
        idp_list = self._directives.keys()
        ret = {}
        for i in idp_list:
            ret[i[0]] = VALID_PROPERTIES[i[0]]
        return ret

    def getHandler(self, request):
        ret = self._directives
        for i in ret:
            if i[0] == request.namespace and i[1] == request.directive:
                return ret[i]

    # See if an Iot class was included and return it if yes
    def _findIot(self):
        if hasattr(self, '__iot__'):
            return self.__iot__
        else:
            return None
