import json
import boto3

from utility import *

class Iot(object):
    def __init__(self, endpointId, region='us-west-2'):
        self.endpointId = endpointId
        self.region = region
        self.client = boto3.client('iot-data', region_name=region)
        self.setTransforms()
        self.reportedState = {}
        self._get()

    def _get(self):
        thingData = json.loads(self.client.get_thing_shadow(thingName=self.endpointId)['payload'].read().decode('utf-8'))
        self.reportedState = thingData['state']['reported']

    def _put(self, newState):
        item = {'state': {'desired': newState}}
        # Send desired changes to shadow
        bdata = json.dumps(item).encode('utf-8')
        response = self.client.update_thing_shadow(thingName=self.endpointId, payload = bdata)

    def __getitem__(self, property):
        (method, variable) = self._getMethodVariable(property, 'to')
        return method(self, self.reportedState[variable])

    def __setitem__(self, property, value):
        (method, variable) = self._getMethodVariable(property, 'from')
        self._put({variable : method(self, value)})

    def _getMethodVariable(self,property, direction='from'):
        fromtoProperties = self.fromPropertybyProperty if direction.lower() == 'from' else self.toPropertybyProperty
        if Iot.validateProperty(property) in fromtoProperties:
            (method, variable) = fromtoProperties[property]
        else:
            method = self.doNothing
            variable = property
        if variable not in self.reportedState:
            raise KeyError
        return (method, variable)

    def _getMethodProperty(self, variable, direction='from'):
        fromtoVariables = self.fromPropertybyVariable if direction.lower() == 'from' else self.toPropertybyVariable
        if variable in fromtoVariables:
            (method, property) = fromtoVariables[variable]
        else:
            property = Iot.validateProperty(variable)
            method = self.doNothing
        return (method, property)

    def batchSet(self, propdict):
        vars = {}
        for property in propdict:
            (method, variable) = _getMethodVariable(property, 'to')
            vars[variable] = method(self, propdict[property])
        self._put(vars)

    def batchGet(self):
        ret = {}
        for variable in self.reportedState:
            (method, property) = _getMethodProperty(variable, 'to')
            ret[property] = method(self, self.reportedState[variable])
        return ret

    def refresh(self):
        self._get()

    @staticmethod
    def doNothing(value):
        return value

    @staticmethod
    def validateProperty(property):
        for interface in VALID_PROPERTIES:
            if property in VALID_PROPERTIES[interface]:
                return property
        raise ValueError('{0} is not a valid property'.format(property))

    @classmethod
    def transformFromProperty(cls, property, variable=None):
        variable = variable if variable else property

        def decorateinterface(func):
            transformFromList = getattr(func, '_transformFromList', {})
            transformFromList[Iot.validateProperty(property)] = variable
            func._transformFromList = transformFromList
            return func

        return decorateinterface

    @classmethod
    def transformToProperty(cls, property, variable=None):
        variable = variable if variable else property

        def decorateinterface(func):
            transformToList = getattr(func, '_transformToList', {})
            transformToList[Iot.validateProperty(property)] = variable
            func._transformToList = transformToList
            return func

        return decorateinterface

    def setTransforms(self):
        """dict(str, function): All actions the appliance supports and their corresponding (unbound)
        method references. Action names are formatted for the DiscoverAppliancesRequest.
        """
        self.fromPropertybyProperty = {}
        self.toPropertybyProperty = {}
        self.fromPropertybyVariable = {}
        self.toPropertybyVariable = {}
        for supercls in self.__class__.__mro__:  # This makes inherited Appliances work
            for method in supercls.__dict__.values():
                for property in getattr(method, '_transformFromList', {}):
                    self.fromPropertybyProperty[property] = (method, getattr(method, '_transformFromList', {}).get(property))
                    self.fromPropertybyVariable[getattr(method, '_transformFromList', {}).get(property)] = (method, property)
                for property in getattr(method, '_transformToList', {}):
                    self.toPropertybyProperty[property] = (method, getattr(method, '_transformToList', {}).get(property))
                    self.toPropertybyVariable[getattr(method, '_transformToList', {}).get(property)] = (method, property)
