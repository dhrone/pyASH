from utility import get_utc_timestamp

class Interface(object):
    interface = None
    version = None
    properties = None

    def __init__(self,iot=None, uncertaintyInMilliseconds=0):
        self.uncertaintyInMilliseconds = uncertaintyInMilliseconds
        self.iot = iot

        if iot and isinstance(iot, Iot) and self.properties:
            timeStamps = iot.timeStamps
            for item in self.properties:
                self[item] = (iot[item], timeStamps[item], self.uncertaintyInMilliseconds)

    @property
    def capability(self):
        return self.jsonDiscover()

    @property
    def jsonDiscover(self):
        if self.properties:
            return { 'type':'AlexaInterface', 'interface':self.interface, 'version': self.version, 'properties': self.properties.discover() }
        return { 'type':'AlexaInterface', 'interface':self.interface, 'version': self.version  }

    @property
    def jsonResponse(self):
        return self.properties.jsonResponse(self.interface)

    def __getitem__(self, property):
        return self.properties.properties[property].value

    def __setitem__(self, property, value):
        self.properties[property] = value

    class Properties(object):
        def __init__(self, properties, proactivelyReported, retrievable):
            properties = properties if type(properties) == list else [ properties ]
            self.properties = {}
            self.proactivelyReported = proactivelyReported
            self.retrievable = retrievable
            for item in properties:
                self.properties[item.name] = item

        def __getitem__(self, property):
            return self.properties[property].value

        def __setitem__(self, property, value):
            if type(value) is tuple:
                (value, timeOfSample, uncertaintyInMilliseconds) = value
            else:
                timeOfSample = get_utc_timestamp()
                uncertaintyInMilliseconds = 0
            self.properties[property].value = value
            self.properties[property].timeOfSample = timeOfSample
            self.properties[property].uncertaintyInMilliseconds = uncertaintyInMilliseconds

        @property
        def jsonDiscover(self):
            proplist = []
            for item in self.properties:
                proplist.append({'name':item})
            return { 'supported': proplist, 'proactivelyReported':self.proactivelyReported, 'retrievable': self.retrievable }

        @property
        def jsonResponse(self, interface, timeOfSample=get_utc_timestamp(), uncertaintyInMilliseconds=0):
            proplist = []
            for item, p in self.properties.items():
                proplist.append({'namespace': interface, 'name':item, 'value': p.value, 'timeOfSample': p.timeOfSample, 'uncertaintyInMilliseconds': p.uncertaintyInMilliseconds})
            return proplist

    class Property(object):
        def __init__(self, name, value=None, timeOfSample = get_utc_timestamp(), uncertaintyInMilliseconds=0):
            self.name = name
            self.pvalue = value
            self.uncertaintyInMilliseconds = uncertaintyInMilliseconds
            self.timeOfSample = timeOfSample

        @property
        def value(self):
            try:
                return self.pvalue.json
            except:
                return self.pvalue

        @value.setter
        def value(self, value):
            self.pvalue = value

class BrightnessController(Interface):
    def __init__(self, iot=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0):
        self.interface = 'Alexa.BrightnessController'
        self.version = '3'
        self.properties = \
            Interface.Properties([ Interface.Property('brightness')], \
                proactivelyReported=proactivelyReported, retrievable=retrievable)
        super(BrightnessController, self).__init__(iot, uncertaintyInMilliseconds)

class Calendar(Interface):
    def __init__(self, proactivelyReported=False, retrievable=False):
        super(Calendar, self).__init__()
        self.interface = 'Alexa.Calendar'
        self.version = '3'

    @property
    def payload(self, organizerName, calendarEventId):
        return { 'organizerName': organizerName, 'calendarEventId':calendarEventId }

class CameraStreamController(Interface):
    def __init__(self, cameraStreams=None):
        super(CameraStreamController, self).__init__()
        self.interface = 'Alexa.CameraStreamController'
        self.version = '3'
        self.cameraStreamConfigurations_value = cameraStreams if type (cameraStreams) is list else [ cameraStreams ]

    @property
    def jsonDiscover(self):
        ret = []
        for item in self.cameraStreamConfigurations_value:
            ret.append(item.json)
        return ret

    @property
    def jsonResponse(self, cameraStreams):
        ret = []
        for item in self.cameraStreams:
            ret.append(item.json)
        return ret

class InputController(Interface):
    def __init__(self, iot=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0):
        self.interface = 'Alexa.InputController'
        self.version = '3'
        self.properties = \
            Interface.Properties([ Interface.Property('input')], \
                proactivelyReported=proactivelyReported, retrievable=retrievable)
        super(InputController, self).__init__(iot, uncertaintyInMilliseconds)

class Speaker(Interface):
    def __init__(self, iot=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0):

        self.interface = 'Alexa.InputController'
        self.version = '3'
        self.properties = \
            Interface.Properties([ Interface.Property('volume'), Interface.Property('muted') ], \
                proactivelyReported=proactivelyReported, retrievable=retrievable)
        super(Speaker, self).__init__(iot, uncertaintyInMilliseconds)
