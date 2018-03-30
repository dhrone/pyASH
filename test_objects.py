# -*- coding: utf-8 -*-

# Copyright 2018 by dhrone. All Rights Reserved.
#

import pytest
import json

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

def test_Connectivity():
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
