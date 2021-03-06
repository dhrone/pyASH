

from abc import ABC, abstractmethod
from threading import Timer, Lock, Thread
import serial
import io
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

    def _iotConnect(self, endpoint, thingName, rootCAPath, certificatePath, privateKeyPath, region):
        ''' Establish connection to the AWS IOT service '''
        # Init AWSIoTMQTTShadowClient
        myAWSIoTMQTTShadowClient = None
        myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient('pyASHdenTV')
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

    def onChange(self, updatedProperties):
        return None

    def start(self):
        self._main()

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
            for message in messages:
                if message['action'] == 'EXIT':
                    ''' If an EXIT message is received then stop processing messages and exit the main thing loop '''
                    return

                if message['action'] == 'UPDATE':
                    if message['source'] == '__thing__':
                        ''' Update is from IOT service.  Determine which device supports the updated property and send an update request to it '''
                        self._propertyHandlers[message['property']].updateDevice(message['property'], message['value'])
                    else:
                        ''' Update is from device. Add it to updatedProperties '''
                        updatedProperties[message['property']] = message['value']

                        localPropertyChanges = self.onChange(updatedProperties)
                        if localPropertyChanges:
                            for k, v in localPropertyChanges:
                                self._propertyHandlers[k].updateDevice(k,v)

            ''' If there are properties to report to the IOT service, send an update message '''
            updateNeeded = False
            payloadDict = { 'state': { 'reported': {}, 'desired': {} } }
            for property, value in updatedProperties.items():
                if self._localShadow[property] != value:
                    print ('IOT UPDATED: [{0}:{1}]'.format(property, value))
                    updateNeeded = True
                    payloadDict['state']['reported'] = updatedProperties
                    payloadDict['state']['desired'] = updatedProperties
            if updateNeeded:
                self._shadowHandler.shadowUpdate(json.dumps(payloadDict), self._updateCallback, 5)

class PhysicalDevice(ABC):
    ''' Device that makes up part of an IOT thing '''
    _logger = logging.getLogger(__name__)

    def __init__(self, name = None, stream = None, properties = None, eol='\n', timeout=5, synchronous=False):
        ''' Initialize device driver and set it to receive updates from the eventQueue '''

        self._stream = stream
        self._eol = eol
        self._timeout = timeout
        self._synchronous = synchronous
        self.properties = properties # dictionary of the properties and starting values for device
        self.__name__ = name if name is not None else self.__class__.__name__
        self._deviceQueue = queue.Queue()
        self.readlock = Lock()
        self._waitFor = None # Are we waiting for a specific value from the device
        self._exit = False # Set when a request has been made to exit the device driver

    def __del__(self):
        self.close()


    def start(self, eventQueue):
        self._eventQueue = eventQueue

        # Starting event loops
        _threadWrite = Thread(target=self._writeLoop)
        _threadWrite.start()

        # If device is asynchronous, start an independent read thread
        if not self._synchronous:
            _threadRead = Thread(target=self._readLoop)
            _threadRead.start()

    def updateDevice(self, property, value):
        ''' Send message to device to tell it to update one of its property values '''
        self._deviceQueue.put({'source': '__thing__', 'action': 'UPDATE', 'property': property, 'value': value })

    def updateThing(self, property, value):
        ''' Send message to thing telling it to update its thing shadow to reflect the device's reported state '''
        self._eventQueue.put({'source': self.__name__, 'action': 'UPDATE', 'property': property, 'value': value })

        # update local property value
        self.properties[property] = value

    def exit(self):
        ''' Shut down device driver '''
        self._exit = True
        self._deviceQueue.put({'action': 'EXIT'})

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
            val = self.read()
            if val:
                #print ('{0}:[{1}]'.format(self.__name__, val.replace('\r','\\r')))
                self._processDeviceResponse(val)

    def _processDeviceResponse(self, val):
        ret = self._deviceToProperty(val) # Retrieve appropriate handler to translate device value into property value
        if ret:
            (property, method, match) = ret
            if type(property) is not list: property = [ property ]

            for i in range(len(property)):
                # Extract out each match group and send to method to get it translated from the value from the device to the property value
                mval = match.group(i+1)
                xval = method(self, property[i], mval)

                if self.properties[property[i]] != xval:
                    # Send updated property to Thing
                    self.updateThing(property[i], xval)
