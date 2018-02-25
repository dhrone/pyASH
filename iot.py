import json
import boto3

class Iot(object):
    def __init__(self, endpointId, region='us-west-2'):
        self.endpointId = endpointId
        self.region = region
        self.client = boto3.client('iot-data', region_name=region)
        self.reportedState = {}
        self._get()

    def _get(self):
        thingData = json.loads(self.client.get_thing_shadow(thingName=self.endpointId)['payload'].read().decode('utf-8'))
        self.reportedState = thingData['state']['reported']

    def _put(self, newState):
        item = {'state': {'desired': newState}}
        # Send desired changes to shadow
        bdata = json.dumps(item).encode('utf-8')
        response = self.client.update_thing_shadow(thingName=self.endpointId, payload = bdata)

    def __getitem__(self, key):
        if key not in self.reportedState:
            raise KeyError
        return self.reportedState[key]

    def __setitem__(self, key, value):
        if key not in self.reportedState:
            raise KeyError
        self._put({key : value})

    def batchSet(self, dict):
        self._put(dict)

    def batchGet(self):
        return self.reportedState

    def refresh(self):
        self._get()
