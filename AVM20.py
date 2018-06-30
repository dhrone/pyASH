

from abc import ABC, abstractmethod
from threading import Timer, Lock, Thread
import logging
import json
import re
import queue
import time
import RPi.GPIO as GPIO

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient

class PhysicalThing(object):
    _logger = logging.getLogger(__name__)

    def __init__(self, endpoint=None, thingName=None, rootCAPath=None, certificatePath=None, privateKeyPath=None, region=None, device=None, devices=None):
        ''' Initialize connection to AWS IOT shadow service '''

        self._eventQueue = queue.Queue()
        self._localShadow = dict() # dictionary of local property values
        self._propertyHandlers = dict() # dictionary to set which device handles which property values
        self._shadowHandler = self._iotConnect(endpoint, thingName, rootCAPath, certificatePath, privateKeyPath, region)

        if device is not None and devices is not None:
            self._logger.debug('Arguments for both device and devices have been provided.  Normal usage is one or the other')

        if device is not None:
            self.registerDevice(device)

        if devices is not None:
            for d in devices:
                self.registerDevice(d)

        self._main()

    def _iotConnect(self, endpoint, thingName, rootCAPath, certificatePath, privateKeyPath, region):
        ''' Establish connection to the AWS IOT service '''
        # Init AWSIoTMQTTShadowClient
        myAWSIoTMQTTShadowClient = None
        myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient('pyASH')
        myAWSIoTMQTTShadowClient.configureEndpoint(endpoint, 8883)
        myAWSIoTMQTTShadowClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

        # AWSIoTMQTTShadowClient configuration
        myAWSIoTMQTTShadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
        myAWSIoTMQTTShadowClient.configureConnectDisconnectTimeout(10)  # 10 sec
        myAWSIoTMQTTShadowClient.configureMQTTOperationTimeout(5)  # 5 sec

        # Connect to AWS IoT
        myAWSIoTMQTTShadowClient.connect()

        # Create a deviceShadow with persistent subscription
        deviceShadowHandler = myAWSIoTMQTTShadowClient.createShadowHandlerWithName(thingName, True)

        # Delete shadow JSON doc
        deviceShadowHandler.shadowDelete(self._deleteCallback, 5)

        # Listen on deltas
        deviceShadowHandler.shadowRegisterDeltaCallback(self._deltaCallback)

        return deviceShadowHandler

    def registerDevice(self, device):
        ''' Register a device as the handler for the set of properties that the device implements '''

        for property in device.properties:
            if property in self._localShadow:
                self._logger.warn('{0} is trying to register {1} which is a property that is already in use.'.format(device.__name__, property))
            self._localShadow[property] = device.properties[property]
            self._propertyHandlers[property] = device
        device.start(self._eventQueue)

    def _deleteCallback(self, payload, responseStatus, token):
        ''' Log result when a request to delete the IOT shadow has been made '''
        if responseStatus == 'accepted':
            self._logger.info("Delete request " + token + " accepted!")
            return

        self._logger.warn({
            'timeout': "Delete request " + token + " time out!",
            'rejected': "Delete request " + token + " rejected!"
        }.get(responseStatus, "Delete request with token " + token + "contained unexpected response status " + responseStatus))

    def _updateCallback(self, payload, responseStatus, token):
        ''' Log result when a request has been made to update the IOT shadow '''
        if responseStatus == 'accepted':
            payloadDict = json.loads(payload)
            self._logger.info("Received delta request: " + json.dumps(payloadDict))
            return

        self._logger.warn({
            'timeout': "Update request " + token + " timed out!",
            'rejected': "Update request " + token + " was rejected!"
        }.get(reponseStatus, "Update request " + token + " contained unexpected response status " + responseStatus))

    def _deltaCallback(self, payload, responseStatus, token):
        ''' Receive an delta message from IOT service and forward update requests for every included property to the event queue '''
        print ('Delta message received with content: {0}'.format(payload))
        payloadDict = json.loads(payload)

        for property in payloadDict['state']:
            self._logger.info('Delta Message: processing item [{0}][{1}]'.format(property, payloadDict['state'][property]))
            self._eventQueue.put({'source': '__thing__', 'action': 'UPDATE', 'property': property, 'value': payloadDict['state'][property] })

    def _main(self):

        while True:
            messages = [ self._eventQueue.get() ]
            self._eventQueue.task_done()

            ''' A new message has come in but it may be a batch of updates so wait for a short time and then read all pending messages '''
            time.sleep(0.1)
            try:
                while True:
                    messages.append( self._eventQueue.get_nowait())
                    self._eventQueue.task_done()
            except queue.Empty:
                pass

            ''' Process all received messages '''
            updatedProperties = dict()
            print ('Processing received messages')
            for message in messages:
                print (message)
                if message['action'] == 'EXIT':
                    ''' If an EXIT message is received then stop processing messages and exit the main thing loop '''
                    return

                if message['action'] == 'UPDATE':
                    if message['source'] == '__thing__':
                        ''' Update is from IOT service.  Determine which device supports the updated property and send an update request to it '''
                        self._propertyHandlers[message['property']].update(message['property'], message['value'])
                    else:
                        ''' Update is from device. Add it to updatedProperties '''
                        updatedProperties[message['property']] = message['value']

            ''' If there are properties to report to the IOT service, send an update message '''
            updateNeeded = False
            payloadDict = { 'state': { 'reported': {}, 'desired': {} } }
            for property, value in updatedProperties.items():
                if self._localShadow[property] != value:
                    updateNeeded = True
                    payloadDict['state']['reported'] = updatedProperties
                    payloadDict['state']['desired'] = updatedProperties
            if updateNeeded:
                self._shadowHandler.shadowUpdate(json.dumps(payloadDict), self._updateCallback, 5)

