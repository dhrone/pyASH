# -*- coding: utf-8 -*-

# Copyright 2018 by dhrone. All Rights Reserved.
#

import json
from datetime import datetime
from datetime import timedelta

from utility import *

# Setup logger
import logging
logger = logging.getLogger(__name__)
logger.setLevel(LOGLEVEL)


# Standard Response.  List of namespaces handled in VALID_SIMPLEINTERFACES
VALID_SIMPLEINTERFACES = ['Alexa.BrightnessController', 'Alexa.ChannelController',\
    'Alexa.Cooking', 'Alexa.InputController', 'Alexa.LockController', \
    'Alexa.PercentageController', 'Alexa.PlaybackController', 'Alexa.PowerController', \
    'Alexa.PowerLevelController', 'Alexa.Speaker', 'Alexa.StepSpeaker', 'Alexa.TemperatureSensor',\
    'Alexa.ThermostatController', 'Alexa.TimeHoldController']


# PropertyElement classes -- These classes help properly format property values
# They are largely used in the Property classes but also the Request class
class PropertyElement(object):
    def __init__(self):
        self.name = ''
        self.value = { }

    def __str__(self):
        json = { 'name': self.name, 'value': self.value}
        return json.dumps(json, indent=4)

class Brightness(PropertyElement):
    def __init__(self, value=None, json=None):
        super(Brightness, self).__init__()

        if type(json) == dict:
            value = json.get('value')

        if type(value) != int:
            raise TypeError('Brightness value must be an integer.  Received a '+str(type(value)))
        self.name = 'brightness'
        self.value = value

class Channel(PropertyElement):
    def __init__(self, number=None, callSign=None, affiliateCallSign=None, uri=None, json=None):
        super(Channel, self).__init__()

        if type(json) == dict:
            self.number = json.get('number')
            self.callSign = json.get('callSign')
            self.affiliateCallSign = json.get('affiliateCallSign')
            self.uri = json.get('uri')
        else:
            self.number = number
            self.callSign = callSign
            self.affiliateCallSign = affiliateCallSign
            self.uri = uri

        if type(self.number) != str:
            raise TypeError('number must be a string.  Received a ' + str(type(self.number)))
        if type(self.callSign) != str:
            raise TypeError('callSign must be a string.  Received a '+ str(type(self.callSign)))
        if type(self.affiliateCallSign) != str:
            raise TypeError('affiliateCallSign must be a string.  Received a '+str(type(self.affiliateCallSign)))
        if self.uri:
            if type(self.uri) != str:
                raise TypeError('uri must be a string.  Received a '+str(type(self.uri)))

        self.name = 'channel'
        self.value = {
            'number': self.number,
            'callSign': self.callSign,
            'affiliateCallSign': self.affiliateCallSign,
        }
        if self.uri:
            self.value['uri'] = self.uri

class Color(PropertyElement):
    def __init__(self, hue=None, saturation=None, brightness=None, json=None):
        super(Color, self).__init__()

        if type(json) == dict:
            self.hue = float(json.get('hue'))
            self.saturation = float(json.get('saturation'))
            self.brightness = float(json.get('brightness'))
        else:
            self.hue = float(hue) if type(hue) == int else hue
            self.saturation = float(saturation) if type(saturation) == int else saturation
            self.brightness = float(brightness) if type(brightness) == int else brightness

        if type(self.hue) != float:
            raise TypeError('Color hue value must be a float.  Received a {0}'.format(str(type(self.hue))))
        if type(self.saturation) != float:
            raise TypeError('Color saturation value must be a float.  Received a {0}'.format(str(type(self.saturation))))
        if type(self.brightness) != float:
            raise TypeError('Color brightness value must be a float.  Received a {0}'.format(str(type(self.brightness))))

        self.name = 'color'
        self.value = { 'hue': hue, 'saturation': saturation, 'brightness': brightness}

class ColorTemperatureInKelvin(PropertyElement):
    def __init__(self, value=None, json=None):
        super(ColorTemperatureInKelvin, self).__init__()

        if type(json) == dict:
            value = json.get('value')

        if type(value) != int:
            raise TypeError('ColorTemperatureInKelvin value must be an integer.  Received a {0}'.format(str(type(value))))
        self.name = 'colorTemperatureInKelvin'
        self.value = value

class CookingMode(PropertyElement):
    def __init__(self, value=None, json=None):
        super(CookingMode, self).__init__()

        if type(json) == dict:
            self.value = json.get('value')
        else:
            self.value = value

        if type(self.value) != str:
            raise TypeError('Cooking mode must be a string value.  Received a '+str(type(self.value)))
        if self.value.upper() not in VALID_COOKINGMODES:
            raise ValueError(self.value.upper() + ' is not a valid cooking mode')
        self.name = 'CookingMode'
        self.value = value.upper()

class CookingHolding(PropertyElement):
    def __init__(self, value=None, json=None):
        super(CookingHolding, self).__init__()

        if type(json) == dict:
            value = json.get('value')

        if type(value) != bool:
            raise TypeError('CookingHolding must be a boolean value.  Received a '+str(type(value)))
        self.name = 'isHolding'
        self.value = value

class CookingPreset(PropertyElement):
    def __init__(self, value=None, json=None):
        super(CookingHolding, self).__init__()

        if type(json) == dict:
            value = json.get('value')

        if type(value) != str:
            raise TypeError('CookingPreset must be a string value.  Received a '+str(type(value)))
        self.name = 'presetName'
        self.value = value

class Connectivity(PropertyElement):
    def __init__(self, value=None, json=None):
        super(Connectivity, self).__init__()

        if type(json) == dict:
            value = json.get('value')

        if type(value) != str:
            raise TypeError('Connectivity must be a string value.  Received a '+str(type(value)))
        if value.upper() not in VALID_CONNECTIVITY:
            raise ValueError(value.upper() + ' is not a valid connectivity value')
        self.name = 'connectivity'
        self.value = { 'value': value.upper() }

class DateTime(PropertyElement):
    def __init__(self, value=None, name=None, json=None):

        if type(json) == dict:
            value = json.get('value')
            name = json.get('name')
        if not type(value) is datetime:
            raise TypeError('Datetime must be a UTC datetime value.  Received a '+str(type(value)))
        if name not in VALID_TIMETYPE:
            raise ValueError(name.upper() + ' is not a valid datetime type')

        super(DateTime, self).__init__()
        self.name = name
        self.value = value.isoformat().split('.')[0]+'Z'

