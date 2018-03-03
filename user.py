 -*- coding: utf-8 -*-

# Copyright 2018 by dhrone. All Rights Reserved.
#
from abc import ABC
import json
import boto3
from botocore.vendored import requests

from utility import *
from exceptions import *
from db import Tokens,Things, Persist
from message import Capability, Request, Response

# Setup logger
import logging
logger = logging.getLogger(__name__)
logger.setLevel(LOGLEVEL)

from decimal import Decimal


class User(ABC):

    def __init__(self, endpoints=[]):
        self.endpoints = endpoints

    @abstractmethod
    def _getEndpoints(token):
        pass

    @abstractmethod
    def handleAcceptGrant(self, request):
        pass

    @abstractmethod
    def handleDiscovery(self, request):
        pass

    def _getUserProfile(self, token):
        response = getUserProfile(token)
        self.userID = response['user_id']
        self.userName = response['name']
        self.userEmail = response['email']

    def _getAccessTokensFromCode(self, code):
        response = getAccessTokenFromCode(code)
        self.accessToken = response['access_token']
        self.refreshToken = response['refresh_token']
        self.accessTokenTimestamp = time.time()
        self.accessTokenExpires = response['expires_in']
        self._getUserProfile(self.accessToken)


class StaticUser(User):
    def __init__(self, endpoints=[]):
        if type(endpoints) != list:
            if isinstance(endpoints, Endpoint):
                endpoints = [ endpoints ]
            else:
                raise TypeError('Must provide a list of endpoints')
        self.endpoints = endpoints

    def _getEndpoints(self, token):
        return self.endpoints

    def handleDiscovery(self, request):
        r = Request(request)
        endpoints = self._getEndpoints(r.token)

        epResponses = []
        for e in endpoints:
            epResponses.append(e.endpointResponse())

        return Response(directive, epResponses)

    def handleAcceptGrant(self, request):
        r = Request(request)
        response = self._getAccessTokenFromCode(r.code)
        profile = self._getUserProfile(response['access_token'])
        print "User {0}'s refreshToken is {1}".format(profile['name'], response['refresh_token'])

class DbUser(User):
    def __init__(self, endpoints=[], region='us-east-1', systemName = 'pyASH'):
        self.region = region
        self.systemName = systemName
        self.endpointClasses = {}
        self.endpoints = []

        if type(endpoints) is not list:
            endpoints = [ endpoints ]

        for item in endpoints:
            if isinstance(item, Endpoint):
                self.endpointClasses[item.__class__.__name__] = item.__class__
            else:
                self.endpointClasses[item.__name__]=item

    def getUser(self, token=None, userId=None):
        self.userId = None
        self.userName = None
        self.userEmail = None
        self.refreshToken = None
        self.accessToken = token
        self.accessTokenTimestamp = 0
        self.accessTokenExpires = 0
        self.accessGrantCode = code
        self.refreshToken = None
        self.ddb = None

        if not token and not userId:
            errmsg = 'Cannot initialize a user without an access token or a userId'
            logger.critical(errmsg)
            raise MissingRequiredValue(errmsg)

        if token:
            self._getUserProfileFromToken()
        else:
            self._retrieveTokens()

    def addEndpoint(self, endpoint):
        self.endpointClasses[endpoint.__class__.__name__] = endpoint.__class__
        self.endpoints.append(endpoint)

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


    def commit(self):
        self._persistEndpoints()

    def _getTokens(self, type):
        if type == 'CODE':
            response = getAccessTokenFromCode(self.accessGrantCode)
        else:
            if not self.refreshToken:
                self._retrieveTokens()
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

    def _getUserProfileFromToken(self):
        response = getUserProfile(self.accessToken)
        self.userID = response['userId']
        self.userName = response['name']
        self.userEmail = response['email']

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

    def _retrieveTokens(self):
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

    def _persistEndpoints(self):
        if self.userId and self.endpoints:
            dbThings = Things(self.userId)
            json_list = []
            for item in self.endpoints:
                json_list.append(item.json)
            dbThings['endpoints'] = json_list

    def _retrieveEndpoints(self):
        self.endpoints = []
        dbThings = Things(self.userId)
        json_list = dbThings['endpoints']
        for item in json_list:
            cls = self.endpointClasses[item['className']]
            self.endpoints.append(cls(json=item))
