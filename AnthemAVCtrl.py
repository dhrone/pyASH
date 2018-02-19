
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient

import serial
import logging
import json
import argparse
import time
import threading
import copy
from datetime import datetime
import re
import queue
from abc import ABC

exitapp = [ False ]


class device_controller(ABC):
    # Abstract class to interface a device to an IOT registry
    #   Updates state variables when value received from device
    #   Sends command to device based upon a change in state variables

    def __init__(self, q_sc=None, cmdack = b'', cmdtimeout = 20, name = 'device'):
        self.device_t = threading.Thread(target=self.run)
        self.device_t.daemon = True

        self.device_to_iot_db = { } # Format { iotvariable: [regex_match, regex_cmd, s2i_func]}
        self.iot_to_device_db = { } # Format { iotvariable: [command, i2s_func] }
        self.device_queries = { } # Format { iotvariable: querystring }
        self.name = name
        self.cmdack = cmdack
        self.cmdtimeout = cmdtimeout
        self.q_sc = q_sc
        self.listenerstarted = False
        self.readlock = threading.Lock()

        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.INFO)


    @abstractmethod
    def open(self):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def get(self, delimiter=b'\n', timeout=0):
        pass

    @abstractmethod
    def send(self, value, ack=b'', timeout=20):
        pass

    def listen(self):
        if not self.q_sc:
            self.logger.critical('Cannot use listen without providing a queue')
            raise RuntimeError('Cannot use listen without providing a queue')
        if type(self.q_sc) != queue.Queue:
            errmsg = 'Cannot use listen without a valid queue.  Type provided was {0}'.format(str(type(self.q_sc)))
            self.logger.critical(errmsg)
            raise RuntimeError(errmsg)

        self.listenerstarted = True
        self.open()
        self.device_t.start()

    def run(self):
        if not self.listenerstarted:
            self.logger.warn('Run can only be started by the listen method.  It is intended to be used only within a separate thread')
            return

        self.logger.debug(u'{0} threaded monitor starting'.format(self.port))

        while not exitapp[0]:
            instr = self.get()
            if instr:
                res = self.device_to_iot(instr)
                self.q_sc.put(res)

        print('{0} controller thread exiting...'.format(self.name))

        self.close()

    def query(self, value=''):
        # This method queries the device to get its status
        # If an IOT variable is specified, it's value will be specifically queried
        # Otherwise all possible IOT variables for this device will be queried
        # Special Note: If this controller is listening (e.g. multithreaded), no
        #               response will be returned.  This is because the response
        #               will be handled in the controllers run method

        if value in self.device_queries:
            qval = self.device_queries[value]
            if type(qval) == str:
                qval = qval.encode()
            instr = self.send(qval, self.cmdack, self.cmdtimeout).strip()
            if not self.listenerstarted:
                res = self.device_to_iot(instr)
                return res
            else:
                return { }

        elif not value:
            results = { }
            for item in self.device_queries:
                qval = self.device_queries[item]
                if type(qval) == str:
                    qval = qval.encode()
                instr = self.send(qval, self.cmdack, self.cmdtimeout).strip()
                if not self.listenerstarted:
                    res = self.device_to_iot(instr)
                    results = {**results, **res}
            return results
        else:
            self.logger.warn('{0} is not a valid query attribute for this device'.format(value))

    def iot_to_device(self, attribute, value):
        self.logger.info ('Received IOT update ['+str(attribute)+'] value ['+str(value)+']')

        if attribute not in self.iot_to_device_db:
#            logging.debug(u'{0} is not a valid IOT attribute for this device'.format(attribute))
            # Ignore a bad value to make updating multiple controllers easier
            return None

        (command, i2s_func) = self.iot_to_device_db[attribute]
        buffer = command.format(i2s_func(value))
        self.send(buffer.encode(), self.cmdack, self.cmdtimeout)

    def device_to_iot(self, data_from_device):

        if len(data_from_device) > 0:
            self.logger.info('From {0}, received [{1}]'.format(self.name, data_from_device.decode()))

        results = { }
        for item in self.device_to_iot_db:
            rule = self.device_to_iot_db[item]
            regex_match = rule[0]
            if type(regex_match) == str:
                regex_match = regex_match.encode()
            m = re.match(regex_match, data_from_device)
            if m:
                if type(item) == tuple:
                    if len(m.groups()) != len(item):
                        self.logger.warn('Mismatch between variables and group.  Variables are [{0}] and groups are [{1}]'.format(item, m.groups()))
                        break
                    for i in range(len(item)):
                        translate_function = rule[i+1]
                        results[item[i]] = translate_function(m.groups()[i])
                else:
                    if len(m.groups()) != 1:
                        self.logger.warn('Mismatch between variables and group.  Variables are [{0}] and groups are [{1}]'.format(item, m.groups()))
                        break
                    translate_function = rule[1]
                    results[item] = translate_function(m.groups()[0])
                break
        return results

    def int_to_bool(self, value):
        try:
            res = bool(int(value))
        except:
            self.logger.warn('{0} type cannot be converted to a boolean value'.format(str(type(value))))
            res = False
        return res

    def bool_to_int(self, value):
        try:
            res = int(value)
        except:
            self.logger.warn('{0} type cannot be converted to an integer value'.format(str(type(value))))
            res = False
        return res

    def bool_to_onoff(self, value):
        try:
            res = 'ON' if int(value) > 0 else 'OFF'
        except:
            self.logger.warn('{0} type cannot be converted to an integer value'.format(str(type(value))))
            res = 'OFF'
        return res


