

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
                    if cre.match(value):
                        return (property, method)
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
                    print ('Sending {0} to event queue'.format(ret))
                    (property, method) = ret

                    # Send updated property to Thing
                    self._eventQueue.put({'source': self.__name__, 'action': 'UPDATE', 'property': property, 'value': method(self,val) })
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
    def _initialize(self):
        pass

    @abstractmethod
    def _close(self):
        pass


class cloudLight(PhysicalDevice):

    def __init__(self, gpio=14):
        self._gpio = gpio
        super(cloudLight, self).__init__(name = 'Cloud Light', properties = { 'powerState': 'UNKNOWN' })

    def _read(self, timeout=0):
        start = time.time()
        while True:
            if self._gpioState != self._gpioCurrent:
                self._gpioCurrent = self._gpioState
                return self._gpioState
            if time.time() - start > timeout and timeout:
                return ''
            time.sleep(.1)

    def _write(self, value):
        if value == '1':
            GPIO.output(self._gpio, GPIO.HIGH)
        else:
            GPIO.output(self._gpio, GPIO.LOW)
        self._gpioState = value

    def _initialize(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self._gpio, GPIO.OUT, initial=GPIO.LOW)
        self._gpioState = '0'
        self._gpioCurrent = '-1'

    def _close(self):
        GPIO.cleanup()

    @PhysicalDevice.deviceToProperty('powerState', '^[01]$')
    def gpioToPowerState(self, value):
        if value == '1':
            return 'ON'
        elif value == '0':
            return 'OFF'
        raise ValueError('{0} is not a valid gpio value'.format(value))

    @PhysicalDevice.propertyToDevice('powerState', '{0}')
    def powerStateToGPIO(self, value):
        if value == 'ON':
            return '1'
        elif value == 'OFF':
            return '0'
        raise ValueError('{0} is not a valid powerState'.format(value))

if __name__ == u'__main__':
#    import RPi.GPIO as GPIO
    try:
        myCloudLightDevice = cloudLight()

        cloudLightThing = PhysicalThing(endpoint='aamloz0nbas89.iot.us-east-1.amazonaws.com', thingName='cloudLightThing', rootCAPath='root-CA.pem', certificatePath='cloudLightThing.cert.pem', privateKeyPath='cloudLightThing.private.key', region='us-east-1', device=myCloudLightDevice)
    except KeyboardInterrupt:
        myCloudLightDevice.exit()
