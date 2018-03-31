# -*- coding: utf-8 -*-

# Copyright 2018 by dhrone. All Rights Reserved.
#

import pytest
import json

from python_jsonschema_objects import ValidationError

from objects import ASHO
from pyASH import Request

def test_AffiliateCallSign():
	expected = 'NBC'
	a = ASHO.AffiliateCallSign('NBC')
	a.validate()
	assert a.as_dict() == expected

def test_AudioCodec():
	expected = 'G711'
	a = ASHO.AudioCodec('G711')
	a.validate()
	assert a.as_dict() == expected

def test_AuthorizationType():
	expected = 'BASIC'
	a = ASHO.AuthorizationType('BASIC')
	a.validate()
	assert a.as_dict() == expected

def test_BCbrightness():
	expected = 45
	a = ASHO.BCbrightness(45)
	a.validate()
	assert a.as_dict() == expected

def test_Brightness():
	# Name conflict between brightness controller and color(hue, saturation, brightness)
	expected = .5
	a = ASHO.Brightness(.5)
	a.validate()
	assert a.as_dict() == expected

def test_CCcolor():
	expected = { 'hue': .5, 'saturation': .4, 'brightness': .3}
	a = ASHO.CCcolor(hue=.5, saturation=.4, brightness=.3)
	a.validate()
	assert a.as_dict() == expected

def test_CTCcolorTemperatureInKelvin():
	expected = 2500
	a = ASHO.CTCcolorTemperatureInKelvin(2500)
	a.validate()
	assert a.as_dict() == expected

def test_CallSign():
	expected = 'NBC4'
	a = ASHO.CallSign('NBC4')
	a.validate()
	assert a.as_dict() == expected

def test_CameraStream():
	expected = {
		"protocol": "RTSP",
		"resolution": {"width":1920, "height":1080},
	    "authorizationType": "BASIC",
	    "videoCodec": "H264",
	    "audioCodec": "G711",
		"uri": 'http://some/uri'
	}

	a = ASHO.CameraStream(resolution=ASHO.Resolution(width=1920,height=1080), protocol=ASHO.Protocol('RTSP'), authorizationType=ASHO.AuthorizationType('BASIC'), videoCodec=ASHO.VideoCodec('H264'), audioCodec=ASHO.AudioCodec('G711'), uri=ASHO.Uri('http://some/uri'))
	a.validate()
	assert a.as_dict() == expected

	a = ASHO.CameraStream().from_json(json.dumps(expected))
	a.validate()
	assert a.as_dict() == expected

def test_Cause():
	expected = {'type':'PHYSICAL_INTERACTION'}
	a = ASHO.Cause(type='PHYSICAL_INTERACTION')
	a.validate()
	assert a.as_dict() == expected

def test_Channel():
	expected = { 'number': '504', 'callSign': 'NBC4', 'affiliateCallSign': 'NBC'}
	a = ASHO.Channel(number='504', callSign='NBC4', affiliateCallSign='NBC')
	a.validate()
	assert a.as_dict() == expected

def test_CorrelationToken():
	expected = 'Correlation-Token'
	a = ASHO.CorrelationToken('Correlation-Token')
	a.validate()
	assert a.as_dict() == expected

def test_CurrentDeviceMode():
	expected = 'ASLEEP'
	a = ASHO.CurrentDeviceMode('ASLEEP')
	a.validate()
	assert a.as_dict() == expected

def test_EHconnectivity():
	expected = {'value':'OK'}
	a = ASHO.EHconnectivity(value='OK')
	a.validate()
	assert a.as_dict() == expected

def test_Endpoint():
	expected =  {
      "endpointId": "appliance-001",
       "scope": {
                "type": "BearerToken",
                "token": "access-token-from-skill"
            },
      "cookie": {}
    }

	a = ASHO.Endpoint(endpointId = 'appliance-001', scope=ASHO.Scope(type='BearerToken', token='access-token-from-skill'),cookie={})
	assert a.as_dict() == expected

def test_EndpointId():
	expected = 'device-001'
	a = ASHO.EndpointId('device-001')
	a.validate()
	assert a.as_dict() == expected

def test_ExpirationTime():
	expected = '2017-02-03T16:20:50.52Z'
	a = ASHO.ExpirationTime('2017-02-03T16:20:50.52Z')
	a.validate()
	assert a.as_dict() == expected