#        else:
#            print ('{0}:[{1}] Ignored'.format(self.__name__, val.replace('\r','\\r')))


    def _writeLoop(self):
        ''' Main event loop for writing to device '''
        print ('Starting {0} writeLoop'.format(self.__name__))

        while not self._exit:
            try:
                # Wait for ready state to be reached
                while not self.ready():
                    print ('{0} Sleeping ...'.format(self.__name__))
                    time.sleep(5)
                    raise queue.Empty

                message = self._deviceQueue.get(block=True, timeout=5)
                self._deviceQueue.task_done()

                if message['action'].upper() == 'EXIT':
                    return
                elif message['action'].upper() == 'UPDATE':
                    print ('IOT requests [{0}:{1}]'.format(message['property'], message['value']))
                    ret = self._propertyToDevice(message['property'])
                    if ret:
                        (cmd, method) = ret

                        # Send updated property to device
                        val = self.write(cmd.format(method(self,message['value'])))

                        # If device is synchronous, it likely returned a response from the command we just sent
                        if val:
                            # If so, process it
                            self._processDeviceResponse(val)
                    else:
                        self._logger.warn('{0} has no property that matches {1}'.format(self.__name__,message['property']))

            except queue.Empty:
                # If nothing waiting to be written or the device is not ready, send a query to get current device status
                qs = self.queryStatus()
                if qs:
                    # Get the query to send.  If the query is a list, process each query individually
                    qs = qs if type(qs) is list else [ qs ]
                    for q in qs:
                        val = self.write(q)
                        if val:
                            self._processDeviceResponse(val)

                continue

    def _queryStatus(self):
        return None

    def queryStatus(self):
        return self._queryStatus()

    def _ready(self):
        return True

    def ready(self):
        return self._ready()

    def _read(self, eol=b'\n', timeout=5):
        eol = eol.encode() if type(eol) is str else eol

        with self.readlock:
            last_activity = time.time()
            buffer = b''
            while True:
                c = self._stream.read()
                if c:
                    buffer += c
                    last_activity = time.time()
                    if buffer.find(eol)>=0:
                        retval = buffer[:buffer.find(eol)]
                        break
                elif time.time() - last_activity > timeout:
                    retval = buffer
                    break
        return retval.decode()

    def _write(self, value, eol=b'\n', timeout=5, synchronous=False):
        value = value.encode() if type(value) is str else value
        eol = eol.encode() if type(eol) is str else eol

        # If device communicates synchronously, after sending request, wait for response
        # reading input until receiving the eol value indicating that it is done responding
        if synchronous:
            with self.readlock:
                self._stream.write(value)
                last_activity = time.time()
                buffer = b''
                while True:
                    c = self._stream.read()
                    if c:
                        buffer += c
                        last_activity = time.time()
                        if buffer.find(eol)>=0:
                            retval = buffer[:buffer.find(eol)]
                            break
                    elif time.time() - last_activity > timeout:
                        retval = buffer
                        break
        else:
            self._stream.write(value)
            retval = b''
        return retval.decode()

    def _close(self):
        self._stream.close()

    ''' Methods for User to override if their device is not operate as a stream '''
    def read(self):
        return self._read(self._eol, self._timeout)

    def write(self,value):
        return self._write(value, self._eol, self._timeout, self._synchronous)

    def close(self):
        self._close()




class AVM(PhysicalDevice):

    def __init__(self, port, baud):
        self._ser = serial.Serial(port, baud, timeout=0.25)
        self._timeout=0.25
        if not self._ser:
            raise IOError('Unable to open serial connection on power {0}'.format(port))
        super(AVM, self).__init__(name = 'AVM', stream = self._ser, properties = { 'powerState': 'UNKNOWN', 'input':'UNKNOWN', 'volume': 'UNKNOWN', 'muted': 'UNKNOWN' })
        self.volarray = [-50, -35, -25, -21, -18, -12, -8, -4, 0, 5, 10 ]

        self.write('P1P?')


    def close(self):
        self._ser.close()

    def queryStatus(self):
        if self.properties['powerState'] == 'ON':
            return 'P1?\n'
        else:
            return 'P1P?\n'

    @PhysicalDevice.deviceToProperty('powerState', '^P1P([0-1])$')
    def avmToPowerState(self, property, value):
        assert (property == 'powerState'), 'Wrong property received: ' + property
        val = { '1': 'ON', '0': 'OFF' }.get(value)
        if val:
            return val
        raise ValueError('{0} is not a valid value for property {1}'.format(value, property))

    @PhysicalDevice.deviceToProperty('input', '^P1S([0-9])$')
    def avmToInput(self, property, value):
        assert (property == 'input'), 'Wrong property received: ' + property
        val = { '0': 'CD', '3': 'TAPE', '5': 'DVD', '6': 'TV', '7': 'SAT', '8': 'VCR', '9': 'AUX' }.get(value)
        if val:
            return val
        raise ValueError('{0} is not a valid value for property {1}'.format(value, property))

    @PhysicalDevice.deviceToProperty('volume', '^P1VM([+-][0-9]{1,2}(?:[\\.][0-9]{1,2})?)$')
    def avmToVolume(self, property, value):
        assert (property == 'volume'), 'Wrong property received: ' + property
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

    @PhysicalDevice.deviceToProperty('muted', '^P1M([0-1])$')
    def avmToMuted(self, property, value):
        assert (property == 'muted'), 'Wrong property received: ' + property
        val = { '1': True, '0': False }.get(value, 'BAD')
        if not val=='BAD':
            return val
        raise ValueError('{0} is not a valid value for property {1}'.format(value, property))

    @PhysicalDevice.deviceToProperty(['input', 'volume', 'muted'], '^P1S([0-9])V([+-][0-9]{2}[\\.][0-9])M([0-1])D[0-9]E[0-9]$')
    def avmcombinedResponse(self, property, value):
        assert (property in ['input','volume', 'muted']), 'Wrong property received: {0}'.format(property)
        return { 'input': self.avmToInput, 'volume': self.avmToVolume, 'muted': self.avmToMuted }.get(property)(property, value)

    @PhysicalDevice.propertyToDevice('powerState', 'P1P{0}')
    def powerStateToAVM(self, value):
        val = { 'ON': '1', 'OFF': '0' }.get(value)
        if val:
            return val
        raise ValueError('{0} is not a valid powerState'.format(value))

    @PhysicalDevice.propertyToDevice('input', 'P1S{0}')
    def inputToAVM(self, value):
        val = { 'CD': '0', 'TAPE': '3', 'DVD': '5', 'TV': '6', 'SAT': '7', 'VCR': '8', 'AUX': '9' }.get(value)
        if val:
            return val
        raise ValueError('{0} is not a valid input'.format(value))

    @PhysicalDevice.propertyToDevice('volume', 'P1VM{0}')
    def volumeToAVM(self, value):
        if type(value) is int:
            value = int(value/10)
            value = 0 if value < 0 else 10 if value > 10 else value
            return self.volarray[value]
        raise ValueError('{0} is not a valid volume'.format(value))

    @PhysicalDevice.propertyToDevice('muted', 'P1M{0}')
    def muteToAVM(self, value):
        val = { True: '1', False: '0' }.get(value)
        if val:
            return val
        raise ValueError('{0} is not a valid muted value'.format(value))

