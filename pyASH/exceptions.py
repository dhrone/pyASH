# -*- coding: utf-8 -*-

# Copyright 2018 by dhrone. All Rights Reserved.
#


# Credit for the concepts behind this module go entirely to Matěj Hlaváček (https://github.com/mathead)

class pyASH_EXCEPTION(Exception):
    def __init__(self, message, *args, **kwargs):
        if hasattr(self, 'payload'):
            self.payload['type'] = type(self).__name__
            self.payload['message'] = message
        else:
            self.payload = { 'type': type(self).__name__, 'message': message }
        super(pyASH_EXCEPTION, self).__init__(message, *args, **kwargs)

class ACCEPT_GRANT_FAILED(pyASH_EXCEPTION):
    pass

class BRIDGE_UNREACHABLE(pyASH_EXCEPTION):
    pass

class ENDPOINT_BUSY(pyASH_EXCEPTION):
    pass

class ENDPOINT_LOW_POWER(pyASH_EXCEPTION):
    def __init__(self, message, percentageState=None, *args, **kwargs):
        if percentageState:
            self.payload = { 'percentageState': percentageState }
        super(ENDPOINT_LOW_POWER, self).__init__(message, *args, **kwargs)

class ENDPOINT_UNREACHABLE(pyASH_EXCEPTION):
    pass

class EXPIRED_AUTHORIZATION_CREDENTIAL(pyASH_EXCEPTION):
    pass

class FIRMWARE_OUT_OF_DATE(pyASH_EXCEPTION):
    pass

class HARDWARE_MALFUNCTION(pyASH_EXCEPTION):
    pass

class INTERNAL_ERROR(pyASH_EXCEPTION):
    def __init__(self, message, *args, **kwargs):
        super(INTERNAL_ERROR, self).__init__(message, *args, **kwargs)
        self.payload['type'] = 'INTERNAL_ERROR'

class INVALID_AUTHORIZATION_CREDENTIAL(pyASH_EXCEPTION):
    pass

class INVALID_DIRECTIVE(pyASH_EXCEPTION):
    pass

class INVALID_VALUE(pyASH_EXCEPTION):
    pass

class NO_SUCH_ENDPOINT(pyASH_EXCEPTION):
    pass

class NOT_SUPPORTED_IN_CURRENT_MODE(pyASH_EXCEPTION):
    def __init__(self, message, mode, *args, **kwargs):
        self.payload = { 'currentDeviceMode': mode }
        super(NOT_SUPPORTED_IN_CURRENT_MODE, self).__init__(message, *args, **kwargs)

class RATE_LIMIT_EXCEEDED(pyASH_EXCEPTION):
    pass

class TEMPERATURE_VALUE_OUT_OF_RANGE(pyASH_EXCEPTION):
    def __init__(self, message, minv=None, maxv=None, scale='FAHRENHEIT', *args, **kwargs):
        minv = minv if isinstance(minv, Temperature) or not minv else Temperature(minv, scale)
        maxv = maxv if isinstance(maxv, Temperature) or not maxv else Temperature(maxv, scale)

        if minv and maxv:
            self.payload= {
                'validRange': {
                    'minimumValue': minv.json,
                    'maximumValue': maxv.json
                }
            }
        super(TEMPERATURE_VALUE_OUT_OF_RANGE, self).__init__(message, *args, **kwargs)

class VALUE_OUT_OF_RANGE(pyASH_EXCEPTION):
    def __init__(self, message, minv=None, maxv=None, *args, **kwargs):
        if minv and maxv:
            self.payload = {
                'validRange': {
                    'minimumValue': minv,
                    'maximumValue': maxv
                }
            }
        super(VALUE_OUT_OF_RANGE, self).__init__(message, *args, **kwargs)

# Additional Exceptions
# These are not directly related to the ASH errors so get reported as INTERNAL_ERROR
class OAUTH2_EXCEPTION(INTERNAL_ERROR):
    pass

class USER_NOT_FOUND_EXCEPTION(INTERNAL_ERROR):
    pass

class MISCELLANIOUS_EXCEPTION(INTERNAL_ERROR):
    pass

#############################################################
# In Alexa Smart Home documentation but missing from schema #
#############################################################

class ALREADY_IN_OPERATION(pyASH_EXCEPTION):
    pass

class NOT_IN_OPERATION(pyASH_EXCEPTION):
    pass

class POWER_LEVEL_NOT_SUPPORTED(pyASH_EXCEPTION):
    pass

# COOKING Interface specific Exceptions
class DOOR_OPEN(pyASH_EXCEPTION):
    pass

class DOOR_CLOSED_TOO_LONG(pyASH_EXCEPTION):
    pass

class COOK_DURATION_TOO_LONG(pyASH_EXCEPTION):
    def __init__(self, message, maxCookTime=None, *args, **kwargs):
        self.payload = { 'maxCookTime': Duration(maxCookTime) }
        super(COOK_DURATION_TOO_LONG, self).__init__(message, *args, **kwargs)

class REMOTE_START_NOT_SUPPORTED(pyASH_EXCEPTION):
    pass

class REMOTE_START_DISABLED(pyASH_EXCEPTION):
    pass

# Video interface specific exceptions
class NOT_SUBSCRIBED(pyASH_EXCEPTION):
    pass
