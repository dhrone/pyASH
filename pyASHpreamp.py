# -*- coding: utf-8 -*-

# Copyright 2018 dhrone. All Rights Reserved.
#

import logging
import time
import json
import uuid
import os
from botocore.vendored import requests
import boto3
import urllib
from datetime import datetime

# Imports for v3 validation
from validation import validate_message
import jsonschema

import pyASH

# Setup logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Valid Inputs
VALID_INPUTS = [ 'CD', '2-Ch Bal', '6-Ch S/E', 'tape', 'FM/AM', 'DVD', 'TV', 'SAT', 'VCR', 'AUX' ]

def lambda_handler(request, context):

    ci = pyASH.ControllerInterface(AcceptGrantHandler, DiscoverHandler)
    ci.register_callback(ReportStateHandler, 'Alexa', 'ReportState')
    ci.register_callback(SpeakerHandler, 'Alexa.Speaker')
    ci.register_callback(PowerHandler, 'Alexa.PowerController')
    ci.register_callback(InputHandler, 'Alexa.InputController')

    try:
        d = pyASH.Directive(request)
    except (ValueError, TypeError) as error:
        # Bad directive received
        logger.error('lambda_handler received a bad directive: ' + str(error))
        raise

    if d.payloadVersion != '3':
        errmsg = 'Received invalid directive version.  Only version 3 is supported.  This directive was version '+version+'.'
        logger.warn(errmsg)
        return pyASH.ErrorResponse('Alexa', 'INVALID_DIRECTIVE', errmsg).get_json()

    response = ci.process_directive(request).get_json()
    try:
        validate_message(request, response)
    except jsonschema.exceptions.ValidationError:
        logger.warn('lambda_handler: response message failed validation.  Response was ' + json.dumps(response, indent=4))
        raise
    except  jsonschema.exceptions.SchemaError:
        logger.warn('lambda_handler: schema failed validation')
        raise

    return response

def AcceptGrantHandler(directive):
    logger.info('Handling AcceptGrant')

    d = pyASH.Directive(directive)

    # Retrieve tokens using Grant code
    lwa_client_id = os.environ['lwa_client_id']
    lwa_client_secret = os.environ['lwa_client_secret']

    payload = {
        'grant_type':'authorization_code',
        'code': d.code,
        'client_id':lwa_client_id,
        'client_secret':lwa_client_secret,
    }

    r = requests.post("https://api.amazon.com/auth/o2/token", data=payload)

    if r.status_code != 200:
        errmsg = 'Unable to receive access/refresh tokens.  Return code was ' + str(r.status_code)
        logger.warn(errmsg)
        return pyASH.ErrorResponse('Alexa', 'ACCEPT_GRANT_FAILED', errmsg, correlationToken=d.correlationToken)

    try:
        response = r.json()
        gateway_access_token = response['access_token']
        gateway_refresh_token = response['refresh_token']
    except KeyError:
        errmsg = 'Tokens not in response'
        logger.warn(errmsg)
        return pyASH.ErrorResponse('Alexa', 'ACCEPT_GRANT_FAILED', errmsg, correlationToken=d.correlationToken)

    try:
        response = r.json()
        gateway_token_duration = response['expires_in']
    except KeyError:
        gateway_token_duration = 900 # Set default token duration to 15 minutes

    # Retrieving Users' profile
    try:
        user_data = get_user_profile(grantee_access_token)
    except requests.exceptions.HTTPError as err:
        errmsg = 'Unable to retrieve profile.  Error was ' + str(err)
        logger.warn(errmsg)
        return pyASH.ErrorResponse('Alexa', 'ACCEPT_GRANT_FAILED', errmsg, correlationToken=d.correlationToken)

    if user_data['user_id'] == '':
        errmsg = 'Requested profile but user_id not received'
        logger.warn(errmsg)
        return pyASH.ErrorResponse('Alexa', 'ACCEPT_GRANT_FAILED', errmsg, correlationToken=d.correlationToken)


    dynamodb_client = boto3.resource('dynamodb')
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

    # Store
    return pyASH.Response(directive)

def DiscoverHandler(directive):
    header = pyASH.Header('Alexa.Discovery','Discover.Response').get_json()
    payload = {
        'endpoints': [ ]
    }

    endpoints = pyASH.Endpoints()
    # Add appliance-001
    cps = []
    cps.append( pyASH.Capability('Alexa.Speaker', pyASH.Properties_supported('volume', False, True), '3') )
    cps.append( pyASH.Capability('Alexa.Speaker', pyASH.Properties_supported('muted', False, True), '3') )
    cps.append( pyASH.Capability('Alexa.PowerController', pyASH.Properties_supported('powerState', False, True), '3') )
    cps.append( pyASH.Capability('Alexa.InputController', pyASH.Properties_supported('input', False, True), '3') )
    ep = pyASH.Endpoint("avmctrl_den", "Anthem", "Family Room Preamp", "AVM20 Preamp by Anthem", ["OTHER"], capabilities = cps)
    endpoints.add(ep)

    return pyASH.Response(directive, endpoints)

