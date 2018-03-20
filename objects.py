# -*- coding: utf-8 -*-

# Copyright 2018 by dhrone. All Rights Reserved.
#

import re
import json
from datetime import timedelta

# pyASH imports
from utility import *

# Setup logger
import logging
logger = logging.getLogger(__name__)
logger.setLevel(LOGLEVEL)

class ashobject(object):

    def __str__(self):
        if hasattr(self,'json'):
            return json.dumps(self.json, indent=4)
        return ''

class CameraStream(ashobject):
    def __init__(self, resolutions=None, resolution=None, protocols = None, protocol=None, authorizationTypes=None, authorizationType=None, videoCodecs=None, videoCodec=None, audioCodecs=None, audioCodec=None, uri=None, expirationTime=None, idleTimeoutSeconds=None, json=None):
        self.resolution_value = self.Resolution()
        self.resolutions_value = {}
        self.protocol_value = None
        self.protocols_value = []
        self.authorizationType_value = None
        self.authorizationTypes_value = []
        self.videoCodec_value = None
        self.videoCodecs_value = []
        self.audioCodec_value = None
        self.audioCodecs_value = []
        self.uri = None
        self.expirationTime = None
        self.idleTimeoutSeconds = None
        if json:
            self.resolutions = json.get('resolutions')
            self.resolution = json.get('resolution')
            self.protocols = json.get('protocols')
            self.protocol = json.get('protocol')
            self.authorizationTypes = json.get('authorizationTypes')
            self.authorizationType = json.get('authorizationType')
            self.videoCodecs = json.get('videoCodecs')
            self.videoCodec = json.get('videoCodec')
            self.audioCodecs = json.get('audioCodecs')
            self.audioCodec = json.get('audioCodec')
            self.uri = json.get('uri')
            self.expirationTime = json.get('expirationTime')
            self.idleTimeoutSeconds = json.get('idleTimeoutSeconds')
        else:
            self.resolutions = resolutions
            self.resolution = resolution
            self.protocols = protocols
            self.protocol = protocol
            self.authorizationTypes = authorizationTypes
            self.authorizationType = authorizationType
            self.videoCodecs = videoCodecs
            self.videoCodec = videoCodec
            self.audioCodecs = audioCodecs
            self.audioCodec = audioCodec
            self.uri = uri
            self.expirationTime = expirationTime
            self.idleTimeoutSeconds = idleTimeoutSeconds

    @property
    def json(self):
        ret = {}
        ret['protocols'] = self.protocols_value
        ret['resolutions'] = list ( map( lambda x: x.json, self.resolutions_value.values()))
        ret['authorizationTypes'] = self.authorizationTypes_value
        ret['videoCodecs'] = self.videoCodecs_value
        ret['audioCodecs'] = self.audioCodecs_value
        ret['uri'] = self.uri
        ret['expirationTime'] = self.expirationTime
        ret['idleTimeoutSeconds'] = self.idleTimeoutSeconds
        ret['protocol'] = self.protocol_value
        ret['resolution'] = self.resolution_value.json
        ret['authorizationType'] = self.authorizationType_value
        ret['videoCodec'] = self.videoCodec_value
        ret['audioCodec'] = self.audioCodec_value

        # Remove any empty values
        ret = { k : v for k,v in ret.items() if v }
        return ret

    @property
    def jsonDiscover(self):
        return { k : v for k,v in self.json.items() if k in ['protocols', 'resolutions', 'authorizationTypes','videoCodecs', 'audioCodecs']}


    @property
    def jsonResponse(self):
        return { k : v for k,v in self.json.items() if k in ['uri', 'expirationTime', 'idleTimeoutSeconds', 'protocol', 'resolution', 'authorizationType','videoCodec', 'audioCodec']}

    @property
    def protocol(self):
        return self.protocol_value

    @protocol.setter
    def protocol(self,value):
        value = value.upper() if value else None
        self.protocol_value = value if value in ['RTSP', 'RTP'] else None
        if not self.protocol_value and value:
            raise ValueError('{0} is not a valid Protocol'.format(value))

    @property
    def protocols(self):
        return self.protocols_value

    @protocols.setter
    def protocols(self, value):
        self.protocols_value = []
        value = value if type(value) is list else [ value ] if value else []
        for item in value:
            self.protocol = item.upper()
            if self.protocol not in self.protocols_value:
                self.protocols_value.append(self.protocol)

    @property
    def authorizationType(self):
        return self.authorizationType_value

    @authorizationType.setter
    def authorizationType(self,value):
        value = value.upper() if value else None
        self.authorizationType_value = value if value in ['BASIC','DIGEST','NONE'] else None
        if not self.authorizationType_value and value:
            raise ValueError('{0} is not a valid Authorization Type'.format(value))


    @property
    def authorizationTypes(self):
        return self.authorizationTypes_value

    @authorizationTypes.setter
    def authorizationTypes(self, value):
        self.authorizationTypes_value = []
        value = value if type(value) is list else [ value ] if value else []
        for item in value:
            self.authorizationType = item.upper()
            if self.authorizationType not in self.authorizationTypes_value:
                self.authorizationTypes_value.append(self.authorizationType)

    @property
    def videoCodec(self):
        return self.videoCodec_value

    @videoCodec.setter
    def videoCodec(self,value):
        value = value.upper() if value else None
        self.videoCodec_value = value if value in VALID_VIDEO_CODECS else None
        if not self.videoCodec_value and value:
            raise ValueError('{0} is not a valid Video Codec'.format(value))

    @property
    def videoCodecs(self):
        return self.videoCodecs_value

    @videoCodecs.setter
    def videoCodecs(self, value):
        self.videoCodecs_value = []
        value = value if type(value) is list else [ value ] if value else []
        for item in value:
            self.videoCodec = item.upper()
            if self.videoCodec not in self.videoCodecs_value:
                self.videoCodecs_value.append(self.videoCodec)

    @property
    def audioCodec(self):
        return self.audioCodec_value

    @audioCodec.setter
    def audioCodec(self,value):
        value = value.upper() if value else None
        self.audioCodec_value = value if value in VALID_AUDIO_CODECS else None
        if not self.audioCodec_value and value:
            raise ValueError('{0} is not a valid Audio Codec'.format(value))

    @property
    def audioCodecs(self):
        return self.audioCodecs_value

    @audioCodecs.setter
    def audioCodecs(self, value):
        self.audioCodecs_value = []
        value = value if type(value) is list else [ value ] if value else []
        for item in value:
            self.audioCodec = item.upper()
            if self.audioCodec not in self.audioCodecs_value:
                self.audioCodecs_value.append(self.audioCodec)

    class Resolution():
        def __init__(self, width=0, height=0):
            print ('W{0}:H{1}'.format(width, height))
            if type(width) is tuple:
                (self.width, self.height) = width
            elif type(width) is dict:
                self.width = width.get('width',0)
                self.height = width.get('height',0)
            else:
                self.width = width
                self.height = height
            print('SW{0}:SH{1}'.format(self.width, self.height))

        @property
        def json(self):
            return { 'width': self.width, 'height': self.height}

    @property
    def resolution(self):
        return self.resolution_value

    @resolution.setter
    def resolution(self, value):
        self.resolution_value = self.value if isinstance(value, self.Resolution) else self.Resolution(value)

    @property
    def resolutions(self):
        return self.resolutions_value.values()

    @resolutions.setter
    def resolutions(self, value):
        self.resolutions_value = {}
        value = value if type(value) is list else [ value ] if value else []
        for item in value:
            print ('ITEM={0}'.format(item))
            self.resolution = item
            self.resolution_value = self.value if isinstance(item, self.Resolution) else self.Resolution(item)
            self.resolutions_value[(self.resolution_value.width,self.resolution_value.height)] = self.resolution_value

