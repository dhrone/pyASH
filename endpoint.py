# -*- coding: utf-8 -*-

# Copyright 2018 dhrone. All Rights Reserved.
#

import json
import pyASH

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
    def __init__(self, request=None):
        """Appliance gets initialized just before its action methods are called. Put your
        logic for preparation before handling the request here.
        """
        if request is not None:
            self.request = request
            self.id = request.appliance_id
            self.additional_details = request.appliance_details

    @classmethod
    def register(cls, *args, **kwargs):
        _interface = kwargs['interface'] if 'interface' in kwargs else ''
        if _interface:
            Endpoint.lookupInterface(_interface)

        def decoratelist(func):
            d = args[0] if type(args[0]) is list else [args[0]]
            for item in d:
                directives = getattr(func, '_directives', [])
                interface = _interface if _interface else Endpoint.lookupInterfaceFromDirective(item)
                func._directives = directives + [(interface, Endpoint.lookupDirective(item,interface))]
            return func
        def decorateinterface(func):
            directives = getattr(func, '_directives', [])
            interface = _interface if _interface else Endpoint.lookupInterfaceFromDirective(func.__name__)
            func._directives = directives + [(interface, Endpoint.lookupDirective(func.__name__, interface))]
            return func

        if args:
            if callable(args[0]):
                directives = getattr(args[0], '_directives', [])
                interface = _interface if _interface else Endpoint.lookupInterfaceFromDirective(args[0].__name__)
                args[0]._directives = directives + [(interface, Endpoint.lookupDirective(args[0].__name__,interface))]
                return args[0]
            else:
                return decoratelist
        else:
            return decorateinterface

    @staticmethod
    def lookupInterface(interface):
        for item in pyASH.VALID_DIRECTIVES:
            if interface == item:
                return interface
        raise ValueError('{0} is not a valid interface'.format(interface))

    @staticmethod
    def lookupInterfaceFromDirective(directive):
        for interface in pyASH.VALID_DIRECTIVES:
            for item in pyASH.VALID_DIRECTIVES[interface]:
                if directive == item:
                    return interface
        raise ValueError('{0} is not a valid directive'.format(directive))

    @staticmethod
    def lookupDirective(directive, interface=''):
        if interface:
            for item in pyASH.VALID_DIRECTIVES[interface]:
                if directive == item:
                    return directive
        else:
            for interface in pyASH.VALID_DIRECTIVES:
                for item in pyASH.VALID_DIRECTIVES[interface]:
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

    class Details:
        """Inner class in ``Appliance`` subclasses provides default values so that they don't
        have to be repeated in ``Smarthome.add_appliance``.
        """
