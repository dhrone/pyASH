# -*- coding: utf-8 -*-

# Copyright 2018 by dhrone. All Rights Reserved.
#

import pytest

from objects import *

def test_CameraStream_json():
	json = {
		"protocols": ["RTSP"],
		"resolutions": [{"width":1920, "height":1080}, {"width":1280, "height":720}],
	    "authorizationTypes": ["BASIC"],
	    "videoCodecs": ["H264", "MPEG2"],
	    "audioCodecs": ["G711"]
	}
	a = CameraStream(json=json)
	assert a.jsonDiscover == json

	a = CameraStream(resolutions=[(1920,1080), (1280,720)], protocols='RTSP', authorizationTypes='BASIC', videoCodecs=['H264','MPEG2'], audioCodecs='G711')
	assert a.jsonDiscover == json

def test_Endpoint():
	json =  {
      "endpointId": "appliance-001",
       "scope": {
                "type": "BearerToken",
                "token": "access-token-from-skill"
            },
      "cookie": {}
    }
	a = Endpoint(json=json)
	assert a.json == json

	a = Endpoint(endpointId = 'appliance-001', token='access-token-from-skill',cookie={})
	assert a.json == json


def test_Header():
	def cleanse(json):
		if 'messageId' in json:
			json['messageId']='TOKEN'
		return json

	json = {
	  "namespace": "Alexa.CameraStreamController",
	  "name": "Response",
	  "payloadVersion": "3",
	  "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
	  "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
	}
	a = Header(json=json)
	assert cleanse(a.json) == cleanse(json)

	a = Header(namespace='Alexa.CameraStreamController', name='Response', correlationToken='dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg==')
	assert cleanse(a.json) == cleanse(json)

def test_Request_1():
	json = {
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
	a = Request(json=json)
	assert a.header.namespace == 'Alexa.BrightnessController'
	assert a.header.name == 'AdjustBrightness'
	assert a.endpoint.id == 'endpoint-001'
	assert a.endpoint.token == 'access-token-from-skill'
	assert a.payload.brightnessDelta == -25
