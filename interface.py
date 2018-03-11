# -*- coding: utf-8 -*-

# Copyright 2018 dhrone. All Rights Reserved.
#


# pyASH imports

from utility import LOGLEVEL

# Setup logger
import logging
logger = logging.getLogger(__name__)
logger.setLevel(LOGLEVEL)


'''
The interface should provide both discovery as well as response capabilities.
Needs to handle complex interfaces like Cooking

An endpoint supports a collection of interfaces

Interfaces generates discovery messages which contain...
    Capabilities which contain...
        properties: (normal case)
            a {'name': property } for each supported property
        cameraStreamConfiguration: (CameraStreamController interface only)
            an array of cameraStream configuration data supported by the device
        configuration: (Cooking interface)
            a set of k, v pairs { 'attribute': value } that is dependent on the interface type

Interface generates response messages appropriate to the interface type
    Uses the current property values for the interface which should be local variables for the class

'''


class Interface(object):
    interface = None
    version = None
    properties = \
        Interface.Properties([ \
            Interface.Property('brightness'), \
            Interface.Property('powerState')], \
            proactivelyReported=True, retrievable=True)
    def __init__(self):
        pass
    @property
    @staticmethod
    def capability():
        return { 'type':'AlexaInterface', 'interface':Interface.interface, 'version': Interface.version, 'properties': Interface.properties.discover  }
    class Properties(object):
        def __init__(self, properties, proactivelyReported, retrievable):
            properties = properties if type(properties) == list else [ properties ]
            self.properties = {}
            for item in properties:
                self.properties[item.name] = item
        def __getitem__(self, property):
            return self.properties[property].value
        def __setitem__(self, property, value):
            self.properties[property].value = value
        @property
        def discover(self):
            proplist = []
            for item in self.properties.keys():
                proplist.append({'name':item})
            return { 'supported': proplist, 'proactivelyReported':self.proactivelyReported, 'retrievable': self.retrievable }
    class Property(object):
        def __init__(self, name, value=None):
            self.namespace = Interface.interface
            self.name = name
            self.value = value
            self.json = { 'namespace': self.namespace, 'name': self.name, 'value': self.value.json if hasattr(self.value, 'json') else self.value }
        @property
        def value(self):
            if hasattr(self.value, 'json'):
                return self.value.json
            return self.value





    @property
    def context(self):
        return {

        }



    def

    properties
    configuration