class Duration(PropertyElement):

    # ACTION: add json functionality

    def __init__(self, value, name):
        super(Duration, self).__init__()
        if not type(value) is timedelta:
            raise TypeError('Duration must be a timedelta value.  Received a '+str(type(value)))
        if name not in VALID_DURATIONS:
            raise ValueError('{0} is not a valid duration type'.format(name))

        self.name = name

        total_seconds = value.total_seconds()

        if total_seconds < 0:
            days = int(total_seconds/86400)
            rs = total_seconds-(days*86400)
            hours = int(rs/3600)
            rs = rs - (hours*3600)
            minutes = int(rs/60)
            rs = rs - (minutes*60)
            seconds = int(rs)
        else:
            days = int(total_seconds/86400)
            hours = int(value.seconds/3600)
            minutes = int(value.seconds%3600/60)
            seconds = int(value.seconds%3600%60)

        if abs(days) > 0:
            self.value = 'PT{0}D{1}H{2}M{3}S'.format(days, hours, minutes, seconds)
        elif abs(hours) > 0:
            self.value = 'PT{0}H{1}M{2}S'.format(hours, minutes, seconds)
        elif abs(minutes) > 0:
            self.value = 'PT{0}M{1}S'.format(minutes, seconds)
        elif abs(seconds) > 0:
            self.value = 'PT{0}S'.format(seconds)
        else:
            self.value = 'PT0S'

class FoodItem(PropertyElement):
    def __init__(self, foodName=None, foodCategory=None, foodQuantity=None, json=None):
        super(FoodItem, self).__init__()

        if type(json) == dict:
            self.foodName = json.get('foodName')
            self.foodCategory = json.get('foodCategory')
            self.foodQuantity = FoodQuantity(json.get('foodQuantity'))
        else:
            self.foodName = foodName
            self.foodCategory = foodCategory
            self.foodQuantity = foodQuantity

        if foodCategory not in VALID_FOODCATEGORIES:
            raise ValueError('{0} is not a valid food category'.format(foodCategory))
        if foodQuantity:
            if not isinstance(foodQuantity, FoodQuantity):
                raise TypeError('foodQuantity must be a valid FoodQuantity object.  Type provided was {0}'.format(type(foodQuantity)))

        self.name = 'foodItem'
        self.value = {
            'foodName': self.foodName,
            'foodCategory': self.foodCategory,
        }
        if foodQuantity:
            self.value['foodQuantity'] = self.foodQuantity.get_json()

# FoodQuantity, FoodCountFoodQuantity, VolumeFoodQuantity and WeightFoodQuantity
# are used within FoodItem property values
class FoodQuantity():
    def __init__(self, type=None, value=None, size=None, unit=None, json=None):

        if type(json) == dict:
            self.value = json.get('value')
            self.unit = json.get('unit')
            self.size = json.get('size')
            self.type = json.get('@type')
        else:
            self.value = value
            self.unit = unit
            self.size = size
            self.type = type

        if self.type.upper() not in VALID_FOODQUANTITYTYPES:
            raise TypeError(self.type.upper() + ' is not a valid Food quantity type')

        if self.type.upper() == 'FOODCOUNT':
            self.json = FoodCountFoodQuantity(self.value, self.size).get_json()
        elif self.type.upper() == 'WEIGHT':
            self.json = WeightFoodQuantity(self.value, self.unit).get_json()
        else:
            self.json = VolumeFoodQuantity(self.value, self.unit).get_json()

class FoodCountFoodQuantity():
    def __init__(self, value, size=''):

        if size:
            if size.upper() not in VALID_FOODCOUNTSIZES:
                raise ValueError( size.upper() + ' is not a valid food count size')
            self.json = { '@type': 'FoodCount', 'value': value, 'size': size.upper() }
        else:
            self.json = { '@type': 'FoodCount', 'value':value }

        self.size = size
        self.value = value

class VolumeFoodQuantity():
    def __init__(self, value, unit):
        if unit.upper() not in VALID_VOLUMEUNITS:
            raise ValueError(unit.upper() + 'is not a valid volume unit')
        self.json = { '@type': 'Volume', 'value': value, 'unit': unit.upper() }
        self.value = value
        self.unit = unit

class WeightFoodQuantity():
    def __init__(self, value, unit):

        if unit.upper() not in VALID_WEIGHTUNITS:
            raise ValueError(unit.upper() + ' is not a valid weight unit'.a)

        self.json = { '@type': 'Weight', 'value': value, 'unit': unit.upper() }
        self.value = value
        self.unit = unit

class IsCookCompletionTimeEstimated(PropertyElement):
    def __init__(self, value=None, json=None):
        super(CookCompletionTimeEstimated, self).__init__()

        if type(json) == dict:
            value = json.get('value')
        if type(value) != bool:
            raise TypeError('IsCookCompletionTimeEstimated must be a boolean value.  Received a '+str(type(value)))
        self.name = 'isCookCompletionTimeEstimated'
        self.value = value

class Input(PropertyElement):
    def __init__(self, value=None, json=None):
        super(Input, self).__init__()

        if type(json) == dict:
            value = json.get('value')
        if type(value) != str:
            raise TypeError('Input must be a string value.  Received a '+str(type(value)))
        self.name = 'input'
        self.value = value.upper()

class LockState(PropertyElement):
    def __init__(self, value=None, json=None):
        super(LockState, self).__init__()

        if type(json) == dict:
            value = json.get('value')
        if type(value) != str:
            raise TypeError('LockState must be a string value.  Received a '+str(type(value)))
        if value.upper() not in VALID_LOCKSTATES:
            raise ValueError(value.upper() + ' is not a valid lock state value')
        self.name = 'lockState'
        self.value = value.upper()

class MuteState(PropertyElement):
    def __init__(self, value=None, json=None):
        super(MuteState, self).__init__()

        if type(json) == dict:
            value = json.get('value')
        if type(value) != bool:
            raise TypeError('MuteState must be a boolean value.  Received a '+str(type(value)))
        self.name = 'muted'
        self.value = value

class Percentage(PropertyElement):
    def __init__(self, value=None, json=None):
        super(Percentage, self).__init__()

        if type(json) == dict:
            value = json.get('value')
        if type(value) != int:
            raise TypeError('Percentage must be an integer value.  Received a '+str(type(value)))
        self.name = 'percentage'
        self.value = value

class PowerState(PropertyElement):
    def __init__(self, value=None, json=None):
        super(PowerState, self).__init__()

        if type(json) == dict:
            value = json.get('value')
        if type(value) != str:
            if type(value) != bool:
                raise TypeError('PowerState must be a string or boolean value.  Received a '+str(type(value)))
        if type(value) == bool:
            if value:
                self.value = VALID_POWERSTATES[0]
            else:
                self.value = VALID_POWERSTATES[1]
        else:
            if value.upper() not in VALID_POWERSTATES:
                raise ValueError(value.upper() + ' is not a valid power state value')
            self.value = value

        self.name = 'powerState'

