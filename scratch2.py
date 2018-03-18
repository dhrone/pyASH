from dhroneTV import iotTV
from concept import *
iot = iotTV('avmctrl_den')
pc = PowerController(iot)
pc.TurnOff('a')


from pyASH import pyASH
from user import StaticUser, DbUser
from dhroneTV import dhroneTV, dhroneTVScene
import json
import time
eid = dhroneTV.__name__ + '|' + 'avmctrl_den'
class r:
    def __init__(self, eid, ns, d, pn, v):
        self.endpointId = eid
        self.namespace = ns
        self.directive = d
        self.payload = { pn:v }
        self.correlationToken = '<correlation token>'
        self.token = 'Atza|IwEBIPbDCkmO-SmFVtoZJpuehXK4Hh3rhKVYtz-FvchlDuu6B4snSSmDLt1wb-FYzWD3z9ZgXb82lrGQv8lNujyG7NtxoluIX2vC0Lj7yqOnUTl1_crDTvosiJ8mBZC18PctA5QX-rVsrLh8bDms5ttydTAPmecRWTe86RiJYMvcailB2OwaE_ZJYMVl7-OaaINJIbYqhUcR73fJVQMTLG6HgtU6uO38p2vL3gJqoZLlWXVHpjDaVFQw1nCqV5l9v01_42n7A1F4T99U5ItB0Yc_Fa60BoPdTP_Mvk2MerPzCIi6XGOiyasxeWqkGfx3TIoiI8GEJAIxZ-2a3ZQPFDw6igNb688rp8LtiXLbH9qwsAxdYlAzjmG_BPOL5ix848iR_phrnLraQs2QY5gfCNIt1AoCPbN81a1L5jeEGWLNgsDzm29rYyaG4pI9O1sTVyRXmtedlELXUvp3-pbM7SKm2E3X89wMXn9skZ0U2rqGIH5UUTpY3Q_XwH2Jqmr5qgSkEFc'
    @property
    def json(self):
        return {
            'directive': {
                'header': {
                    'namespace': self.namespace,
                    'name': self.directive,
                    'payloadVersion': '3',
                    'correlationToken': self.correlationToken,
                    'token': self.token
                },
                'endpoint': {
                    'endpointId': self.endpointId,
                },
                'payload': self.payload,
            }
        }



user = DbUser(endpointClasses=[dhroneTV, dhroneTVScene],userEmail='ron@ritchey.org')
pyash = pyASH(user)
request = r(eid, 'Alexa.Speaker', 'SetVolume', 'volume', 40)
ret = pyash.handleDirective(request)
print(json.dumps(ret, indent=4))

ret = pyash.lambda_handler(request)

user.addEndpoint(dhroneTV, 'avmctrl_den', 'Den TV', 'TV by Me', 'Me', 'OTHER', True, True, 0)

