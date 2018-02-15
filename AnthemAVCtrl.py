
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient

import serial
import logging
import json
import argparse
import time
import threading
import copy

exitapp = [ False ]

class receiver_serial_controller():
	# Communicates with receiver over serial interface
	# Updates receiver state variables when command received through input queue


	def __init__(self, port, baud, receiverdata={}, deviceShadowHandler=''):
#		threading.Thread.__init__(self)

#		self.daemon = True
		self.deviceShadowHandler = deviceShadowHandler
		self.receiverdata = receiverdata

		self.ser = serial.Serial(port, baud, timeout=0.25)

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

		self.allowedcommands = {'volume','source','power','mute'}

		# Send requests for status to receiver
		self.ser.write('P1P?\n')
		self.ser.write('P1VM?\n')
		self.ser.write('P1S?\n')

		# Parse responses
		self.readupdates()

#	def run(self):
#		logging.debug(u'Receiver monitor starting')

#		while not exitapp[0]:
#			self.readupdates()


	def readupdates(self):
		# Need to specifically detect when a message comes in that might be confused with a
		# a command that needs to be monitored but is otherwise not interesting
		receiver_ignored_commands = [
			'P1VMD',
			'P1VMU',
			'P1SS',
			'P1MT'
		]

		instr = 'dummy'
		while not instr == '':
			instr = self.ser.readline().strip()
			if len(instr) > 0:
				print 'readupdates: received ['+instr+']'

			# Check to make sure this is not an ignored commands
			for cmd in receiver_ignored_commands:
				if cmd == instr[0:len(cmd)]:
					continue

			# Power for Zone 1 status
			if instr[0:3] == 'P1P':
				pwrstr = instr[3:]
				if pwrstr == '1':
					self.receiverdata['power'] = True
					# On power-on, query for other status variables
					self.ser.write('P1VM?\n')
					self.ser.write('P1S?\n')

					# System always starts with Mute off
					self.receiverdata['mute'] = False
				else:
					self.receiverdata['power'] = False
				print 'readupdates: updated power to ' + pwrstr
				continue

			# Volume for Zone 1 status
			if instr[0:4] == 'P1VM':
				volstr = instr[4:]
				try:
					rawvol = float(volstr)
				except ValueError:
					return

				for i in range(len(self.volarray)):
					if rawvol <= self.volarray[i]:
						self.receiverdata['volume'] = i
						break
				else:
					# volume greater than max array value
					self.receiverdata['volume'] = len(volstr)

				print 'readupdates: updated volume to ' + str(i)
				continue

			# Mute status
			if instr[0:3] == 'P1M':
				mutestr = instr[3:]
				if mutestr == '1':
					self.receiverdata['mute'] = True
				else:
					self.receiverdata['mute'] = False

				print 'readupdates: updated mute to ' + mutestr
				continue

			# Current source status
			if instr[0:3] == 'P1S':
				srcstr = instr[3:]
				try:
					self.receiverdata['source'] = self.sources[srcstr]
				except KeyError:
					self.receiverdata['source'] = 'Unknown'

				print 'readupdates: updated source to ' + srcstr


	def sendupdate(self, command, value):
		# Ignore bad commands

		print 'sendupdate: received command ['+str(command)+'] value ['+str(value)+']'

		if command.lower() not in self.allowedcommands:
			logging.debug(u'sendupdate: received bad command '+command)
			return

		if command == 'volume':

			# if value is not an int, end update
			if type(value) != type(1):
				logging.debug(u'sendupdate: volume update not an int.  Instead received '+str(type(value)))
				return

			# bounds correct value
			value = 0 if value < 0 else value
			value = len(self.volarray) if value > len(self.volarray) else value

			self.ser.write('P1VM'+str(self.volarray[value])+'\n')

		elif command == 'source':
			print 'sendupdate: command == source'
			if type(value) != type('a') and type(value) != type(u'a'):
				logging.debug(u'sendupdate: source update not a string.  Instead received '+str(type(value)))
				print 'sendupdate: source update not a string.  Instead received '+str(type(value))
				return

			for item in self.sources:
				if value == self.sources[item]:
					print 'sendupdate: sending '+'P1S'+item
					self.ser.write('P1S'+item+'\n')
					return
			else:
				logging.debug(u'sendupdate: source update with invalid source.  Received '+value)
				print u'sendupdate: source update with invalid source.  Received '+value
				return

		elif command == 'power':

			if type(value) != type(False):
				logging.debug(u'sendupdate: power update not a boolean.  Instead received '+str(type(value)))
				return

			if value:
				self.ser.write('P1P1\n')
				# If power is coming on, make sure to cause the tracked variables to report their values
				self.ser.write('P1VM?\n')
				self.ser.write('P1S?\n')
				# System always starts with Mute off
				self.receiverdata['mute'] = False

			else:
				self.ser.write('P1P0\n')

		elif command == 'mute':

			if type(value) != type(False):
				logging.debug(u'sendupdate: mute update not a boolean.  Instead received '+str(type(value)))
				return

			if value:
				self.ser.write('P1M1\n')
			else:
				self.ser.write('P1M0\n')