class PowerLevel(PropertyElement):
    def __init__(self, pvalue=None, json=None):
        super(PowerLevel, self).__init__()

        if type(json) == dict:
            self.type = dict.get('@type')
            self.pvalue = dict.get('value')

        if type(pvalue) == int:
            object = IntegralPowerLevel(pvalue)
        elif type(value) == str:
            object = EnumeratedPowerLevel(pvalue)
        else:
            object = pvalue

        if not isinstance(object, EnumeratedPowerLevel) and not isinstance(object, IntegralPowerLevel):
            raise TypeError('Power level must be either a EnumeratedPowerLevel object or a IntegralPowerLevel object.  Received ' + str(type(object)))

        self.value = object.value
        self.name = 'powerLevel'

class EnumeratedPowerLevel():
    def __init__(self, pvalue):
        super(EnumeratedPowerLevel, self).__init__()
        if type(pvalue) != str:
            raise TypeError('EnumeratedPowerLevel must be a string value.  Received a '+str(type(pvalue)))
        if pvalue.upper() not in VALID_ENUMERATEDPOWERLEVELS:
            raise ValueError(value.upper() + ' is not a valid EnumeratedPowerLevel value')
        self.name = 'EnumeratedPowerLevel'
        self.value = { '@type': self.name, 'value': self.pvalue }

class IntegralPowerLevel():
    def __init__(self, pvalue):
        super(IntegralPowerLevel, self).__init__()
        if type(pvalue) != int:
            raise TypeError('IntegralPowerLevel must be an integer value.  Received a '+str(type(pvalue)))
        self.name = 'IntegralPowerLevel'
        self.value = { '@type': self.name, 'value': self.value }

class Scope(PropertyElement):
    def __init__(self, stype='', token='', partition='', userId='', json=None):
        super(Scope, self).__init__()

        if type(json) == dict:
            self.stype = json.get('type')
            self.token = json.get('token')
            self.partition = json.get('partition')
            self.userId = json.get('userId')
        else:
            self.stype = stype
            self.token = token
            self.partition = partition
            self.userId = userId

        if type(self.stype) != str:
            raise TypeError('Scope type must be a string.  Received a ' + str(type(self.stype)))
        if type(self.token) != str:
            raise TypeError('Scope token must be a string.  Received a '+ str(type(self.token)))
        if type(self.partition) != str and self.partition:
            raise TypeError('If provided, scope partition must be a string.  Received a '+str(type(self.partition)))
        if type(self.userId) != str and self.userId:
            raise TypeError('If provided, scope userId must be a string.  Received a '+str(type(self.userId)))

        self.name = 'scope'
        self.value = { }
        self.value['type'] = self.stype
        self.value['token'] = self.token
        if self.partition:
            self.value['partition'] = self.partition
        if self.userId:
            self.value['userId'] = self.userId

class Temperature(PropertyElement):
    def __init__(self, value=None, scale=None, name=None, json=None):
        super(Temperature, self).__init__()

        if type(json) == dict:
            value = json.get('value')
            scale = json.get('scale')
            name = json.get('name')

        if not type(value) == int and not type(value) == float:
            raise TypeError('Temperature value must be a number.  Received a '+str(type(value)))
        if type(scale) != str:
            raise TypeError('Temperature scale must be a string.  Received a '+str(type(scale)))
        if scale.upper() not in VALID_TEMPERATURESCALES:
            raise ValueError(scale.upper() + ' is not a valid temperature scale')
        if name not in VALID_TEMPERATURETYPES:
            raise ValueError(str(name) + ' is not a valid temperature type')

        self.name = name
        self.value = { 'value': float(value), 'scale': scale.upper() }

class ThermostatMode(PropertyElement):
    def __init__(self, value='', customName='', json=None):
        super(ThermostatMode, self).__init__()

        if type(json) == dict:
            self.value = json.get('value')
            self.customName = json.get('customName')
        else:
            self.value = value
            self.customName = customName

        if type(self.value) != str:
            raise TypeError('ThermostatMode must be a string value.  Received a '+str(type(value)))
        if type(customName) != str:
            raise TypeError('Custom names for a thermostat mode must be a string value.  Received a '+str(type(customName)))
        if value.upper() not in VALID_THERMOSTATMODES:
            raise ValueError(value.upper() + ' is not a valid thermostat mode')

        self.name = 'thermostatMode'
        self.value = value.upper()
        if customName:
            self.value = {
                'value': value.upper(),
                'customName': self.customName
            }

class VolumeLevel(PropertyElement):
    def __init__(self, value=None, json=None):
        super(VolumeLevel, self).__init__()

        if type(json) == dict:
            value = json.get('value')
        if type(value) != int:
            raise TypeError('VolumeLevel must be an integer value.  Received a '+str(type(value)))
        self.name = 'volume'
        self.value = value

class Resolution():
    def __init__(self, width, height):
        if type(width) != int:
            raise TypeError('Width for a resolution must be an integer.  Received a '+str(type(width)))
        if type(height) != int:
            raise TypeError('Height for a resolution must be an integer.  Received a '+str(type(height)))

        self.name = 'resolution'
        self.width = width
        self.height = height
        self.value = {
            'width': width,
            'height': height
        }

class CameraStreamConfigurations():
    def __init__(self, camerastreamConfiguration=None):
        self.value = []

        if camerastreamConfiguration:
            self.add(CameraStreamConfiguration)

    def add(self, camerastreamConfiguration):
        if not isinstance(camerastreamConfiguration, CameraStreamConfiguration):
            raise TypeError('CameraStreamConfigurations only accepts CameraStreamConfiguration objects.  Received a ' + str(type(camerastreamConfiguration)))

        self.value.append(camerastreamConfiguration.value)


class CameraStreamConfiguration():
    def __init__(self, protocol=None, resolution=None, authorizationType=None,videoCodec=None,audioCodec=None,width=None,height=None):
        self.protocols = []
        self.resolutions = []
        self.authorizationTypes = []
        self.videoCodecs = []
        self.audioCodecs = []
        self.value = {}

        if protocol:
            self.addProtocol(protocol)
        if resolution or (width and height):
            if resolution:
                self.addResolution(resolution)
            else:
                self.addResolution(width=width, height=height)
        if authorizationType:
            self.addAuthorizatonType(authorizationType)
        if videoCodec:
            self.addVideoCodec(videoCodec)
        if audioCodec:
            self.addAudioCodec(audioCodec)

    def addProtocol(self, protocol):
        if type(protocol) == list:
            for item in protocol:
                self.addProtocol(item)
        else:
            if type(protocol) != str:
                raise TypeError('CameraStream protocol must be a string.  Received a '+str(type(protocol)))
            self.protocols.append(protocol)
            self.value['protocols'] = self.protocols

    def addResolution(self, resolution=None, width=None, height=None):
        if not resolution:
            resolution = Resolution(width, height)
        if type(resolution) == list:
            for item in resolution:
                self.addResolution(item)
        else:
            if isinstance(resolution, Resolution):
                self.resolutions.append(resolution.value)
            else:
                raise TypeError('CameraStream resolution must be either an instance of Resolution or integers expressing a width and a height')
            self.value['resolutions'] = self.resolutions

    def addAuthorizatonType(self, authorizationType):
        if type(authorizationType) == list:
            for item in authorizationType:
                self.addAuthorizatonType(item)
        else:
            if authorizationType in VALID_AUTHORIZATION_TYPES:
                self.authorizationTypes.append(authorizationType)
            else:
                raise ValueError('{0} is not a valid CameraStream authorizationType'.format(authorizationType))
            self.value['authorizationTypes'] = self.authorizationTypes

    def addVideoCodec(self, videoCodec):
        if type(videoCodec) == list:
            for item in videoCodec:
                self.addVideoCodec(item)
        else:
            if videoCodec in VALID_VIDEO_CODECS:
                self.videoCodecs.append(videoCodec)
            else:
                raise ValueError('{0} is not a valid CameraStream video codec'.format(videoCodec))
            self.value['videoCodecs'] = self.videoCodecs

    def addAudioCodec(self, audioCodec):
        if type(audioCodec) == list:
            for item in audioCodec:
                self.addAudioCodec(item)
        else:
            if audioCodec in VALID_AUDIO_CODECS:
                self.audioCodecs.append(audioCodec)
            else:
                raise ValueError('{0} is not a valid CameraStream audio codec'.format(audioCodec))
            self.value['audioCodecs'] = self.audioCodecs