class Epson1080UB(PhysicalDevice):

    def __init__(self, port, baud):
        self._ser = serial.Serial(port, baud, timeout=0.25)
        self._timeout=0.25
        if not self._ser:
            raise IOError('Unable to open serial connection on power {0}'.format(port))
        super(Epson1080UB, self).__init__(name = 'Epson1080UB', eol='\r:', stream = self._ser, properties = { 'projPowerState': 'UNKNOWN', 'projInput':'UNKNOWN'  }, synchronous=True)

        self.write('PWR?\r')

    def close(self):
        self._ser.close()

    def queryStatus(self):
        if self.properties['projPowerState'] == 'ON':
            return ['PWR?\r','SOURCE?\r']
        else:
            return 'PWR?\r'

    def ready(self):
        return True if self.properties['projPowerState'] in ['ON', 'OFF', 'UNKNOWN'] else False

    @PhysicalDevice.deviceToProperty('projPowerState', '^PWR=([0-9]{2})$')
    def toProjPowerState(self, property, value):
        assert (property == 'projPowerState'), 'Wrong property received: ' + property
        val = { '00': 'OFF', '01': 'ON', '02': 'WARMING', '03': 'COOLING', '04': 'STANDBY', '05': 'ABNORMAL' }.get(value)
        if val:
            return val
        raise ValueError('{0} is not a valid value for property {1}'.format(value, property))

    @PhysicalDevice.deviceToProperty('projInput', '^SOURCE=([a-zA-Z0-9]{2})$')
    def toProjInput(self, property, value):
        assert (property == 'projInput'), 'Wrong property received: ' + property
        val = { '30': 'HDMI1', 'A0': 'HDMI2', '41': 'VIDEO', '42': 'S-VIDEO' }.get(value)
        if val:
            return val
        raise ValueError('{0} is not a valid value for property {1}'.format(value, property))

    @PhysicalDevice.propertyToDevice('projPowerState', 'PWR {0}\r')
    def projPowerStateToProj(self, value):
        if value in ['ON', 'OFF']:
            return value
        raise ValueError('{0} is not a valid powerState'.format(value))

    @PhysicalDevice.propertyToDevice('projInput', 'SOURCE {0}\r')
    def projInputToProj(self, value):
        val = { 'HDMI1': '30', 'HDMI2': 'A0', 'VIDEO': '41', 'S-VIDEO': '42' }.get(value)
        if val:
            return val
        raise ValueError('{0} is not a valid input'.format(value))


class denTVThing(PhysicalThing):

    def onChange(self, updatedProperties):
        rv = []
        # Make sure AVM is always on and set to the Alexa input when not watching TV
        if updatedProperties.get('powerState') == 'OFF':
            print ('Returning powerState to ON and input to Alexa')
            rv.append(('powerState','ON'))
            rv.append(('input', 'CD'))
        return rv

if __name__ == u'__main__':

    try:
        denAVM = AVM('/dev/ttyUSB1',9600)
        denEpson = Epson1080UB('/dev/ttyUSB0',9600)

        denTV = denTVThing(endpoint='aamloz0nbas89.iot.us-east-1.amazonaws.com', thingName='denTVThing', rootCAPath='root-CA.crt', certificatePath='denTVThing.crt', privateKeyPath='denTVThing.private.key', region='us-east-1', devices=[denAVM,denEpson])
        denTV.start()
    except KeyboardInterrupt:
        denAVM.exit()
        denEpson.exit()
