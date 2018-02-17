
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

exitapp = [ False ]


# P1VM+12.34 'P1VM[+-]?[0-9]{1,2}([\\.][0-9]{1,2})?'

# iotk, iotv, device_cmd, translate_function
# 'power', True, 'P1P', vars(__builtins__)['int']

class serial_controller(object):
    # Communicates with receiver over serial interface
    # Updates receiver state variables when command received through input queue

    def __init__(self, port, baud, q_sc=None, cmdack = b'', cmdtimeout = 20):
        self.serial_t = threading.Thread(target=self.run)
        self.serial_t.daemon = True

        self.serial_to_iot_db = { } # Format { iotvariable: [regex_match, regex_cmd, s2i_func]}
        self.iot_to_serial_db = { } # Format { iotvariable: [serialcommand, i2s_func] }
        self.device_queries = { } # Format { iotvariable: querystring }
        self.port = port
        self.baud = baud
        self.cmdack = cmdack
        self.cmdtimeout = cmdtimeout
        self.q_sc = q_sc
        self.listenerstarted = False
        self.ser = None

    def listen(self):
        if not self.q_sc:
            logging.critical('Cannot use listen without providing a queue')
            raise RuntimeError('Cannot use listen without providing a queue')
        if type(self.q_sc) != queue.Queue:
            errmsg = 'Cannot use listen without a valie queue.  Type provided was {0}'.format(str(type(self.q_sc)))
            logging.critical(errmsg)
            raise RuntimeError(errmsg)

        self.listenerstarted = True
        self.open()
        self.serial_t.start()

    def open(self):
        if not self.ser:
            self.ser = serial.Serial(self.port, self.baud, timeout=0.25)

    def close(self):
        self.ser.close()

    def run(self):
        if not self.listenerstarted:
            logging.warn('Run can only be started by the listen method.  It is intended to be used only within a separate thread')
            return

        logging.debug(u'{0} threaded monitor starting'.format(self.port))

        while not exitapp[0]:
            instr = self.get_input()
            res = self.serial_to_iot(instr)
            q_sc.put([item, res])

        self.close()

    def get_input(self, delimiter=b'\n', timeout=0):
        # Should return a single key value from the input

        self.open()

        if not timeout:
            if self.cmdtimeout:
                timeout = self.cmdtimeout

        buffer = b''
        if type(delimiter) == str:
            delimiter = delimiter.encode()
            last_activity = time.time()
        while True:
            c = self.ser.read()
            if c:
                last_activity = time.time()
            if c == delimiter:
                return buffer
            buffer += c
            if time.time() - last_activity > timeout:
                return buffer

    def iot_to_serial(self, attribute, value):
        # Ignore bad commands

        print ('Received IOT update ['+str(attribute)+'] value ['+str(value)+']')

        if attribute not in self.iot_to_serial_db:
            logging.debug(u'{0} is not a valid IOT attribute for this device'.format(attribute))
            return None

        (serialcommand, i2s_func) = self.iot_to_serial_db[attribute]
        buffer = serialcommand.format(value)
        self.send_serial(buffer.encode(), self.cmdack, self.cmdtimeout)

    def send_serial(self, value, ack=b'', timeout=20):
        self.open()

        if type(value) == str:
            value = value.encode()
        self.ser.write(value)
        if ack:
            if ack == str:
                ack = ack.encode()
            last_activity = time.time()
            buffer = b''
            while True:
                c = self.ser.read()
                buffer += c
                if (buffer == ack) or (time.time() - last_activity > timeout):
                    return buffer

    def query(self, value=''):
        # This method queries the serial device to get its status
        # If an IOT variable is specified, it's value will be specifically queried
        # Otherwise all possible IOT variables for this device will be queried
        # Special Note: If this serial controller is listening (e.g. multithreaded),
        #               no response will be returned.  This is because the response
        #               will be handled in the controllers run method

        if value in self.device_queries:
            qval = self.device_queries[value]
            if type(qval) == str:
                qval = qval.encode()
            self.send_serial(qval, self.cmdack, self.cmdtimeout)
            if not self.listenerstarted:
                instr = self.get_input()
                res = self.serial_to_iot(instr)
                return { value: res }
            else:
                return { }

        elif not value:
            results = { }
            for item in self.device_queries:
                qval = self.device_queries[item]
                if type(qval) == str:
                    qval = qval.encode()
                self.send_serial(qval, self.cmdack, self.cmdtimeout)
                if not self.listenerstarted:
                    instr = self.get_input()
                    res = self.serial_to_iot(instr)
                    results[item] = res
            return results
        else:
            logging.warn('{0} is not a valid query attribute for this device'.format(value))


    def serial_to_iot(self, data_from_serial):

        if len(data_from_serial) > 0:
            print ('From serial, received ['+data_from_serial+']')

        for item in self.serial_to_iot_db:
            (regex_match, regex_cmd, translate_function) = self.serial_to_iot_db[item]
            m = re.match(regex_match, data_from_serial)
            if m:
                return translate_function(re.split(regex_cmd, data_from_serial)[1])  # Split command from variable and return translated variable

    def int_to_bool(self, value):
        try:
            res = bool(value)
        except:
            logging.warn('{0} type cannot be converted to a boolean value'.format(str(type(value))))
            res = False
        return res

    def bool_to_int(self, value):
        try:
            res = int(value)
        except:
            logging.warn('{0} type cannot be converted to an integer value'.format(str(type(value))))
            res = False
        return res

    def bool_to_onoff(self, value):
        try:
            res = 'ON' if int(value) > 0 else 'OFF'
        except:
            logging.warn('{0} type cannot be converted to an integer value'.format(str(type(value))))
            res = 'OFF'
        return res