class CameraStreamsPayload():
    def __init__(self, camerastreams, imageUri=None):
        self.value = []

        if not isinstance(camerastreams, CameraStreams):
            raise TypeError('CameraStreamsPayload only accepts a CameraStreams object.  Received a ' + str(type(camerastreams)))

        self.value = {
            'cameraStreams': camerastreams.value,
        }
        if imageUri:
            if type(imageUri) != str:
                TypeError('imageUri if provided must be a string.  Received a '+str(type(imageUri)))
            self.value['imageUri'] = imageUri

class CameraStreams():
    def __init__(self, camerastream = None):
        self.value = []

        if isinstance(camerastream, CameraStream):
            self.add(camerastream)

    def add(self, camerastream):
        if not isinstance(camerastream, CameraStream):
            raise TypeError('CameraStreams can only add CameraStream objects.  Received a ' + str(type(camerastream)))

        self.value.append(camerastream.value)

class CameraStream():
    def __init__(self, protocol=None, resolution=None, authorizationType=None, videoCodec=None, audioCodec=None, uri=None, expirationTime=None, idleTimeoutSeconds=None, json=None):

        if type(json) == dict:
            self.protocol = json.get('protocol')
            self.authorizationType = json.get('authorizationType')
            self.videoCodec = json.get('videoCodec')
            self.audioCodec = json.get('audioCodec')
            self.uri = json.get('uri')
            self.expirationTime = json.get('expirationTime')
            self.idleTimeoutSeconds = json.get('idleTimeoutSeconds')
            if 'resolution' not in json:
                raise TypeError('Resolution object not provided')
            self.width = json['resolution'].get('width')
            self.height = json['resolution'].get('height')
            if not self.width or not self.height:
                TypeError('Resolution must contain width and height values')
            self.resolution = Resolution(self.width, self.height)
        else:
            self.protocol = protocol
            self.authorizationType = authorizationType
            self.videoCodec = videoCodec
            self.audioCodec = audioCodec
            self.uri = uri
            self.expirationTime = expirationTime
            self.idleTimeoutSeconds = idleTimeoutSeconds
            if not resolution:
                raise TypeError('Resolution object not provided')
            if not isinstance(resolution, Resolution):
                raise TypeError('Resolution must be a resolution object.  Received a '+str(type(resolution)))
            self.width = resolution.width
            self.height = resolution.height
            if not self.width or not self.height:
                TypeError('Resolution must contain width and height values')
            self.resolution = resolution

        if type(self.protocol) != str:
            raise TypeError('protocol must be a string.  Received a ' + str(type(self.protocol)))
        if not isinstance(self.resolution, Resolution):
            raise TypeError('resolution must be a Resolution object.  Received a '+ str(type(self.resolution)))
        if type(self.authorizationType) != str:
            raise TypeError('authorizationType must be a string.  Received a '+ str(type(self.authorizationType)))
        if type(self.videoCodec) != str:
            raise TypeError('videoCodec must be a string.  Received a '+str(type(self.videoCodec)))
        if type(self.audioCodec) != str:
            raise TypeError('audioCodec must be a string.  Received a '+str(type(self.audioCodec)))
        if self.uri:
            if type(self.uri) != str:
                raise TypeError('Uri if provided must be a string.  Received a '+str(type(self.uri)))
        if self.expirationTime:
            if type(self.expirationTime) != str:
                raise TypeError('expirationTime if provided must be a string.  Received a '+str(type(self.expirationTime)))
        if self.idleTimeoutSeconds:
            if type(self.idleTimeoutSeconds) != int:
                raise TypeError('idleTimeoutSeconds if provided must be an integer.  Received a '+str(type(self.idleTimeoutSeconds)))
        if self.authorizationType not in VALID_AUTHORIZATION_TYPES:
            raise ValueError('{0} is not a valid authorization type'.format(self.authorizationType))
        if self.videoCodec not in VALID_VIDEO_CODECS:
            raise ValueError('{0} is not a valid video codec'.format(self.videoCodec))
        if self.audioCodec not in VALID_AUDIO_CODECS:
            raise ValueError('{0} is not a valid audio codec'.format(self.audioCodec))

        self.name = 'cameraStream'
        self.value = {
            'protocol': self.protocol,
            'resolution': self.resolution.value,
            'authorizationType': self.authorizationType,
            'videoCodec': self.videoCodec,
            'audioCodec': self.audioCodec
        }
        if self.uri:
            self.value['uri'] = self.uri
        if self.expirationTime:
            self.value['expirationTime'] = self.expirationTime
        if self.idleTimeoutSeconds:
            self.value['idleTimeoutSeconds'] = self.idleTimeoutSeconds

class ChannelMetadata():
    def __init__(self, name='', image='', json=None):

        if type(json) == dict:
            self.name = json.get('name')
            self.image = json.get('image')
        else:
            self.name = name
            self.image = image

        if type(self.name) != str:
            raise TypeError('ChannelMetadata name must be a string.  Received a ' + str(type(str.name)))
        if type(self.image) != str:
            raise TypeError('ChannelMetadata image must be a string.  Received a '+ str(type(self.image)))

        self.name = 'ChannelMetadata'
        self.value = {
            'name': self.name,
            'image': self.image,
        }


