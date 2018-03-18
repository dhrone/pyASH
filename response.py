# -*- coding: utf-8 -*-

# Copyright 2018 by dhrone. All Rights Reserved.
#

from utility import *
# Setup logger
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def HEADER(namespace, name, correlationToken=''):
    messageId = get_uuid()
    json = { 'namespace': namespace, 'name':name, 'messageId': messageId, 'payloadVersion': '3' }
    if correlationToken: json['correlationToken'] = correlationToken
    return json