def test_Header():
	def cleanse(json):
		if 'messageId' in json:
			json['messageId']='TOKEN'
		return json

	expected = {
	  "namespace": "Alexa.CameraStreamController",
	  "name": "Response",
	  "payloadVersion": "3",
	  "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
	  "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
	}

	a = ASHO.Header(namespace='Alexa.CameraStreamController', name='Response', messageId="5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4", correlationToken='dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg==', payloadVersion='3')
	a.validate()
	assert a.as_dict() == expected

	a = ASHO.Header().from_json(json.dumps(expected))
	a.validate()
	assert a.as_dict() == expected

def test_Height():
	expected = 1920
	a = ASHO.Height(1920)
	a.validate()
	assert a.as_dict() == expected

	with pytest.raises(ValidationError) as e_info:
		a = ASHO.Height('1920')

def test_Hue():
	expected = .5
	a = ASHO.Hue(.5)
	a.validate()
	assert a.as_dict() == expected

	with pytest.raises(ValidationError) as e_info:
		a = ASHO.Hue(2000)

def test_LClockstate():
	expected = 'JAMMED'
	a = ASHO.LClockState('JAMMED')
	a.validate()
	assert a.as_dict() == expected

	with pytest.raises(ValidationError) as e_info:
		a = ASHO.LClockState('OPEN')

def test_IdleTimeoutSeconds():
	expected = 60
	a = ASHO.IdleTimeoutSeconds(60)
	a.validate()
	assert a.as_dict() == expected

	with pytest.raises(ValidationError) as e_info:
		a = ASHO.IdleTimeoutSeconds('60')

def test_Input():
	expected = 'CD'
	a = ASHO.Input('CD')
	a.validate()
	assert a.as_dict() == expected

	with pytest.raises(ValidationError) as e_info:
		a = ASHO.Input(0)

def test_Message():
	expected = 'A message'
	a = ASHO.Message('A message')
	a.validate()
	assert a.as_dict() == expected

	with pytest.raises(ValidationError) as e_info:
		a = ASHO.Message(0)

def test_MessageId():
	expected = '123-456'
	a = ASHO.MessageId('123-456')
	a.validate()
	assert a.as_dict() == expected

	with pytest.raises(ValidationError) as e_info:
		a = ASHO.MessageId('123|456')

def test_Muted():
	expected = False
	a = ASHO.Muted(False)
	a.validate()
	assert a.as_dict() == expected

	with pytest.raises(ValidationError) as e_info:
		a = ASHO.Muted('Off')

def test_Name():
	expected = 'Response'
	a = ASHO.Name('Response')
	a.validate()
	assert a.as_dict() == expected

	with pytest.raises(ValidationError) as e_info:
		a = ASHO.Name('NotAResponse')

def test_Namespace():
	expected = 'Alexa.BrightnessController'
	a = ASHO.Namespace('Alexa.BrightnessController')
	a.validate()
	assert a.as_dict() == expected

	with pytest.raises(ValidationError) as e_info:
		a = ASHO.Namespace('Alexa.NewController')

def test_Number():
	expected = '504'
	a = ASHO.Number('504')
	a.validate()
	assert a.as_dict() == expected

	with pytest.raises(ValidationError) as e_info:
		a = ASHO.Number(504)

def test_PCpercentage():
	expected = 67
	a = ASHO.PCpercentage(67)
	a.validate()
	assert a.as_dict() == expected

	with pytest.raises(ValidationError) as e_info:
		a = ASHO.PCpercentage(102)

def test_PCpowerState():
	expected = 'ON'
	a = ASHO.PCpowerState('ON')
	a.validate()
	assert a.as_dict() == expected

	with pytest.raises(ValidationError) as e_info:
		a = ASHO.PCpowerState(True)

def test_PLCpowerLevel():
	expected = 50
	a = ASHO.PLCpowerLevel(50)
	a.validate()
	assert a.as_dict() == expected

	with pytest.raises(ValidationError) as e_info:
		a = ASHO.PLCpowerLevel(102)

def test_PayloadVersion():
	expected = '3'
	a = ASHO.PayloadVersion('3')
	a.validate()
	assert a.as_dict() == expected

	with pytest.raises(ValidationError) as e_info:
		a = ASHO.PayloadVersion('2')

def test_Protocol():
	expected = 'RTSP'
	a = ASHO.Protocol('RTSP')
	a.validate()
	assert a.as_dict() == expected

	with pytest.raises(ValidationError) as e_info:
		a = ASHO.Protocol('MPEG2')

