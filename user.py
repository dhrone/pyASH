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
from db import Tokens, Things, Persist, UUIDemail, UUIDuserid
from message import Capability, Request, Response, defaultResponse
from endpoint import Endpoint

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
        # Pull user token from request.
        # Use it to retrieve user and then retrieve the user's endpoints
        pass

    @abstractmethod
    def getEndpoint(self, request):
        # Pull endpointId from request
        # Use it to create endpoint for that endpointId
        pass

    @abstractmethod
    def storeTokens(self, access, refresh, expires_in):
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

    @staticmethod
    def _getEndpointId(cls, things):
        if ':' in things:
            raise ValueError(': symbol not allowed in thing names')
        things = things if type(things) is list else [things]
        return cls.__name__ + '|' + ':'.join(things)

    @staticmethod
    def _retrieveThings(endpointId):
        (cls, things) = endpointId.split('|')
        things = things.split(':')
        return things

    def _retrieveClass(self, endpointId):
        (cls, things) = endpointId.split('|')
        return self.endpointClasses[cls]

    def addEndpoint(self, endpointClass, things=None, friendlyName=None, description=None, manufacturerName=None,displayCategories=None, proactivelyReported=None, retrievable=None, uncertaintyInMilliseconds=None, supportsDeactivation=None, cookie=None):
        self.endpointClasses[endpointClass.__name__] = endpointClass
        endpointId = self._getEndpointId(endpointClass, things)
        self.endpoints[endpointId] = endpointClass(endpointId, things, friendlyName, description, manufacturerName,displayCategories, proactivelyReported, retrievable, uncertaintyInMilliseconds, supportsDeactivation, cookie)


class StaticUser(User):
    def __init__(self):
        super(StaticUser, self).__init__()

    def getEndpoints(self, request):
        return self.endpoints.values()

    def getEndpoint(self, request):
        return self.endpoints[request.endpointId]

    def storeTokens(self, access, refresh, expires_in):
        print ('ACCESSGRANT Refresh[{0}], Access[{1}], Expires_In [{2}]'.format(access,refresh,expires_in))

class DbUser(User):
    def __init__(self, region='us-east-1', systemName = 'pyASH'):
        super(DbUser, self).__init__()

        self.region = region
        self.systemName = systemName
        self.uuid = None

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
