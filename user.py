import json
import boto3
from botocore.vendored import requests

from utility import *

# Setup logger
import logging
logger = logging.getLogger(__name__)
logger.setLevel(LOGLEVEL)

from decimal import Decimal


class User(object):
    def __init__(self, token=None, code=None, region='us-east-1', systemName = 'pyASH'):
        self.region = region
        self.userId = ''
        self.userName = ''
        self.userEmail = ''
        self.refreshToken = ''
        self.accessToken = token
        self.accessGrantCode = code
        self.accessDuration = 0
        self.endpoints = {}
        self.ddb = None
        self.systemName = systemName

        # Initialize tables if needed
        self._createTokenTable()
        self._createThingTable()

        if not token and not code:
            errmsg = 'Cannot initialize a user without either an access token or an AccessGrant code'
            logger.critical(errmsg)
            raise MissingRequiredValue(errmsg)

        if token:
            self._getUserProfile(token)
        else:
            self._getAccessTokenFromCode(code)
            self._getUserProfile(self.accessToken)

    def _refreshAccessToken(self):
        if not self.refreshToken:
            # Need to retrieve user's refreshToken from storage

    def _getUserProfile(self, token):
        payload = { 'access_token': token }
        r = requests.get("https://api.amazon.com/user/profile", params=payload)

        validateReturnCode(r.status_code)

        try:
            self.userId = r.json()['user_id']
            self.userEmail = r.json()['email']
            self.userName = r.json()['name']
        except KeyError:
            if user_id == '':
                errmsg = 'Requested profile but user_id not received'
            elif user_name == '' or user_email == '':
                errmsg = 'Requested profile but user_name or user_email not received'
            logger.warn(errmsg)

    def _getAccessTokenFromCode(self, code):

        try:
            # Retrieve tokens using Grant code
            lwa_client_id = os.environ['lwa_client_id']
            lwa_client_secret = os.environ['lwa_client_secret']
        except KeyError:
            errmsg = 'Missing "login with amazon" (LWA) credentials.  Unable to store AccessGrant code'
            logger.critical(errmsg)
            raise MissingCredential(errmsg)

        payload = {
            'grant_type':'authorization_code',
            'code': d.code,
            'client_id':lwa_client_id,
            'client_secret':lwa_client_secret,
        }

        r = requests.post("https://api.amazon.com/auth/o2/token", data=payload)
        validateReturnCode(r.status_code)

        try:
            response = r.json()
            self.accessToken = response['access_token']
            self.refreshToken = response['refresh_token']
            self.refreshTokenIssued = time.time()
        except KeyError:
            errmsg = 'Tokens not in response'
            logger.warn(errmsg)
            raise TokenMissing(errmsg)

        try:
            response = r.json()
            self.accessDuration = response['expires_in']
        except KeyError:
            self.accessDuration = 900 # Set default token duration to 15 minutes


    def _persistTokens(self):
        tn = self.systemName + '_user_tokens'
        key = {'userId': self.userId }
        ue = 'set accessToken = :at, refreshToken = :rt, accessDuration = :d, tokenIssued = :ti'
        eav = { ':at': self.accessToken, ':rt': self.refreshToken, ':d':str(self.accessDuration), ':ti':Decimal(self.refreshTokenIssued)}
        ddb = boto3.resource('dynamodb', self.region)
        table = ddb.Table(tn)
        try:
            res = table.update_item(Key=key, UpdateExpression=ue, ExpressionAttributeValues=eav, ReturnValues="UPDATED_NEW")
        except ClientError as e: # boto3.exceptions.ResourceNotFoundException:
            if e.__class__.__name__ == 'ResourceNotFoundException':
                try:
                    _createTokenTable()
                    time.sleep(10)
                except:
                    errmsg = 'Needed to create new {0} table but failed'.format(tn)
                    logger.critical(errmsg)
                    raise
                expires = time.time()+20
                while True:
                    try:
                        time.sleep(1) # Give the new table a chance to update
                        print ('Attempting again with {0} seconds remaining'.format(int(expires-time.time())))
                        table = ddb.Table(tn)
                        res = table.update_item(Key=key, UpdateExpression=ue, ExpressionAttributeValues=eav, ReturnValues="UPDATED_NEW")
                        break
                    except ClientError as e:
                        if e.__class__.__name__ == 'ResourceNotFoundException':
                            if time.time() > expires:
                                errmsg = 'Successfully created new {0} table but have been unable to store tokens into it'
                                raise
                        else:
                            raise
            else:
                raise


    def _persistEndpoints(self):

    def _getTokens(self):

    def _getDDB(self):
        self.ddb = boto3.resource('dynamodb', self.region)
        tablename = 'test'
        keyconditionexpression='UserId = :user_id'
        expressionattributevalues = {":username": { "S": "ron@ritchey.org"}}

        key = { 'customer': user_data['user_id'] }

        logger.info( 'handle_authorization: profile received with values user_id [' + user_data['user_id'] + '] user_email [' + user_data['email'] + '] user_name [' + user_data['name'] + ']' )

        # Store tokens to database
        table = dynamodb_client.Table('preampskill_customers')
        response = table.update_item (
            Key = key,
            UpdateExpression = "set user_name = :n, email = :e, access_token = :a, refresh_token = :r, expires_in = :i",
            ExpressionAttributeValues =  {
                ':n': user_data['name'],
                ':e': user_data['email'],
                ':a': gateway_access_token,
                ':r': gateway_refresh_token,
                ':i': gateway_token_duration
            },
            ReturnValues="UPDATED_NEW"
        )

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
