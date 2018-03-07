# -*- coding: utf-8 -*-

# Copyright 2018 by dhrone. All Rights Reserved.
#
from abc import ABC, abstractmethod
import json
import re
import boto3
from botocore.vendored import requests
from decimal import Decimal

# pyASH imports
from exceptions import *
from db import Tokens,Things, Persist, UUIDemail, UUIDuserid
from message import Capability, Request, Response, defaultResponse
from endpoint import Endpoint

from utility import *

# Setup logger
import logging
logger = logging.getLogger(__name__)
logger.setLevel(LOGLEVEL)

class User(ABC):

    def __init__(self, endpointClasses = []):
        self.endpoints = {}
        self.endpointClasses = {}
        for item in endpointClasses:
            if isinstance(item, Endpoint):
                self.endpointClasses[item.__class__.__name__] = item.__class__
            else:
                self.endpointClasses[item.__name__]=item

    @abstractmethod
    def handleAcceptGrant(self, request):
        pass

    @abstractmethod
    def handleDiscovery(self, request):
        pass

    def handleReportState(seld, request):
        pass

    def _getUserProfile(self, token):
        response = getUserProfile(token)
        self.userID = response['user_id']
        self.userName = response['name']
        self.userEmail = response['email']
        return response

    def _getAccessTokensFromCode(self, code):
        response = getAccessTokenFromCode(code)
        self.accessToken = response['access_token']
        self.refreshToken = response['refresh_token']
        self.accessTokenTimestamp = time.time()
        self.accessTokenExpires = response['expires_in']
        self._getUserProfile(self.accessToken)
        return response

    def handleDirective(self, request):

        # Decode endpointId
        (className, endpointId) = request.endpointId.split('|')
        try:
            endpoint = self.endpoints[endpointId]
        except KeyError:
            # Ok, endpoint wasn't found.  Let's see if we can find the class name
            class = self.endpointClasses.get(className)
            if not class:
                raise EndpointNotFoundException('{0} not found'.format(request.endpointId))

        # If no endpoint found but we have the class, create an instance to handle request
        if not endpoint:
            endpoint = self.endpointClasses[className](endpointId)

        method = endpoint.getHandler(request)
        if not method:
            raise NoMethodToHandleDirectiveException('No method to handle {0}:{1}'.format(request.namespace,request.directive))

        # bind the method to it's class
        method = method.__get__(endpoint, endpoint.__class__)

        response = method(request)
        if response:
            return response
        return defaultResponse(request,endpoint.iot)

    def lambda_handler(self, request, context=None):
        def doNothing(request):

        return {
            'Alexa' : self.handleReportState,
            'Alexa.Authorization' : self.handleAcceptGrant,
            'Alexa.Discovery' : self.handleDiscovery,
            'Alexa.BrightnessController' : self.handleDirective,
            'Alexa.Calendar' :
            'Alexa.CameraStreamController' :
            'Alexa.ChannelController' :
            'Alexa.ColorController' :
            'Alexa.ColorTemperatureController' : self.handleDirective,
            'Alexa.Cooking' :
            'Alexa.Cooking.TimeController' :
            'Alexa.Cooking.PresetController' :
            'Alexa.EndpointHealth' :
            'Alexa.InputController' : self.handleDirective,
            'Alexa.LockController' : self.handleDirective,
            'Alexa.MeetingClientController' :
            'Alexa.PercentageController' : self.handleDirective,
            'Alexa.PlaybackController' : self.handleDirective,
            'Alexa.PowerController' : self.handleDirective,
            'Alexa.PowerLevelController' : self.handleDirective,
            'Alexa.SceneController' : self.handleDirective,
            'Alexa.Speaker' : self.handleDirective,
            'Alexa.StepSpeaker' : self.handleDirective,
            'Alexa.TemperatureSensor' : self.handleDirective,
            'Alexa.ThermostatController' :
            'Alexa.TimeHoldController' :
        }.get(request.namespace)(request)


    def addEndpoint(self, endpoint):
        self.endpointClasses[endpoint.__class__.__name__] = endpoint.__class__
        self.endpoints[endpoint.endpointID] = endpoint

class StaticUser(User):
    def __init__(self, endpoints=[], endpointClasses=[]):
        super(StaticUser, self).__init__(endpointClasses)

        if type(endpoints) != list:
            if isinstance(endpoints, Endpoint):
                endpoints = [ endpoints ]
            else:
                raise TypeError('Must provide a list of endpoints')
        for item in endpoints:
            self.addEndpoint(item)

    def handleDiscovery(self, request):
        # Need to determine the encoding of the endpointId

        epResponses = []
        for e in self.endpoints.values():
            epResponses.append(e.endpointResponse())
        return Response(request, epResponses)

    def handleAcceptGrant(self, request):
        response = self._getAccessTokenFromCode(request.code)
        profile = self._getUserProfile(self.accessToken)
        print ("User {0}'s refreshToken is {1}".format(self.userName, self.refreshToken))