class PhysicalDevice(ABC):
    ''' Device that makes up part of an IOT thing '''
    _logger = logging.getLogger(__name__)

    def __init__(self, name = None, properties = None):
        ''' Initialize device driver and set it to receive updates from the eventQueue '''

        self.properties = properties # dictionary of the properties and starting values for device
        self.__name__ = name if name is not None else self.__class__.__name__
        self._deviceQueue = queue.Queue()
        self._ready = Lock()    # Is it safe to send a command to the device
        self._waitFor = None # Are we waiting for a specific value from the device
        self._exit = False # Set when a request has been made to exit the device driver

        self._initialize()

    def start(self, eventQueue):
        self._eventQueue = eventQueue

        # Starting event loops
        _threadRead = Thread(target=self._readLoop)
        _threadRead.start()
        _threadWrite = Thread(target=self._writeLoop)
        _threadWrite.start()

    def update(self, property, value):
        ''' Change the physical state of the device by updating property to value '''
        self._deviceQueue.put({'action': 'UPDATE', 'property': property, 'value': value })

    def exit(self):
        ''' Shut down device driver '''
        self._exit = True
        self._deviceQueue.put({'action': 'EXIT'})
        self._close()

    @classmethod
    def deviceToProperty(cls, property, regex):

        def decorateinterface(func):
            transform = getattr(func, '__deviceToProperty__', {})
            cre = re.compile(regex)
            transform[cre] = (property, func)
            func.__deviceToProperty__ = transform
            return func

        return decorateinterface

    @classmethod
    def propertyToDevice(cls, property, cmd):

        def decorateinterface(func):
            transform = getattr(func, '__propertyToDevice__', {})
            transform[property] = (cmd, func)
            func.__propertyToDevice__ = transform
            return func

        return decorateinterface

    @classmethod
    def _deviceToProperty(cls, value):
        for supercls in cls.__mro__:  # This makes inherited Appliances work
            for method in supercls.__dict__.values():
                d2pList = getattr(method, '__deviceToProperty__', {})
                for cre, (property, method) in d2pList.items():
                    match = cre.match(value)
                    if match:
                        return (property, method, match)
        return None

    @classmethod
    def _propertyToDevice(cls, property):
        for supercls in cls.__mro__:  # This makes inherited Appliances work
            for method in supercls.__dict__.values():
                p2dList = getattr(method, '__propertyToDevice__', {})
                if p2dList and property in p2dList:
                    return p2dList.get(property)

    def _readLoop(self):
        ''' Main event loop for reading from device '''
        print ('Starting {0} readLoop'.format(self.__name__))
        while not self._exit:
            val = self._read(5) # Read input.  Timeout after 5 seconds to make sure we are checking that an exit hasn't been commanded.
            if val:
                print ('Received {0} from device'.format(val))
                ret = self._deviceToProperty(val) # Retrieve appropriate handler to translate device value into property value
                if ret:
                    (property, method, match) = ret
                    if type(property) is not list: property = [ property ]

                    for i in range(len(property)):
                        # Extract out each match group and send to method to get it translated from the value from the device to the property value
                        mval = match(i+1)
                        xval = method(self, property[i], mval)
                        print ('Sending {0}:{1} to event queue'.format(property[i], xval))

                        # Send updated property to Thing
                        self._eventQueue.put({'source': self.__name__, 'action': 'UPDATE', 'property': property[i], 'value': xval })
                else:
                    self._logger.warn('No method matches {0}'.format(val))

    def _writeLoop(self):
        ''' Main event loop for writing to device '''
        print ('Starting {0} writeLoop'.format(self.__name__))

        while not self._exit:
            try:
                message = self._deviceQueue.get(5)
                self._deviceQueue.task_done()

                print ('Received request to update device: {0}'.format(message))
                if message['action'].upper() == 'EXIT':
                    return
                elif message['action'].upper() == 'UPDATE':
                    ret = self._propertyToDevice(message['property'])
                    if ret:
                        (cmd, method) = ret

                        # Send updated property to device
                        self._write(cmd.format(method(self,message['value'])))
                    else:
                        self._logger.warn('No property matches {0}'.format(message['property']))



            except queue.Empty:
                continue



    ''' User Defined Methods '''
    @abstractmethod
    def _read(self,timeout=0):
        pass

    @abstractmethod
    def _write(self,value):
        pass

    @abstractmethod
    def _close(self):
        pass