class AVM20_serial_controller(serial_controller):

    def __init__(self, port, baud, q_sc):
        super(AVM20_serial_controller, self).__init__(port, baud, q_sc, cmdtimeout=5)

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
        self.serial_to_iot_db = {
            'volume': ['P1VM[+-][0-9]{1,2}([\\.][0-9]{1,2})?', 'P1VM', self.volume_to_iot ],
            'source': ['P1S[0-9]','P1S', self.source_to_iot],
            'power': ['P1P[0-1]','P1P', self.int_to_bool],
            'mute': ['P1M[0-1]','P1M', self.int_to_bool]
        } # Format { iotvariable: [regex_match, regex_cmd, s2i_func]}

        self.iot_to_serial_db = {
            'volume': ['P1VM{0}\n', self.iot_to_volume],
            'source': ['P1S{0}\n', self.iot_to_source],
            'power': ['P1P{0}\n', self.bool_to_int],
            'mute': ['P1M{0}\n', self.bool_to_int]
        } # Format { iotvariable: [serialcommand, i2s_func] }

        self.device_queries = {
            'volume': 'P1VM?\n',
            'source': 'P1S?\n',
            'power': 'P1P?\n',
            'mute': 'P1M?\n'
        }

        self.listen()

    def volume_to_iot(self, value):
        try:
            rawvol = float(value)
        except:
            logging.warn('{0} is not a valid type for a preamp volume'.format(str(type(value))))
            rawvol = float(-50.0)
        for i in range(len(self.volarray)):
            if value <= self.volarray[i]:
                return i
        else:
            # volume greater than max array value
            return len(volstr)

    def iot_to_volume(self,value):
        try:
            value = int(value)
        except:
            logging.warn('IOT volume must be numeric.  Recieved type {0}'.format(str(type(value))))
            value = 0
        if value < 0 or value > 10:
            logging.warn('IOT volume must be between 0 and 10.  Received {0}'.format(value))
        return self.volarray[value]

    def source_to_iot(self, value):
        if type(value) == bytes:
            value = value.decode()
        try:
            source = self.sources[value]
        except:
            logging.warn('{0} is not a valid source value'.format(value))
            source = 'Unknown'
        return source

    def iot_to_source(self, value):
        for k in self.sources:
            if self.sources[k] == value:
                return k
        else:
            logging.warn('{0} is not a valid IOT source'.format(value))
            return '0'

