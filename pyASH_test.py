
import logging
import time
import json
import uuid
import os
#from botocore.vendored import requests
#import boto3
import urllib
from datetime import datetime
from datetime import timedelta

import pyASH


# Setup logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

alexa_testset = [
    { 'name': 'AcceptGrantTest',
        'input': {
          "directive": {
            "header": {
              "namespace": "Alexa.Authorization",
              "name": "AcceptGrant",
              "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
              "payloadVersion": "3"
            },
            "payload": {
              "grant": {
                "type": "OAuth2.AuthorizationCode",
                "code": "VGhpcyBpcyBhbiBhdXRob3JpemF0aW9uIGNvZGUuIDotKQ=="
              },
              "grantee": {
                "type": "BearerToken",
                "token": "access-token-from-skill"
              }
            }
          }
        },
        'output': {
          "event": {
            "header": {
              "messageId": "30d2cd1a-ce4f-4542-aa5e-04bd0a6492d5",
              "namespace": "Alexa.Authorization",
              "name": "AcceptGrant.Response",
              "payloadVersion": "3"
            },
            "payload": {
            }
          }
        }
    },
    { 'name': 'DiscoverTest',
        'input': {
            "directive": {
                "header": {
                    "namespace": "Alexa.Discovery",
                    "name": "Discover",
                    "payloadVersion": "3",
                    "messageId": "1bd5d003-31b9-476f-ad03-71d471922820"
                },
                "payload": {
                        "scope": {
                        "type": "BearerToken",
                        "token": "access-token-from-skill"
                    }
                }
            }
        },
        'output': {
            "event": {
                "header": {
                  "namespace": "Alexa.Discovery",
                  "name": "Discover.Response",
                  "payloadVersion": "3",
                  "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4"
                },
                "payload": {
                  "endpoints": [
                    {
                      "endpointId": "appliance-001",
                      "friendlyName": "Living Room Light",
                      "description": "Smart Light by Sample Manufacturer",
                      "manufacturerName": "Sample Manufacturer",
                      "displayCategories": [
                        "LIGHT"
                      ],
                      "cookie": {
                        "extraDetail1": "optionalDetailForSkillAdapterToReferenceThisDevice",
                        "extraDetail2": "There can be multiple entries",
                        "extraDetail3": "but they should only be used for reference purposes",
                        "extraDetail4": "This is not a suitable place to maintain current device state"
                      },
                      "capabilities": [
                        {
                          "type": "AlexaInterface",
                          "interface": "Alexa.ColorTemperatureController",
                          "version": "3",
                          "properties": {
                            "supported": [
                              {
                                "name": "colorTemperatureInKelvin"
                              }
                            ],
                            "proactivelyReported": True,
                            "retrievable": True
                          }
                        },
                        {
                          "type": "AlexaInterface",
                          "interface": "Alexa.EndpointHealth",
                          "version": "3",
                          "properties": {
                            "supported": [
                              {
                                "name": "connectivity"
                              }
                            ],
                            "proactivelyReported": True,
                            "retrievable": True
                          }
                        },
                        {
                          "type": "AlexaInterface",
                          "interface": "Alexa",
                          "version": "3"
                        },
                        {
                          "type": "AlexaInterface",
                          "interface": "Alexa.ColorController",
                          "version": "3",
                          "properties": {
                            "supported": [
                              {
                                "name": "color"
                              }
                            ],
                            "proactivelyReported": True,
                            "retrievable": True
                          }
                        },
                        {
                          "type": "AlexaInterface",
                          "interface": "Alexa.PowerController",
                          "version": "3",
                          "properties": {
                            "supported": [
                              {
                                "name": "powerState"
                              }
                            ],
                            "proactivelyReported": True,
                            "retrievable": True
                          }
                        },
                        {
                          "type": "AlexaInterface",
                          "interface": "Alexa.BrightnessController",
                          "version": "3",
                          "properties": {
                            "supported": [
                              {
                                "name": "brightness"
                              }
                            ],
                            "proactivelyReported": True,
                            "retrievable": True
                          }
                        }
                      ]
                    },
                    {
                      "endpointId": "appliance-002",
                      "friendlyName": "Hallway Thermostat",
                      "description": "Smart Thermostat by Sample Manufacturer",
                      "manufacturerName": "Sample Manufacturer",
                      "displayCategories": [
                        "THERMOSTAT"
                      ],
                      "cookie": {},
                      "capabilities": [
                        {
                          "type": "AlexaInterface",
                          "interface": "Alexa",
                          "version": "3"
                        },
                        {
                          "type": "AlexaInterface",
                          "interface": "Alexa.ThermostatController",
                          "version": "3",
                          "properties": {
                            "supported": [
                              {
                                "name": "lowerSetpoint"
                              },
                              {
                                "name": "targetSetpoint"
                              },
                              {
                                "name": "upperSetpoint"
                              },
                              {
                                "name": "thermostatMode"
                              }
                            ],
                            "proactivelyReported": True,
                            "retrievable": True
                          }
                        },
                        {
                          "type": "AlexaInterface",
                          "interface": "Alexa.TemperatureSensor",
                          "version": "3",
                          "properties": {
                            "supported": [
                              {
                                "name": "temperature"
                              }
                            ],
                            "proactivelyReported": False,
                            "retrievable": True
                          }
                        }
                      ]
                    },
                    {
                      "endpointId": "appliance-003",
                      "friendlyName": "Front Door",
                      "description": "Smart Lock by Sample Manufacturer",
                      "manufacturerName": "Sample Manufacturer",
                      "displayCategories": [
                        "SMARTLOCK"
                      ],
                      "cookie": {},
                      "capabilities": [
                        {
                          "type": "AlexaInterface",
                          "interface": "Alexa.LockController",
                          "version": "3",
                          "properties": {
                            "supported": [
                              {
                                "name": "lockState"
                              }
                            ],
                            "proactivelyReported": True,
                            "retrievable": True
                          }
                        },
                        {
                          "type": "AlexaInterface",
                          "interface": "Alexa.EndpointHealth",
                          "version": "3",
                          "properties": {
                              "supported": [
                                  {
                                      "name": "connectivity"
                                  }
                              ],
                              "proactivelyReported": True,
                              "retrievable": True
                          }
                        }
                      ]
                    },
                    {
                      "endpointId": "appliance-004",
                      "friendlyName": "Goodnight",
                      "description": "Smart Scene by Sample Manufacturer",
                      "manufacturerName": "Sample Manufacturer",
                      "displayCategories": [
                        "SCENE_TRIGGER"
                      ],
                      "cookie": {},
                      "capabilities": [
                        {
                          "type": "AlexaInterface",
                          "interface": "Alexa.SceneController",
                          "version": "3",
                          "supportsDeactivation": False,
                          "proactivelyReported": True
                        }
                      ]
                    },
                    {
                      "endpointId": "appliance-005",
                      "friendlyName": "Watch TV",
                      "description": "Smart Activity by Sample Manufacturer",
                      "manufacturerName": "Sample Manufacturer",
                      "displayCategories": [
                        "ACTIVITY_TRIGGER"
                      ],
                      "cookie": {},
                      "capabilities": [
                        {
                          "type": "AlexaInterface",
                          "interface": "Alexa",
                          "version": "3"
                        },
                        {
                          "type": "AlexaInterface",
                          "interface": "Alexa.SceneController",
                          "version": "3",
                          "supportsDeactivation": True,
                          "proactivelyReported": True
                        },
                        {
                          "type": "AlexaInterface",
                          "interface": "Alexa.EndpointHealth",
                          "version": "3",
                          "properties": {
                              "supported": [
                                  {
                                      "name": "connectivity"
                                  }
                              ],
                              "proactivelyReported": True,
                              "retrievable": True
                          }
                        }
                      ]
                    },
                    {
                      "endpointId": "appliance-006",
                      "friendlyName": "Back Door Camera",
                      "description": "Smart Camera by Sample Manufacturer",
                      "manufacturerName": "Sample Manufacturer",
                      "displayCategories": [
                        "CAMERA"
                      ],
                      "cookie": {},
                      "capabilities": [
                        {
                          "type": "AlexaInterface",
                          "interface": "Alexa",
                          "version": "3"
                        },
                        {
                          "type": "AlexaInterface",
                          "interface": "Alexa.CameraStreamController",
                          "version": "3",
                          "cameraStreamConfigurations": [
                            {
                              "protocols": [
                                "RTSP"
                              ],
                              "resolutions": [
                                {
                                  "width": 1920,
                                  "height": 1080
                                },
                                {
                                  "width": 1280,
                                  "height": 720
                                }
                              ],
                              "authorizationTypes": [
                                "BASIC"
                              ],
                              "videoCodecs": [
                                "H264",
                                "MPEG2"
                              ],
                              "audioCodecs": [
                                "G711"
                              ]
                            },
                            {
                              "protocols": [
                                "RTSP"
                              ],
                              "resolutions": [
                                {
                                  "width": 1920,
                                  "height": 1080
                                },
                                {
                                  "width": 1280,
                                  "height": 720
                                }
                              ],
                              "authorizationTypes": [
                                "NONE"
                              ],
                              "videoCodecs": [
                                "H264"
                              ],
                              "audioCodecs": [
                                "AAC"
                              ]
                            }
                          ]
                        },
                        {
                          "type": "AlexaInterface",
                          "interface": "Alexa.PowerController",
                          "version": "3",
                          "properties": {
                            "supported": [
                              {
                                "name": "powerState"
                              }
                            ],
                            "proactivelyReported": True,
                            "retrievable": True
                          }
                        },
                        {
                          "type": "AlexaInterface",
                          "interface": "Alexa.EndpointHealth",
                          "version": "3",
                          "properties": {
                              "supported": [
                                  {
                                      "name": "connectivity"
                                  }
                              ],
                              "proactivelyReported": True,
                              "retrievable": True
                          }
                        }
                      ]
                    }
                  ]
                }
              }
        }
    },
    { 'name': 'Adjust Brightness Test',
        'input': {
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
                "token": "access-token-from-Amazon"
              },
              "endpointId": "appliance-001",
              "cookie": {}
            },
            "payload": {
              "brightnessDelta": 3
            }
          }
        },
        'output':{
          "context": {
            "properties": [ {
              "namespace": "Alexa.BrightnessController",
              "name": "brightness",
              "value": 42,
              "timeOfSample": "2017-02-03T16:20:50.52Z",
              "uncertaintyInMilliseconds": 1000
            } ]
          },
          "event": {
            "header": {
              "namespace": "Alexa",
              "name": "Response",
              "payloadVersion": "3",
              "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
              "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
              "scope": {
                "type": "BearerToken",
                "token": "access-token-from-Amazon"
              },
              "endpointId": "appliance-001"
            },
            "payload": {}
          }
        }
    },
    {
        'name': 'Calendar Test',
        'input':
        {
            "directive": {
                "endpoint": {
                    "endpointId": "applianceId",
                    "cookie": {
                    },
                    "scope": {
                        "type": "BearerTokenWithPartition",
                        "token": "access-token-from-skill",
                        "partition": "room101"
                    }
                },
                "header": {
                    "namespace": "Alexa.Calendar",
                    "name": "GetCurrentMeeting",
                    "messageId": "15d0ec9d-801d-4f51-9321-206510d64d9c",
                    "payloadVersion": "3",
                    "correlationToken": "dFMb0z+PgpgdDmlu/jCc8ptlAKulUj90jSqg=="
                },
                "payload": {}
            }
        },
        'output':
        {
            "event": {
                "header": {
                    "namespace": "Alexa.Calendar",
                    "name": "Response",
                    "messageId": "c60bc9c1-63c8-4cfc-ae44-22c43140c32e",
                    "payloadVersion": "3",
                    "correlationToken": "dFMb0z+PgpgdDmlu/jCc8ptlAKulUj90jSqg=="
                },
                "payload": {
                    "organizerName": "John Smith",
                    "calendarEventId": "1234567890"
                }
            }
        }
    },
    {
        'name': 'Camera Test',
        'input':
        {
          "directive": {
            "header": {
              "namespace": "Alexa.CameraStreamController",
              "name": "InitializeCameraStreams",
              "payloadVersion": "3",
              "messageId": "1bd5d003-31b9-476f-ad03-71d471922820",
              "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
              "endpointId": "appliance-001",
               "scope": {
                        "type": "BearerToken",
                        "token": "access-token-from-skill"
                    },
              "cookie": {}
            },
            "payload": {
              "cameraStreams": [{
                "protocol": "RTSP",
                "resolution": {
                  "width": 1920,
                  "height": 1080
                },
                "authorizationType": "BASIC",
                "videoCodec": "H264",
                "audioCodec": "AAC"
              }, {
                "protocol": "RTSP",
                "resolution": {
                  "width": 1280,
                  "height": 720
                },
                "authorizationType": "NONE",
                "videoCodec": "MPEG2",
                "audioCodec": "G711"
              }]
            }
          }
        },
        'output':
        {
          "event": {
            "header": {
              "namespace": "Alexa.CameraStreamController",
              "name": "Response",
              "payloadVersion": "3",
              "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
              "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
            },
            "endpoint": {
               "endpointId": "appliance-001"
            },
            "payload": {
              "cameraStreams": [ {
                "uri": "rtsp://username:password@link.to.video:443/feed1.mp4",
                "expirationTime": "2017-02-03T16:20:50.52Z",
                "idleTimeoutSeconds": 30,
                "protocol": "RTSP",
                "resolution": {
                  "width": 1920,
                  "height": 1080
                },
                "authorizationType": "BASIC",
                "videoCodec": "H264",
                "audioCodec": "AAC"
              }
             ],
              "imageUri": "https://username:password@link.to.image/image.jpg"
            }
          }
        }
    },
    {
        'name': 'Change channel test',
        'input': {
          "directive": {
            "header": {
              "namespace": "Alexa.ChannelController",
              "name": "ChangeChannel",
              "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
              "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg==",
              "payloadVersion": "3"
            },
            "endpoint": {
              "scope": {
                "type": "BearerToken",
                "token": "access-token-from-skill"
              },
              "endpointId": "appliance-001",
              "cookie": {

              }
            },
            "payload": {
              "channel": {
                  "number": "1234",
                  "callSign": "callsign1",
                  "affiliateCallSign": "callsign2",
                  "uri": "someUrl"
              },
              "channelMetadata": {
                  "name": "Alternate Channel Name",
                  "image": "urlToImage"
              }
            }
          }
        },
        'output': {
          "context": {
            "properties": [
              {
                "namespace": "Alexa.ChannelController",
                "name": "channel",
                "value": {
                  "number": "1234",
                  "callSign": "callsign1",
                  "affiliateCallSign": "callsign2"
                },
                "timeOfSample": "2017-02-03T16:20:50.52Z",
                "uncertaintyInMilliseconds": 0
              }
            ]
          },
          "event": {
            "header": {
              "messageId": "30d2cd1a-ce4f-4542-aa5e-04bd0a6492d5",
              "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg==",
              "namespace": "Alexa",
              "name": "Response",
              "payloadVersion": "3"
            },
            "endpoint":{
              "endpointId":"appliance-001"
            },
            "payload":{ }
         }
        }
    },
    {
        'name': 'PlaybackController Fastforward Test',
        'input': {
          "directive": {
            "header": {
              "namespace": "Alexa.PlaybackController",
              "name": "FastForward",
              "messageId": "c8d53423-b49b-48ee-9181-f50acedf2870",
              "payloadVersion": "3"
            },
            "endpoint": {
              "scope": {
                "type": "BearerToken",
                "token": "access-token-from-skill"
              },
              "endpointId": "appliance-001",
              "cookie": {

              }
            },
            "payload": {
            }
          }
        },
        'output':{
          "context": {
            "properties": []
          },
          "event": {
            "header": {
              "messageId": "30d2cd1a-ce4f-4542-aa5e-04bd0a6492d5",
              "namespace": "Alexa",
              "name": "Response",
              "payloadVersion": "3"
            },
            "endpoint":{
               "endpointId":"appliance-001"
            },
            "payload":{ }
         }
        }
    },
    {
        'name': 'Speaker Volume Test',
        'input':{
          "directive": {
            "header": {
              "namespace": "Alexa.Speaker",
              "name": "SetVolume",
              "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
              "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg==",
              "payloadVersion": "3"
            },
            "endpoint": {
              "scope": {
                "type": "BearerToken",
                "token": "access-token-from-skill"
              },
              "endpointId": "appliance-001",
              "cookie": {

              }
            },
            "payload": {
              "volume": 50
            }
          }
        },
        'output':{
          "context": {
            "properties": [
              {
                "namespace": "Alexa.Speaker",
                "name": "volume",
                "value": 50,
                "timeOfSample": "2017-02-03T16:20:50.52Z",
                "uncertaintyInMilliseconds": 0
              },
              {
                "namespace": "Alexa.Speaker",
                "name": "muted",
                "value": False,
                "timeOfSample": "2017-02-03T16:20:50.52Z",
                "uncertaintyInMilliseconds": 0
              }
            ]
          },
          "event": {
            "header": {
              "messageId": "30d2cd1a-ce4f-4542-aa5e-04bd0a6492d5",
              "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg==",
              "namespace": "Alexa",
              "name": "Response",
              "payloadVersion": "3"
            },
            "endpoint":{
               "endpointId":"appliance-001"
            },
            "payload":{ }
         }
        }
    },
    {
        'name': 'ReportState test',
        'input': {
            "directive": {
                "header": {
                    "namespace": "Alexa",
                    "name": "ReportState",
                    "payloadVersion": "3",
                    "messageId": "1bd5d003-31b9-476f-ad03-71d471922820",
                    "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
                },
                "endpoint": {
                    "endpointId": "endpoint-001",
                    "cookie": {},
                    "scope": {
                        "type": "BearerToken",
                        "token": "access-token-from-Amazon"
                    }
                },
                "payload": {}
            }
        },
        'output': {
            "context": {
                "properties": [
                    {
                        "namespace": "Alexa.EndpointHealth",
                        "name": "connectivity",
                        "value": {
                            "value": "OK"
                        },
                        "timeOfSample": "2017-09-27T18:30:30.45Z",
                        "uncertaintyInMilliseconds": 200
                    },
                    {
                        "name": "targetSetpoint",
                        "namespace": "Alexa.ThermostatController",
                        "value": {
                            "scale": "CELSIUS",
                            "value": 25
                        },
                        "timeOfSample": "2017-09-27T18:30:30.45Z",
                        "uncertaintyInMilliseconds": 200
                    },
                    {
                        "name": "thermostatMode",
                        "namespace": "Alexa.ThermostatController",
                        "value": "AUTO",
                        "timeOfSample": "2017-09-27T18:30:30.45Z",
                        "uncertaintyInMilliseconds": 200
                    },
                    {
                        "name": "temperature",
                        "namespace": "Alexa.TemperatureSensor",
                        "value": {
                            "scale": "CELSIUS",
                            "value": 20
                        },
                        "timeOfSample": "2017-09-27T18:30:30.45Z",
                        "uncertaintyInMilliseconds": 200
                    }
                ]
            },
            "event": {
                "header": {
                    "namespace": "Alexa",
                    "name": "StateReport",
                    "payloadVersion": "3",
                    "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
                    "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
                },
                "endpoint": {
                    "scope": {
                        "type": "BearerToken",
                        "token": "access-token-from-Amazon"
                    },
                    "endpointId": "endpoint-001"
                },
                "payload": {}
            }
        }
    }
]

