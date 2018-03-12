from iot import Iot
from objects import *
from utility import get_utc_timestamp


class Interface(object):
    interface = None
    version = None
    properties = None

    def __init__(self,iot=None, uncertaintyInMilliseconds=0):
        self.uncertaintyInMilliseconds = uncertaintyInMilliseconds
        self.iot = iot

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
        if self.iot:
            timeStamps = self.iot.timeStamps
            for item in self.properties.properties:
                self.properties._set( item, (self.iot[item], timeStamps[item], self.uncertaintyInMilliseconds) )
        return self.properties[property]

    def __setitem__(self, property, value):
        if self.iot:
            if type(value) is tuple:
                value = value[0]
            if self.iot[property] != value:
                self.iot[property] = value
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
            self._set(property, value)

        def _set(self, property, value):
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

    def _setdirective(self, request, propertyName, payloadName, validRange=None):
        # Should really send an error if out of range
        v = request.payload[payloadName]
        if validRange:
            v = v if v in validRange else validRange[0] if v < validRange[0] else validRange[-1]
        self[propertyName] = (v, get_utc_timestamp(), self.uncertaintyInMilliseconds)

    def _adjustdirective(self, request, propertyName, payloadName, validRange=None):
        v = self[propertyName]+request.payload[payloadName]
        if validRange:
            v = v if v in validRange else validRange[0] if v < validRange[0] else validRange[-1]
        self[propertyName] = (v, get_utc_timestamp(), self.uncertaintyInMilliseconds)

class BrightnessController(Interface):
    def __init__(self, iot=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0):
        self.interface = 'Alexa.BrightnessController'
        self.version = '3'
        self.properties = \
            Interface.Properties(self.interface, [ Interface.Property('brightness')], \
                proactivelyReported=proactivelyReported, retrievable=retrievable)
        super(BrightnessController, self).__init__(iot, uncertaintyInMilliseconds)

    def SetBrightness(self, request):
        self._setdirective(request, 'brightness', 'brightness', range(101))

    def AdjustBrightness(self, request):
        self._adjustdirective(request, 'brightness', 'brightnessDelta', range(101))

class Calendar(Interface):
    def __init__(self, proactivelyReported=False, retrievable=False):
        super(Calendar, self).__init__()
        self.interface = 'Alexa.Calendar'
        self.version = '3'

    @property
    def payload(self, organizerName, calendarEventId):
        return { 'organizerName': organizerName, 'calendarEventId':calendarEventId }

    def GetCurrentMeeting(self, request):
        raise NotImplementedError('No default directive for {0}'.format(self.__class__.__name__))

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

    def InitializeCameraStreams(self, request):
        raise NotImplementedError('No default directive for {0}'.format(self.__class__.__name__))

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

    def SelectInput(self, request):
        self['input'] = (request.payload['input'], get_utc_timestamp(), self.uncertaintyInMilliseconds)

class LockController(Interface):
    def __init__(self, iot=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0):
        self.interface = 'Alexa.LockController'
        self.version = '3'
        self.properties = \
            Interface.Properties(self.interface, [ Interface.Property('lockState')], \
                proactivelyReported=proactivelyReported, retrievable=retrievable)
        super(LockController, self).__init__(iot, uncertaintyInMilliseconds)

    # If lock is slow, need to send deferred response
    # Possibility that lock will jam which should be indicated by lockState=='JAMMED'
    def Lock(self, request):
        self['lockState'] = ('LOCKED', get_utc_timestamp(), self.uncertaintyInMilliseconds)

    def Unlock(self, request):
        self['lockState'] = ('UNLOCKED', get_utc_timestamp(), self.uncertaintyInMilliseconds)

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

    def SetPercentage(self, request):
        self._setdirective(request, 'percentage', 'percentage', range(101))

    def AdjustPercentage(self, request):
        self._adjustdirective(request, 'percentage', 'percentageDelta', range(101))

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

    def TurnOn(self, request):
        self['powerState'] = ('ON', get_utc_timestamp(), self.uncertaintyInMilliseconds)

    def TurnOff(self, request):
        self['powerState'] = ('OFF', get_utc_timestamp(), self.uncertaintyInMilliseconds)