class receiver_serial_controller():
	# Communicates with receiver over serial interface
	# Updates receiver state variables when command received through input queue


	def __init__(self, port, baud, projectordata={}, deviceShadowHandler=''):
#		threading.Thread.__init__(self)

#		self.daemon = True
		self.deviceShadowHandler = deviceShadowHandler
		self.projectordata = projectordata

		self.ser = serial.Serial(port, baud, timeout=0.25)

		# Maps from db to 0-10 volume scale
		self.sources = {
			'30':'HDMI1',
			'A0':'HDMI2',
			'41':'VIDEO',
			'42':'S-VIDEO'
		}

		self.allowedcommands = {'source','power'}

		# Send requests for status to receiver
		self.ser.write('PWR?\n')

		# Parse responses
		self.readupdates()

#	def run(self):
#		logging.debug(u'Receiver monitor starting')

#		while not exitapp[0]:
#			self.readupdates()


	def readupdates(self):
		# Need to specifically detect when a message comes in that might be confused with a
		# a command that needs to be monitored but is otherwise not interesting

		instr = 'dummy'
		while not instr == '':
			instr = self.ser.readline().strip()
			if instr[0:1] == ':':
				instr = instr[1:]
			if len(instr) > 0:
				print 'readupdates: received ['+instr+']'

			# Power for Zone 1 status
			if instr[0:3] == 'PWR':
				pwrstr = int(instr[3:])
				if pwrstr > 0:
					self.receiverdata['power'] = True
					# On power-on, query for other status variables
					self.ser.write('P1VM?\n')
					self.ser.write('P1S?\n')

					# System always starts with Mute off
					self.receiverdata['mute'] = False
				else:
					self.receiverdata['power'] = False
				print 'readupdates: updated power to ' + pwrstr
				continue

			# Volume for Zone 1 status
			if instr[0:4] == 'P1VM':
				volstr = instr[4:]
				try:
					rawvol = float(volstr)
				except ValueError:
					return

				for i in range(len(self.volarray)):
					if rawvol <= self.volarray[i]:
						self.receiverdata['volume'] = i
						break
				else:
					# volume greater than max array value
					self.receiverdata['volume'] = len(volstr)

				print 'readupdates: updated volume to ' + str(i)
				continue

			# Mute status
			if instr[0:3] == 'P1M':
				mutestr = instr[3:]
				if mutestr == '1':
					self.receiverdata['mute'] = True
				else:
					self.receiverdata['mute'] = False

				print 'readupdates: updated mute to ' + mutestr
				continue

			# Current source status
			if instr[0:3] == 'P1S':
				srcstr = instr[3:]
				try:
					self.receiverdata['source'] = self.sources[srcstr]
				except KeyError:
					self.receiverdata['source'] = 'Unknown'

				print 'readupdates: updated source to ' + srcstr


	def sendupdate(self, command, value):
		# Ignore bad commands

		print 'sendupdate: received command ['+str(command)+'] value ['+str(value)+']'

		if command.lower() not in self.allowedcommands:
			logging.debug(u'sendupdate: received bad command '+command)
			return

		if command == 'volume':

			# if value is not an int, end update
			if type(value) != type(1):
				logging.debug(u'sendupdate: volume update not an int.  Instead received '+str(type(value)))
				return

			# bounds correct value
			value = 0 if value < 0 else value
			value = len(self.volarray) if value > len(self.volarray) else value

			self.ser.write('P1VM'+str(self.volarray[value])+'\n')

		elif command == 'source':
			print 'sendupdate: command == source'
			if type(value) != type('a') and type(value) != type(u'a'):
				logging.debug(u'sendupdate: source update not a string.  Instead received '+str(type(value)))
				print 'sendupdate: source update not a string.  Instead received '+str(type(value))
				return

			for item in self.sources:
				if value == self.sources[item]:
					print 'sendupdate: sending '+'P1S'+item
					self.ser.write('P1S'+item+'\n')
					return
			else:
				logging.debug(u'sendupdate: source update with invalid source.  Received '+value)
				print u'sendupdate: source update with invalid source.  Received '+value
				return

		elif command == 'power':

			if type(value) != type(False):
				logging.debug(u'sendupdate: power update not a boolean.  Instead received '+str(type(value)))
				return

			if value:
				self.ser.write('P1P1\n')
				# If power is coming on, make sure to cause the tracked variables to report their values
				self.ser.write('P1VM?\n')
				self.ser.write('P1S?\n')
				# System always starts with Mute off
				self.receiverdata['mute'] = False

			else:
				self.ser.write('P1P0\n')

		elif command == 'mute':

			if type(value) != type(False):
				logging.debug(u'sendupdate: mute update not a boolean.  Instead received '+str(type(value)))
				return

			if value:
				self.ser.write('P1M1\n')
			else:
				self.ser.write('P1M0\n')

