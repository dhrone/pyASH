# -*- coding: utf-8 -*-

# Copyright 2018 by dhrone. All Rights Reserved.
#

import logging
import time
import uuid
import os
import configparser
import requests
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

# Set up logging
LOGLEVEL = logging.WARN

logger = logging.getLogger(__name__)
logger.setLevel(LOGLEVEL)

# pyASH imports
from exceptions import *

DEFAULT_REGION = 'us-east-1'
DEFAULT_IOTREGION = 'us-west-2'
DEFAULT_SYSTEM_NAME = 'pyASH'

VALID_PROPERTIES = {
    'Alexa': [],
    'Alexa.Authorization': [],
    'Alexa.Discovery': [],
    'Alexa.BrightnessController': ['brightness'],
    'Alexa.Calendar': [],
    'Alexa.CameraStreamController': [],
    'Alexa.ChannelController': ['channel'],
    'Alexa.ColorController': ['color'],
    'Alexa.ColorTemperatureController': ['colorTemperatureInKelvin'],
    'Alexa.Cooking': ['cookingMode', 'cookCompletionTime', 'isCookCompletionTimeEstimated', 'cookStartTime', 'foodItem', 'isHolding' ],
    'Alexa.Cooking.TimeController': ['requestedCookTime', 'cookingPowerLevel'],
    'Alexa.Cooking.PresetController': ['presetName'],
    'Alexa.EndpointHealth': ['connectivity'],
    'Alexa.InputController': ['input'],
    'Alexa.LockController': ['lockState'],
    'Alexa.MeetingClientController': [],
    'Alexa.PercentageController': ['percentage'],
    'Alexa.PlaybackController': [],
    'Alexa.PowerController': ['powerState'],
    'Alexa.PowerLevelController': ['powerLevel'],
    'Alexa.SceneController': [],
    'Alexa.Speaker': ['volume', 'muted'],
    'Alexa.StepSpeaker': [],
    'Alexa.TemperatureSensor': ['temperature'],
    'Alexa.ThermostatController': ['targetSetpoint', 'lowerSetpoint', 'upperSetpoint', 'thermostatMode'],
    'Alexa.TimeHoldController': ['holdStartTime']
}

# If a directive is not included, it is assumed to not require any property
### Incomplete.  Not sure if I needs this
PROPERTIES_BY_DIRECTIVE = {
    'AdjustBrightness': 'brightness',
    'SetBrightness': 'brightness',
    'ChangeChannel': 'channel',
    'SkipChannels': 'channel',
    'SetColor': 'color',
    'DecreaseColorTemperature': 'colorTemperatureInKelvin',
    'IncreaseColorTemperature': 'colorTemperatureInKelvin',
    'SetColorTemperature': 'colorTemperatureInKelvin',
    'SetCookingMode': ['cookingMode', 'cookStartTime','cookCompletionTime', 'isCookCompletionTimeEstimated', 'foodItem' ],
    'CookByPreset': 'presetName',
    'CookByTime': ['requestedCookTime', 'cookingPowerLevel'],
    'TurnOn': 'powerState',
    'TurnOff': 'powerState'
}