class EPSON1080UB_serial_controller(serial_controller):

    # The Epson works purely on challenge response.  No need for multi-threading

    def __init__(self, port, baud):
        super(EPSON1080UB_serial_controller, self).__init__(port, baud, q_sc=None, cmdack=b':', cmdtimeout=20)

        # Maps from db to 0-10 volume scale
        self.sources = {
            '30':'HDMI1',
            'A0':'HDMI2',
            '41':'VIDEO',
            '42':'S-VIDEO'
        }

        self.serial_to_iot_db = {
            'source': ['P1S[0-9]','P1S', self.source_to_iot],
            'power': ['P1P[0-1]','P1P', self.int_to_bool]
        } # Format { iotvariable: [regex_match, regex_cmd, s2i_func]}

        self.iot_to_serial_db = {
            'source': ['SOURCE {0}\r', self.iot_to_source],
            'power': ['PWR {0}\r', self.bool_to_onoff],
        } # Format { iotvariable: [serialcommand, i2s_func] }

        self.device_queries = {
            'source': 'SOURCE?\r',
            'power': 'PWR?\r'
        }

    def source_to_iot(self, value):
        if type(value) == bytes:
            value = value.decode()
        try:
            source = self.sources[value]
        except:
            logging.warn('{0} is not a valid source value'.format(value))
            source = 'Unknown'
        return source

    def iot_to_source(self, value):
        for k in self.sources:
            if self.sources[k] == value:
                return k
        else:
            logging.warn('{0} is not a valid IOT source'.format(value))
            return '00'

# Custom Shadow callback
def customShadowCallback_Delta(payload, responseStatus, token):
    # payload is a JSON string ready to be parsed using json.loads(...)
    # in both Py2.x and Py3.x
#    print(responseStatus)
    payloadDict = json.loads(payload)

    # Get global reference to receiver serial controller, state data and ShadowHandler
    global rc
    global receiverdata
    global receiverdata_shadow
    global deviceShadowHandler

    print("++++++++DELTA++++++++++")
#    print("property: " + str(payloadDict["state"]["property"]))
#    print("version: " + str(payloadDict["version"])
    print (payloadDict)
    print("+++++++++++++++++++++++\n\n")

    update_needed = False
    for item in payloadDict['state']:
        print ('customShadowCallback_Delta: processing item ' + str(item))
        if item not in rc.allowedcommands:
            # Ignore attributes that are not valid valid commands
            logging.debug(u'customShadowCallback_Delta: invalid command received in payload.  Value was '+str(item))
            continue
        try:
            if item in receiverdata:
                if receiverdata[item] != payloadDict['state'][item]:
                    # Need to update receiver
                    rc.sendupdate(item,payloadDict['state'][item])
                    receiverdata_shadow[item] = receiverdata[item]
                    update_needed = True
            else:
                rc.sendupdate(item,payloadDict['state'][item])
                receiverdata[item] = payloadDict['state'][item]
                receiverdata_shadow[item] = receiverdata[item]
                update_needed = True

        except KeyError:
            logging.debug(u'customShadowCallback_Delta: item missing from receiverdata.  Item was '+item)

#    payload_dict = {'state':{'reported':{}}}
#    payload_dict['state']['reported'] = receiverdata
#    JSONPayload = json.dumps(payload_dict)
#    deviceShadowHandler.shadowUpdate(JSONPayload, customShadowCallback_Update, 5)


def customShadowCallback_Update(payload, responseStatus, token):
    # payload is a JSON string ready to be parsed using json.loads(...)
    # in both Py2.x and Py3.x
    if responseStatus == "timeout":
        print("Update request " + token + " time out!")
    if responseStatus == "accepted":
        payloadDict = json.loads(payload)
        print("~~~~~~~~~~~~~~UPDATE~~~~~~~~~~~~~~~")
#        print("Update request with token: " + token + " accepted!")
#        print("update: " + str(payloadDict["state"]["desired"]))
        print (payloadDict)
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n")
    if responseStatus == "rejected":
        print("Update request " + token + " rejected!")

def customShadowCallback_Delete(payload, responseStatus, token):
    if responseStatus == "timeout":
        print("Delete request " + token + " time out!")
    if responseStatus == "accepted":
        print("~~~~~~~~~~~~~~~~~~~~~~~")
        print("Delete request with token: " + token + " accepted!")
        print("~~~~~~~~~~~~~~~~~~~~~~~\n\n")
    if responseStatus == "rejected":
        print("Delete request " + token + " rejected!")

