# -*- coding: utf-8 -*-

# Copyright 2018 dhrone. All Rights Reserved.
#

import json
import time
from abc import ABC, abstractmethod
import boto3

# pyASH imports
from .utility import *

# Setup logger
import logging
logger = logging.getLogger(__name__)
logger.setLevel(LOGLEVEL)


def doNothing(obj, value):
    return value

class Thing(object):
    def __init__(self, name, iotcls):
        self.name = name
        self.iotcls = iotcls

class IotBase(ABC):
    def __init__(self, endpointId, consideredStaleAfter=2):
        self.endpointId = endpointId
        self.setTransforms()
        self.reportedState = { 'connectivity': {'value': 'OK'} }
        self.reportedStateTimeStamp = { 'connectivity': {'timestamp': time.time() } }
        self.lastGet = 0
        self.consideredStaleAfter = consideredStaleAfter

        self.get()

    def getThingName(self):
        return self.endpointId

    @abstractmethod
    def get(self):
        pass

    @abstractmethod
    def put(self, newState):
        pass

    @property
    @abstractmethod
    def timeStamps(self):
        pass

    def updateFinished(self):
        self.reportedState['connectivity'] = {'value': 'OK'}
        self.reportedStateTimeStamp['connectivity'] = {'timestamp': time.time() }
        return True

    def _stale(self):
        return True if self.lastGet + self.consideredStaleAfter < time.time() else False

    def __getitem__(self, property):
        if self._stale():
            self.get()
        (method, variable) = self._getMethodVariable(property, 'to')
        return method(self, self.reportedState[variable])

    def __setitem__(self, property, value):
        try:
            (method, variable) = self._getMethodVariable(property, 'from')
        except KeyError:
            method = doNothing
            variable = property
        self.put({variable : method(self, value)})

    def _getMethodVariable(self,property, direction='from'):
        fromtoProperties = self.fromPropertybyProperty if direction.lower() == 'from' else self.toPropertybyProperty
        if Iot.validateProperty(property) in fromtoProperties:
            (method, variable) = fromtoProperties[property]
        else:
            method = doNothing
            variable = property
        if variable not in self.reportedState:
            raise KeyError('{0} is not a valid value for this Iot device'.format(variable))
        return (method, variable)

    def _getMethodProperty(self, variable, direction='from'):
        fromtoVariables = self.fromPropertybyVariable if direction.lower() == 'from' else self.toPropertybyVariable
        if variable in fromtoVariables:
            (method, property) = fromtoVariables[variable]
        else:
            property = Iot.validateProperty(variable)
            method = doNothing
        return (method, property)

    def batchSet(self, propdict):
        vars = {}
        for property in propdict:
            try:
                (method, variable) = self._getMethodVariable(property, 'to')
            except (KeyError, ValueError):
                method = doNothing
                variable = property
            vars[variable] = method(self, propdict[property])
        self.put(vars)

    def batchGet(self):
        if self._stale():
            self.get()
        ret = {}
        for variable in self.reportedState:
            try:
                (method, property) = self._getMethodProperty(variable, 'to')
            except ValueError:
                continue
            ret[property] = method(self, self.reportedState[variable])
        return ret

    def refresh(self):
        self.get()

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

class IotTest(IotBase):
    def __init__(self, *args, **kwargs):
        super(IotTest, self).__init__('endpointId')

        currentTime = int(time.time())
        if hasattr(self, '__initials__'):
            for k,v in self.__initials__.items():
                self.reportedState[k] = v
                self.reportedStateTimeStamp[k] = {'timestamp': currentTime}


    def get(self):
        try:
            filename = self.__class__.__name__+'.json'
            with open(filename) as json_file:
                df = json.load(json_file)
                self.reportedState = { **self.reportedState, **df['reportedState'] }
                self.reportedStateTimeStamp = { **self.reportedStateTimeStamp, **df['reportedStateTimeStamp'] }
        except FileNotFoundError:
            pass

    def put(self, newState):
        currentTime = int(time.time())
        for item in newState:
            print ('Storing {0}:{1}'.format(item,newState[item]))
            self.reportedState[item] = newState[item]
            self.reportedStateTimeStamp[item] = {'timestamp': currentTime }
        df = {'reportedState': self.reportedState, 'reportedStateTimeStamp': self.reportedStateTimeStamp }
        filename = self.__class__.__name__+'.json'
        with open(filename,'w') as outfile:
            json.dump(df, outfile)

    @property
    def timeStamps(self):
        ret = {}
        for variable in self.reportedState:
            try:
                (method, property) = self._getMethodProperty(variable, 'to')
                ret[property] = self.reportedStateTimeStamp[variable]['timestamp']
            except ValueError:
                # If a variable can not be translated from device to property then skip it
                pass
        return ret

    @staticmethod
    def initial(name, value):

        def wrapper(func):
            if hasattr(func, '__initials__'):
                func.__initials__[name] = value
            else:
                func.__initials__ = { name: value }
            return func

        return wrapper