VALID_DIRECTIVES = {
    'Alexa': ['ReportState'],
    'Alexa.Authorization': ['AcceptGrant'],
    'Alexa.Discovery': ['Discover'],
    'Alexa.BrightnessController': ['AdjustBrightness', 'SetBrightness'],
    'Alexa.Calendar': ['GetCurrentMeeting'],
    'Alexa.CameraStreamController': ['InitializeCameraStreams'],
    'Alexa.ChannelController': ['ChangeChannel', 'SkipChannels'],
    'Alexa.ColorController': ['SetColor'],
    'Alexa.ColorTemperatureController': ['DecreaseColorTemperature', 'IncreaseColorTemperature', 'SetColorTemperature'],
    'Alexa.Cooking': ['SetCookingMode'],
    'Alexa.Cooking.TimeController': ['CookByTime', 'AdjustCookTime'],
    'Alexa.Cooking.PresetController': ['CookByPreset'],
    'Alexa.EndpointHealth': [],
    'Alexa.InputController': ['SelectInput'],
    'Alexa.LockController': ['Lock', 'Unlock'],
    'Alexa.MeetingClientController': ['JoinMeeting', 'EndMeeting', 'JoinScheduledMeeting'],
    'Alexa.PercentageController': ['SetPercentage', 'AdjustPercentage'],
    'Alexa.PlaybackController': ['FastForward', 'Next', 'Pause', 'Play', 'Previous', 'Rewind', 'StartOver', 'Stop' ],
    'Alexa.PowerController': ['TurnOn', 'TurnOff'],
    'Alexa.PowerLevelController': ['SetPowerLevel', 'AdjustPowerLevel'],
    'Alexa.SceneController': ['Activate', 'Deactivate'],
    'Alexa.Speaker': ['SetVolume', 'AdjustVolume', 'SetMute'],
    'Alexa.StepSpeaker': ['AdjustVolume', 'SetMute'],
    'Alexa.TemperatureSensor': [],
    'Alexa.ThermostatController': ['SetTargetTemperature', 'AdjustTargetTemperature', 'SetThermostatMode'],
    'Alexa.ThermostatControllerSingle': ['SetTargetTemperature', 'AdjustTargetTemperature', 'SetThermostatMode'],
    'Alexa.ThermostatControllerDual': ['SetTargetTemperature', 'AdjustTargetTemperature', 'SetThermostatMode'],
    'Alexa.ThermostatControllerTriple': ['SetTargetTemperature', 'AdjustTargetTemperature', 'SetThermostatMode'],
    'Alexa.TimeHoldController': ['Hold', 'Resume']
}
VALID_INTERFACES =[]
for item in VALID_PROPERTIES:
    VALID_INTERFACES.append(item)
del (item)

VALID_COOKINGMODES = [ 'DEFROST', 'OFF', 'PRESET', 'REHEAT', 'TIMECOOK']
VALID_CONNECTIVITY = ['OK', 'UNREACHABLE']
VALID_ENUMERATEDPOWERLEVELS = ['LOW','MED_LOW', 'MEDIUM', 'MED_HIGH', 'HIGH']
VALID_FOODCOUNTSIZES = ['EXTRA_EXTRA_LARGE', 'JUMBO', 'EXTRA_LARGE', 'LARGE', 'MEDIUM', 'SMALL', 'EXTRA_SMALL', 'SIZE_A', 'SIZE_B']
VALID_FOODQUANTITYTYPES=['Weight', 'FoodCount', 'Volume']
VALID_VOLUMEUNITS = ['LITER', 'MILLILITER', 'TEASPOON', 'UK_GALLON', 'US_FLUID_GALLON', 'US_FLUID_OUNCE', 'US_DRY_GALLON', 'US_DRY_OUNCE' ]
VALID_WEIGHTUNITS = ['GRAM', 'KILOGRAM', 'OUNCE', 'POUND']
VALID_FOODCATEGORIES = ['BEEF', 'BEVERAGE', 'CHICKEN', 'FISH', 'MEAT', 'PASTA', 'PIZZA', 'POPCORN', 'PORK', 'POTATO', 'SHRIMP', 'SOUP', 'TURKEY', 'WATER', 'UNKNOWN']
VALID_LOCKSTATES = ['LOCKED', 'UNLOCKED', 'JAMMED']
VALID_TEMPERATURESCALES = ['CELSIUS', 'FAHRENHEIT', 'KELVIN']
VALID_TEMPERATURETYPES = ['targetSetpoint', 'lowerSetpoint', 'upperSetpoint', 'temperature']
VALID_THERMOSTATMODES = ['AUTO', 'COOL', 'HEAT', 'ECO', 'OFF', 'CUSTOM']
VALID_POWERSTATES = ['ON', 'OFF']
VALID_ERROR_TYPES = [ 'BRIDGE_UNREACHABLE', 'ENDPOINT_BUSY', 'ENDPOINT_LOW_POWER', 'ENDPOINT_UNREACHABLE', 'EXPIRED_AUTHORIZATION_CREDENTIAL', 'FIRMWARE_OUT_OF_DATE', 'HARDWARE_MALFUNCTION', 'INTERNAL_ERROR', 'INVALID_AUTHORIZATION_CREDENTIAL', 'INVALID_DIRECTIVE', 'INVALID_VALUE', 'NO_SUCH_ENDPOINT', 'NOT_SUPPORTED_IN_CURRENT_MODE', 'RATE_LIMIT_EXCEEDED', 'TEMPERATURE_VALUE_OUT_OF_RANGE', 'VALUE_OUT_OF_RANGE', 'ACCEPT_GRANT_FAILED']
VALID_TIMETYPE = ['cookCompletionTime', 'cookStartTime']
VALID_DURATIONS = ['cookDuration', 'cookDurationDelta', 'cookTime']
VALID_AUTHORIZATION_TYPES = ['BASIC','DIGEST','NONE', 'BEARER']
VALID_VIDEO_CODECS = ['H264', 'MPEG2', 'MJPEG', 'JPG']
VALID_AUDIO_CODECS = ['G711', 'AAC', 'NONE']
VALID_PAYLOADVERSIONS = ['2', '3']

