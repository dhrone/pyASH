# -*- coding: utf-8 -*-

# Copyright 2018 by dhrone. All Rights Reserved.
#

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

from utility import *

# Setup logger
logger = logging.getLogger(__name__)
logger.setLevel(LOGLEVEL)


# ControllerInterface class -- Function router for implementing an Alexa Smart Home application
#
# Two main methods...
# register_callback -- Registers a function to handle specific requests
#     When register_callback is called without a directive name, the function provided will be
#     registered for all directives supported by that interface
# process_request -- Accepts a alexa smart home request, and then invokes the appropriate function
#     All functions are expected to accept a json formatted request as received from
#     the Alexa Smart Home service and return a properly formatted response message
#
# Handlers for AcceptGrant and Discover are mandatory so they are part of the class constructor

class ControllerInterface():
    def __init__(self, acceptgranthandler, discoverhandler):
        self.callbacks = {}
        if not callable(acceptgranthandler):
            raise TypeError('The acceptgranthandler must be a function.  Type received was {0}'.format(type(acceptgranthandler)))
        else:
            self.register_callback(acceptgranthandler, 'Alexa.Authorization', 'AcceptGrant')

        if not callable(discoverhandler):
            raise TypeError('The discoverhandler must be a function.  Type received was {0}'.format(type(discovershandler)))
        else:
            self.register_callback(discoverhandler, 'Alexa.Discovery', 'Discover')

    def register_callback(self, func, interface, directive=None ):

        if not callable(func):
            raise TypeError('Callback function must be callable')

        interface = fix_interface(interface)

        if directive is None:
            for n in VALID_DIRECTIVES[interface]:
                self.callbacks[(interface, n)]=func
        else:
            directive = fix_directive(interface, directive)
            self.callbacks[(interface, directive)]=func


    def process_request(self, request):
        r = Request(request)

        if r.namespace not in VALID_PROPERTIES:
            raise ValueError('{0} is not a valid namespace'.format(r.namespace))

        if r.name not in VALID_DIRECTIVES[r.namespace]:
            raise ValueError('{0} is not a valid directive for {1}'.format(r.name, r.namespace))

        if (r.namespace,r.name) not in self.callbacks:
            raise KeyError('[{0}][{1}] does not have a callback handler'.format(r.namespace, r.name))

        res = self.callbacks[(r.namespace, r.name)](request)
        if not isinstance(res, Response) and not isinstance(res, ErrorResponse):
            raise TypeError('Callback [{0}][{1}] returned an invalid response.  Type returned was {2}'.format(r.namespace, r.name, str(type(res))))

        return res

if __name__ == u'__main__':

    ts = get_utc_timestamp()
    u = 0

    p = BrightnessProperty(45, ts, u)
    print (p)

    p = ChannelProperty('6','PBS','KBTC', ts, u)
    print (p)

    p = ColorProperty(350.5, 0.7138, 0.6524, ts, u)
    print (p)

    p = ColorTemperatureInKelvinProperty(7500, ts, u)
    print (p)

    p = CookingModeProperty('TIMECOOK', ts, u)
    print (p)

    p = CookingModeProperty('OFF', ts, u)
    print (p)

    p = EndpointHealthProperty('UNREACHABLE', ts, u)
    print (p)

    p = CookingTimeProperty(datetime(2017,8,30,1,18,21),'cookCompletionTime', ts, u)
    print (p)

    p = CookingTimeControllerTimeProperty(timedelta(minutes=3, seconds=15), ts, u)
    print (p)

    p = CookingTimeControllerPowerProperty('MEDIUM', ts, u)
    print (p)

    fq = WeightFoodQuantity(2.5, 'POUND')
    p = CookingFoodItemProperty('Cooper river salmon', 'FISH', fq, ts, u)
    print(p)

    fq = FoodCountFoodQuantity(1, 'LARGE')
    p = CookingFoodItemProperty('Cooper river salmon', 'FISH', fq, ts, u)
    print (p)

    fq = VolumeFoodQuantity(2, 'LITER')
    p = CookingFoodItemProperty('Salmon Soup', 'FISH', fq, ts, u)
    print (p)

    p = InputProperty('HDMI1', ts, u)
    print (p)

    p = PowerLevelProperty(5, ts, u)
    print (p)

    p = LockProperty('LOCKED', ts, u)
    print (p)

    p = SpeakerMuteProperty(False, ts, u)
    print (p)

    p = PercentageProperty(74, ts, u)
    print (p)

    p = PowerStateProperty('OFF', ts, u)
    print (p)

    p = PowerLevelProperty('MEDIUM', ts, u)
    print (p)

    p = TemperatureProperty(68, 'FAHRENHEIT', ts, u)
    print (p)

    p = ThermostatModeProperty('AUTO','', ts, u)
    print (p)

    p = ThermostatModeProperty('AUTO', 'VENDOR_HEAT_COOL', ts, u)
    print (p)

    p = ThermostatModeProperty('CUSTOM', 'VENDOR_HEAT_COOL', ts, u)
    print (p)