class Channel(ashobject):
    def __init__(self, number=None, callSign=None, affiliateCallSign=None, uri=None, json=None):
        self.number = json.get('number') if json else number
        self.callSign = json.get('callSign') if json else callSign
        self.affiliateCallSign = json.get('affiliateCallSign') if json else affiliateCallSign
        self.uri = json.get('uri') if json else uri

    @property
    def json(self):
        ret = {}
        ret['number'] = self.number
        ret['callSign'] = self.callSign
        ret['affiliateCallSign'] = self.affiliateCallSign
        ret['uri'] = self.uri
        return { k : v for k,v in ret.items() if v }

class ChannelMetadata(ashobject):
    def __init__(self, name=None, image=None, json=None):
        self.name = json.get('name') if json else name
        self.image = json.get('image') if json else image

    @property
    def json(self):
        ret = {}
        ret['name'] = self.name
        ret['image'] = self.image
        return { k : v for k,v in ret.items() if v }

class Color(ashobject):
    def __init__(self, hue=None, saturation=None, brightness=None, json=None):
        self.hue = json.get('hue') if json else hue
        self.saturation = json.get('saturation') if json else saturation
        self.brightness = json.get('brightness') if json else brightness

    @property
    def json(self):
        ret = {}
        ret['hue'] = self.hue
        ret['saturation'] = self.saturation
        ret['brightness'] = self.brightness
        return { k : v for k,v in ret.items() if v }


