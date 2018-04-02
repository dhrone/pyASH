# -*- coding: utf-8 -*-

# Copyright 2018 by dhrone. All Rights Reserved.
#

import json
import os
import python_jsonschema_objects as pjs

from .utility import VALID_DIRECTIVES


with open(os.path.dirname(__file__)+'/alexa_smart_home_message_schema.json') as json_file:
    schema = json.load(json_file)

# Calculate all of the possible values for name in a header
DIRECTIVES = list(set([item for nested in VALID_DIRECTIVES.values() for item in nested]))
DIRECTIVES += schema['definitions']['ErrorResponse.properties']['name']['enum']
DIRECTIVES += schema['definitions']['ResponseOrStateReport.properties']['name']['enum']
DIRECTIVES += schema['definitions']['ChangeReport.properties']['name']['enum']
DIRECTIVES += schema['definitions']['DeferredResponse.properties']['name']['enum']
DIRECTIVES += schema['definitions']['Discover.Response.properties']['name']['enum']

cp = { k:v for k,v in schema['definitions']['common.properties'].items() if k in ['payloadVersion', 'message', 'currentDeviceMode', 'messageId', 'correlationToken', 'temperature', 'channel', 'input', 'volume', 'muted', 'timestamp', 'uncertaintyInMilliseconds', 'resolution', 'protocol', 'authorizationType', 'videoCodec', 'audioCodec', 'cameraStream', 'cause', 'version', 'endpointId']}

# Add Header
cp['header'] = schema['definitions']['ErrorResponse.properties']['header.general']
cp['header']['properties']['namespace']['enum'] = [x for x in VALID_DIRECTIVES.keys()]
cp['header']['properties']['name'] = { 'enum': DIRECTIVES }

cp['scope'] = {"type": "object", "required": ["type", "token"], "properties": {"type": {"enum": ["BearerToken"]}, "token": {"type": "string", "minLength": 1}}}

cp['endpoint'] = {"type": "object", "additionalProperties": False, "required": ["endpointId"], "properties": {"scope": {"$ref": "#/definitions/scope"}, "endpointId": {"$ref": "#/definitions/common.properties/endpointId"}, "cookie": {"type": "object"}}}


# Add objects from interfaces if missing from common.properties
for iName, iValue in schema['definitions']['common.properties']['interfaces'].items():
    if iName in ['BrightnessController', 'ColorController', 'ColorTemperatureController', 'EndpointHealth', 'LockController', 'PercentageController', 'PowerController', 'PowerLevelController', 'ThermostatController']:
        for objName, objDef in { k:v for k,v in iValue.items() if k not in 'capabilities'}.items():
            iobj = ''.join([ x for x in iName if x.isupper() ])+objName
            cp[iobj] = objDef['property']['properties']['value']

def fixCommonProperties(ashSchema):
    for k, v in ashSchema.items():
        if k == '$ref':
            ashSchema[k] = '/'.join([ x for x in v.split("/") if x not in ['common.properties'] ])
        elif type(v) is dict: fixCommonProperties(v)
        elif type(v) is list:
            for item in v:
                if type(item) is dict: fixCommonProperties(item)

fixCommonProperties(cp)

schema = {
    "title": "Test",
    "id": "tst",
    "definitions": cp,
    "oneOf": [
        { "$ref": "#/definitions/channel"}
    ]
}

builder = pjs.ObjectBuilder(schema)
ASHO = builder.build_classes()

class Request(dict):
    """Simplifies retrieval of values from a request.

    Request takes a json object and exposes its contents as dynamically generated
    attributes.  It will search, depth-first to find a key within the json object
    that matches the requested attribute and will raise an AttributeError if no key
    within the json object matches the requested attribute.  If you need to ensure
    that the key you are requesting comes from a specific path within the json
    object, you can string together attributes to specify the path that you want
    Request to follow to find the key.

    Note:

        Request will only return the first value that matches the requested attribute

    Example:

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
        request = Request(json)
        >>> request.endpointId
        "endpoint-001"
        >>> request.endpoint.endpointId
        "endpoint-001"
        >>> request.payload
        { 'brightnessDelta': -25 }
        >>> request.brightnessDelta
        -25
        >>> request.payload.brightnessDelta
        -25
    """
    def __init__(self, rawRequest):
        super(Request, self).__init__(rawRequest)
        self.raw = rawRequest

    def __getattr__(self, name):
        if name == 'raw': raise AttributeError()
        res = self.findkey(name, self.raw)
        if isinstance(res, dict):
            return Request(res)
        if res:
            return res
        raise AttributeError()

    def findkey(self, key, dictionary):
        for k,v in dictionary.items():
            if k==key:
                return v
            elif isinstance(v, dict):
                res = self.findkey(key,v)
                if res: return res
            else:
                continue
        return None