class serial_controller(device_controller):
    # Communicates with receiver over serial interface
    # Updates receiver state variables when command received through input queue

    def __init__(self, port, baud, q_sc=None, cmdack = b'', cmdtimeout = 20, name = 'serial'):
        super(serial_controller, self).__init__(q_sc, cmdack, cmdtimeout, name)
        self.port = port
        self.name = name
        self.baud = baud
        self.ser = None

    def open(self):
        if not self.ser:
            self.ser = serial.Serial(self.port, self.baud, timeout=0.25)

    def close(self):
        self.ser.close()

    def get(self, delimiter=b'\n', timeout=0):
        # Should return a single key value from the input

        self.open()

        if not timeout:
            if self.cmdtimeout:
                timeout = self.cmdtimeout

        buffer = b''
        if type(delimiter) == str:
            delimiter = delimiter.encode()
        last_activity = time.time()

        self.readlock.acquire()
        while True:
            c = self.ser.read()
            if c:
                last_activity = time.time()
            if c == delimiter:
                self.readlock.release()
                return buffer
            buffer += c
            if time.time() - last_activity > timeout:
                self.readlock.release()
                return buffer

    def send(self, value, ack=b'', timeout=20):
        self.open()

        if type(value) == str:
            value = value.encode()
        self.ser.write(value)
        self.logger.info ('From {0}, Sending  [{1}]'.format(self.name,value))
        if ack:
            if ack == str:
                ack = ack.encode()
            last_activity = time.time()
            buffer = b''
            self.readlock.acquire()
            while True:
                c = self.ser.read()
                buffer += c
                if buffer.find(ack)>=0:
                    self.readlock.release()
                    return buffer[:buffer.find(ack)]
                elif time.time() - last_activity > timeout:
                    self.readlock.release()
                    return buffer
        else:
            return b''


class AVM20_serial_controller(serial_controller):

    def __init__(self, port, baud, q_sc):
        super(AVM20_serial_controller, self).__init__(port, baud, q_sc, cmdtimeout=5, name='AVM20')

        # Maps from db to 0-10 volume scale
        self.volarray = [-50, -35, -25, -21, -18, -12, -8, -4, 0, 5, 10 ]
        self.sources = {
            '0':'CD',
            '1':'2-Ch Bal',
            '2':'6-Ch S/E',
            '3':'tape',
            '4':'FM/AM',
            '5':'DVD',
            '6':'TV',
            '7':'SAT',
            '8':'VCR',
            '9':'AUX'
        }
        self.device_to_iot_db = {
            'volume': [b'^P1VM([+-][0-9]{1,2}(?:[\\.][0-9]{1,2})?)$', self.volume_to_iot ],
            'asource': ['^P1S([0-9])$', self.source_to_iot],
            'apower': ['^P1P([0-1])$', self.int_to_bool],
            'mute': ['^P1M([0-1])$', self.int_to_bool],
            ('asource', 'volume', 'mute'): [b'^P1S([0-9])V([+-][0-9]{2}[\\.][0-9])M([0-1])D[0-9]E[0-9]$', self.source_to_iot, self.volume_to_iot, self.int_to_bool ]
        } # Format { iotvariable: [regex_match, regex_cmd, s2i_func]}

        self.iot_to_device_db = {
            'volume': ['P1VM{0}\n', self.iot_to_volume],
            'asource': ['P1S{0}\n', self.iot_to_source],
            'apower': ['P1P{0}\n', self.bool_to_int],
            'mute': ['P1M{0}\n', self.bool_to_int]
        } # Format { iotvariable: [command, i2s_func] }

        self.device_queries = {
            'apower': 'P1P?\n',
            'system': 'P1?\n'
        }

        self.listen()

    def volume_to_iot(self, value):
        try:
            rawvol = float(value)
        except:
            self.logger.warn('{0} is not a valid type for a preamp volume'.format(str(type(value))))
            rawvol = float(-50.0)
        for i in range(len(self.volarray)):
            if rawvol <= self.volarray[i]:
                return i
        else:
            # volume greater than max array value
            return len(volstr)

    def iot_to_volume(self,value):
        try:
            value = int(value)
        except:
            self.logger.warn('IOT volume must be numeric.  Recieved type {0}'.format(str(type(value))))
            value = 0
        if value < 0 or value > 10:
            self.logger.warn('IOT volume must be between 0 and 10.  Received {0}'.format(value))
        return self.volarray[value]

    def source_to_iot(self, value):
        if type(value) == bytes:
            value = value.decode()
        try:
            source = self.sources[value]
        except:
            self.logger.warn('{0} is not a valid source value'.format(value))
            source = 'Unknown'
        return source

    def iot_to_source(self, value):
        for k in self.sources:
            if self.sources[k] == value:
                return k
        else:
            self.logger.warn('{0} is not a valid IOT source'.format(value))
            return '0'