class Iot(IotBase):
    def __init__(self, endpointId, region=DEFAULT_IOTREGION, consideredStaleAfter=2):
        self.client = None
        self.region = region
        super(Iot, self).__init__(endpointId, consideredStaleAfter)

    @staticmethod
    def createIot(endpointId, region, profileName):
        tp = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    # "iot:*"
                    "iot:Connect",
                    "iot:Publish",
                    "iot:Receive",
                    "iot:Subscribe"
                ],
                "Resource": [
                    "arn:aws:iot:{0}:*:*".format(region)
                ]
            }]
        }
        iot = Session(region_name=region,
        profile_name=profileName).client('iot')

        cert = iot.create_keys_and_certificate(setAsActive=True)
        iot.create_thing(thingName=endpointId)
        iot.attach_thing_principal(
            thingName=endpointId, principal=cert['certificateArn'])

        ### Check to see if a single policy can be reused across Iot instances
        p = iot.create_policy(
            policyName=policy_name,
            policyDocument=policy
        )
        iot.attach_principal_policy(
            policyName=policy_name, principal=thing_cert_arn)

        try:
            with open(certName, 'w') as pf:
                pf.write(cert['certificatePem'])
            with open(pkName, 'w') as pf:
                pf.write(cert['keyPair']['PublicKey'])
            with open(prvkName) as pf:
                pf.write(cert['keyPair']['PrivateKey'])
        except OSError:
            pass

    def get(self):
        if not self.client:
            self.client = boto3.client('iot-data', region_name=self.region)
        thingData = json.loads(self.client.get_thing_shadow(thingName=self.getThingName())['payload'].read().decode('utf-8'))
        self.reportedState = { **self.reportedState, **thingData['state']['reported'] }
        self.reportedStateTimeStamp = { **self.reportedStateTimeStamp, **thingData['metadata']['reported'] }
        self.lastGet = time.time()
        return thingData

    def put(self, newState):
        if not self.client:
            self.client = boto3.client('iot-data', region_name=self.region)
        item = {'state': {'desired': newState}}
        # Send desired changes to shadow
        bdata = json.dumps(item).encode('utf-8')
        response = self.client.update_thing_shadow(thingName=self.getThingName(), payload = bdata)
        currentTime = int(time.time())
        for item in newState:
            self.reportedStateTimeStamp[item] = {'timestamp': currentTime}

    def updateFinished(self, timeout=5):
        start = time.time()
        while start+timeout > time.time():
            ret = self.get()
            if 'delta' in ret['state']:
                time.sleep(.1)
                continue
            self.reportedState['connectivity'] = {'value': 'OK'}
            self.reportedStateTimeStamp['connectivity'] = {'timestamp': time.time() }
            return True
        self.reportedState['connectivity'] = {'value': 'UNREACHABLE'}
        self.reportedStateTimeStamp['connectivity'] = {'timestamp': time.time() }
        return False

    @property
    def timeStamps(self):
        ret = {}
        for variable in self.reportedState:
            try:
                (method, property) = self._getMethodProperty(variable, 'to')
                ret[property] = self.reportedStateTimeStamp[variable]['timestamp']
            except ValueError:
                # If a variable can not be translated from device to property then skip it
                pass
        return ret