def EXAMPLEacceptgranthandler(directive):
    return pyASH.Response(directive)


def EXAMPLEcalendarhandler(directive):

    # Here is where you would call to get information about meeting
    # for this example sample data is being provided
    organizerName = "John Smith"
    calendarEventId = '1234567890'

    return pyASH.Response(directive, { 'organizerName': organizerName, 'calendarEventId': calendarEventId })

def EXAMPLEcamerastreamhandler(directive):

    c = pyASH.CameraStream('RTSP',pyASH.Resolution(1920,1080), 'BASIC', 'H264', 'AAC', "rtsp://username:password@link.to.video:443/feed1.mp4", "2017-02-03T16:20:50.52Z", 30)
    cs = pyASH.CameraStreams(c)
    csp = pyASH.CameraStreamsPayload(cs, 'https://username:password@link.to.image/image.jpg')

    return pyASH.Response(directive, csp)


def EXAMPLEdiscoverhandler(directive):

    header = pyASH.Header('Alexa.Discovery','Discover.Response').get_json()
    payload = {
        'endpoints': [ ]
    }

    endpoints = []
    # Add appliance-001
    cps = []
    cps.append( pyASH.Capability('Alexa.ColorTemperatureController', 'colorTemperatureInKelvin', True, True) )
    cps.append( pyASH.Capability('Alexa.EndpointHealth', 'connectivity', True, True) )
    cps.append( pyASH.Capability('Alexa') )
    cps.append( pyASH.Capability('Alexa.ColorController', 'color', True, True) )
    cps.append( pyASH.Capability('Alexa.PowerController', 'powerState', True, True) )
    cps.append( pyASH.Capability('Alexa.BrightnessController', 'brightness', True, True) )
    ep = pyASH.EndpointResponse("appliance-001", "Sample Manufacturer", "Living Room Light", "Smart Light by Sample Manufacturer", ["LIGHT"], \
        cookie = { \
           "extraDetail1":"optionalDetailForSkillAdapterToReferenceThisDevice", \
           "extraDetail2":"There can be multiple entries", \
           "extraDetail3":"but they should only be used for reference purposes", \
           "extraDetail4":"This is not a suitable place to maintain current device state" \
        }, capabilities = cps)
    endpoints.append(ep)

    # Add appliance-002
    cps = []
    cps.append( pyASH.Capability('Alexa', version='3') )
    cps.append( pyASH.Capability('Alexa.ThermostatController', ['lowerSetpoint','targetSetpoint', 'upperSetpoint', 'thermostatMode'], True, True) )
    cps.append( pyASH.Capability('Alexa.TemperatureSensor', 'temperature', False, True) )
    ep = pyASH.EndpointResponse("appliance-002", "Sample Manufacturer", "Hallway Thermostat", "Smart Thermostat by Sample Manufacturer", ["THERMOSTAT"], cookie = {}, capabilities = cps)
    endpoints.append(ep)

    # Add appliance-003
    cps = []
    cps.append( pyASH.Capability('Alexa.LockController', 'lockState', True, True) )
    cps.append( pyASH.Capability('Alexa.EndpointHealth', 'connectivity', True, True) )
    ep = pyASH.EndpointResponse("appliance-003", "Sample Manufacturer", "Front Door", "Smart Lock by Sample Manufacturer", ["SMARTLOCK"], cookie = {}, capabilities = cps)
    endpoints.append(ep)

    # Add appliance-004
    cps = []
    cps.append( pyASH.Capability('Alexa.SceneController', proactivelyReported=True, supportsDeactivation = False))
    ep = pyASH.EndpointResponse("appliance-004", "Sample Manufacturer", "Goodnight", "Smart Scene by Sample Manufacturer", ["SCENE_TRIGGER"], cookie = {}, capabilities = cps)
    endpoints.append(ep)

    # Add appliance-005
    cps = []
    cps.append( pyASH.Capability('Alexa', version='3') )
    cps.append( pyASH.Capability('Alexa.SceneController', proactivelyReported=True, supportsDeactivation = True))
    cps.append( pyASH.Capability('Alexa.EndpointHealth', 'connectivity', True, True) )
    ep = pyASH.EndpointResponse("appliance-005", "Sample Manufacturer", "Watch TV", "Smart Activity by Sample Manufacturer", ["ACTIVITY_TRIGGER"], cookie = {}, capabilities = cps)
    endpoints.append(ep)

    # Add appliance-006
    cps = []
    cscs = pyASH.CameraStreamConfigurations()
    csc = pyASH.CameraStreamConfiguration('RTSP', [pyASH.Resolution(1920,1080),pyASH.Resolution(1280,720)], 'BASIC', ['H264','MPEG2'],'G711')
    cscs.add(csc)
    csc = pyASH.CameraStreamConfiguration('RTSP', [pyASH.Resolution(1920,1080),pyASH.Resolution(1280,720)], 'NONE', 'H264','AAC')
    cscs.add(csc)

    cps.append( pyASH.Capability('Alexa') )
    cps.append( pyASH.Capability('Alexa.CameraStreamController', cameraStreamConfigurations=cscs.value) )
    cps.append( pyASH.Capability('Alexa.PowerController', 'powerState', True, True) )
    cps.append( pyASH.Capability('Alexa.EndpointHealth', 'connectivity', True, True) )
    ep = pyASH.EndpointResponse("appliance-006", "Sample Manufacturer", "Back Door Camera", "Smart Camera by Sample Manufacturer", ["CAMERA"], cookie = {}, capabilities = cps)
    endpoints.append(ep)

    return pyASH.Response(directive, endpoints)

