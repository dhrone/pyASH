# -*- coding: utf-8 -*-

# Copyright 2018 dhrone. All Rights Reserved.
#


# pyASH imports
from pyASH.endpoint import Endpoint
from pyASH.iot import Iot, Thing
from pyASH.interface import PowerController, EndpointHealth
from pyASH.utility import LOGLEVEL
from pyASH.user import DbUser

# Setup logger
import logging
logger = logging.getLogger(__name__)
logger.setLevel(LOGLEVEL)


class iotCloudLight(Iot):

    @Iot.transformFromProperty('powerState', 'apower')
    def fromPowerState(self, value):
        return { 'ON': True, 'OFF': False }.get(value, value)

    @Iot.transformToProperty('powerState', 'apower')
    def toPowerState(self, value):
        return { True: 'ON', False: 'OFF'}.get(value, value)


@Endpoint.addInterface(PowerController)
@Endpoint.addInterface(EndpointHealth)
class cloudLight(Endpoint):
    manufacturerName = 'dhrone'
    description = 'Light controller demo'
    displayCategories = 'LIGHT'
    @Endpoint.addDirective(['TurnOn'])
    def TurnOn(self, request):
        self.iot['powerState'] = True
    @Endpoint.addDirective
    def TurnOff(self, request):
        self.iot['powerState'] = False


if __name__ == u'lambda_function':
    def lambda_handler(request, context):
        token = Request(request).token
        user = DbUser(token=Request(request).token, classes=[cloudLight, Iot])
        pyASH(user).lambda_handler(request)


if __name__ == u'__main__':
    user = DbUser()
    user.createTables()
    user.createUser('ron@ritchey.org')
    user.addEndpoint(cloudLight(things=Thing('cloudLightThing', Iot), friendlyName='Cloud'))
    user.commit()