VALID_TERMS = [ VALID_COOKINGMODES, VALID_CONNECTIVITY, VALID_ENUMERATEDPOWERLEVELS,
    VALID_FOODCOUNTSIZES, VALID_FOODQUANTITYTYPES, VALID_VOLUMEUNITS, VALID_WEIGHTUNITS,
    VALID_FOODCATEGORIES, VALID_LOCKSTATES, VALID_TEMPERATURESCALES, VALID_TEMPERATURETYPES,
    VALID_THERMOSTATMODES, VALID_POWERSTATES, VALID_ERROR_TYPES, VALID_TIMETYPE,
    VALID_DURATIONS, VALID_AUTHORIZATION_TYPES, VALID_VIDEO_CODECS, VALID_AUDIO_CODECS,
    VALID_PAYLOADVERSIONS
]



# Utilities



def get_utc_timestamp(seconds=None):
    return time.strftime("%Y-%m-%dT%H:%M:%S.", time.gmtime(seconds)) + str(time.time()).split('.')[1][:2] + 'Z'

def get_uuid():
    return str(uuid.uuid4())

# Derived from Tin Can Python (https://github.com/RusticiSoftware/TinCanPython)
# Modified to support negative values and fixed what I think was a bug in the rstrip call for fractional seconds
def iso8601(value):
    # split seconds to larger units
    negative= False if value.total_seconds() >= 0 else True
    seconds = -value.total_seconds() if negative else value.total_seconds()
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    days, hours, minutes = map(int, (days, hours, minutes))
    seconds = round(seconds, 6)
    ## build date
    date = ''
    if days:
        date = '%sD' % days if not negative else '-%sD' % days
    ## build time
    time = u'T' if date else u'T' if not negative else u'T-'
    # hours
    bigger_exists = date or hours
    if bigger_exists:
        time += '{:01}H'.format(hours)
    # minutes
    bigger_exists = bigger_exists or minutes
    if bigger_exists:
      time += '{:01}M'.format(minutes)
    # seconds
    if seconds.is_integer():
        seconds = '{:01}'.format(int(seconds))
    else:
        # 9 chars long w/leading 0, 6 digits after decimal
        seconds = '%09.6f' % seconds
        # remove trailing zeros
        seconds = seconds.rstrip('0')
    time += '{}S'.format(seconds)
    return u'P' + date + time

# The fix_xxx functions clean up capitalization issues with interfaces, directives, properties and terms
# as these need to be exactly what Alexa Smart Home is expecting and are very easy to get wrong
# They will log the action though so that you can clean the requests up later if desired.
def fix_interface(interface):
    if interface[:6] != 'Alexa.' and interface != 'Alexa':
        interface = 'Alexa.' + interface
    if interface in VALID_DIRECTIVES:
        return interface

    for i in VALID_DIRECTIVES:
        if i.lower() == interface.lower():
            logger.warn('Adjusted interface from {0} to {1}'.format(interface, i))
            return i

    raise INVALID_DIRECTIVE('{0} is not a valid interface'.format(interface))