# Custom Shadow callback
def customShadowCallback_Delta(payload, responseStatus, token):
	# payload is a JSON string ready to be parsed using json.loads(...)
	# in both Py2.x and Py3.x
#	print(responseStatus)
	payloadDict = json.loads(payload)

	# Get global reference to receiver serial controller, state data and ShadowHandler
	global rc
	global receiverdata
	global receiverdata_shadow
	global deviceShadowHandler

	print("++++++++DELTA++++++++++")
#    print("property: " + str(payloadDict["state"]["property"]))
#    print("version: " + str(payloadDict["version"])
	print payloadDict
	print("+++++++++++++++++++++++\n\n")

	update_needed = False
	for item in payloadDict['state']:
		print 'customShadowCallback_Delta: processing item ' + str(item)
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

#	payload_dict = {'state':{'reported':{}}}
#	payload_dict['state']['reported'] = receiverdata
#	JSONPayload = json.dumps(payload_dict)
#	deviceShadowHandler.shadowUpdate(JSONPayload, customShadowCallback_Update, 5)


def customShadowCallback_Update(payload, responseStatus, token):
	# payload is a JSON string ready to be parsed using json.loads(...)
	# in both Py2.x and Py3.x
	if responseStatus == "timeout":
		print("Update request " + token + " time out!")
	if responseStatus == "accepted":
		payloadDict = json.loads(payload)
		print("~~~~~~~~~~~~~~UPDATE~~~~~~~~~~~~~~~")
#        print("Update request with token: " + token + " accepted!")
#		print("update: " + str(payloadDict["state"]["desired"]))
		print payloadDict
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
#	rc.start()
	time.sleep(1)

	firstpass = True
	try:
		while True:
#			for item in receiverdata:
#				value = receiverdata[item]
#				print "[{0}] {1}".format(item, value)
#			print '\n\n'

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
#		exitapp[0] = True

		#rc.join()
		logging.info('Exiting...')