class DbUser(User):
    def __init__(self, endpointClasses=[], region='us-east-1', systemName = 'pyASH'):
        super(DbUser, self).__init__(endpointClasses)

        self.region = region
        self.systemName = systemName
        self.uuid = None

    def handleAcceptGrant(self, request):
        response = self._getAccessTokenFromCode(request.code)

    def handleDiscovery(self, request):
        self.getUserProfileFromToken(request.token)
        self.getUser(self.userId)
        self._retrieveEndpoints()

        epResponses = []
        for e in self.endpoints.values():
            epResponses.append(e.endpointResponse())
        return Response(request, epResponses)

    def getUser(self, token=None, userId=None, userEmail=None):
        self.userId = userId
        self.userName = None
        self.userEmail = userEmail
        self.refreshToken = None
        self.accessToken = token
        self.accessTokenTimestamp = 0
        self.accessTokenExpires = 0
        self.accessGrantCode = None
        self.refreshToken = None
        self.ddb = None

        if not token and not userId and not userEmail:
            errmsg = 'Cannot initialize a user without an access token, an email address or a userId'
            logger.critical(errmsg)
            raise MissingRequiredValueException(errmsg)

        if token:
            self._getUserProfileFromToken()
        elif userId:
            self._getUserProfileFromDb()
        else:
            self._getUserUUID()

        self._retrieveEndpoints()

    def _getUserUUID(self):
        res = None
        if self.userId:
            dbUUIDuserid = UUIDuserid(self.userId)
            res = dbUUIDuserid['uuid']
        if self.userEmail and not res:
            dbUUIDemail = UUIDemail(self.userEmail)
            res = dbUUIDemail['uuid']
        if res:
            self.uuid = res
            return self.uuid
        raise UserNotFoundException

    def _getUserProfileFromToken(self):
        response = getUserProfile(self.accessToken)
        self.userID = response['userId']
        self.userName = response['name']
        self.userEmail = response['email']
        self._getUserUUID()

    def _getUserProfileFromDb(self):
        dbTokens = Tokens(self.userId)

        self.refreshToken = dbTokens['refreshToken']
        self.userName = dbTokens['userName']
        self.userEmail = dbTokens['userEmail']
        if dbTokens['accessTokenTimestamp'] + dbTokens['accessTokenExpires'] < time.time():
            # Need to refresh access token
            self._refreshAccessToken()
        else:
            self.accessToken = dbTokens['accessToken']
            self.accessTokenTimestamp = dbTokens['accessTokenTimestamp']
            self.accessTokenExpires = dbTokens['accessTokenExpires']
        self._getUserUUID()

    def createUser(self, email):
        dbUUIDemail = UUIDemail(email)
        uuid = dbUUIDemail['uuid']
        if not uuid:
            uuid = get_uuid()
            dbUUIDemail['uuid'] = uuid
        print ('creating user {0} with uuid {1}'.format(email, uuid))
        self.getUser(userEmail=email)

    def commit(self):
        self._persistEndpoints()

    @staticmethod
    def createTables():
    	dbUUIDemail = UUIDemail()
    	dbUUIDuserid = UUIDuserid()
    	dbTokens = Tokens()
    	dbThings = Things()
    	dbs = [ dbUUIDemail,dbUUIDuserid,dbTokens,dbThings ]
    	for item in dbs:
    		item.createTable()

    	print ('Creating Tables.  This can take up to 60 seconds')
    	starttime = time.time()

    	for item in dbs:
    		while True:
    			if item.ready():
    				break
    			print ('{0} seconds elapsed'.format(int(time.time() - starttime)))
    	print ('Finished')

    def _getTokens(self, type):
        if type == 'CODE':
            response = getAccessTokenFromCode(self.accessGrantCode)
        else:
            if not self.refreshToken:
                self._getUserProfileFromDb()
            response = refreshAccessToken(self.refreshToken)
        self.accessToken = response['access_token']
        self.refreshToken = response['refresh_token']
        self.accessTokenExpires = response['expires_in']
        self.accessTokenTimestamp = time.time()
        self._persistTokens()

    def _getAccessTokenFromCode(self):
        self._getTokens('CODE')

    def _refreshAccessToken(self):
        self._getTokens('REFRESH')

    def _persistTokens(self):
        dbTokens = Tokens(self.userId)
        dbTokens['values'] = {
            'accessToken': self.accessToken,
            'accessTokenTimestamp': self.accessTokenTimestamp,
            'accessTokenExpires': self.accessTokenExpires,
            'refreshToken': self.refreshToken,
            'userName': self.userName,
            'userEmail': self.userEmail
        }

    def _persistEndpoints(self):
        if self.uuid and self.endpoints:
            dbThings = Things(self.uuid)
            json_list = []
            for item in self.endpoints.values():
                json_list.append(item.json)
            dbThings['endpoints'] = json_list

    def _retrieveEndpoints(self):
        self.endpoints = {}
        dbThings = Things(self.uuid)
        json_list = dbThings['endpoints']
        for item in json_list:
            cls = self.endpointClasses[item['className']]
            self.endpoints[item['endpointId']] = cls(json=item)