def fix_directive(interface, directive):
    interface = fix_interface(interface)

    if directive in VALID_DIRECTIVES[interface]:
        return directive

    directives = ''
    for d in VALID_DIRECTIVES[interface]:
        directives += '{0}, '.format(d)
        if d.lower() == directive.lower():
            logger.warn('Adjusted directive from {0} to {1}'.format(directive, d))
            return d
    directives = directives[:len(directives)-2] if len(directives)>=2 else directives
    raise INVALID_DIRECTIVE('{0} is not a valid directive for interface {1}.  Valid values are {2}'.format(directive, interface, directives))

def fix_property(interface, property):
    interface = fix_interface(interface)

    if property in VALID_PROPERTIES[interface]:
        return property

    if not VALID_PROPERTIES[interface] and not property:
        return property

    properties = ''
    for p in VALID_PROPERTIES[interface]:
        properties += '{0}, '.format(p)
        if p.lower() == property.lower():
            logger.warn('Adjusted property from {0} to {1}'.format(property, p))
            return p
    properties = properties[:len(properties)-2] if len(properties)>=2 else properties
    raise ValueError('{0} is not a valid property for interface {1}.  Valid values are {2}'.format(property, interface, properties))

def fix_term(term):
    for ti in VALID_TERMS:
        for i in ti:
            if term.lower() == i.lower():
                if term != i:
                    logger.warn('Adjusted term from {0} to {1}'.format(term, i))
                return i
    raise ValueError('{0} not a valid term'.format(term))


# Oauth2 utilities
def validateReturnCode(response):
    error = response.json().get('error')
    error_description = response.json().get('error_description')

    if response.status_code in [401,403,405]:
        raise OAUTH2_PermissionDenied(error, error_description)
    elif response.status_code == 400:
        raise EXPIRED_AUTHORIZATION_CREDENTIAL(error, error_description)
    elif response.status_code != 200:
        raise OAUTH2_IOError(error, error_description)
    return response.status_code

def validateValue(value, validList, errmsg=None):
    if value.upper() in map(str.upper, validList):
        return list(filter(lambda x: x.upper() == value.upper(), validList))[0]
    errmsg = errmsg if type(errmsg) == str else '{0} is not a valid value'
    raise ValueError(errmsg.format(value))

def getUserProfile(accessToken):
    payload = { 'access_token': accessToken }
    r = requests.get("https://api.amazon.com/user/profile", params=payload)
    validateReturnCode(r)
    return r.json()

def _getOauth2Credentials():
    try:
        # Try to get credentials from environmental variables
        oauth2_client_id = os.environ['oauth2_client_id']
        oauth2_client_secret = os.environ['oauth2_client_secret']
    except KeyError:
        oauth2_client_id = None
        oauth2_client_secret = None

    if not oauth2_client_id or not oauth2_client_secret:
        try:
            # Try to get them from the pyASH config file
            config = configparser.ConfigParser()
            config.read('./.pyASH/config')
            oauth2_client_id = config['DEFAULT']['oauth2_client_id']
            oauth2_client_secret = config['DEFAULT']['oauth2_client_secret']
        except:
            errmsg = 'Unable to retrieve oauth2 credentials.  Must set oauth2_client_id and oauth2_client_secret as environment variables or within the pyASH config file'
            logger.critical(errmsg)
            raise OAUTH2_CredentialMissing(errmsg)
    return (oauth2_client_id, oauth2_client_secret)

def refreshAccessToken(refreshToken):
    oauth2_client_id, oauth2_client_secret = _getOauth2Credentials()

    payload = {
        'grant_type':'refresh_token',
        'client_id':oauth2_client_id,
        'client_secret':oauth2_client_secret,
    }

    r = requests.post("https://api.amazon.com/auth/o2/token", data=payload)
    validateReturnCode(r)

    try:
        return r.json()
    except KeyError:
        errmsg = 'Tokens not in response'
        logger.warn(errmsg)
        raise TokenMissingException(errmsg)

def getAccessTokenFromCode(code):
    oauth2_client_id, oauth2_client_secret = _getOauth2Credentials()

    payload = {
        'grant_type':'authorization_code',
        'code': d.code,
        'client_id':oauth2_client_id,
        'client_secret':oauth2_client_secret,
    }

    r = requests.post("https://api.amazon.com/auth/o2/token", data=payload)
    validateReturnCode(r)

    return r.json()
