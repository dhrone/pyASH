# -*- coding: utf-8 -*-

# Copyright 2018 by dhrone. All Rights Reserved.
#

# Custom Exceptions
class MissingCredential(Exception):
    pass

class MissingRequiredValue(Exception):
    pass

class FailedAuthorization(Exception):
    pass

class BadRequest(IOError):
    pass

class TokenMissing(Exception):
    pass
