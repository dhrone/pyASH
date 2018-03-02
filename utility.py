# -*- coding: utf-8 -*-

# Copyright 2018 by dhrone. All Rights Reserved.
#

import logging
import time
import uuid
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

LOGLEVEL = logging.WARN

logger = logging.getLogger(__name__)
logger.setLevel(LOGLEVEL)

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
    'Alexa.Cooking.TimeController': ['cookTime', 'cookingPowerLevel'],
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
REQUIRED_PROPERTIES = {
    'AdjustBrightness': 'brightness',
    'SetBrightness': 'brightness',
    'ChangeChannel': 'channel',
    'SkipChannels': 'channel',
    'SetColor': 'color',
    'DecreaseColorTemperature': 'colorTemperatureInKelvin',
    'IncreaseColorTemperature': 'colorTemperatureInKelvin',
    'SetColorTemperature': 'colorTemperatureInKelvin',
    'SetCookingMode': 'cookingMode', 'cookCompletionTime'
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
VALID_FOODQUANTITYTYPES=['WEIGHT', 'FOODCOUNT', 'VOLUME']
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
VALID_AUTHORIZATION_TYPES = ['BASIC','DIGEST','NONE']
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

DEFAULT_REGION = 'us-east-1'
DEFAULT_SYSTEM_NAME = 'pyASH'

# Utilities

# Custom Exceptions
class MissingCredential(Exception):
    pass

class MissingRequiredValue(Exception):
    pass

class FailedAuthorization(Exception):
    pass

class BadRequest(IOError):
    pass

class TokenMissing(Exception):
    pass

def get_utc_timestamp(seconds=None):
    return time.strftime("%Y-%m-%dT%H:%M:%S.", time.gmtime(seconds)) + str(time.time()).split('.')[1][:2] + 'Z'

def get_uuid():
    return str(uuid.uuid4())

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

    raise ValueError('{0} is not a valid interface'.format(interface))

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
    raise ValueError('{0} is not a valid directive for interface {1}.  Valid values are {2}'.format(directive, interface, directives))

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


class _classproperty(property):
    """Utility class for @property fields on the class."""
    def __init__(self, func):
        self.func = func
        self.__doc__ = func.__doc__

    def __get__(self, instance, owner):
        # This makes docstrings work
        if owner is Endpoint:
            return self
        return self.func(owner)

# Oauth2 utilities
def validateReturnCode(status_code):
    if status_code == 401:
        errmsg = 'Permission denied.  Unable to retrieve profile.'
        logger.warn(errmsg)
        raise FailedAuthorization(errmsg)
    elif status_code == 400:
        errmsg = 'Bad request.  Unable to retrieve profile.'
        logger.warn(errmsg)
        raise BadRequest(errmsg)
    elif status_code != 200:
        errmsg = 'Unable to retrieve profile.  Error code returned was {0}'.format(r.status_code)
        logger.warn(errmsg)
        raise IOError(errmsg)
    return status_code


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
