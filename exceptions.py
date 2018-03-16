# -*- coding: utf-8 -*-

# Copyright 2018 by dhrone. All Rights Reserved.
#


# Credit for the concepts behind this module go entirely to Matěj Hlaváček (https://github.com/mathead)

class InterfaceException(Exception):
    def __init__(self, message, *args, **kwargs):
        if hasattr(self, 'payload'):
            self.payload['type'] = type(self).__name__
            self.payload['message'] = message
        else:
            self.payload = { 'type': type(self).__name__, 'message': message }
        super(InterfaceException, self).__init__(message, *args, **kwargs)

class ACCEPT_GRANT_FAILED(InterfaceException):
    pass

class ALREADY_IN_OPERATION(InterfaceException):
    pass

class BRIDGE_UNREACHABLE(InterfaceException):
    pass

class ENDPOINT_BUSY(InterfaceException):
    pass

class ENDPOINT_LOW_POWER(InterfaceException):
    def __init__(self, message, percentageState=None, *args, **kwargs):
        if percentageState:
            self.payload = { 'percentageState': percentageState }
        super(ENDPOINT_LOW_POWER, self).__init__(message, *args, **kwargs)

    pass

class ENDPOINT_UNREACHABLE(InterfaceException):
    pass

class EXPIRED_AUTHORIZATION_CREDENTIAL(InterfaceException):
    pass

class FIRMWARE_OUT_OF_DATE(InterfaceException):
    pass

class HARDWARE_MALFUNCTION(InterfaceException):
    pass

class INTERNAL_ERROR(InterfaceException):
    pass

class INVALID_AUTHORIZATION_CREDENTIAL(InterfaceException):
    pass

class INVALID_DIRECTIVE(InterfaceException):
    pass

class INVALID_VALUE(InterfaceException):
    pass

class NO_SUCH_ENDPOINT(InterfaceException):
    pass

class NOT_SUPPORTED_IN_CURRENT_MODE(InterfaceException):
    def __init__(self, message, mode, *args, **kwargs):
        self.payload = { 'currentDeviceMode': mode }
        super(NOT_SUPPORTED_IN_CURRENT_MODE, self).__init__(message, *args, **kwargs)

class NOT_IN_OPERATION(InterfaceException):
    pass

class POWER_LEVEL_NOT_SUPPORTED(InterfaceException):
    pass

class RATE_LIMIT_EXCEEDED(InterfaceException):
    pass

class TEMPERATURE_VALUE_OUT_OF_RANGE(InterfaceException):
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

class VALUE_OUT_OF_RANGE(InterfaceException):
    def __init__(self, message, minv=None, maxv=None, *args, **kwargs):
        if minv and maxv:
            self.payload = {
                'validRange': {
                    'minimumValue': minv,
                    'maximumValue': maxv
                }
            }
        super(VALUE_OUT_OF_RANGE, self).__init__(message, *args, **kwargs)

class OauthException(Exception):
    pass

# COOKING Interface specific Exceptions
class DOOR_OPEN(InterfaceException):
    pass

class DOOR_CLOSED_TOO_LONG(InterfaceException):
    pass

class COOK_DURATION_TOO_LONG(InterfaceException):
    def __init__(self, message, maxCookTime=None, *args, **kwargs):
        self.payload = { 'maxCookTime': Duration(maxCookTime) }
        super(COOK_DURATION_TOO_LONG, self).__init__(message, *args, **kwargs)

class REMOTE_START_NOT_SUPPORTED(InterfaceException):
    pass

class REMOTE_START_DISABLED(InterfaceException):
    pass

# Video interface specific exceptions
class NOT_SUBSCRIBED(InterfaceException):
    pass

# OAUTH2 Exceptions
class OAUTH2_EXCEPTION(Exception):
    pass

class OAUTH2_CredentialMissing(OAUTH2_EXCEPTION):
    pass

class OAUTH2_AccessGrantFailed(OAUTH2_EXCEPTION):
    pass

class OAUTH2_PermissionDenied(OAUTH2_EXCEPTION):
    pass

class OAUTH2_BadRequest(OAUTH2_EXCEPTION):
    pass

class OAUTH2_IOError(OAUTH2_EXCEPTION):
    pass

# Miscellanious Exceptions
class MISCELLANIOUS_EXCEPTION(Exception):
    pass
class MissingRequiredValueException(MISCELLANIOUS_EXCEPTION):
    pass

class UserNotFoundException(MISCELLANIOUS_EXCEPTION):
	pass

class UserNotInitialized(MISCELLANIOUS_EXCEPTION):
    pass

class EndpointNotFoundException(MISCELLANIOUS_EXCEPTION):
	pass

class NoMethodToHandleDirectiveException(MISCELLANIOUS_EXCEPTION):
	pass

class NoIOThandlerProvidedException(MISCELLANIOUS_EXCEPTION):
	pass

class OnlyOneIOTallowedPerEndpoint(MISCELLANIOUS_EXCEPTION):
	pass
