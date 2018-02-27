userId = 'ron@ritchey.org'
accessToken = 'Access Token'
refreshToken = 'Refresh Token'
accessDuration = 900
region = 'us-east-1'
import boto3
import time
from botocore.exceptions import ClientError

systemName = 'pyASH'
region = 'us-east-1'

import logging
LOGLEVEL = logging.WARN
logger = logging.getLogger(__name__)
logger.setLevel(LOGLEVEL)

def _createThingTable():
    ddb = boto3.resource('dynamodb', region)
    try:
        tn = systemName + '_user_things'
        ddb.create_table(TableName = tn, KeySchema=[{ 'AttributeName':'userId', 'KeyType':'HASH'}, {'AttributeName':'thing', 'KeyType':'RANGE'}],AttributeDefinitions=[{'AttributeName':'userId', 'AttributeType':'S'}, { 'AttributeName':'thing', 'AttributeType':'S'}],ProvisionedThroughput={'ReadCapacityUnits':5, 'WriteCapacityUnits':5})
    except ClientError as e:
        if e.__class__.__name__ == 'ResourceInUseException':
            # Table already exists
            pass
        else:
            errmsg = 'Needed to create new {0} table but failed'.format(tn)
            logger.critical(errmsg)
            raise

def _createTokenTable():
    ddb = boto3.resource('dynamodb', region)
    try:
        tn = systemName + '_user_tokens'
        ddb.create_table(TableName = tn, KeySchema=[{ 'AttributeName':'userId', 'KeyType':'HASH'}],AttributeDefinitions=[{'AttributeName':'userId', 'AttributeType':'S'}],ProvisionedThroughput={'ReadCapacityUnits':5, 'WriteCapacityUnits':5})
    except ClientError as e:
        if e.__class__.__name__ == 'ResourceInUseException':
        # Table already exists
            pass
        else:
            errmsg = 'Needed to create new {0} table but failed'.format(tn)
            logger.critical(errmsg)
            raise

def _persistTokens():
    tn = systemName + '_user_tokens'
    key = {'userId': userId }
    ue = 'set accessToken = :at, refreshToken = :rt, accessDuration = :d'
    eav = { ':at': accessToken, ':rt': refreshToken, ':d':str(accessDuration)}
    ddb = boto3.resource('dynamodb', region)
    table = ddb.Table(tn)
    try:
        res = table.update_item(Key=key, UpdateExpression=ue, ExpressionAttributeValues=eav, ReturnValues="UPDATED_NEW")
        print (res)
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
                    print (res)
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