class EPSON1080UB_serial_controller(serial_controller):

    # The Epson works purely on challenge response.  No need for multi-threading

    def __init__(self, port, baud):
        super(EPSON1080UB_serial_controller, self).__init__(port, baud, q_sc=None, cmdack=b':', cmdtimeout=20,name='Epson1080UB')

        # Maps from db to 0-10 volume scale
        self.sources = {
            '30':'HDMI1',
            'A0':'HDMI2',
            '41':'VIDEO',
            '42':'S-VIDEO'
        }

        self.device_to_iot_db = {
            'esource': ['^SOURCE=([a-zA-Z0-9]{2})$', self.source_to_iot],
            'epower': ['^PWR=([0-9]{2})$', self.int_to_bool]
        } # Format { iotvariable: [regex_match, regex_cmd, s2i_func]}

        self.iot_to_device_db = {
            'esource': ['SOURCE {0}\r', self.iot_to_source],
            'epower': ['PWR {0}\r', self.bool_to_onoff],
        } # Format { iotvariable: [devicecommand, i2s_func] }

        self.device_queries = {
            'esource': 'SOURCE?\r',
            'epower': 'PWR?\r'
        }

    def source_to_iot(self, value):
        if type(value) == bytes:
            value = value.decode()
        try:
            source = self.sources[value]
        except:
            self.logger.warn('{0} is not a valid source value'.format(value))
            source = 'Unknown'
        return source

    def iot_to_source(self, value):
        for k in self.sources:
            if self.sources[k] == value:
                return k
        else:
            self.logger.warn('{0} is not a valid IOT source'.format(value))
            return '00'

# Custom Shadow callback
def customShadowCallback_Delta(payload, responseStatus, token):
    payloadDict = json.loads(payload)

    # Get global reference to receiver device controllers, state data and ShadowHandler
    global avmSC
    global epsSC
    global receiverdata
    global receiverdata_shadow
    global logger

    update_needed = False
    for item in payloadDict['state']:
        logger.info('Delta Message: processing item [{0}][{1}]'.format(item, payloadDict['state'][item]))
        try:
            if item in receiverdata:
                if receiverdata[item] != payloadDict['state'][item]:
                    # Need to update receiver
                    avmSC.iot_to_device(item, payloadDict['state'][item])
                    epsSC.iot_to_device(item, payloadDict['state'][item])
#                    rc.sendupdate(item,payloadDict['state'][item])
                    receiverdata_shadow[item] = receiverdata[item]
                    update_needed = True
            else:
                avmSC.iot_to_device(item, payloadDict['state'][item])
                epsSC.iot_to_device(item, payloadDict['state'][item])
#                rc.sendupdate(item,payloadDict['state'][item])
                receiverdata[item] = payloadDict['state'][item]
                receiverdata_shadow[item] = receiverdata[item]
                update_needed = True

        except KeyError:
            logger.debug(u'Received unexpected attribute in delta message.  Item was '+item)

def customShadowCallback_Update(payload, responseStatus, token):
    # payload is a JSON string ready to be parsed using json.loads(...)
    # in both Py2.x and Py3.x
    if responseStatus == "timeout":
        logging.warn("Update request " + token + " timed out!")
    if responseStatus == "accepted":
        payloadDict = json.loads(payload)
#        print("Update request with token: " + token + " accepted!")
#        print("update: " + str(payloadDict["state"]["desired"]))
        logging.info ('IOT device update with...')
        logging.info (json.dumps(payloadDict, indent=4))
    if responseStatus == "rejected":
        logging.warn("Update request " + token + " rejected!")

