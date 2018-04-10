# -*- coding: utf-8 -*-

# Copyright 2018 dhrone. All Rights Reserved.
#

import json

# pyASH imports
from .iot import Iot, Thing
from .exceptions import INVALID_DIRECTIVE, MISCELLANIOUS_EXCEPTION
from .utility import LOGLEVEL, VALID_DIRECTIVES
from .interface import getInterfaceClass, InterfaceMeta

# Setup logger
import logging
logger = logging.getLogger(__name__)
logger.setLevel(LOGLEVEL)

class _classproperty(property):
    def __init__(self, func):
        self.func = func
        self.__doc__ = func.__doc__

    def __get__(self, instance, owner):
        # This makes docstrings work
        if owner is Endpoint:
            return self
        return self.func(owner)

class Endpoint(object):
    '''

    Inherit from Endpoint to define how your device should respond to Alexa Smart Home messages.

    In pyASH, Endpoints are responsible for responding to Alexa Smart Home directives which can include instructions to change the device's state (e.g. TurnOn, SetVolume, AdjustBrightness), respond to discover requests about the endpoint, and report on the current state of the Endpoint.  pyASH handles discovery and state reporting automatically and includes default directive handling where possible.  If your device implements a directive that does not have a defined default method or you need to implement different behavior for a directive, you must implement a method for the directive within your Endpoint derived class.

    When specifying a directive method, you must decorate the method with ``Endpoint.addDirective``.  If you name the method the same as the directive you are trying to handle, pyASH will automatically register that method as the handler for the directive.  If you name your method anything else, you must include a list of the directives your method will handle as a parameter to the ``Endpoint.addDirective``

    .. code-block:: python

        @Endpoint.addDirective(['AdjustVolume','SetVolume'])
        def Volume(self, request):
            if request.name == 'AdjustVolume':
                v = self.iot['volume'] + request.payload['volume']
               self.iot['volume'] = 0 if v < 0 else 100 if v > 100 else v
            else:
                self.iot['volume'] = request.payload['volume']

    In the Alexa Smart Home service, directives belong to Interfaces.  When you add a directive to an Endpoint, pyASH will determine which Interface the directive is associated with and automatically add that Interface to your class.  This can occasionally be ambiguous (e.g. Speaker, StepSpeaker).  In those situations, you should declare which Interface you want as an additional parameter to Endpoint.addDirective::

        @Endpoint.addDirective(['AdjustVolume','SetVolume'], interface='Alexa.Speaker')

    It is also important that you make sure to implement a directive method for all of the directives contained within each Interface your device implements.  Note: most interfaces require you to handle multiple directives.  As example, if you implement SetBrightness, pyASH will add the BrightnessController interface to your class.  This interface also requires you to implement AdjustBrightness.  If you do not provide a directive for an included interface, a default method will be used if available.

    Endpoint classes can be decorated to specify which interfaces they support (``Endpoint.addInterface``).  This can be useful if you want to add an interface and are relying completely on the interfaces default methods or you need to specify specific configuration values for the interface.

    Endpoint classes should be decorated to add an Iot class (``Endpoint.addIot``) which is used to integrate the device with an Internet of Things service (see Iot for more information).

    **Attributes:**
        **endpointId** (*str*): A unique identifier for Alexa Smart Home Kit API to reference a specific endpoint normally constructed as the name of the Endpoint class concatenated with a ':' and the identified for the device within its Iot service.  To change this behavior, override the getEndpointId static method.

        **things** (**list**): A list of identifiers for all of the Iot devices that make up this endpoint.  Can also specify a (str) if the endpoint only uses a single thing.

        **Interface Variables -- set the default values on all interfaces for this endpoint.**
            **proactivelyReported** (*bool*): True if Alexa should expect state updates from you asynchronously

            **retrievable** (*bool*): True if Alexa can expect you to respond to a ReportState directive

            **uncertaintyInMilliseconds** (*int*): Amount of time (in milliseconds) your reported state value could be out of date (e.g. stale)

            **supportsDeactivation** (*bool*): True if the Endpoint implements the Deactivate directive (for devices supporting the SceneController interface only)

            **cameraStreamConfigurations** (*list*): A list of dictionaries describing the cameraStreamConfigurations supported by this endpoint (for devices supporting the CameraStreamController interface only)

        **Discovery Variables -- reported to Alexa in response to a discovery message for this endpoint.**
            **friendlyName** (*str*): A name normally created by your end user to refer to this endpoint

            **description** (*str*): A description of the endpoint

            **manufacturerName** (*str*): The name of the manufacturer of the endpoint

            **displayCategories** (*list*): A list of the display categories that are appropriate for this endpoint

            **cookie** (*dict*): A dictionary of key, value pairs that you want Alexa to report back to you when processing messages for this endpoint.

        **json** (*dict*): Endpoint can also be instantiated from a dictionary with a key entry for each attribute that you are passing in

    **Defaults:**
        If you want to establish default values for all of the endpoints that will be created from your class, you can add them as class variables

        .. code-block:: python

            class myEndpoint(Endpoint):
                manufacturerName = 'Me'
                description = 'FancyTV controller by Me'
                displayCategories = 'OTHER'
                proactivelyReported = False
                retrievable=False
                uncertaintyInMilliseconds=0

    '''
    friendlyName = 'pyASH device'
    manufacturerName = 'pyASH'
    description = 'Generic device by pyASH'
    displayCategories = ['OTHER']
    cookie = None

    def __init__(self, things=None, friendlyName=None, description=None, manufacturerName=None, displayCategories=None, cookie=None):

        self.things = things
        self.friendlyName = friendlyName if friendlyName is not None else self.friendlyName
        self.manufacturerName = manufacturerName if manufacturerName is not None else self.manufacturerName
        self.description = description if description is not None else self.description
        self.displayCategories = displayCategories if displayCategories is not None else self.displayCategories
        self.displayCategories = self.displayCategories if self.displayCategories is None or type(self.displayCategories) is list else [self.displayCategories]
        self.cookie = cookie if cookie is not None else self.cookie
        self.things = self.things if type(self.things) is list else [self.things] if self.things is not None else None

    @staticmethod
    def addInterface(interface, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0, supportsDeactivation = False, cameraStreamConfigurations = None):
        '''Decorator to associates an interface with the Endpoint class and allows that interface's attributes to be specified (if different from the endpoint itself).

        Parameters:
            interface(str or interface class): The name or the class of the interface to bind to this Endpoint.
            proactivelyReported(bool): See class attributes
            retrievable(bool): See class attributes
            uncertaintyInMilliseconds(bool): See class attributes
            supportsDeactivation(bool): See class attributes
            cameraStreamConfigurations(list): See class attributes

        '''
        if type(interface) is str:
            interface = getInterfaceClass(interface)
        name = 'Alexa.'+ interface.__name__
        Endpoint._lookupInterface(name)


        def wrapper(func):
            item = { 'interface': interface, 'proactivelyReported': proactivelyReported, 'retrievable': retrievable, 'uncertaintyInMilliseconds': uncertaintyInMilliseconds, 'supportsDeactivation': supportsDeactivation, 'cameraStreamConfigurations': cameraStreamConfigurations }
            func.__interfaces__ = getattr(func, '__interfaces__', {})
            func.__interfaces__[name] = item if name not in func.__interfaces__
            return func

        return wrapper

    @classmethod
    def addDirective(cls, *args, **kwargs):
        '''Decorator to declare that a method is responsible for handling a directive or set of directives

        Parameters:
            args[0](str or list): A single name or list of names for the directives this method will handle
            interface(str): Name of the interface that the method is supporting

        If interface name is not provided, an attempt will be made to look it up from the name of the directives that have been requested.

        If no argument is provided, the name of the decorated method will be used as the directive name.
        '''
        _interface = kwargs['interface'] if 'interface' in kwargs else ''
        if _interface:
            Endpoint._lookupInterface(_interface)

        # Set interface attributes if included
        proactivelyReported = kwargs.get('proactivelyReported',False)
        retrievable = kwargs.get('retrievable',False)
        uncertaintyInMilliseconds = kwargs.get('uncertaintyInMilliseconds',0)
        supportsDeactivation = kwargs.get('supportsDeactivation',False)
        cameraStreamConfigurations = kwargs.get('cameraStreamConfigurations',None)

        def decoratelist(func):
            d = args[0] if type(args[0]) is list else [args[0]]

            for item in d:
                directives = getattr(func, '__directives__', [])
                interface = _interface if _interface else Endpoint._lookupInterfaceFromDirective(item)
                func.__directives__ = directives + [(interface, Endpoint._lookupDirective(item,interface))]

                # Add interface associated with directive if it has not already been added
                intf = { 'interface': interface, 'proactivelyReported': proactivelyReported, 'retrievable': retrievable, 'uncertaintyInMilliseconds': uncertaintyInMilliseconds, 'supportsDeactivation': supportsDeactivation, 'cameraStreamConfigurations': cameraStreamConfigurations }
                func.__interfaces__ = getattr(func, '__interfaces__', {})
                func.__interfaces__[name] = intf if name not in func.__interfaces__

            return func
        def decorateinterface(func):
            directives = getattr(func, '__directives__', [])
            interface = _interface if _interface else Endpoint._lookupInterfaceFromDirective(func.__name__)
            func.__directives__ = directives + [(interface, Endpoint._lookupDirective(func.__name__, interface))]

            # Add interface associated with directive if it has not already been added
            item = { 'interface': interface, 'proactivelyReported': proactivelyReported, 'retrievable': retrievable, 'uncertaintyInMilliseconds': uncertaintyInMilliseconds, 'supportsDeactivation': supportsDeactivation, 'cameraStreamConfigurations': cameraStreamConfigurations }
            func.__interfaces__ = getattr(func, '__interfaces__', {})
            func.__interfaces__[name] = item if name not in func.__interfaces__
            return func

        if args:
            if callable(args[0]):
                directives = getattr(args[0], '__directives__', [])
                interface = _interface if _interface else Endpoint._lookupInterfaceFromDirective(args[0].__name__)
                args[0].__directives__ = directives + [(interface, Endpoint._lookupDirective(args[0].__name__,interface))]

                # Add interface associated with directive if it has not already been added
                item = { 'interface': interface, 'proactivelyReported': proactivelyReported, 'retrievable': retrievable, 'uncertaintyInMilliseconds': uncertaintyInMilliseconds, 'supportsDeactivation': supportsDeactivation, 'cameraStreamConfigurations': cameraStreamConfigurations }
                args[0].__interfaces__ = getattr(func, '__interfaces__', {})
                args[0].__interfaces__[name] = item if name not in func.__interfaces__

                return args[0]
            else:
                return decoratelist
        else:
            return decorateinterface

    @property
    def _getCapabilities(self):
        capabilities = [{
            "type": "AlexaInterface",
            "interface": "Alexa",
            "version": "3"
        }]

        for object in self._generateInterfaces(iot=None).values():
            capabilities.append(object.jsonDiscover)
        return capabilities

    @property
    def _getProperties(self):
        properties = []
        for object in self._generateInterfaces(iot=self.iot).values():
            if object.jsonResponse: properties += object.jsonResponse
        return properties

    def _generateInterfaces(self,iot=None):
        ret = {}
        for name, interface in self._interfaces.items():
            object = interface['interface'] \
                ( \
                    iot=iot, \
                    proactivelyReported=interface['proactivelyReported'], \
                    retrievable = interface['retrievable'], \
                    uncertaintyInMilliseconds = interface['uncertaintyInMilliseconds'], \
                    supportsDeactivation = interface['supportsDeactivation'], \
                    cameraStreamConfigurations= interface['cameraStreamConfigurations']
                )
            ret[name]=object
        return ret

    @property
    def jsonDiscover(self):
        '''Formats and returns a dictionary that contains a capability object appropriate to support discovery for the endpoint'''
        return { k:v for k,v in {
            'endpointId' : self.EndpointId,
            'manufacturerName' : self.manufacturerName,
            'friendlyName' : self.friendlyName,
            'description' : self.description,
            'displayCategories' : self.displayCategories,
            'cookie' : self.cookie,
            'capabilities' : self._getCapabilities
        }.items() if v is not None }

    @property
    def jsonResponse(self):
        '''Formats and returns a list of property values (e.g. current state) for the endpoint'''
        return self._getProperties

    @staticmethod
    def _lookupInterface(interface):
        for item in VALID_DIRECTIVES:
            if interface == item:
                return interface
        raise INVALID_DIRECTIVE('{0} is not a valid interface'.format(interface))

    @staticmethod
    def _lookupInterfaceFromDirective(directive):
        for interface in VALID_DIRECTIVES:
            for item in VALID_DIRECTIVES[interface]:
                if directive == item:
                    return interface
        raise INVALID_DIRECTIVE('{0} is not a valid directive'.format(directive))

    @staticmethod
    def _lookupDirective(directive, interface=''):
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
            raise INVALID_DIRECTIVE('{0} is not a valid directive for interface {1}'.format(directive,interface))
        raise INVALID_DIRECTIVE('{0} is not a valid directive'.format(directive))

    @property
    def EndpointId(self):
        '''Returns the endpointId of the Endpoint

        Default behavior is to concatenate the class name of the Endpoint with a ':' and the thingName of this specific Endpoint object.  This method can be overridden if a different scheme for identifying the endpoint is desired.

        Note:
            The default user class relies upon this encoding to instantiate endpoints.  If you change it you should override both getEndpointId and retrieveThings within the User class (or it's children).

            Currently the ':' is not escaped so it should not be used within a thing name
        '''
        thingNames = [ t.name for t in self.things ]
        return self.__name__ + ':' + ':'.join(thingNames)

    @_classproperty
    def _directives(cls):
        ret = {}
        # Add in default handlers from interface
        for supercls in cls.__mro__:  # This makes inherited Appliances work
            for name, interface in getattr(supercls, '__interfaces__', {}).items():
                for d in VALID_DIRECTIVES[name]:
                    if hasattr(interface['interface'], d):
                        ret[(name, d)] = (interface['interface'], getattr(interface['interface'], d))

        # Override those with any locally defined ones
        for supercls in cls.__mro__:
            for method in supercls.__dict__.values():
                for directive in getattr(method, '__directives__', []):
                    ret[directive] = (supercls, method)
        return ret

    @_classproperty
    def _interfaces(cls):
        ret = {}

        for supercls in cls.__mro__:
            for name, interface in getattr(supercls, '__interfaces__', {}).items():
                ret[name] = interface

        return ret

    @property
    def _properties(self):
        idp_list = self._directives.keys()
        ret = {}
        for i in idp_list:
            ret[i[0]] = VALID_PROPERTIES[i[0]]
        return ret

    def _getHandler(self, request):
        ret = self._directives
        for i in ret:
            if i[0] == request.namespace and i[1] == request.name:
                return ret[i]
        raise INVALID_DIRECTIVE('{0} has no method to handle {1}:{2}'.format(self.__class__.__name__,request.namespace,request.name))

    # See if an Iot class was included and return it if yes
    def _findIot(self):
        if hasattr(self, '__iot__'):
            return self.__iot__
        else:
            return None