import requests
accessToken = 'bad token'
accessToken = 'Atza|IwEBIAP-BeEUAbw5rLQ9gapSAObgszFNmYHizS2AAv7SaT1vbLQnj5_1Kp4eG0ZLImMIt0W-vrsLwZRtRTM7okLiyBnAiwLy2VdYfVLgHhj4B9LUgzwhE6DZ-xgKCfGGCyCxVUHD-MkKMCgOTd0G9p-IVjLZE0Cg0hlf1ylOlWkIFD7dvN1aalGhAG5TavDccfa9Z6rQ2W5PPLRGPa1rhVjNzkDf827W3SxgSzjuJ3KRbj3pHIzaqRuiGiMabptCfpaL18S8fBYVtoGHfppYu7I8e-CrTpgGFdBrjopD3zsbeRHZRO48SEth0FD7C8NWd98uA-BY2Xz_Q6e1GU8Mk2kPDxC6RDFt7n7TK7ysNlEm6J1k-a2UoyUb5RQKErXgvLcukXVAZzTedpkJ10AJkWngx4QFJqem4Wr0Vg0v3Bu6AfVebZccGFJEaUMcjfBDpHqxT7heSZTVHsHMnNcdGdeldZj6O--056AwCdrSrL764Izs-s-aNdFHseO_Gp9coYHRzsc'
accessToken = 'Atza|IwEBIEpleooa2Maoj29jRgfZ4WqO7TEZru_yI7jSGFcP41F1VfoNMFa5JH5wEu0ersgo1rdy6I74sN8V4A0mxtmsEcpBNBwRPKYeY5slRnJZbwAJr398X2rSdun4Z4s3GzaQgHDmNXBdye3IkotAPVHGCAxaVoMQPnvYORUHnhuP9-cBK6e3aqbZPsOR2J2Wi20RLh1ivLzZgRvO4J00svwX6bK2uy-nHlZ8mEx_pPrrZBvX-dLzz7jhkvjEE_hXLAjxVpgl-tFwBtcn8lH7kuhIdlTW-2wOGKoaRf8ZE0JfGc5_dtwyZOSv5dpF1NN9ILy9bJAPuM6sbxDs2QiHkLlSF6ygxuVsroDCcZV4OUFrfeiWajGp0oszIbpmju8MGB0KOUwRuSL95glvTa-WhaOYPlBq1kxJH6yMssWMT7PVQYlxCwro_MpqGc9UqImLs8tMyGnO_-1DT80-92gC0sjsbUG9VzIQGtKBLv03rqdDOC7NUoSwG-qXg6jDeyLCSwiTL1c'
accessToken = 'Atza|IwEBIAHnt6lXI-ZKo31P6GIivTq5_oPUqi7TIocQwDxjjqD8E9J_A9qeujd5uhPzbTh0GyANyAEuaW4roS2xd0nU_uTGr9xdpIscQYO6duZvKZOmY72mmbNEqWabWaxh-uMr74jb32mT8THKHj2Ia7KTfvm5vvLBGLuvgTc-Af3J5wSEb4atXOxV6A1HgMk2kGdehpLLnyUzt56JZatmWfBTmsrqpx6vp4yOhv2rZl-nbE0O_DmQhnY9sTpM_AI7fOIZMO6I-L6yihY1VdPgtKFAPjpOF5DeKRLMDKemyI4mqQjOUUc_MQSaC-NhKDfSob5uTx7vChyyxXDwuH3v9rCNbQDTQrbo8giPgpYZHjTdB1KQSaQXAWkPnKLIN3NpjDwl7Rs9F106dYlM3J4nuFlMMJ0usmANt4rOxYv0a_PO12nOaGLrEI-w1GBXSnxc4ddj7Ze8PvViPbt0lazaHG0vyXKXlp-Ix5GYcmuiIlhYUGPfiTeDg61Gmda9CiRCD41UU7U'
payload = { 'access_token': accessToken }
r = requests.get("https://api.amazon.com/user/profile", params=payload)

from test_pyASH import dhroneTV
from user import DemoUser
from pyASH import pyASH
user = DemoUser()
user.addEndpoint(endpointClass=dhroneTV, things='device_1', friendlyName='Sound', description='Sound by dhrone')
pyash = pyASH(user)
endpoint = pyash.user.endpoints['dhroneTV:device_1']
from message import Request
d = {
    "directive": {
        "header": {
            "namespace": "Alexa.PowerLevelController",
            "name": "SetPowerLevel",
            "payloadVersion": "3",
            "messageId": "1bd5d003-31b9-476f-ad03-71d471922820",
            "correlationToken": "dFMb0z+PgpgdDmluhJ1LddFvSqZ/jCc8ptlAKulUj90jSqg=="
        },
        "endpoint": {
            "scope": {
                "type": "BearerToken",
                "token": "access-token-from-skill"
            },
            "endpointId": "dhroneTV:device_1",
            "cookie": {}
        },
        "payload": {
            "powerLevel": 42
        }
    }
}
request = Request(d)
cls, handler = endpoint.getHandler(request)
method = handler.__get__(cls(iots=endpoint.iots), cls)
interface = endpoint.generateInterfaces(endpoint.iots[0])[request.namespace]