# Property classes -- Used to return a specific property within a response
# Used in a ReportState responses or when reporting state after handling a directive
class Property(object):
    def __init__(self, namespace, propertyelement, timeOfSample, uncertaintyInMilliseconds):
        self.json = {}
        self.json['namespace'] = namespace
        self.json['timeOfSample'] = timeOfSample
        self.json['uncertaintyInMilliseconds'] = uncertaintyInMilliseconds
        self.json['name'] =  propertyelement.name
        self.json['value'] = propertyelement.value
#        elif 'powerLevel' in propertyelement.get_json():
#            self.json['value'] = propertyelement.get_json()

    def get_json(self):
        return self.json

    def __str__(self):
        return json.dumps(self.json, indent=4)

class BrightnessProperty(Property):
    def __init__(self, value, timeOfSample, uncertaintyInMilliseconds):
        pe = Brightness(value)
        super(BrightnessProperty, self).__init__('Alexa.BrightnessController', pe, timeOfSample, uncertaintyInMilliseconds)

class ChannelProperty(Property):
    def __init__(self, number, callSign, affiliateCallSign, timeOfSample, uncertaintyInMilliseconds):
        pe = Channel(number, callSign, affiliateCallSign)
        super(ChannelProperty, self).__init__('Alexa.ChannelController', pe, timeOfSample, uncertaintyInMilliseconds)

class ColorProperty(Property):
    def __init__(self, hue, saturation, brightness, timeOfSample, uncertaintyInMilliseconds):
        pe = Color(hue, saturation, brightness)
        super(ColorProperty, self).__init__('Alexa.ColorController', pe, timeOfSample, uncertaintyInMilliseconds)

class ColorTemperatureInKelvinProperty(Property):
    def __init__(self, value, timeOfSample, uncertaintyInMilliseconds):
        pe = ColorTemperatureInKelvin(value)
        super(ColorTemperatureInKelvinProperty, self).__init__('Alexa.ColorTemperatureController', pe, timeOfSample, uncertaintyInMilliseconds)

class CookingModeProperty(Property):
    def __init__(self, mode, timeOfSample, uncertaintyInMilliseconds):
        pe = CookingMode(mode)
        super(CookingModeProperty, self).__init__('Alexa.Cooking', pe, timeOfSample, uncertaintyInMilliseconds)

class CookingTimeProperty(Property):
    def __init__(self, time, type, timeOfSample, uncertaintyInMilliseconds):
        pe = DateTime(time, type)
        super(CookingTimeProperty, self).__init__('Alexa.Cooking', pe, timeOfSample, uncertaintyInMilliseconds)

class CookingCompletionTimeEstimatedProperty(Property):
    def __init__(self, value, timeOfSample, uncertaintyInMilliseconds):
        pe = CookCompletionTimeEstimated(value)
        super(CookingCompletionTimeEstimatedProperty, self).__init__('Alexa.Cooking', pe, timeOfSample, uncertaintyInMilliseconds)

class CookingFoodItemProperty(Property):
    def __init__(self, foodName, foodCategory, foodQuantity, timeOfSample, uncertaintyInMilliseconds):
        pe = FoodItem(foodName, foodCategory, foodQuantity)
        super(CookingFoodItemProperty, self).__init__('Alexa.Cooking', pe, timeOfSample, uncertaintyInMilliseconds)

class CookingTimeControllerTimeProperty(Property):
    def __init__(self, timeDelta, timeOfSample, uncertaintyInMilliseconds):
        pe = Duration(timeDelta, 'cookTime')
        super(CookingTimeControllerTimeProperty, self).__init__('Alexa.Cooking.TimeController', pe, timeOfSample, uncertaintyInMilliseconds)

class CookingTimeControllerPowerProperty(Property):
    def __init__(self, value, timeOfSample, uncertaintyInMilliseconds):
        pe = PowerLevel(value)
        super(CookingTimeControllerPowerProperty, self).__init__('Alexa.Cooking.TimeController', pe, timeOfSample, uncertaintyInMilliseconds)

class CookingHoldingProperty(Property):
    def __init__(self, value, timeOfSample, uncertaintyInMilliseconds):
        pe = CookingHolding(value)
        super(CookingHoldingProperty, self).__init__('Alexa.Cooking', pe, timeOfSample, uncertaintyInMilliseconds)

class CookingPresetProperty(Property):
    def __init__(self, value, timeOfSample, uncertaintyInMilliseconds):
        pe = CookingPreset(value)
        super(CookingPresetProperty, self).__init__('Alexa.Cooking.PresetController', pe, timeOfSample, uncertaintyInMilliseconds)

class EndpointHealthProperty(Property):
    def __init__(self, value, timeOfSample, uncertaintyInMilliseconds):
        pe = Connectivity(value)
        super(EndpointHealthProperty, self).__init__('Alexa.EndpointHealth', pe, timeOfSample, uncertaintyInMilliseconds)

class InputProperty(Property):
    def __init__(self, value, timeOfSample, uncertaintyInMilliseconds):
        pe = Input(value)
        super(InputProperty, self).__init__('Alexa.InputController', pe, timeOfSample, uncertaintyInMilliseconds)

class LockProperty(Property):
    def __init__(self, value, timeOfSample, uncertaintyInMilliseconds):
        pe = LockState(value)
        super(LockProperty, self).__init__('Alexa.LockController', pe, timeOfSample, uncertaintyInMilliseconds)

class PercentageProperty(Property):
    def __init__(self, value, timeOfSample, uncertaintyInMilliseconds):
        pe = Percentage(value)
        super(PercentageProperty, self).__init__('Alexa.PercentageController', pe, timeOfSample, uncertaintyInMilliseconds)

class PowerStateProperty(Property):
    def __init__(self, value, timeOfSample, uncertaintyInMilliseconds):
        if type(value)==bool:
            value = 'ON' if value else 'OFF'
        pe = PowerState(value)
        super(PowerStateProperty, self).__init__('Alexa.PowerController', pe, timeOfSample, uncertaintyInMilliseconds)

class PowerLevelProperty(Property):
    def __init__(self, value, timeOfSample, uncertaintyInMilliseconds):
        pe = PowerLevel(value)
        super(PowerLevelProperty, self).__init__('Alexa.PowerLevelController', pe, timeOfSample, uncertaintyInMilliseconds)

class SpeakerVolumeProperty(Property):
    def __init__(self, value, timeOfSample, uncertaintyInMilliseconds):
        pe = VolumeLevel(value)
        super(SpeakerVolumeProperty, self).__init__('Alexa.Speaker', pe, timeOfSample, uncertaintyInMilliseconds)

class SpeakerMuteProperty(Property):
    def __init__(self, value, timeOfSample, uncertaintyInMilliseconds):
        pe = MuteState(value)
        super(SpeakerMuteProperty, self).__init__('Alexa.Speaker', pe, timeOfSample, uncertaintyInMilliseconds)

class TemperatureProperty(Property):
    def __init__(self, value, scale, timeOfSample, uncertaintyInMilliseconds):
        pe = Temperature(value, scale, 'temperature')
        super(TemperatureProperty, self).__init__('Alexa.TemperatureSensor', pe, timeOfSample, uncertaintyInMilliseconds)