class CookTime(ashobject):
    def __init__(self, value=None, json=None):
        if value is None and json: value = json
        self.value = Duration(value) if type(value) is not dict else Duration(value.get('value')) if 'get' in value else None
        self.json = self.value if type(value) is not dict else { 'value': self.value }
        self.seconds = self.totalSeconds = self.value.totalSeconds
        self.timedelta = self.value.timedelta

class Duration(ashobject):
    def __init__(self, duration):
        if type(duration) == str:
            m = re.match('^PT([-+])?(?:([0-9]+)D)?(?:([0-9]+)H)?(?:([0-9]+)M)?(?:([0-9]+)S)?$', duration)
            if not m:
                raise ValueError('{0} is not a valid duration'.format(duration))
            (days, hours, minutes, seconds) = map( self._int, m.groups()[1:] )
            sign = m.groups()[0]
            self.totalSeconds = days*24*60*60 + hours*60*60 + minutes*60 + seconds
            self.totalSeconds = -self.totalSeconds if sign and sign=='-' else self.totalSeconds
        elif type(duration) in [int, float]:
            self.totalSeconds = int(duration)
        elif isinstance(duration, timedelta):
            self.totalSeconds = int(timedelta.total_seconds())
        else:
            raise TypeError('{0} is not a valid Duration'.format(duration))
        self.seconds = self.totalSeconds

    @property
    def timedelta(self):
        return timedelta(seconds=self.totalSeconds)

    def _int(self, val):
        try:
            val = int(val)
        except:
            val = 0
        return val

    @property
    def json(self):
        return iso8601(timedelta(seconds=self.totalSeconds))

class Endpoint(ashobject):
    def __init__(self, endpointId=None, token=None, cookie=None, json=None):
        self.endpointId = endpointId if endpointId is not None else json.get('endpointId') if json else None
        self.id = self.endpointId
        self.token = token if token is not None else json['scope'].get('token') if json and 'scope' in json else None
        self.cookie = cookie if cookie is not None else json.get('cookie') if json else None
        self.scope = { 'type': 'BearerToken', 'token': self.token } if self.token is not None else None
        self.json = { 'endpointId': self.endpointId }
        if self.token is not None: self.json['scope'] = { 'type': 'BearerToken', 'token': self.token }
        if self.cookie is not None: self.json['cookie'] = self.cookie

