# -*- coding: utf-8 -*-

# Copyright 2018 by dhrone. All Rights Reserved.
#
from abc import ABC, abstractmethod
import json
import time
import re
import pickle
import boto3
from botocore.vendored import requests
from decimal import Decimal


# pyASH imports
from .db import Persist
from .endpoint import Endpoint
from .exceptions import NO_SUCH_ENDPOINT, USER_NOT_FOUND_EXCEPTION, MISCELLANIOUS_EXCEPTION
from .utility import LOGLEVEL, DEFAULT_SYSTEM_NAME, DEFAULT_REGION, DEFAULT_IOTREGION, getAccessTokenFromCode, getUserProfile

# Setup logger
import logging
logger = logging.getLogger(__name__)
logger.setLevel(LOGLEVEL)

class User(ABC):

    def __init__(self):
        self.endpoints = {}

    @abstractmethod
    def getEndpoints(self, request):
        pass

    @abstractmethod
    def getEndpoint(self, request):
        pass

    def getTokens(self, request):
        response = getAccessTokenFromCode(request['payload']['grant']['code'])
        self.storeTokens(response['access_token'], response['refresh_token'], response['expires_in'])

    @abstractmethod
    def storeTokens(self, access, refresh, expires_in):
        pass

    def _storeTokens(self, access, refresh, expires_in):
        self.accessToken = access
        self.refreshToken = refresh
        self.accessTokenExpires = expires_in
        self.accessTokenTimestamp = time.time()

    def _persistEndpoints(self):
        pass

    def _retrieveEndpoints(self):
        pass

    def addEndpoint(self, endpoint):
        self.endpoints[endpoint.endpointId] = endpoint
        self._persistEndpoints()

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
            response = { 'access_token': '<access token>', 'refresh_token':'<refresh token>', 'expires_in': 3600 }
        self.storeTokens(response['access_token'], response['refresh_token'], response['expires_in'])

class DbUser(User):
    def __init__(self, userEmail=None, userId=None, token=None, region='us-east-1', systemName = 'pyASH', classes=None):
        super(DbUser, self).__init__()

        self.region = region
        self.systemName = systemName
        self.uuid = None
        self.classes = classes

        if userId or userEmail or token:
            self._getUser(userId=userId, userEmail=userEmail, token=token)
            if not self.uuid:
                un = userId if userId else userEmail
                raise USER_NOT_FOUND_EXCEPTION('Could not find {0}'.format(un))

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
            raise MISCELLANIOUS_EXCEPTION(errmsg)

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
        msg = 'No user with UserId of {0}'.format(self.userId) if self.userId else 'No user with Email address of {0}'.format(self.userEmail) if self.userEmail else 'No ability to retrieve user.  Neither userId nor userEmail provided'
        raise USER_NOT_FOUND_EXCEPTION(msg)

    def _getUserProfileFromToken(self):
        response = getUserProfile(self.accessToken)
        self.userId = response['user_id']
        self.userName = response['name']
        self.userEmail = response['email']
        self._getUserUUID()

    def _getUserProfileFromDb(self):
        dbTokens = DBTokens(self.userId)

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

    def removeUser(self, user):
        pass

    def commit(self):
        self._persistEndpoints()

    @staticmethod
    def createTables():
        dbs = [ UUIDemail(),UUIDuserid(),DBTokens(),DBEndpoints() ]
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

    @staticmethod
    def delTables():
        dbs = [ UUIDemail(),UUIDuserid(),DBTokens(),DBEndpoints() ]
        for item in dbs:
            item.delTable()


    def _getTokens(self, type):
        if type == 'CODE':
            response = getAccessTokenFromCode(self.accessGrantCode)
        else:
            if not self.refreshToken:
                self._getUserProfileFromDb()
            response = refreshAccessToken(self.refreshToken)
        self._storeTokens(response['access_token'], response['refresh_token'], response['expires_in'])
        self._persistTokens()

    def _persistTokens(self):
        dbTokens = DBTokens(self.userId)
        dbTokens['values'] = {
            'accessToken': self.accessToken,
            'accessTokenTimestamp': self.accessTokenTimestamp,
            'accessTokenExpires': self.accessTokenExpires,
            'refreshToken': self.refreshToken,
            'userName': self.userName,
            'userEmail': self.userEmail
        }

    def _persistEndpoints(self):
        dbEndpoints = DBEndpoints(self.uuid)
        endpointList = []
        for item in self.endpoints.values():
            endpointList.append(item.json)
        dbEndpoints['endpoints'] = endpointList

    def _retrieveEndpoints(self):
        self.endpoints = {}
        dbEndpoints = DBEndpoints(self.uuid)
        endpointList = dbEndpoints['endpoints']
        if endpointList:
            for epJson in endpointList:
                item = json.loads(epJson)
                print (item['__classname__'])
                for clsinstance in self.classes:
                    print ('Checking '+clsinstance.__name__)
                    if item['__classname__'] == clsinstance.__name__:
                        print ('Matched '+clsinstance.__name__)
                        endpointClass = clsinstance
                        break
                else:
                    raise Exception('No endpoint class found to handle retrieved endpoint')
                endpoint = endpointClass(json=item, iotClasses = self.classes)
                self.endpoints[endpoint.endpointId] = endpoint

class DBEndpoints(Persist):
    def __init__(self, uuid='', systemName=DEFAULT_SYSTEM_NAME, region=DEFAULT_REGION):
        super(DBEndpoints, self).__init__(uuid, 'uuid', 'Endpoints')

class DBTokens(Persist):
    def __init__(self, userId='', systemName=DEFAULT_SYSTEM_NAME, region=DEFAULT_REGION):
        super(DBTokens, self).__init__(userId, 'userId', 'Tokens')

class UUIDemail(Persist):
    def __init__(self, email='', systemName=DEFAULT_SYSTEM_NAME, region=DEFAULT_REGION):
        super(UUIDemail, self).__init__(email, 'email', 'UUIDlookupEmail')

class UUIDuserid(Persist):
    def __init__(self, userId='', systemName=DEFAULT_SYSTEM_NAME, region=DEFAULT_REGION):
        super(UUIDuserid, self).__init__(userId, 'userId', 'UUIDlookupUserId')