class ThermostatTargetSetpointProperty(Property):
    def __init__(self, value, scale, timeOfSample, uncertaintyInMilliseconds):
        pe = Temperature(value, scale, 'targetSetpoint')
        super(ThermostatTargetSetpointProperty, self).__init__('Alexa.ThermostatController', pe, timeOfSample, uncertaintyInMilliseconds)

class ThermostatLowerSetpointProperty(Property):
    def __init__(self, value, scale, timeOfSample, uncertaintyInMilliseconds):
        pe = Temperature(value, scale, 'lowerSetpoint')
        super(ThermostatLowerSetpointProperty, self).__init__('Alexa.ThermostatController', pe, timeOfSample, uncertaintyInMilliseconds)

class ThermostatUpperSetpointProperty(Property):
    def __init__(self, value, scale, timeOfSample, uncertaintyInMilliseconds):
        pe = Temperature(value, scale, 'upperSetpoint')
        super(ThermostatUpperSetpointProperty, self).__init__('Alexa.ThermostatController', pe, timeOfSample, uncertaintyInMilliseconds)

class ThermostatModeProperty(Property):
    def __init__(self, value, customName, timeOfSample, uncertaintyInMilliseconds):
        pe = ThermostatMode(value, customName)
        super(ThermostatModeProperty, self).__init__('Alexa.ThermostatController', pe, timeOfSample, uncertaintyInMilliseconds)

# ResponseElement classes -- used to propertly format the elements of a response message
class ResponseElement(object):
    def __init__(self):
        self.json = {}

    def get_json(self):
        return self.json

    def __str__(self):
        return json.dumps(self.get_json(), indent=4)

class Context(ResponseElement):
    def __init__(self):
        super(Context, self).__init__()
        self.properties = []

    def add_property(self, property):
        if isinstance(property, Property):
            self.properties.append(property.get_json())
        else:
            self.properties.append(property)
        self.json = { 'properties': self.properties }

class Event(ResponseElement):
    def __init__(self,header, endpoint, payload):
        super(Event, self).__init__()

        h = header.get_json() if isinstance(header, Header) else header
        e = endpoint.get_json() if isinstance(endpoint, Endpoint) else endpoint
        p = payload.get_json() if isinstance(payload, Payload) else payload

        self.json = {
            'header': h,
            'endpoint': e,
            'payload': p
        }

class Header(ResponseElement):
    def __init__(self, namespace='', name='', messageId='', correlationToken='', payloadVersion='3', json=None):
        super(Header, self).__init__()

        if type(json) == dict:
            self.namespace = json.get('namespace')
            self.name = json.get('name')
            self.payloadVersion = json.get('payloadVersion')
            self.messageId = json.get('messageId')
            self.correlationToken = json.get('correlationToken')
        else:
            self.namespace = namespace
            self.name = name
            self.payloadVersion = payloadVersion
            self.messageId = messageId
            self.correlationToken= correlationToken

        if not self.messageId:
            self.messageId = get_uuid()
        if self.namespace and self.name:
            self.json = { 'namespace': self.namespace, 'name':self.name, 'messageId':self.messageId }
        else:
            raise TypeError('Header must have a namespace and a name')
        if self.correlationToken:
            self.json['correlationToken'] = self.correlationToken

        if self.payloadVersion not in VALID_PAYLOADVERSIONS:
            raise ValueError(self.payloadVersion + ' is not a valid value')
        self.json['payloadVersion'] = self.payloadVersion

class Meeting(ResponseElement):
    def __init__(self, id='', pin='', endpoint='', protocol='', provider='', json=None):
        super(Meeting, self).__init__()

        if type(json) == dict:
            self.id = json.get('id')
            self.pin = json.get('pin')
            self.endpoint = json.get('endpoint')
            self.protocol = json.get('protocol')
            self.provider = json.get('provider')
        else:
            self.id = id
            self.pin = pin
            self.endpoint = endpoint
            self.protocol = protocol
            self.provider= provider

        self.name = 'meeting'
        self.json = { 'id': self.id }
        if self.pin:
            self.json['pin'] = self.pin
        if self.endpoint:
            self.json['endpoint'] = self.endpoint
        if self.protocol:
            self.json['protocol'] = self.protocol
        if self.provider:
            self.json['provider'] = self.provider

class Setpoint(ResponseElement):
    def __init__(self, value=0, scale='', json=None):
        super(Setpoint, self).__init__()

        if type(json) == dict:
            self.value = json.get('value')
            self.scale = json.get('scale')
        else:
            self.value = value
            self.scale = scale

        if type(value) != int and type(value) != float:
            raise TypeError('Setpoint value must be an integer or a float.  Received a '+str(type(value)))
        if self.scale not in VALID_TEMPERATURESCALES:
            raise ValueError(self.scale + ' is not a valid temperature scale')

        self.name = 'Setpoint'
        self.json = { 'value': self.value, 'scale': self.scale }
        if self.pin:
            self.json['pin'] = self.pin
        if self.endpoint:
            self.json['endpoint'] = self.endpoint
        if self.protocol:
            self.json['protocol'] = self.protocol
        if self.provider:
            self.json['provider'] = self.provider

class TargetSetpoint(Setpoint):
    def __init__(self, value=0, scale='', json=None):

        if type(json) == dict:
            super(TargetSetpoint, self).__init__(json=json)
        else:
            super(TargetSetpoint, self).__init__(value=value, scale=scale)

        self.name = 'targetSetpoint'

class LowerSetpoint(Setpoint):
    def __init__(self, value=0, scale='', json=None):

        if type(json) == dict:
            super(LowerSetpoint, self).__init__(json=json)
        else:
            super(LowerSetpoint, self).__init__(value=value, scale=scale)

        self.name = 'lowerSetpoint'

class UpperSetpoint(Setpoint):
    def __init__(self, value=0, scale='', json=None):

        if type(json) == dict:
            super(UpperSetpoint, self).__init__(json=json)
        else:
            super(UpperSetpoint, self).__init__(value=value, scale=scale)

        self.name = 'upperSetpoint'

class TargetSetpointDelta(Setpoint):
    def __init__(self, value=0, scale='', json=None):

        if type(json) == dict:
            super(TargetSetpointDelta, self).__init__(json=json)
        else:
            super(TargetSetpointDelta, self).__init__(value=value, scale=scale)

        self.name = 'targetSetpointDelta'


class Payload(ResponseElement):
    def __init__(self, name='', value=''):
        super(Payload, self).__init__()
        self.json = { }

        if name:
            self.add_attribute(name, value)

    def add_attribute(name, value):
        self.json[name] = value