def test_Resolution():
	expected = { 'width': 1920, 'height': 1080 }
	a = ASHO.Resolution(width=1920, height=1080)
	a.validate()
	assert a.as_dict() == expected

	with pytest.raises(ValidationError) as e_info:
		a = ASHO.Resolution(width='1920')

def test_Saturation():
	expected = 0.385
	a = ASHO.Saturation(0.385)
	a.validate()
	assert a.as_dict() == expected

	with pytest.raises(ValidationError) as e_info:
		a = ASHO.Saturation(2)

def test_Scale():
	expected = 'KELVIN'
	a = ASHO.Scale('KELVIN')
	a.validate()
	assert a.as_dict() == expected

	with pytest.raises(ValidationError) as e_info:
		a = ASHO.Scale('CHILLY')

def test_Scope():
	expected = { 'type': 'BearerToken', 'token': 'Atoken'}
	a = ASHO.Scope(type='BearerToken', token='Atoken')
	a.validate()
	assert a.as_dict() == expected

	with pytest.raises(ValidationError) as e_info:
		a = ASHO.Scope(type='NotaBearerToken', token='Atoken')

def test_TCsetpoint():
	expected = { 'scale': 'CELSIUS', 'value': 25.3}
	a = ASHO.TCsetpoint(scale='CELSIUS', value=25.3)
	a.validate()
	assert a.as_dict() == expected

	with pytest.raises(ValidationError) as e_info:
		a = ASHO.TCsetpoint(scale='Chilly', value=25.3)

def test_TCthermostatMode():
	expected = 'CUSTOM'
	a = ASHO.TCthermostatMode('CUSTOM')
	a.validate()
	assert a.as_dict() == expected

	with pytest.raises(ValidationError) as e_info:
		a = ASHO.TCthermostatMode('HOT')

def test_Temperature():
	expected = { 'scale': 'CELSIUS', 'value': 25.3}
	a = ASHO.Temperature(scale='CELSIUS', value=25.3)
	a.validate()
	assert a.as_dict() == expected

	with pytest.raises(ValidationError) as e_info:
		a = ASHO.Temperature(scale='Chilly', value=25.3)

def test_Timestamp():
	expected = '2017-02-03T16:20:50.52Z'
	a = ASHO.Timestamp('2017-02-03T16:20:50.52Z')
	a.validate()
	assert a.as_dict() == expected

def test_Token():
	expected = 'a token'
	a = ASHO.Token('a token')
	a.validate()
	assert a.as_dict() == expected

def test_UncertaintyInMilliseconds():
	expected = 1000
	a = ASHO.UncertaintyInMilliseconds(1000)
	a.validate()
	assert a.as_dict() == expected

def test_Uri():
	expected = 'http://an.address.on.the.network/stuff'
	a = ASHO.Uri('http://an.address.on.the.network/stuff')
	a.validate()
	assert a.as_dict() == expected

def test_VideoCodec():
	expected = 'MPEG2'
	a = ASHO.VideoCodec('MPEG2')
	a.validate()
	assert a.as_dict() == expected

	with pytest.raises(ValidationError) as e_info:
		a = ASHO.VideoCodec('MPEG1000')

def test_Volume():
	expected = 100
	a = ASHO.Volume(100)
	a.validate()
	assert a.as_dict() == expected

	expected = 0
	a = ASHO.Volume(0)
	a.validate()
	assert a.as_dict() == expected

	with pytest.raises(ValidationError) as e_info:
		a = ASHO.Volume(101)
		a = ASHO.Volume(-1)


def test_Width():
	expected = 1080
	a = ASHO.Height(1080)
	a.validate()
	assert a.as_dict() == expected

	with pytest.raises(ValidationError) as e_info:
		a = ASHO.Height('1080')


def test_Request_1():
	expected = {
	    "directive": {
	        "header": {
	            "namespace": "Alexa.BrightnessController",
	            "name": "AdjustBrightness",
	            "payloadVersion": "3",
	            "messageId": "1bd5d003-31b9-476f-ad03-71d471922820",
	            "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
	        },
	        "endpoint": {
	            "scope": {
	                "type": "BearerToken",
	                "token": "access-token-from-skill"
	            },
	            "endpointId": "endpoint-001",
	            "cookie": {}
	        },
	        "payload": {
	            "brightnessDelta": -25
	        }
	    }
	}
	a = Request(expected)
	assert a.header.namespace == 'Alexa.BrightnessController'
	assert a.header.name == 'AdjustBrightness'
	assert a.endpointId == 'endpoint-001'
	assert a.endpoint.token == 'access-token-from-skill'
	assert a.payload.brightnessDelta == -25