def EXAMPLEreportstatehandler(directive):
    d = pyASH.Request(directive)
    ts = pyASH.get_utc_timestamp()
    properties = []


    ephp = pyASH.EndpointHealthProperty('OK', ts, 200)
    properties.append(ephp)
    tsp = pyASH.ThermostatTargetSetpointProperty(25, 'CELSIUS', ts, 200)
    properties.append(tsp)
    tmp = pyASH.ThermostatModeProperty('AUTO', '', ts, 200)
    properties.append(tmp)
    tp = pyASH.TemperatureProperty(20, 'CELSIUS', ts, 200)
    properties.append(tp)


    return pyASH.Response(directive, properties)

def EXAMPLEgenerichandler(directive):

    d = pyASH.Request(directive)
    ts = pyASH.get_utc_timestamp()
    properties = pyASH.Properties()
    if d.namespace == 'Alexa.BrightnessController':
        property = pyASH.BrightnessProperty(42, ts, 1000)
        properties.add(property)
    elif d.namespace == 'Alexa.Speaker':
        if d.name == 'SetVolume':
            volume = d.payload['volume']
            print ('Sending SetVolume[{0}] to device [{1}]'.format(volume,d.endpointId))
        if d.name == 'AdjustVolume':
            volume = d.payload['volume']
            print ('Sending AdjustVolume[{0}] to device [{1}]'.format(volume,d.endpointId))
        if d.name == 'SetMute':
            mute = d.payload['mute']
            print ('Sending SetMute[{0}] to device [{1}]'.format(mute,d.endpointId))
        volume_property = pyASH.SpeakerVolumeProperty(50, ts, 0)
        mute_property = pyASH.SpeakerMuteProperty(False, ts, 0)
        properties.add(volume_property)
        properties.add(mute_property)
    elif d.namespace == 'Alexa.ChannelController':
        property = pyASH.ChannelProperty(d.channel.number,d.channel.callSign,d.channel.affiliateCallSign,ts,0)
        properties.add(property)
    elif d.namespace == 'Alexa.PlaybackController':
        pass

    return pyASH.Response(directive, properties)