class Endpoints():
    def __init__(self, endpoint = None):
        self.value = []

        if isinstance(endpoint, Endpoint):
            add(endpoint)

    def add(self, endpoint):
        if not isinstance(endpoint, Endpoint):
            raise TypeError('Endpoints can only add Endpoint objects.  Received a ' + str(type(endpoint)))

        self.value.append(endpoint.get_json())

class Properties():
    def __init__(self, property = None):
        self.value = []

        if isinstance(property, Property):
            add(property)

    def add(self, property):
        if not isinstance(property, Property):
            raise TypeError('Properties can only add Property objects.  Received a ' + str(type(property)))

        self.value.append(property.get_json())


#class Properties(ResponseElement):
#    def __init__(self, proactivelyReported=False, retrievable=False):
class Properties_supported(ResponseElement):
    def __init__(self, values, proactivelyReported='', retrievable=''):
        super(Properties_supported, self).__init__()

        # If a single string is passed in, convert it to an array
        if type(values) == str:
            values = [ values ]

        self.json = {
            'supported': []
        }
        if type(proactivelyReported) == bool:
            self.json['proactivelyReported'] = proactivelyReported
        if type(retrievable) == bool:
            self.json['retrievable'] = retrievable

        for item in values:
            prop = { 'name': item }
            self.json['supported'].append(prop)

class Capability(ResponseElement):
    def __init__(self, interface, property_names = [], proactivelyReported='', retrievable='', supportsDeactivation='', version='3', supportedOperations=[], cameraStreamConfigurations=[]):
        super(Capability, self).__init__()

        interface = fix_interface(interface)

        if type(property_names) != list:
            property_names = [ property_names ]

        for i in range(len(property_names)):
            property_names[i] = fix_property(interface, property_names[i])


        # Correct type if a numeric value provided for version
        if type(version) == int:
            version = str(version)

        self.json = {
            'type': 'AlexaInterface',
            'interface': interface,
            'version':version,
        }
        if property_names:
            properties_supported = Properties_supported(property_names, proactivelyReported, retrievable).get_json()
            if 'supported' in properties_supported:
                if properties_supported['supported']:
                    self.json['properties'] = properties_supported
                else:
                    raise ValueError('properties.supported contained no services')
            else:
                raise ValueError('properties did not have a supported object')
        if supportedOperations:
            self.json['supportedOperations'] = supportedOperations
        if cameraStreamConfigurations:
            self.json['cameraStreamConfigurations'] = cameraStreamConfigurations
        if type(proactivelyReported) == bool:
            self.json['proactivelyReported'] = proactivelyReported
        if type(supportsDeactivation) == bool:
            self.json['supportsDeactivation'] = supportsDeactivation


class Endpoint(ResponseElement):
    def __init__(self, endpointId, manufacturerName='', friendlyName='', description='', displayCategories=[], cookie='', capabilities=[], token={}):
        super(Endpoint, self).__init__()

        if token:
            self.json = { 'endpointId': endpointId, 'scope': { 'type':'BearerToken', 'token': token }}
        else:
            self.json = { 'endpointId': endpointId }

        if manufacturerName:
            self.json['manufacturerName'] = manufacturerName
        if friendlyName:
            self.json['friendlyName'] = friendlyName
        if description:
            self.json['description'] = description
        if displayCategories:
            self.json['displayCategories'] = displayCategories
        if type(cookie) == dict:
            self.json['cookie'] = cookie
        if capabilities:
            for item, value in enumerate(capabilities):
                if isinstance(capabilities[item], Capability):
                    capabilities[item] = capabilities[item].get_json()
            self.json['capabilities'] = capabilities

class Request():
    def __init__(self, request):
        if type(request) != dict:
            raise TypeError('Expected a dict.  Received a {0}'.format(str(type(request))))

        # Save original request
        self.raw = request

        # Initial required request components
        self.header = self.endpoint = self.payload = {}

        if 'directive' not in request:
            raise TypeError('Invalid message.  It does not contain a directive')

        if 'header' in request['directive']:
            self.namespace = request['directive']['header'].get('namespace')
            self.interface = self.namespace.split('.')[1] if '.' in self.namespace else ''
            self.name = self.directive = request['directive']['header'].get('name')
            self.payloadVersion = request['directive']['header'].get('payloadVersion')
            self.messageId = request['directive']['header'].get('messageId')
            self.correlationToken = request['directive']['header'].get('correlationToken')
            self.header = Header(json=request['directive']['header'])
        if 'endpoint' in request['directive']:
            self.endpointId = request['directive']['endpoint'].get('endpointId')
            if 'scope' in request['directive']['endpoint']:
                self.scope = Scope(json=request['directive']['endpoint']['scope'])
            self.cookie = request['directive']['endpoint'].get('cookie')
        self.payload = request['directive'].get('payload')
        if 'payload' in request['directive']:
            if 'scope' in request['directive']['payload']:
                self.scope = Scope(json=request['directive']['payload']['scope'])
            if 'grant' in request['directive']['payload']:
                self.code = request['directive']['payload']['grant'].get('code')
            if 'grantee' in request['directive']['payload']:
                self.token = request['directive']['payload']['grantee'].get('token')
            if 'cameraStreams' in request['directive']['payload']:
                if type(request['directive']['payload']['cameraStreams']) != list:
                    raise TypeError('cameraStreams must be a list.  Received a '+ str(type(request['directive']['payload']['cameraStreams'])))
                self.cameraStreams = CameraStreams()
                for cs in request['directive']['payload']['cameraStreams']:
                    self.cameraStreams.add(CameraStream(json=cs))
            if 'channel' in request['directive']['payload']:
                self.channel = Channel(json=request['directive']['payload']['channel'])
            if 'channelMetadata' in request['directive']['payload']:
                self.channelMetaData = ChannelMetadata(json=request['directive']['payload']['channelMetadata'])
            if 'color' in request['directive']['payload']:
                self.color = Color(json=request['directive']['payload']['color'])
            if 'cookingMode' in request['directive']['payload']:
                self.cookingMode = CookingMode(json=request['directive']['payload']['cookingMode'])
            if 'foodItem' in request['directive']['payload']:
                self.foodItem = FoodItem(json=request['directive']['payload']['foodItem'])
            if 'presetName' in request['directive']['payload']:
                self.presetName = request['directive']['payload'].get('presetName')
            if 'cookTime' in request['directive']['payload']:
                self.cookTime = request['directive']['payload'].get('cookTime')
            if 'cookingPowerLevel' in request['directive']['payload']:
                self.cookingPowerLevel = CookingPowerLevel(json=request['directive']['payload']['cookingPowerLevel'])
            if 'meeting' in request['directive']['payload']:
                self.meeting = Meeting(json=request['directive']['payload']['meeting'])
            if 'targetSetpoint' in request['directive']['payload']:
                self.targetSetpoint = TargetSetPoint(json=request['directive']['payload']['targetSetpoint'])
            if 'targetSetpointDelta' in request['directive']['payload']:
                self.targetSetpointDelta = TargetSetPoint(json=request['directive']['payload']['targetSetpointDelta'])
            if 'lowerSetpoint' in request['directive']['payload']:
                self.targetSetpoint = TargetSetPoint(json=request['directive']['payload']['lowerSetpoint'])
            if 'upperSetpoint' in request['directive']['payload']:
                self.targetSetpoint = TargetSetPoint(json=request['directive']['payload']['upperSetpoint'])
            if 'thermostatMode' in request['directive']['payload']:
                self.thermostatMode = ThermostatMode(json=request['directive']['payload']['thermostatMode'])