def ReportStateHandler(directive):
    d = pyASH.Directive(directive)
    ts = pyASH.get_utc_timestamp()
    properties = pyASH.Properties()

    # Retrieve state of endpoint from AWS IOT service
    jsonState = IOT_get_state(d.endpointId, 'us-west-2')
    reported = jsonState['state']['reported']

    p = pyASH.SpeakerVolumeProperty(reported['volume'],ts,0)
    properties.add(p)

    p = pyASH.SpeakerMuteProperty(reported['mute'], ts, 0)
    properties.add(p)

    p = pyASH.PowerStateProperty(reported['apower'],ts,0)
    properties.add(p)

    p = pyASH.InputProperty(reported['asource'],ts,0)
    properties.add(p)
    return pyASH.Response(directive, properties)

def SpeakerHandler(directive):
    d = pyASH.Directive(directive)

    # Get state of endpoint
    jsonState = IOT_get_state(d.endpointId, 'us-west-2')
    reported = jsonState['state']['reported']

    current_volume = reported['volume']*10
    current_mute = reported['mute']

    new_volume = current_volume
    new_mute = current_mute

    if d.name == "SetVolume":
        try:
            new_volume = d.payload["volume"]
        except KeyError:
            errmsg = 'SetVolume request contained no volume payload'
            logger.warn(errmsg)
            return pyASH.ErrorResponse('Alexa', 'INVALID_DIRECTIVE', errmsg, correlationToken=d.correlationToken)
        if new_volume < 0 or new_volume > 100:
            errmsg = 'Volume must be between 0 and 100.  Received value was ' + str(new_volume)
            logger.warn(errmsg)
            return pyASH.ErrorResponse('Alexa', 'VALUE_OUT_OF_RANGE', errmsg, correlationToken=d.correlationToken, min=0, max=100)

    elif d.name == "AdjustVolume":
        try:
            change_volume = d.payload["volume"]
        except KeyError:
            errmsg = 'AdjustVolume request contained no volume payload'
            logger.warn(errmsg)
            return pyASH.ErrorResponse('Alexa', 'INVALID_DIRECTIVE', errmsg, correlationToken=d.correlationToken)
        if change_volume < -100 or new_volume > 100:
            errmsg = 'ChangeVolume must be between -100 and 100.  Received value was ' + str(change_volume)
            logger.warn(errmsg)
            return pyASH.ErrorResponse('Alexa', 'VALUE_OUT_OF_RANGE', errmsg, correlationToken=d.correlationToken, min=-100, max=100)

        new_volume = current_volume + change_volume
        new_volume = 0 if new_volume < 0 else new_volume
        new_volume = 100 if new_volume > 100 else new_volume

    elif d.name == "SetMute":
        try:
            new_mute = d.payload["mute"]
        except KeyError:
            errmsg = 'SetMute request contained no mute payload'
            logger.warn(errmsg)
            return pyASH.ErrorResponse('Alexa', 'INVALID_DIRECTIVE', errmsg, correlationToken=d.correlationToken)
    else:
        errmsg = 'Received invalid directive for speaker.  Value was '+d.name
        logger.warn(errmsg)
        return pyASH.ErrorResponse('Alexa', 'INVALID_DIRECTIVE', errmsg, correlationToken=d.correlationToken)

    desired_state = { }
    if new_volume != current_volume:
        desired_state['volume'] = int(new_volume/10)
    if new_mute != current_mute:
        desired_state['mute'] = new_mute

    print (json.dumps(desired_state, indent=4))

    # Issue command to preamp
    IOT_update_desired_state(desired_state, d.endpointId, 'us-west-2')
    time.sleep(.25) # Wait a short time to allow preamp to change and reported state to be updated

    # Get state of endpoint
    jsonState = IOT_get_state(d.endpointId, 'us-west-2')
    reported = jsonState['state']['reported']

    ts = pyASH.get_utc_timestamp()
    properties = pyASH.Properties()
    p = pyASH.SpeakerVolumeProperty(reported['volume'],ts,0)
    properties.add(p)

    p = pyASH.SpeakerMuteProperty(reported['mute'], ts, 0)
    properties.add(p)

    # Send report state back to Alexa
    return pyASH.Response(directive, properties)

