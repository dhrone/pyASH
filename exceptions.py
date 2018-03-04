# -*- coding: utf-8 -*-

# Copyright 2018 by dhrone. All Rights Reserved.
#

# Custom Exceptions
class MissingCredentialException(Exception):
    pass

class MissingRequiredValueException(Exception):
    pass

class FailedAuthorizationException(Exception):
    pass

class BadRequestException(IOError):
    pass

class TokenMissingException(Exception):
    pass

class UserNotFoundException(Exception):
	pass

class EndpointNotFoundException(Exception):
	pass

class NoMethodToHandleDirectiveException(Exception):
	pass