class Response(ResponseElement):
    def __init__(self, request, response=None):
        super(Response, self).__init__()

        d = Request(request)

        # Respond to AcceptGrant
        if d.namespace == 'Alexa.Authorization' and d.name == 'AcceptGrant':
            header = Header('Alexa.Authorization', 'AcceptGrant.Response', payloadVersion = d.payloadVersion)
            self.json = { 'event': { 'header': header.get_json(), 'payload': {} }}

        # Respond to Discovery
        # No default possible
        elif d.namespace == 'Alexa.Discovery' and d.name == 'Discover':
            if isinstance(response, Endpoint):
                response = [ response ]
            if type(response) != list:
                raise TypeError('Discovery response requires either an endpoint object or an array of endpoint objects')
            for i in range(len(response)):
                if not isinstance(response[i], Endpoint):
                    raise TypeError('Endpoint array contains a non-endpoint.  Type was {0}'.format(str(type(response[i]))))
                response[i] = response[i].get_json()
            header = Header('Alexa.Discovery', 'Discover.Response',payloadVersion=d.payloadVersion)
            self.json = {
                'event': {
                    'header': header.get_json(),
                    'payload': {
                        'endpoints': response
                    }
                }
            }

        # Respond to Calendar
        # No default possible
        elif d.namespace == 'Alexa.Calendar' and d.name == 'GetCurrentMeeting':
            header = Header('Alexa.Calendar', 'Response', payloadVersion=d.payloadVersion, correlationToken = d.correlationToken)
            if type(response) != dict:
                raise TypeError('Calendar response requires a dictionary with organizerName and calendarEventId keys.  Received a '+str(type(response)))
            if 'organizerName' not in response:
                raise TypeError('Calendar response requires a dictionary with organizerName and calendarEventId keys. OrganizerName is missing')
            if 'calendarEventId' not in response:
                raise TypeError('Calendar response requires a dictionary with organizerName and calendarEventId keys. calendarEventId is missing')
            organizerName = response['organizerName']
            calendarEventId = response['calendarEventId']
            self.json = {
                'event': {
                    'header': header.get_json(),
                    'payload': {
                        'organizerName': organizerName,
                        'calendarEventId': calendarEventId
                    }
                }
            }

        # Respond to CameraStreamController
        # No default possible
        elif d.namespace == 'Alexa.CameraStreamController':
            if not isinstance(response, CameraStreamsPayload):
                raise TypeError('CameraStreamController response requires an a CameraStreamsPayload object.  Received a '+str(type(response)))
            header = Header(d.namespace, 'Response', payloadVersion=d.payloadVersion, correlationToken=d.correlationToken)
            self.json = {
                'event': {
                    'header': header.get_json(),
                    'endpoint': {
                        'endpointId': d.endpointId
                    },
                    'payload': response.value
                }
            }

        elif d.namespace == 'Alexa' and d.name == 'ReportState':
            if isinstance(response, Property):
                response = [ response ]
            if type(response) != list:
                raise TypeError('ReportState response requires either a Property object or an array of Property objects')
            for i in range(len(response)):
                if not isinstance(response[i], Property):
                    raise TypeError('Property array contains a non-property.  Type was {0}'.format(str(type(response[i]))))
                response[i] = response[i].get_json()
            header = Header('Alexa', 'StateReport', payloadVersion=d.payloadVersion, correlationToken=d.correlationToken)
            self.json = {
                'context': {
                    'properties': response,
                },
                'event': {
                    'header': header.get_json(),
                    'endpoint': {
                        'endpointId': d.endpointId
                    },
                    'payload': { }
                }
            }
            if d.scope:
                self.json['event']['endpoint']['scope'] = d.scope.value
            if d.cookie:
                self.json['event']['endpoint']['cookie'] = d.cookie

        # Respond to SceneController.  Need to determine whether affected devices need to be in context
        elif d.namespace == 'Alexa.SceneController':
            if d.name == 'Activate':
                action = 'ActivationStarted'
            else:
                action = 'DeactivationStarted'
            header = Header(d.namespace, action, payloadVersion = d.payloadVersion, correlationToken = d.correlationToken )
            try:
                tok = d.token
            except:
                tok = None
            endpoint = Endpoint(d.endpointId, token=tok)
            self.json = {
                'context': {},
                'event': {
                    'header': header.get_json(),
                    'endpoint': endpoint.get_json(),
                    'payload': {
                        'cause': {
                            'type': 'VOICE_INTERACTION'
                        },
                        'timestamp': get_utc_timestamp()
                    }
                }
            }

        elif d.namespace in pyASH.VALID_SIMPLEINTERFACES:
            if not isinstance(response, Properties):
                raise TypeError('Simple responses requires an a Properties object.  Received a '+str(type(response)))
            header = Header('Alexa', 'Response', payloadVersion=d.payloadVersion, correlationToken=d.correlationToken)
            self.json = {
                'context': {
                    'properties': response.value,
                },
                'event': {
                    'header': header.get_json(),
                    'endpoint': {
                        'endpointId': d.endpointId
                    },
                    'payload': { }
                }
            }
            if d.scope:
                self.json['event']['endpoint']['scope'] = d.scope.value
            if d.cookie:
                self.json['event']['endpoint']['cookie'] = d.cookie




class ErrorResponse(ResponseElement):
    def __init__(self, namespace, type, reason, correlationToken='', endpoint={}, min={}, max={}):
        super(ErrorResponse, self).__init__()

        self.type = type
        if self.type not in pyASH.VALID_ERROR_TYPES:
            raise TypeError('{0} is not a valid error value'.format(self.type))

        header = Header(namespace, 'ErrorResponse', correlationToken = correlationToken).get_json()

        self.json = {
            'event': {
                'header': header,
                'payload': {
                    'type': type,
                    'message': reason
                }
            }
        }

        if isinstance(endpoint, Endpoint):
            endpoint = endpoint.get_json()

        if endpoint:
            self.json['event']['endpoint'] = endpoint

        if type == 'VALUE_OUT_OF_RANGE' or type == 'TEMPERATURE_VALUE_OUT_OF_RANGE':
            self.json['event']['payload']['validRange'] = {
                'minimumValue': min,
                'maximumValue': max
            }
