# -*- coding: utf-8 -*-

# Copyright 2018 dhrone. All Rights Reserved.
#
from botocore.exceptions import ClientError

# pyASH imports
from utility import *

# Setup logger
import logging
logger = logging.getLogger(__name__)
logger.setLevel(LOGLEVEL)

class Persist(object):
    def __init__(self, primaryKey, primaryKeyName, tableName = 'Persist', secondaryKey=None, secondaryKeyName=None, systemName=DEFAULT_SYSTEM_NAME, region=DEFAULT_REGION, dataAgeMax=5):
        self.primaryKey = primaryKey
        self.primaryKeyName = primaryKeyName
        self.tableName = tableName
        self.secondaryKey = secondaryKey
        self.secondaryKeyName = secondaryKeyName
        self.systemName = systemName
        self.region = region
        self.item = {}
        self.dataAgeMax = dataAgeMax
        self.dataAge = 0

    def _get(self):
        ddb = boto3.resource('dynamodb', self.region)
        table = ddb.Table(self._tableName)
        key = { self.primaryKeyName: self.primaryKey }
        if self.secondaryKeyName:
            key[self.secondaryKeyName] = self.secondaryKey
        result = table.get_item(Key=key)
        self.dataAge = time.time()
        if 'Item' in result:
            self.item = result['Item']
        else:
            self.item = {}

    def _commit(self):
        self.item[self.primaryKeyName] = self.primaryKey
        if self.secondaryKeyName:
            self.item[self.secondaryKeyName] = self.secondaryKey
        ddb = boto3.resource('dynamodb', self.region)
        table = ddb.Table(self._tableName)
        self.dataAge = time.time()
        return table.put_item(Item=self.item)

    @property
    def _tableName(self):
        return self.systemName + '_' + self.tableName

    @staticmethod
    def _attributeType(val):
        if type(val) in [int, float]:
            return 'N'
        if type(val) is bytes:
            return 'B'
        if type(val) is bool:
            return 'BOOL'
        if type(val) is list:
            return 'L'
        if type(val) is dict:
            return 'M'
        if type(val) is str:
            return 'S'

    def __getitem__(self, property):
        if time.time() > self.dataAge+self.dataAgeMax:
            self._get()
        return self.item.get(property)

    def __setitem__(self, property, value):
        self.item[property] = value
        self._commit()

    def createTable(self):
        ddb = boto3.resource('dynamodb', self.region)

        keyschema = [{'AttributeName':self.primaryKeyName, 'KeyType':'HASH'}]
        attributedefinitions = [{'AttributeName': self.primaryKeyName, 'AttributeType':self._attributeType(self.primaryKey)}]
        if self.secondaryKey:
            keyschema.append({'AttributeName':self.secondaryKeyName, 'KeyType':'RANGE'})
            attributedefinitions.append({'AttributeName':self.secondaryKeyName, 'AttributeType':self._attributeType(self.secondaryKey)})

        try:
            ddb.create_table(TableName = self._tableName, KeySchema=keyschema,AttributeDefinitions=attributedefinitions,ProvisionedThroughput={'ReadCapacityUnits':5, 'WriteCapacityUnits':5})
            return True
        except ClientError as e:
            if e.__class__.__name__ == 'ResourceInUseException':
                # Table already exists
                return False
            else:
                errmsg = 'Needed to create new {0} table but failed'.format(tn)
                logger.critical(errmsg)
                raise

    def ready(self, timeout=5): # Called by user program to check if the table exists and is ready to be interacted with
        ddb = boto3.resource('dynamodb', self.region)
        table = ddb.Table(self._tableName)
        timeExpired = time.time() + timeout
        while time.time() < timeExpired:
            try:
                table.scan()
                return True
            except ClientError as e:
                if e.__class__.__name__ == 'ResourceNotFoundException':
                    # Table either does not exist or has not finished being created
                    time.sleep(1)
                    continue
                else:
                    raise
        return False

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