class PowerLevelController(Interface):
    def __init__(self, iot=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0):
        self.interface = 'Alexa.PowerLevelController'
        self.version = '3'
        self.properties = \
            Interface.Properties(self.interface, [ Interface.Property('powerLevel')], \
                proactivelyReported=proactivelyReported, retrievable=retrievable)
        super(PowerLevelController, self).__init__(iot, uncertaintyInMilliseconds)

    def SetPowerLevel(self, request):
        self._setdirective(request, 'powerLevel', 'powerLevel', range(101))

    def AdjustPowerLevel(self, request):
        self._adjustdirective(request, 'powerLevel', 'powerLevelDelta', range(101))

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

    # Assumes that iot['volume'] is used to tell the speaker how much to increase or decrease the volume by
    def SetVolume(self, request):
        self._setdirective(request, 'volume', 'volumeSteps', range(101))

    def SetMute(self, request):
        self['muted'] = (request.payload['mute'], get_utc_timestamp(), self.uncertaintyInMilliseconds)

class Speaker(Interface):
    def __init__(self, iot=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0):
        self.interface = 'Alexa.InputController'
        self.version = '3'
        self.properties = \
            Interface.Properties(self.interface, [ Interface.Property('volume'), Interface.Property('muted') ], \
                proactivelyReported=proactivelyReported, retrievable=retrievable)
        super(Speaker, self).__init__(iot, uncertaintyInMilliseconds)

    def SetVolume(self, request):
        self._setdirective(request, 'volume', 'volume', range(101))

    def AdjustVolume(self, request):
        self._adjustdirective(request, 'volume', 'volume', range(101))

    def SetMute(self, request):
        self['muted'] = (request.payload['mute'], get_utc_timestamp(), self.uncertaintyInMilliseconds)


class TemperatureSensor(Interface):
    def __init__(self, iot=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0):
        self.interface = 'Alexa.TemperatureSensor'
        self.version = '3'
        self.properties = \
            Interface.Properties(self.interface, [ Interface.Property('temperature') ], \
                proactivelyReported=proactivelyReported, retrievable=retrievable)
        super(TemperatureSensor, self).__init__(iot, uncertaintyInMilliseconds)

class ThermostatController(Interface):
    def __init__(self, iot=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0, thermostatType='single'):
        self.interface = 'Alexa.ThermostatController'
        self.version = '3'
        prop_list = [ Interface.Property('thermostatMode') ]
        if thermostatType.lower() == 'single':
            prop_list.append( Interface.Property('TargetSetpoint'))
        elif thermostatType.lower() == 'dual':
            prop_list.append( Interface.Property('lowerSetpoint'))
            prop_list.append( Interface.Property('upperSetpoint'))
        else:
            prop_list.append( Interface.Property('TargetSetpoint'))
            prop_list.append( Interface.Property('lowerSetpoint'))
            prop_list.append( Interface.Property('upperSetpoint'))

        self.properties = \
            Interface.Properties(self.interface, prop_list, \
                proactivelyReported=proactivelyReported, retrievable=retrievable)
        super(ThermostatControllerSingle, self).__init__(iot, uncertaintyInMilliseconds)

    def SetTargetTemperature(self, request):
        if 'targetSetpoint' in request.payload:
            self['targetSetpoint'] = (Temperature(request.payload['targetSetpoint']), get_utc_timestamp(), self.uncertaintyInMilliseconds)
        if 'lowerSetpoint' in request.payload:
            self['lowerSetpoint'] = (Temperature(request.payload['lowerSetpoint']), get_utc_timestamp(), self.uncertaintyInMilliseconds)
        if 'upperSetpoint' in request.payload:
            self['upperSetpoint'] = (Temperature(request.payload['upperSetpoint']), get_utc_timestamp(), self.uncertaintyInMilliseconds)

    # Documentation only shows targetSetpoint being adjust.  Not 100% sure what to do with dual mode thermostats
    # Also not sure what range to enforce
    def AdjustTargetTemperature(self, request):
        tsp = Temperature(request.payload['targetSetpointDelta'])
        tsp.value = self['targetSetpoint'].value + tsp.value
        self['targetSetpoint'] = (tsp, get_utc_timestamp(), self.uncertaintyInMilliseconds)

    def SetThermostatMode(self, request):
        tm = ThermostatMode(request.payload['thermostatMode'])
        self['thermostatMode'] = (tm, get_utc_timestamp(), self.uncertaintyInMilliseconds)