class FoodQuantity(ashobject):
    def __init__(self, foodQuantityType=None, value=None, unit=None, size=None, json=None):
        self.foodQuantityType = json.get('@type') if json else foodQuantityType
        self.value = json.get('value') if json else value
        self.unit = json.get('unit') if json else unit
        self.size = json.get('size') if json else size

        self.foodQuantityType = validateValue(self.foodQuantityType, VALID_FOODQUANTITYTYPES, '{0} is not a valid FoodQuantity type')
        self.unit = \
            validateValue(self.unit, VALID_VOLUMEUNITS, '{0} is not a valid Volume unit') if self.foodQuantityType == 'Volume' else \
            validateValue(self.unit, VALID_WEIGHTUNITS, '{0} is not a valid Weight unit') if self.foodQuantityType == 'Weight' else None
        self.size = validateValue(self.size, VALID_FOODCOUNTSIZES, '{0} is not a valid FoodCount size') if self.foodQuantityType == 'FoodCount' else None

    @property
    def json(self):
        ret = { '@type': self.foodQuantityType, 'value': self.value }
        if self.foodQuantityType in ['Weight','Volume']:
            ret['unit'] = self.unit
        else:
            ret['size'] = self.size
        return ret

class FoodItem(ashobject):
    def __init__(self, name=None, category=None, quantity=None, json=None):
        self.name = json.get('name') if json else name
        self.category = json.get('category') if json else category
        self.quantity = json.get('quantity') if json else quantity
        self.quantity = self.quantity if isinstance(self.quantity, FoodQuantity) else FoodQuantity(self.quantity) if type(self.quantity) is dict else None

        self.category = validateValue(self.category, VALID_FOODCATEGORIES, '{0} is not a valid food category')

    @property
    def json(self):
        return {
            'foodName': self.name,
            'foodCategory': self.category,
            'foodQuantity': self.quantity.json
        }

class Header(ashobject):
    def __init__(self, namespace=None, name=None, correlationToken=None, json=None):
        self.messageId = get_uuid()
        self.id = self.messageId
        self.namespace = namespace if namespace is not None else json.get('namespace') if json else None
        self.name = name if name is not None else json.get('name') if json else None
        self.correlationToken = correlationToken if correlationToken is not None else json.get('correlationToken') if json else None
        self.token = self.correlationToken
        self.interface = self.namespace.split('.')[1] if '.' in self.namespace else self.namespace
        self.json = { 'namespace': self.namespace, 'name':self.name, 'messageId': self.messageId, 'payloadVersion': '3' }
        if self.correlationToken is not None: self.json['correlationToken'] = self.correlationToken

class PowerLevel(ashobject):
    def __init__(self, powerLevelType=None, value=None, json=None):
        self.powerLevelType = json.get('@type') if json else powerLevelType
        self.value = json.get('value') if json else value
        self.powerLevelType = validateValue(self.powerLevelType, ['EnumeratedPowerLevel', 'IntegralPowerLevel'], '{0} is not a valid powerLevel type')
        self.value = validateValue(self.value, VALID_ENUMERATEDPOWERLEVELS, '{0} is not a valid EnumeratedPowerLevel type') if self.powerLevelType == 'EnumeratedPowerLevel' else self.value if type(self.value) is int else None
        if type(self.value) == str:
            self.value = self.value if re.match('^[0-9]+$',self.value) else None
        if not self.value:
            raise ValueError('{0} is not a valid powerLevel'.format(self.value))

    @property
    def json(self):
        return { '@type': self.powerLevelType, 'value': self.value }