receiverdata = {
    'power':False,
    'volume':0,
    'mute':False,
    'source':'Unknown'
}



if __name__ == u'__main__':


    q_avmSC = queue.Queue()
    avmSC = AVM20_serial_controller('/dev/ttyUSB0',9600, q_avmSC)
    epsSC = EPSON1080UB_serial_controller('/dev/ttyUSB1', 9600)

    duration = 60

    start = time.time()
    while start+60 > time.time():
        eps_res = epsSC.query()
        avm_res = q_avmSC.get()
        q_avmSC.task_done()
        print (json.dumps(eps_res,indent=4))
        print (json.dumps(avm_res, indent=4))



'''
    # Read in command-line parameters
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--endpoint", action="store", required=True, dest="host", help="Your AWS IoT custom endpoint")
    parser.add_argument("-r", "--rootCA", action="store", required=True, dest="rootCAPath", help="Root CA file path")
    parser.add_argument("-c", "--cert", action="store", dest="certificatePath", help="Certificate file path")
    parser.add_argument("-k", "--key", action="store", dest="privateKeyPath", help="Private key file path")
    parser.add_argument("-w", "--websocket", action="store_true", dest="useWebsocket", default=False,
                        help="Use MQTT over WebSocket")
    parser.add_argument("-n", "--thingName", action="store", dest="thingName", default="Bot", help="Targeted thing name")
    parser.add_argument("-id", "--clientId", action="store", dest="clientId", default="basicShadowUpdater", help="Targeted client id")

    args = parser.parse_args()
    host = args.host
    rootCAPath = args.rootCAPath
    certificatePath = args.certificatePath
    privateKeyPath = args.privateKeyPath
    useWebsocket = args.useWebsocket
    thingName = args.thingName
    clientId = args.clientId

    if args.useWebsocket and args.certificatePath and args.privateKeyPath:
        parser.error("X.509 cert authentication and WebSocket are mutual exclusive. Please pick one.")
        exit(2)

    if not args.useWebsocket and (not args.certificatePath or not args.privateKeyPath):
        parser.error("Missing credentials for authentication.")
        exit(2)

    # Configure logging
    logger = logging.getLogger("AWSIoTPythonSDK.core")
    logger.setLevel(logging.INFO)
    streamHandler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    streamHandler.setFormatter(formatter)
    logger.addHandler(streamHandler)

    # Init AWSIoTMQTTShadowClient
    myAWSIoTMQTTShadowClient = None
    if useWebsocket:
        myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient(clientId, useWebsocket=True)
        myAWSIoTMQTTShadowClient.configureEndpoint(host, 443)
        myAWSIoTMQTTShadowClient.configureCredentials(rootCAPath)
    else:
        myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient(clientId)
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

    receiverdata_shadow = copy.deepcopy(receiverdata)

    rc = receiver_serial_controller('/dev/ttyUSB0',9600,receiverdata)
    rc.readupdates()

#    rc.start()
    time.sleep(1)

    firstpass = True
    try:
        while True:
#            for item in receiverdata:
#                value = receiverdata[item]
#                print "[{0}] {1}".format(item, value)
#            print '\n\n'

            rc.readupdates()
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
                payload_dict = {'state':{'desired':{}}}
                payload_dict['state']['desired'] = receiverdata_update
                JSONPayload = json.dumps(payload_dict)
                deviceShadowHandler.shadowUpdate(JSONPayload, customShadowCallback_Update, 5)
                payload_dict['state']['reported'] = receiverdata_update
                JSONPayload = json.dumps(payload_dict)
                deviceShadowHandler.shadowUpdate(JSONPayload, customShadowCallback_Update, 5)

            # Make sure that preamp defaults to on and source:CD to enable echo to speak
            if receiverdata['power']==False:
                rc.ser.write('P1P1;P1S0\n')
                receiverdata['mute']=False
                time.sleep(0.1)
                rc.ser.write('P1S?;P1VM?\n')

    except KeyboardInterrupt:
        pass

    finally:
        print "Exiting..."
#        exitapp[0] = True

        #rc.join()
        logging.info('Exiting...')
'''