def customShadowCallback_Delete(payload, responseStatus, token):
    if responseStatus == "timeout":
        logging.warn("Delete request " + token + " time out!")
    if responseStatus == "accepted":
        logging.info("Delete request with token: " + token + " accepted!")
    if responseStatus == "rejected":
        logging.warn("Delete request " + token + " rejected!")

receiverdata = {
    'apower':False,
    'epower':False,
    'volume':0,
    'mute':False,
    'asource':'Unknown',
    'esource':'Unknown'
}

if __name__ == u'__main__':

    # Read in command-line parameters
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--endpoint", action="store", required=True, dest="host", help="Your AWS IoT custom endpoint")
    parser.add_argument("-r", "--rootCA", action="store", required=True, dest="rootCAPath", help="Root CA file path")
    parser.add_argument("-c", "--cert", action="store", dest="certificatePath", help="Certificate file path")
    parser.add_argument("-k", "--key", action="store", dest="privateKeyPath", help="Private key file path")
    parser.add_argument("-n", "--thingName", action="store", dest="thingName", default="Bot", help="Targeted thing name")
    parser.add_argument("-id", "--clientId", action="store", dest="clientId", default="basicShadowUpdater", help="Targeted client id")

    args = parser.parse_args()
    host = args.host
    rootCAPath = args.rootCAPath
    certificatePath = args.certificatePath
    privateKeyPath = args.privateKeyPath
#    useWebsocket = args.useWebsocket
    thingName = args.thingName
    clientId = args.clientId

    if (not args.certificatePath or not args.privateKeyPath):
        parser.error("Missing credentials for authentication.")
        exit(2)

    # Configure logging
    logger = logging.getLogger("AWSIoTPythonSDK.core")
    logger.setLevel(logging.WARNING)
    streamHandler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    streamHandler.setFormatter(formatter)
    logger.addHandler(streamHandler)

    # Init AWSIoTMQTTShadowClient
    myAWSIoTMQTTShadowClient = None
    myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient('pyASHTV')
    myAWSIoTMQTTShadowClient.configureEndpoint(host, 8883)
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
    deviceShadowHandler.shadowDelete(customShadowCallback_Delete, 5)

    # Listen on deltas
    deviceShadowHandler.shadowRegisterDeltaCallback(customShadowCallback_Delta)

    q_avmSC = queue.Queue()
    avmSC = AVM20_serial_controller('/dev/ttyUSB0',9600, q_avmSC)
    avmSC.query()
    epsSC = EPSON1080UB_serial_controller('/dev/ttyUSB1', 9600)

    receiverdata_shadow = copy.deepcopy(receiverdata)

    firstpass = True
    epson_update_timer = 0
    try:
        while True:
            time.sleep(.5)

            # Process queue messages
            while True:
                try:
                    res = q_avmSC.get_nowait()
                    q_avmSC.task_done()
                    for item in res:
                        receiverdata[item] = res[item]
                except:
                    break


            # Poll Epson status every 5 seconds
            if time.time() > epson_update_timer:
                res = epsSC.query()
                for item in res:
                    receiverdata[item] = res[item]
                epson_update_timer = time.time() + 5

            if not firstpass:
                # Check to see if anything has changed
                receiverdata_update = { }
                for item in receiverdata:
                    if receiverdata[item] != receiverdata_shadow[item]:
                        receiverdata_update[item] = receiverdata[item]
                        receiverdata_shadow[item] = receiverdata[item]
            else:
                firstpass = False
                receiverdata_update = copy.deepcopy(receiverdata)

            # If there are changes, update the AWS shadow
            if len(receiverdata_update) > 0:
                for item in receiverdata_update:
                    print ('Updating shadow [{0}][{1}]'.format(item, receiverdata_update[item]))
                payload_dict = {'state':{'desired':{}}}
                payload_dict['state']['desired'] = receiverdata_update
                JSONPayload = json.dumps(payload_dict)
                deviceShadowHandler.shadowUpdate(JSONPayload, customShadowCallback_Update, 5)
                payload_dict['state']['reported'] = receiverdata_update
                JSONPayload = json.dumps(payload_dict)
                deviceShadowHandler.shadowUpdate(JSONPayload, customShadowCallback_Update, 5)

            # Make sure that preamp defaults to on and source:CD to enable echo to speak
            if receiverdata['apower']==False:
                avmSC.iot_to_device('apower',True)
                avmSC.iot_to_device('asource', 'CD')
#                rc.ser.write('P1P1;P1S0\n')
#                receiverdata['mute']=False
                time.sleep(0.1)
                avmSC.query()
#                rc.ser.write('P1S?;P1VM?\n')

    except KeyboardInterrupt:
        pass

    finally:
        print ("Exiting...")
        if epsSC:
            epsSC.close()
        exitapp[0] = True
        logging.info('Exiting...')
        time.sleep(1)
