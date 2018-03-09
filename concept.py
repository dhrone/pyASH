from iot import Iot
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
            for item in self.properties.properties:
                self[item] = (iot[item], timeStamps[item], self.uncertaintyInMilliseconds)

    @property
    def capability(self):
        return self.jsonDiscover()

    @property
    def jsonDiscover(self):
        if self.properties:
            return { 'type':'AlexaInterface', 'interface':self.interface, 'version': self.version, 'properties': self.properties.jsonDiscover }
        return { 'type':'AlexaInterface', 'interface':self.interface, 'version': self.version  }

    @property
    def jsonResponse(self):
        return self.properties.jsonResponse

    def __getitem__(self, property):
        return self.properties.properties[property].value

    def __setitem__(self, property, value):
        self.properties[property] = value

    class Properties(object):
        def __init__(self, interface, properties, proactivelyReported, retrievable):
            properties = properties if type(properties) == list else [ properties ]
            self.interface = interface
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
        def jsonResponse(self):
            proplist = []
            for item, p in self.properties.items():
                proplist.append({'namespace': self.interface, 'name':item, 'value': p.value, 'timeOfSample': p.timeOfSample, 'uncertaintyInMilliseconds': p.uncertaintyInMilliseconds})
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
            Interface.Properties(self.interface, [ Interface.Property('brightness')], \
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
        cameraStreams = []
        for item in self.cameraStreamConfigurations_value:
            cameraStreams.append(item.json)

        return { 'type': 'AlexaInterface', 'interface': self.interface, 'version': self.version, 'cameraStreamConfigurations': cameraStreams }

    #  Need to figure out how to get the selected cameraStream into this class!!
    @property
    def jsonResponse(self, cameraStreams):
        ret = []
        for item in self.cameraStreams:
            ret.append(item.json)
        return ret

class ChannelController(Interface):
    def __init__(self, iot=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0):
        self.interface = 'Alexa.ChannelController'
        self.version = '3'
        self.properties = \
            Interface.Properties(self.interface, [ Interface.Property('channel')], \
                proactivelyReported=proactivelyReported, retrievable=retrievable)
        super(ChannelController, self).__init__(iot, uncertaintyInMilliseconds)

class ColorController(Interface):
    def __init__(self, iot=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0):
        self.interface = 'Alexa.ColorController'
        self.version = '3'
        self.properties = \
            Interface.Properties(self.interface, [ Interface.Property('color')], \
                proactivelyReported=proactivelyReported, retrievable=retrievable)
        super(ColorController, self).__init__(iot, uncertaintyInMilliseconds)

class ColorTemperatureController(Interface):
    def __init__(self, iot=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0):
        self.interface = 'Alexa.EndpointHealth'
        self.version = '3'
        self.properties = \
            Interface.Properties(self.interface, [ Interface.Property('colorTemperatureInKelvin')], \
                proactivelyReported=proactivelyReported, retrievable=retrievable)
        super(ColorTemperatureController, self).__init__(iot, uncertaintyInMilliseconds)

class EndpointHealth(Interface):
    def __init__(self, iot=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0):
        self.interface = 'Alexa.ColorTemperatureController'
        self.version = '3'
        super(EndpointHealth, self).__init__(iot, uncertaintyInMilliseconds)

class InputController(Interface):
    def __init__(self, iot=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0):
        self.interface = 'Alexa.InputController'
        self.version = '3'
        self.properties = \
            Interface.Properties(self.interface, [ Interface.Property('input')], \
                proactivelyReported=proactivelyReported, retrievable=retrievable)
        super(InputController, self).__init__(iot, uncertaintyInMilliseconds)

class LockController(Interface):
    def __init__(self, iot=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0):
        self.interface = 'Alexa.LockController'
        self.version = '3'
        self.properties = \
            Interface.Properties(self.interface, [ Interface.Property('lockState')], \
                proactivelyReported=proactivelyReported, retrievable=retrievable)
        super(LockController, self).__init__(iot, uncertaintyInMilliseconds)

class MeetingClientController(Interface):
    def __init__(self, iot=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0):
        self.interface = 'Alexa.MeetingClientController'
        self.version = '3'
        super(MeetingClientController, self).__init__(iot, uncertaintyInMilliseconds)

        # Needs special discovery logic
        # Need to add another structure for meeting.  See https://developer.amazon.com/docs/device-apis/alexa-meetingclientcontroller.html#properties payload details
        # Uses generic response with no context object

class PercentageController(Interface):
    def __init__(self, iot=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0):
        self.interface = 'Alexa.PercentageController'
        self.version = '3'
        self.properties = \
            Interface.Properties(self.interface, [ Interface.Property('percentage')], \
                proactivelyReported=proactivelyReported, retrievable=retrievable)
        super(PercentageController, self).__init__(iot, uncertaintyInMilliseconds)

class PlaybackController(Interface):
    def __init__(self, iot=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0):
        self.interface = 'Alexa.PlaybackController'
        self.version = '3'
        super(PlaybackController, self).__init__(iot, uncertaintyInMilliseconds)

        # Requires special discovery logic
        # Basicallly receives player state events and needs to command that action for the device
        # Response is just a generic message.  Weirdly the example shows a context but the properties are empty.

class PowerController(Interface):
    def __init__(self, iot=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0):
        self.interface = 'Alexa.PowerController'
        self.version = '3'
        self.properties = \
            Interface.Properties(self.interface, [ Interface.Property('powerState')], \
                proactivelyReported=proactivelyReported, retrievable=retrievable)
        super(PowerController, self).__init__(iot, uncertaintyInMilliseconds)

class PowerLevelController(Interface):
    def __init__(self, iot=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0):
        self.interface = 'Alexa.PowerLevelController'
        self.version = '3'
        self.properties = \
            Interface.Properties(self.interface, [ Interface.Property('powerLevel')], \
                proactivelyReported=proactivelyReported, retrievable=retrievable)
        super(PowerLevelController, self).__init__(iot, uncertaintyInMilliseconds)

class SceneController(Interface):
    def __init__(self, iot=None, proactivelyReported=False, supportsDeactivation=False):
        self.interface = 'Alexa.SceneController'
        self.version = '3'
        self.proactivelyReported = proactivelyReported
        self.supportsDeactivation = supportsDeactivation
        super(SceneController, self).__init__(iot, uncertaintyInMilliseconds)
    @property
    def jsonDiscover(self):
        return { 'type':'AlexaInterface', 'interface':self.interface, 'version': self.version, 'supportsDeactivation': self.supportsDeactivation, 'proactivelyReported': self.proactivelyReported }

class StepSpeaker(Interface):
    def __init__(self, iot=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0):

        self.interface = 'Alexa.StepSpeaker'
        self.version = '3'
        super(StepSpeaker, self).__init__(iot, uncertaintyInMilliseconds)

class Speaker(Interface):
    def __init__(self, iot=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0):

        self.interface = 'Alexa.InputController'
        self.version = '3'
        self.properties = \
            Interface.Properties(self.interface, [ Interface.Property('volume'), Interface.Property('muted') ], \
                proactivelyReported=proactivelyReported, retrievable=retrievable)
        super(Speaker, self).__init__(iot, uncertaintyInMilliseconds)

class TemperatureSensor(Interface):
    def __init__(self, iot=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0):

        self.interface = 'Alexa.TemperatureSensor'
        self.version = '3'
        self.properties = \
            Interface.Properties(self.interface, [ Interface.Property('temperature') ], \
                proactivelyReported=proactivelyReported, retrievable=retrievable)
        super(TemperatureSensor, self).__init__(iot, uncertaintyInMilliseconds)

class ThermostatControllerSingle(Interface):
    def __init__(self, iot=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0):

        self.interface = 'Alexa.ThermostatController'
        self.version = '3'
        self.properties = \
            Interface.Properties(self.interface, [ Interface.Property('targetSetpoint'), Interface.Property('thermostatMode') ], \
                proactivelyReported=proactivelyReported, retrievable=retrievable)
        super(ThermostatControllerSingle, self).__init__(iot, uncertaintyInMilliseconds)

class ThermostatControllerDual(Interface):
    def __init__(self, iot=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0):

        self.interface = 'Alexa.ThermostatController'
        self.version = '3'
        self.properties = \
            Interface.Properties(self.interface, [ Interface.Property('lowerSetpoint'), Interface.Property('upperSetpoint'), \
            Interface.Property('thermostatMode') ], \
                proactivelyReported=proactivelyReported, retrievable=retrievable)
        super(ThermostatControllerDual, self).__init__(iot, uncertaintyInMilliseconds)

class ThermostatControllerTripleInterface):
    def __init__(self, iot=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0):

        self.interface = 'Alexa.ThermostatController'
        self.version = '3'
        self.properties = \
            Interface.Properties(self.interface, [ Interface.Property('lowerSetpoint'), Interface.Property('upperSetpoint'), \
            Interface.Property('targetSetpoint'), Interface.Property('thermostatMode') ], \
                proactivelyReported=proactivelyReported, retrievable=retrievable)
        super(ThermostatControllerTriple, self).__init__(iot, uncertaintyInMilliseconds)
