# -*- coding: utf-8 -*-

# Copyright 2018 by dhrone. All Rights Reserved.
#

import pytest
import json

from python_jsonschema_objects import ValidationError

from pyASH.exceptions import *
from pyASH.pyASH import pyASH

from pyASH.objects import Request

# Imports for v3 validation
import jsonschema
from jsonschema import validate
import json
from pyASH.validation import validate_message

@pytest.fixture
def setup():
    request = {
        "directive": {
            "header": {
                "namespace": "Alexa.PowerController",
                "name": "TurnOff",
                "payloadVersion": "3",
                "messageId": "1bd5d003-31b9-476f-ad03-71d471922820",
                "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-skill"
                },
                "endpointId": "dhroneTV:device_1",
                "cookie": {}
            },
            "payload": {}
        }
    }
    return Request(request)

def validate(request, response):
    validateFailed = False
    try:
        validate_message(request, response)
    except:
        validateFailed=True
        print ('Validation Error')
    if validateFailed:
        print (response)
        raise Exception

def test_INTERNAL_ERROR(setup):
    request = setup

    try:
        raise INTERNAL_ERROR('test message')
    except pyASH_EXCEPTION as e:
        response = pyASH._errorResponse(request, e)
        validate(request, response)

def test_USER_NOT_FOUND_EXCEPTION(setup):
    request = setup
    try:
        raise USER_NOT_FOUND_EXCEPTION('test message')
    except pyASH_EXCEPTION as e:
        response = pyASH._errorResponse(request, e)
        validate(request, response)
