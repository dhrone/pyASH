# -*- coding: utf-8 -*-

# Copyright 2018 by dhrone. All Rights Reserved.
#
from abc import ABC, abstractmethod
import json
import time
import re
import boto3
from botocore.vendored import requests
from decimal import Decimal

# pyASH imports
from db import Persist
from message import Capability, Request, Response, defaultResponse
from endpoint import Endpoint
from exceptions import *
from utility import *

# Setup logger
import logging
logger = logging.getLogger(__name__)
logger.setLevel(LOGLEVEL)

class User(ABC):

    def __init__(self):
        self.endpoints = {}
        self.endpointClasses = {}

    @abstractmethod
    def getEndpoints(self, request):
        pass

    @abstractmethod
    def getEndpoint(self, request):
        pass

    @abstractmethod
    def storeTokens(self, access, refresh, expires_in):
        pass

    def _storeTokens(self, access, refresh, expires_in):
        self.accessToken = access
        self.refreshToken = refresh
        self.accessTokenExpires = expires_in
        self.accessTokenTimestamp = time.time()

    @staticmethod
    def _getEndpointId(cls, things):
        if ':' in things:
            raise ValueError(': symbol not allowed in thing names')
        things = things if type(things) is list else [things]
        return cls.__name__ + ':' + ':'.join(things)

    @staticmethod
    def _retrieveThings(endpointId):
        things = endpointId.split(':')
        cls = things[0]
        things = things[1:]
        return things

    def _retrieveClass(self, endpointId):
        cls = endpointId.split(':')[0]
        return self.endpointClasses[cls]

    def getTokens(self, request):
        response = getAccessTokenFromCode(request['payload']['grant']['code'])
        self.storeTokens(response['access_token'], response['refresh_token'], response['expires_in'])

    def addEndpoint(self, endpointClass, things=None,   friendlyName=None, description=None, manufacturerName=None,displayCategories=None, proactivelyReported=None, retrievable=None, uncertaintyInMilliseconds=None, supportsDeactivation=None, cookie=None):
        self.endpointClasses[endpointClass.__name__] = endpointClass
        endpointId = self._getEndpointId(endpointClass, things)
        self.endpoints[endpointId] = endpointClass(endpointId, things, friendlyName, description, manufacturerName,displayCategories, proactivelyReported, retrievable, uncertaintyInMilliseconds, supportsDeactivation, cookie)

class StaticUser(User):
    def __init__(self):
        super(StaticUser, self).__init__()

    def getEndpoints(self, request):
        return self.endpoints.values()

    def getEndpoint(self, request):
        try:
            return self.endpoints[request.endpointId]
        except KeyError:
            raise NO_SUCH_ENDPOINT('{0} is not a valid endpoint'.format(request.endpointId))

    def storeTokens(self, access, refresh, expires_in):
        self._storeTokens(access, refresh, expires_in)
        print ('ACCESSGRANT Refresh[{0}], Access[{1}], Expires_In [{2}]'.format(access,refresh,expires_in))

class DemoUser(StaticUser):
    def getTokens(self, request):
        try:
            response = getAccessTokenFromCode(request['payload']['grant']['code'])
        except:
            # Return dummy values if unable to retrieve real user profile
            request = { 'access_token': '<access token>', 'refresh_token':'<refresh token>', 'expires_in': 3600 }
        self.storeTokens(response['access_token'], response['refresh_token'], response['expires_in'])

class DbUser(User):
    def __init__(self, endpointClasses=None, userEmail=None, userId=None, region='us-east-1', systemName = 'pyASH'):
        super(DbUser, self).__init__()

        self.region = region
        self.systemName = systemName
        self.uuid = None

        if endpointClasses:
            endpointClasses = endpointClasses if type(endpointClasses) is list else [ endpointClasses ]
            for cls in endpointClasses:
                self.endpointClasses[cls.__name__] = cls

        if userId or userEmail:
            self._getUser(userId=userId, userEmail=userEmail)
            if not self.uuid:
                un = userId if userId else userEmail
                raise UserNotFoundException('Could not find {0}'.format(un))

    def getEndpoints(self, request):
        self._getUser(token=request.token)
        self._retrieveEndpoints()
        return self.endpoints.values()

    def getEndpoint(self, request):
        self._getUser(token=request.token)
        self._retrieveEndpoints()
        try:
            return self.endpoints[request.endpointId]
        except KeyError:
            raise NO_SUCH_ENDPOINT('{0} is not a valid endpoint'.format(request.endpointId))

    def storeTokens(self, access, refresh, expires_in):
        self._getUser(token=access)
        self._storeTokens(access, refresh, expires_in)
        self._persistTokens()
        dbUUIDuserid = UUIDuserid(self.userId)
        dbUUIDuserid['uuid'] = self.uuid


    def addEndpoint(self, endpointClass, things=None,   friendlyName=None, description=None, manufacturerName=None,displayCategories=None, proactivelyReported=None, retrievable=None, uncertaintyInMilliseconds=None, supportsDeactivation=None, cookie=None):
        super(DbUser, self).addEndpoint(endpointClass, things,   friendlyName, description, manufacturerName,displayCategories, proactivelyReported, retrievable, uncertaintyInMilliseconds, supportsDeactivation, cookie)
        self._persistEndpoints()

    def _getUser(self, token=None, userId=None, userEmail=None):
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
        msg = 'No user with UserId of {0}'.format(self.userId) if self.userId else 'No user with Email address of {0}'.format(self.userEmail) if self.userEmail else 'No ability to retrieve user.  Both userId and userEmail not provided'
        raise UserNotFoundException(msg)

    def _getUserProfileFromToken(self):
        response = getUserProfile(self.accessToken)
        self.userId = response['user_id']
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
            self._getTokens('REFRESH')
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
        self._getUser(userEmail=email)

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
        if self.uuid:
            dbThings = Things(self.uuid)
            json_list = []
            for item in self.endpoints.values():
                json_list.append(item.json)
            dbThings['endpoints'] = json_list
        else:
            raise UserNotInitialized('UUID not set.  _persistEndpoints likely called prior to _getUser')

    def _retrieveEndpoints(self):
        self.endpoints = {}
        dbThings = Things(self.uuid)
        json_list = dbThings['endpoints']
        if json_list:
            for item in json_list:
                cls = self.endpointClasses[item['className']]
                self.endpoints[item['endpointId']] = cls(json=item)

class Things(Persist):
    def __init__(self, uuid='', systemName=DEFAULT_SYSTEM_NAME, region=DEFAULT_REGION):
        super(Things, self).__init__(uuid, 'uuid', 'Things')

class Tokens(Persist):
    def __init__(self, userId='', systemName=DEFAULT_SYSTEM_NAME, region=DEFAULT_REGION):
        super(Tokens, self).__init__(userId, 'userId', 'Tokens')

class UUIDemail(Persist):
    def __init__(self, email='', systemName=DEFAULT_SYSTEM_NAME, region=DEFAULT_REGION):
        super(UUIDemail, self).__init__(email, 'email', 'UUIDlookupEmail')

class UUIDuserid(Persist):
    def __init__(self, userId='', systemName=DEFAULT_SYSTEM_NAME, region=DEFAULT_REGION):
        super(UUIDuserid, self).__init__(userId, 'userId', 'UUIDlookupUserId')
