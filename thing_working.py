Callbacks.  Functions to interfact with IOT shadow
	In their own threads (implemented by AWS MQTT library)
	Leverage queue to report actions.

	Delta
	Update
	Delete

Devices.
	Set of the devices that make up the thing.
		Normally single item

	Each device uses a dedicated queue to receive command from thing
	Each device contains a dictionary of the properties that it implements
		No two devices can support the same property

Input
	iot service endpoint
	thingName
	rootCA
	certificate
	privateKey
	region

Classes
	Thing.  Main class
	Device.  A physical device that is part of the thing


class Thing(object):
	_logger = logging.getLogger(__name__)

	def __init__(self, ep=None, thingName=None, rootCAPath=None, certificatePath=None, privateKeyPath=None, region=None, device=None, devices=None):
		''' Initialize connection to AWS IOT shadow service '''

		self._eventQueue = queue.Queue()
		self._localShadow = dict() ''' dictionary of local property values '''
		self._propertyHandlers = dict() ''' dictionary to set which device handles which property values '''
		self._shadowHandler = self._iotConnect(ep, thingName, rootCA, cert, pk, region)

		if device is not None and devices is not None:
			_logger.debug('Arguments for both device and devices have been provided.  Normal usage is one or the other')

		if device is not None:
			self.registerDevice(device)

		if devices is not None:
			for d in devices:
				self.registerDevice(d)

		self._main()

	def _iotConnect(self, ep, thingName, rootCAPath, certificatePath, privateKeyPath, region):
		''' Establish connection to the AWS IOT service '''
	    # Init AWSIoTMQTTShadowClient
	    myAWSIoTMQTTShadowClient = None
	    myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient('pyASH')
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
	    deviceShadowHandler.shadowDelete(self._deleteCallback, 5)

	    # Listen on deltas
	    deviceShadowHandler.shadowRegisterDeltaCallback(self._deltaCallback)

		return deviceShadowHandler

	def registerDevice(self, device):
		''' Register a device as the handler for the set of properties that the device implements '''

		for property in device.properties:
			if property in self._localShadow:
				_logger.warn('{0} is trying to register {1} which is a property that is already in use.'.format(device.__name__, property))
			self._localShadow[property] = device.properties[property]
			self._propertyHandlers[property] = device

	def _deleteCallback(self, payload, responseStatus, token):
		''' Log result when a request to delete the IOT shadow has been made '''
		if responseStatus == 'accepted':
			_logger.info("Delete request " + token + " accepted!")
			return

		_logger.warn({
			'timeout': "Delete request " + token + " time out!",
			'rejected': "Delete request " + token + " rejected!"
		}.get(reponseStatus, "Delete request with token " + token + "contained unexpected response status " + responseStatus))

	def _updateCallback(self, payload, responseStatus, token):
		''' Log result when a request has been made to update the IOT shadow '''
		if responseStatus == 'accepted':
			payloadDict = json.loads(payload)
			_logger.info("Received delta request: " + json.dumps(payloadDict))
			for property in payloadDict:
				self._eventQueue.put({'source': '__thing__', 'action': 'UPDATE', 'property': property, 'value': payloadDict[property] })
			return

		_logger.warn({
			'timeout': "Update request " + token + " timed out!",
			'rejected': "Update request " + token + " was rejected!"
		}.get(reponseStatus, "Update request " + token + " contained unexpected response status " + responseStatus))

	def _deltaCallback(self, payload, responseStatus, token):
		''' Receive an delta message from IOT service and forward update requests for every included property to the event queue '''
	    payloadDict = json.loads(payload)

	    for property in payloadDict['state']:
	        logger.info('Delta Message: processing item [{0}][{1}]'.format(property, payloadDict['state'][property]))
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

class device(object):
	''' Device that makes up part of an IOT thing '''

	def __init__(self, eventQueue = None, name = None, deviceState = None):
		''' Initialize device driver and set it to receive updates from the eventQueue '''
		self._eventQueue = eventQueue
		self.__name__ = name if name is not None else self.__class__.__name__
		self._deviceQueue = queue.Queue()
		self._deviceState = deviceState ''' dictionary of the properties and starting values for device '''

		# Need to create a thread for the devices event loop

	def update(self, property, value):
		''' Change the physical state of the device by updating property to value '''
		self._deviceQueue.put({'action': 'UPDATE', 'property': property, 'value': value })

    @classmethod
    def transfromProperty(cls, destination, property):

        def decorateinterface(func):
			direction = { 'DEVICE': '_transformToDevice', 'PROPERTY': '_transformToProperty' }.get(destination.upper())
			if not direction raise ValueError('{0} is not a valid direction.  Acceptable values are DEVICE or PROPERTY'.format(destination))
            transform = getattr(func, '_transformToDevice', {})
            transform[property] = variable
            func._transformToList = transformToList
            return func

        return decorateinterface

    @classmethod
    def transformPropertyfromDevice(cls, property, variable=None):
        variable = variable if variable else property

        def decorateinterface(func):
            transformToList = getattr(func, '_transformToList', {})
            transformToList[Iot.validateProperty(property)] = variable
            func._transformToList = transformToList
            return func

        return decorateinterface

	def _main(self):
		''' Handle interactions between device and thing '''
		while True:
			pass