class Request(ashobject):
    def __init__(self, request=None, json=None):
        if request is None and json: request = json

        # Save original request
        self.raw = request

        # Initial required request components
        self.header = self.endpoint = self.payload = {}

        if 'directive' not in request:
            raise TypeError('Invalid message.  It does not contain a directive')
        directive = request['directive']

        self.header = Header(json=directive['header']) if 'header' in directive else None
        self.endpoint = Endpoint(json=directive['endpoint']) if 'endpoint' in directive else None
        self.payload = Payload(json=directive['payload'] if 'payload' in directive else None


class Payload(ashobject):
    def __init__(self, scope=None, grant=None, grantee=None, cameraStreams=None, channel=None, channelMetadata=None, color=None, cookingMode=None, foodItem=None, presetName=None, cookTime=None, cookingPowerLevel=None, meeting=None, targetSetPoint=None, targetSetpointDelta=None, lowerSetpoint=None, upperSetpoint=None, thermostatMode=None, json=None):

        self.scope = Token(json=scope) if scope is not None else Token(json=json.get('scope')) if json and json.get('scope') is not None else None
        self.grant = Grant(json=grant) if grant is not None else Grant(json=json.get('grant')) if json and json.get('grant') is not None else None
        self.grantee = Token(json=grantee) if grantee is not None else Token(json=json.get('grantee')) if json and json.get('grantee') is not None else None

        self.cameraStreams_value = cameraStreams if cameraStreams is not None else json.get('cameraStreams')
        if self.cameraStreams_value:
            self.cameraStreams = []
            if self.cameraStreams_value is not list: self.cameraStreams = [ self.cameraStreams ]
            for item in self.cameraStreams_value:
                self.cameraStreams.append(CameraStream(json=item))
        del(self.cameraStreams_value)

        self.channel = Channel(json=channel) if channel is not None else Channel(json=json.get('channel')) if json and json.get('channel') is not None else None
        self.channelMetadata = ChannelMetadata(json=channelMetadata) if channelMetadata is not None else ChannelMetadata(json=json.get('channelMetadata')) if json and json.get('channelMetadata') is not None else None
        self.color = Color(json=color) if color is not None else Color(json=json.get('color')) if json and json.get('color') is not None else None
        self.cookingMode = ValueObject(json=cookingMode) if cookingMode is not None else ValueObject(json=json['cookingMode']) if json and 'cookingMode' in json else None
        self.foodItem = FoodItem(json=foodItem) if foodItem is not None else FoodItem(json=json.get('foodItem')) if json and json.get('foodItem') is not None else None
        self.presetName = ValueObject(json=presetName) if presetName is not None else ValueObject(json=json['presetName']) if json and 'presetName' in json else None
        self.cookTime = CookTime(json=cookTime) if cookTime is not None else CookTime(json=json['cookTime']) if json and 'cookTime' in json else None

        if payload:
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

class ValueObject(ashobject):
    def __init__(self, value=None, json=None):
        if value is None and json: value = json
        self.value = value if type(value) is not dict else value.get('value')
        self.json = self.value if type(value) is not dict else { 'value': self.value }

class Token(ashobject):
    def __init__(self, type=None, token=None, json=None):
        self.type = type if type is not None else json.get('type') if json else None
        self.token = token if token is not None else json.get('token') if json in json else None
        self.json = { 'type': self.type, 'token': self.token }

class Grant(ashobject):
    def __init__(self, type=None, code=None, json=None):
        self.type = type if type is not None else json.get('type') if json else None
        self.code = code if code is not None else json.get('code') if json else None
        self.json = { 'type': self.type, 'code': self.token }

class Temperature(ashobject):
    def __init__(self, value=None, scale='FAHRENHEIT', json=None):
        self.value = json.get('value') if json else value
        self.scale = json.get('scale') if json else scale

        self.scale = validateValue(self.scale, ['FAHRENHEIT', 'CELSIUS'], '{0} is not a valid temperature scale')
        if type(self.value) in [str, int]:
            try:
                self.value = float(self.value)
            except:
                self.value = None
        if not self.value:
            raise ValueError('{0} is not a valid Temperature'.format(self.value))

    @property
    def json(self):
        return { 'value': self.value, 'scale': self.scale }

class ThermostatMode(ashobject):
    class Value():
        def __init__(self, value=None, customName=None, json=None):
            self.value = json.get('value') if json else value
            self.customName = json.get('customName') if json else customName
            self.value = validateValue(self.value, VALID_THERMOSTATMODES, '{0} is not a valid thermostat mode')

        @property
        def json(self):
            return self.value if not self.customName else { 'value': self.value, 'customName': self.customName }

    def __init__(self, value=None, customName=None, json=None):
        self.value = self.Value(json=json.get('value')) if json else value if isinstance(value, self.Value) else self.Value(value,customName)
        if self.value.value == 'CUSTOM' and not self.value.customName:
            raise ValueError('CUSTOM mode invalid without a customName')


    @property
    def json(self):
        return self.value.json