def PowerHandler(directive):
    d = pyASH.Directive(directive)

    # Get state of endpoint
    jsonState = IOT_get_state(d.endpointId, 'us-west-2')
    reported = jsonState['state']['reported']

    powerState = reported['apower']


    if d.name == "TurnOn":
        requestedPowerState = True
    elif d.name == 'TurnOff':
        requestedPowerState = False
    else:
        errmsg = 'Received invalid directive for PowerController.  Value was '+d.name
        logger.warn(errmsg)
        return pyASH.ErrorResponse('Alexa', 'INVALID_DIRECTIVE', errmsg, correlationToken=d.correlationToken)


    desired_state = { }
    if powerState != requestedPowerState:
        desired_state['apower'] = requestedPowerState

        # Issue command to preamp
        IOT_update_desired_state(desired_state, d.endpointId, 'us-west-2')
        time.sleep(.25) # Wait a short time to allow preamp to change and reported state to be updated

        # Get state of endpoint
        jsonState = IOT_get_state(d.endpointId, 'us-west-2')
        reported = jsonState['state']['reported']

    ts = pyASH.get_utc_timestamp()
    properties = pyASH.Properties()
    p = pyASH.PowerStateProperty(reported['apower'],ts,0)
    properties.add(p)

    # Send report state back to Alexa
    return pyASH.Response(directive, properties)

def InputHandler(directive):
    d = pyASH.Directive(directive)

    # Get state of endpoint
    jsonState = IOT_get_state(d.endpointId, 'us-west-2')
    reported = jsonState['state']['reported']

    reported_input = reported['asource']


    if d.name == "SelectInput":
        try:
            requested_input = d.payload["input"]
        except KeyError:
            errmsg = 'SelectInput request contained no valid payload'
            logger.warn(errmsg)
            return pyASH.ErrorResponse('Alexa', 'INVALID_DIRECTIVE', errmsg, correlationToken=d.correlationToken)
        if requested_input not in VALID_INPUTS:
            errmsg = '{0} is not a valid input value'.format(requested_input)
            logger.warn(errmsg)
            return pyASH.ErrorResponse('Alexa', 'INVALID_VALUE', errmsg, correlationToken=d.correlationToken)
    else:
        errmsg = 'Received invalid directive for InputController.  Value was '+d.name
        logger.warn(errmsg)
        return pyASH.ErrorResponse('Alexa', 'INVALID_DIRECTIVE', errmsg, correlationToken=d.correlationToken)


    desired_state = { }
    if reported_input != requested_input:

        # If the input is TV, turn on the projector.  Otherwise turn it off.
        if requested_input == 'TV':
            desired_state['asource'] = 'SAT'
            desired_state['epower'] = True
        else:
            desired_state['asource'] = requested_input
            desired_state['epower'] = False

        # Issue command to preamp
        IOT_update_desired_state(desired_state, d.endpointId, 'us-west-2')
        time.sleep(.25) # Wait a short time to allow preamp to change and reported state to be updated

        # Get state of endpoint
        jsonState = IOT_get_state(d.endpointId, 'us-west-2')
        reported = jsonState['state']['reported']

    ts = pyASH.get_utc_timestamp()
    properties = pyASH.Properties()
    p = pyASH.InputProperty(reported['asource'],ts,0)
    properties.add(p)

    # Send report state back to Alexa
    return pyASH.Response(directive, properties)

# IOT functions
def IOT_update_desired_state(jsondata, thing, region):

    item = {
        'state': {
            'desired': jsondata
        }
    }
    # Send desired changes to shadow
    bdata = json.dumps(item).encode('utf-8')
    client = boto3.client('iot-data', region_name=region)
    response = client.update_thing_shadow(thingName=thing, payload = bdata)

def IOT_get_state(thing, region):
    client = boto3.client('iot-data', region_name=region)
    response = client.get_thing_shadow(thingName=thing)

    streamingBody = response["payload"]
    rawDataBytes = streamingBody.read()  # rawDataBytes is of type 'bytes' in, Python 3.x specific
    rawDataString = rawDataBytes.decode('utf-8')  # Python 3.x specific
    jsonState = json.loads(rawDataString)

    return jsonState

# Utility functions
def get_user_profile(user_token):
    payload = { 'access_token': user_token }
    r = requests.get("https://api.amazon.com/user/profile", params=payload)

    if r.status_code != 200:
        errmsg = 'get_user_id: unable to retrieve profile.  Return code was ' + str(r.status_code)
        logger.warn(errmsg)
        r.raise_for_status()

    user_id = ''
    user_email = ''
    user_name = ''
    try:
        user_id = r.json()['user_id']
        user_email = r.json()['email']
        user_name = r.json()['name']
    except KeyError:
        if user_id == '':
            errmsg = 'handle_authorization: requested profile but user_id not received'
        elif user_name == '' or user_email == '':
            errmsg = 'handle_authorization: requested profile but user_name or user_email not received'
        logger.warn(errmsg)

    return { 'user_id': user_id, 'email': user_email, 'name': user_name }
