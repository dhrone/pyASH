import json
import python_jsonschema_objects as pjs

from utility import VALID_DIRECTIVES

DIRECTIVES = []
for x in VALID_DIRECTIVES.values():
  for y in x:
    if y not in DIRECTIVES: DIRECTIVES.append(y)

with open('alexa_smart_home_message_schema.json') as json_file:
    schema = json.load(json_file)

DIRECTIVES += schema['definitions']['ErrorResponse.properties']['name']['enum']
DIRECTIVES += schema['definitions']['ResponseOrStateReport.properties']['name']['enum']
DIRECTIVES += schema['definitions']['ChangeReport.properties']['name']['enum']
DIRECTIVES += schema['definitions']['DeferredResponse.properties']['name']['enum']
DIRECTIVES += schema['definitions']['Discover.Response.properties']['name']['enum']

cp = { k:v for k,v in schema['definitions']['common.properties'].items() if k in ['payloadVersion', 'message', 'currentDeviceMode', 'messageId', 'correlationToken', 'temperature', 'channel', 'input', 'volume', 'muted', 'timestamp', 'uncertaintyInMilliseconds', 'resolution', 'protocol', 'authorizationType', 'videoCodec', 'audioCodec', 'cameraStream', 'cause', 'version', 'endpointId']
}

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
			cp[objName] = objDef['property']['properties']['value']

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