class AVM20(PhysicalDevice):

    def __init__(self, port, baud):
        self._ser = serial.Serial(port, baud, timeout=0.25)
        self._timeout=timeout
        if not self._ser:
            raise IOError('Unable to open serial connection on power {0}'.format(port))
        super(AVM20, self).__init__(name = 'AVM20', properties = { 'powerState': 'UNKNOWN', 'input':'UNKNOWN', 'volume': 0, 'muted': False })

    def _read(self):

        delimiter = b'\n'
        buffer = b''
        last_activity = time.time()

        while True:
            c = self._ser.read()
            if c:
                last_activity = time.time()
            if c == delimiter:
                return buffer.decode()
            buffer += c
            if time.time() - last_activity > timeout:
                return buffer.decode()

    def _write(self, value):
        if type(value) == str:
            value = value.encode()
        self._ser.write(value)
        self.logger.info ('From {0}, Sending  [{1}]'.format(self.name,value))

    def _close(self):
        self._ser.close()

    @PhysicalDevice.deviceToProperty('powerState', '^P1P([0-1])$')
    def avm20ToPowerState(self, property, value):
        assert (property == 'powerState'), 'Wrong property received: ' + property
        val = { '1': 'ON', '0': 'OFF' }.get(value)
        if val:
            return val
        raise ValueError('{0} is not a valid value for property {1}'.format(value, property))

    @PhysicalDevice.deviceToProperty('input', '^P1S([0-9])$')
    def avm20ToInput(self, property, value):
        assert (property == 'input'), 'Wrong property received: ' + property
        val = { '1': 'ON', '0': 'OFF' }.get(value)
        if val:
            return val
        raise ValueError('{0} is not a valid value for property {1}'.format(value, property))

    @PhysicalDevice.deviceToProperty('input', '^P1S([0-9])$')
    def avm20ToMuted(self, property, value):
        assert (property == 'muted'), 'Wrong property received: ' + property
        val = { '1': True, '0': False }.get(value)
        if val:
            return val
        raise ValueError('{0} is not a valid value for property {1}'.format(value, property))

    @PhysicalDevice.deviceToProperty('volume', '^P1VM([+-][0-9]{1,2}(?:[\\.][0-9]{1,2})?)$')
    def avm20ToVolume(self, property, value):
        assert (property == 'volume'), 'Wrong property received: ' + property
        volarray = [-50, -35, -25, -21, -18, -12, -8, -4, 0, 5, 10 ]
        try:
            rawvol = float(value)
        except:
            raise ValueError('{0} is not a valid value for property {1}'.format(value, property))
        for i in range(len(self.volarray)):
            if rawvol <= self.volarray[i]:
                return i*10
        else:
            # volume greater than max array value
            return len(volstr)*10

    @PhysicalDevice.deviceToProperty(['input', 'volume', 'muted'], '^P1S([0-9])V([+-][0-9]{2}[\\.][0-9])M([0-1])D[0-9]E[0-9]$')
    def avm20combinedResponse(self, property, value):
        assert (property in ['input','volume', 'muted']), 'Wrong property received: {0}'.format(property)
        return { 'input': self.avm20ToInput, 'volume': self.avm20ToVolume, 'muted': self.avm20ToMuted }.get(property)(property, value)


    @PhysicalDevice.propertyToDevice('powerState', '{0}')
    def powerStateToAVM20(self, value):
        val = { 'ON': 'P1P1', 'OFF': 'P1P0' }.get(value)
        if val:
            return val
        raise ValueError('{0} is not a valid powerState'.format(value))

    @PhysicalDevice.propertyToDevice('input', '{0}')
    def inputToAVM20(self, value):
        val = { 'CD': 'P1S0', 'TAPE': 'P1P3', 'DVD': 'P1S5', 'TV': 'P1S6', 'SAT': 'P1S7', 'VCR': 'P1S8', 'AUX': 'P1S9' }.get(value)
        if val:
            return val
        raise ValueError('{0} is not a valid input'.format(value))




if __name__ == u'__main__':
#    import RPi.GPIO as GPIO
    try:
        myCloudLightDevice = cloudLight()

        cloudLightThing = PhysicalThing(endpoint='aamloz0nbas89.iot.us-east-1.amazonaws.com', thingName='cloudLightThing', rootCAPath='root-CA.pem', certificatePath='cloudLightThing.cert.pem', privateKeyPath='cloudLightThing.private.key', region='us-east-1', device=myCloudLightDevice)
    except KeyboardInterrupt:
        myCloudLightDevice.exit()
