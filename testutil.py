dAdjustVolumeUp = {
    "directive": {
        "header": {
            "namespace": "Alexa.Speaker",
            "name": "AdjustVolume",
            "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
            "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg==",
            "payloadVersion": "3"
        },
        "endpoint": {
            "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-skill"
            },
            "endpointId": "avmctrl_den",
            "cookie": { }
        },
        "payload": {
            "volume": 10
        }
    }
}
dAdjustVolumeDown = {
    "directive": {
        "header": {
            "namespace": "Alexa.Speaker",
            "name": "AdjustVolume",
            "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
            "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg==",
            "payloadVersion": "3"
        },
        "endpoint": {
            "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-skill"
            },
            "endpointId": "avmctrl_den",
            "cookie": { }
        },
        "payload": {
            "volume": -10
        }
    }
}
dSetVolume = {
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
            "endpointId": "avmctrl_den",
            "cookie": { }
        },
        "payload": {
            "volume": 50
        }
    }
}

dTurnOff = {
    "directive": {
        "header": {
            "namespace": "Alexa.PowerController",
            "name": "TurnOff",
            "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
            "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg==",
            "payloadVersion": "3"
        },
        "endpoint": {
            "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-skill"
            },
            "endpointId": "avmctrl_den",
            "cookie": { }
        },
        "payload": {
        }
    }
}

dActivate = {
    "directive": {
        "header": {
            "namespace": "Alexa.SceneController",
            "name": "Activate",
            "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
            "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg==",
            "payloadVersion": "3"
        },
        "endpoint": {
            "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-skill"
            },
            "endpointId": "avmctrl_den:watch",
            "cookie": { }
        },
        "payload": {
        }
    }
}

dDeactivate = {
    "directive": {
        "header": {
            "namespace": "Alexa.SceneController",
            "name": "Deactivate",
            "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4",
            "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg==",
            "payloadVersion": "3"
        },
        "endpoint": {
            "scope": {
                    "type": "BearerToken",
                    "token": "access-token-from-skill"
            },
            "endpointId": "avmctrl_den:watch",
            "cookie": { }
        },
        "payload": {
        }
    }
}

rVolumeUp = Request(dAdjustVolumeUp)
rVolumeDown = Request(dAdjustVolumeDown)
rSetVolume = Request(dSetVolume)
rOff = Request(dTurnOff)
rActivate = Request(dActivate)
rDeactivate = Request(dDeactivate)