def compare_dict(input, output):
    for item in output:
#        print ('Working on dictionary item {0}:{1}'.format(item,str(output[item])[:40]))
#        print ('{0}'.format(item))

        if item == 'endpointId':
            print ('Working on endpointId {0}'.format(output[item]))
        if item not in input:
            print ('{0} is not in result'.format(item))
        else:
            if type(output[item]) in [list, dict]:
                compare_results(input[item], output[item])
            else:
                if input[item] != output[item]:
                    print ('{0}: {1} != {2}'.format(item, input[item], output[item]))

def compare_list(input, output):
    if len(input) != len(output):
        print ('List are of different lengths. input: {0}, output {1}'.format(len(input), len(output)))
    for i in range(len(output)):
#        if input[i] != output[i]:
        if type(output[i]) in [dict,list]:
            compare_results(input[i], output[i])
        elif input != output:
            print ('Line {0}: {1} != {2}'.format(i, input[i], output[i]))


def compare_results(input, output):

    if type(output) == dict:
        compare_dict(input, output)
    elif type(output) == list:
        compare_list(input, output)
    else:
        if input != output:
            print ('{0} != {1}'.format(input, output))




if __name__ == u'__main__':

    ci = pyASH.ControllerInterface(EXAMPLEacceptgranthandler, EXAMPLEdiscoverhandler)
    ci.register_callback(EXAMPLEgenerichandler,'Alexa.Speaker')
    ci.register_callback(EXAMPLEgenerichandler,'Alexa.BrightnessController')
    ci.register_callback(EXAMPLEcalendarhandler, 'Alexa.Calendar' )
    ci.register_callback(EXAMPLEcamerastreamhandler, 'Alexa.CameraStreamController')
    ci.register_callback(EXAMPLEgenerichandler, 'Alexa.ChannelController')
    ci.register_callback(EXAMPLEgenerichandler, 'Alexa.PlaybackController')
    ci.register_callback(EXAMPLEreportstatehandler, 'Alexa', 'ReportState')



#    i = 1
#    print ('Test {0} {1}'.format(i,alexa_testset[i-1]['name']))
#    res = ci.process_directive(alexa_testset[i-1]['input'])
#    compare_results(res.get_json(), alexa_testset[i-1]['output'])
    for i in range(len(alexa_testset)):
        print ('\nTest {0} {1}'.format(i,alexa_testset[i]['name']))
        res = ci.process_request(alexa_testset[i]['input'])
#        print (json.dumps(res.get_json(),indent=4))
        compare_results(res.get_json(), alexa_testset[i]['output'])
