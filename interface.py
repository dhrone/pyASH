import time

from iot import Iot
from utility import get_utc_timestamp

from objects import ASHO


class Interface(object):
    interface = None
    version = None
    properties = None

    def __init__(self,iot=None, iots=None, uncertaintyInMilliseconds=0):
        if not self.interface: self.interface = 'Alexa.'+self.__class__.__name__
        self.version='3'
        self.uncertaintyInMilliseconds = uncertaintyInMilliseconds
        self.iots = iots if type(iots) is list else [iots] if iots is not None else None
        self.iot = self.iots[0] if type(self.iots) is list else iot

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
        if not self.properties: return None
        if self.iot:
            timeStamps = self.iot.timeStamps
            for item, value in self.properties.properties.items():
                uncertaintyInMilliseconds = value.uncertaintyInMilliseconds if value.uncertaintyInMilliseconds is not None else self.uncertaintyInMilliseconds
                self.properties._set( item, (self._formatForProperty(self.iot[item]), timeStamps[item], uncertaintyInMilliseconds) )
        else:
            for k, prop in self.properties.properties.items():
                prop.uncertaintyInMilliseconds = prop.uncertaintyInMilliseconds if prop.uncertaintyInMilliseconds is not None else self.uncertaintyInMilliseconds
        return self.properties.jsonResponse

    def __getitem__(self, property):
        if self.iot:
            timeStamps = self.iot.timeStamps
            for item, value in self.properties.properties.items():
                uncertaintyInMilliseconds = value.uncertaintyInMilliseconds if value.uncertaintyInMilliseconds is not None else self.uncertaintyInMilliseconds
                self.properties._set( item, (self._formatForProperty(self.iot[item]), timeStamps[item], uncertaintyInMilliseconds) )
        return self.properties[property]

    def __setitem__(self, property, value):
        if self.iot:
            if type(value) is tuple:
                value = value[0]
            if self.iot[property] != value:
                self.iot[property] = self._formatForProperty(value)
        self.properties[property] = value

    def _formatForProperty(self, value):
        return value

    class Properties(object):
        def __init__(self, interface, properties, proactivelyReported, retrievable, uncertaintyInMilliseconds = None):
            properties = properties if type(properties) == list else [ properties ]
            self.interface = interface
            self.properties = {}
            self.proactivelyReported = proactivelyReported
            self.retrievable = retrievable
            self.uncertaintyInMilliseconds = uncertaintyInMilliseconds
            for item in properties:
                if item.uncertaintyInMilliseconds is None: item.uncertaintyInMilliseconds = uncertaintyInMilliseconds
                self.properties[item.name] = item

        def __getitem__(self, property):
            return self.properties[property].value

        def __setitem__(self, property, value):
            self._set(property, value)

        def _set(self, property, value):
            if type(value) is tuple:
                (value, timeOfSample, uncertaintyInMilliseconds) = value
            else:
                timeOfSample = time.time()
                uncertaintyInMilliseconds = self.uncertaintyInMilliseconds

            # Check uncertaintyInMilliseconds if it exists and is not Null, otherwise take the value receieved
            uncertaintyInMilliseconds = self.properties[property].uncertaintyInMilliseconds if property in self.properties and self.properties[property].uncertaintyInMilliseconds is not None else uncertaintyInMilliseconds

            # If the property version and the received version are None, use the default for the Properties object
            uncertaintyInMilliseconds = uncertaintyInMilliseconds if uncertaintyInMilliseconds is not None else self.uncertaintyInMilliseconds

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
                proplist.append({'namespace': self.interface, 'name':item, 'value': p.value, 'timeOfSample': get_utc_timestamp(p.timeOfSample), 'uncertaintyInMilliseconds': p.uncertaintyInMilliseconds})
            return proplist

    class Property(object):
        def __init__(self, name, value=None, timeOfSample = time.time(), uncertaintyInMilliseconds=None):
            self.name = name
            self.pvalue = value
            self.uncertaintyInMilliseconds = uncertaintyInMilliseconds
            self.timeOfSample = timeOfSample

        @property
        def value(self):
            try:
                return self.pvalue.jsonResponse
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
    def __init__(self, iots=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0, iot=None, *args, **kwargs):
        super(BrightnessController, self).__init__(iots=iots, iot=iot, uncertaintyInMilliseconds=uncertaintyInMilliseconds)

        self.properties = \
            Interface.Properties(self.interface, [ Interface.Property('brightness')], \
                proactivelyReported=proactivelyReported, retrievable=retrievable)

    def SetBrightness(self, request):
        self._setdirective(request, 'brightness', 'brightness', range(101))

    def AdjustBrightness(self, request):
        self._adjustdirective(request, 'brightness', 'brightnessDelta', range(101))

class Calendar(Interface):
    def __init__(self, proactivelyReported=False, retrievable=False, *args, **kwargs):
        super(Calendar, self).__init__()

    def payload(self, organizerName, calendarEventId):
        return { 'organizerName': organizerName, 'calendarEventId':calendarEventId }

class CameraStreamController(Interface):
    def __init__(self, cameraStreamConfigurations=None, *args, **kwargs):
        super(CameraStreamController, self).__init__()
        print ('**********')
        print (cameraStreamConfigurations)
        print ('**********')
        self.cameraStreamConfigurations_value = cameraStreamConfigurations if type (cameraStreamConfigurations) is list else [ cameraStreamConfigurations ] if cameraStreamConfigurations is not None else None

    @property
    def jsonDiscover(self):
        cameraStreams = []
        if self.cameraStreamConfigurations_value:
            for item in self.cameraStreamConfigurations_value:
                cameraStreams.append(item)

        return { 'type': 'AlexaInterface', 'interface': self.interface, 'version': self.version, 'cameraStreamConfigurations': cameraStreams }

class ChannelController(Interface):
    def __init__(self, iots=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0, iot=None, *args, **kwargs):
        super(ChannelController, self).__init__(iots=iots, iot=iot, uncertaintyInMilliseconds=uncertaintyInMilliseconds)
        self.properties = \
            Interface.Properties(self.interface, [ Interface.Property('channel')], \
                proactivelyReported=proactivelyReported, retrievable=retrievable)

    def _formatForProperty(self, value):
        value = value.json if hasattr(value,'json') else value
        return { k:v for k, v in value.items() if k in ['number','callSign','affiliateCallSign'] }

class ColorController(Interface):
    def __init__(self, iots=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0, iot=None, *args, **kwargs):
        super(ColorController, self).__init__(iots=iots, iot=iot, uncertaintyInMilliseconds=uncertaintyInMilliseconds)
        self.properties = \
            Interface.Properties(self.interface, [ Interface.Property('color')], \
                proactivelyReported=proactivelyReported, retrievable=retrievable)

    def SetColor(self, request):
        self._setdirective(request, 'color', 'color')

class ColorTemperatureController(Interface):
    def __init__(self, iots=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0, iot=None, *args, **kwargs):
        super(ColorTemperatureController, self).__init__(iots=iots, iot=iot, uncertaintyInMilliseconds=uncertaintyInMilliseconds)
        self.properties = \
            Interface.Properties(self.interface, [ Interface.Property('colorTemperatureInKelvin')], \
                proactivelyReported=proactivelyReported, retrievable=retrievable)

    def SetColorTemperature(self, request):
        self._setdirective(request, 'colorTemperatureInKelvin', 'colorTemperatureInKelvin', range(1000,10001))

    def IncreaseColorTemperature(self, request):
        ranges_of_cool = [1000, 2200, 2700, 4000, 5500, 7000, 10000]
        v = [x for x in ranges_of_cool if x > self['colorTemperatureInKelvin']+500 ]
        v = v[0] if v else ranges_of_cool[-1]
        self['colorTemperatureInKelvin'] = (v, get_utc_timestamp(), self.uncertaintyInMilliseconds)

    def DecreaseColorTemperature(self, request):
        ranges_of_cool = [1000, 2200, 2700, 4000, 5500, 7000, 10000]
        v = [x for x in ranges_of_cool if x < self['colorTemperatureInKelvin']-500 ]
        v = v[-1] if v else ranges_of_cool[0]
        self['colorTemperatureInKelvin'] = (v, get_utc_timestamp(), self.uncertaintyInMilliseconds)

class EndpointHealth(Interface):
    def __init__(self, iots=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0, iot=None, *args, **kwargs):
        super(EndpointHealth, self).__init__(iots=iots, iot=iot, uncertaintyInMilliseconds=uncertaintyInMilliseconds)
        self.properties = \
            Interface.Properties(self.interface, [ Interface.Property('connectivity')], \
                proactivelyReported=proactivelyReported, retrievable=retrievable)

class InputController(Interface):
    def __init__(self, iots=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0, iot=None, *args, **kwargs):
        super(InputController, self).__init__(iots=iots, iot=iot, uncertaintyInMilliseconds=uncertaintyInMilliseconds)
        self.properties = \
            Interface.Properties(self.interface, [ Interface.Property('input')], \
                proactivelyReported=proactivelyReported, retrievable=retrievable)

    def SelectInput(self, request):
        self['input'] = (request.payload['input'], get_utc_timestamp(), self.uncertaintyInMilliseconds)

class LockController(Interface):
    def __init__(self, iots=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0, iot=None, *args, **kwargs):
        super(LockController, self).__init__(iots=iots, iot=iot, uncertaintyInMilliseconds=uncertaintyInMilliseconds)
        self.properties = \
            Interface.Properties(self.interface, [ Interface.Property('lockState')], \
                proactivelyReported=proactivelyReported, retrievable=retrievable)

    # If lock is slow, need to send deferred response
    # Possibility that lock will jam which should be indicated by lockState=='JAMMED'
    def Lock(self, request):
        self['lockState'] = ('LOCKED', get_utc_timestamp(), self.uncertaintyInMilliseconds)

    def Unlock(self, request):
        self['lockState'] = ('UNLOCKED', get_utc_timestamp(), self.uncertaintyInMilliseconds)

class MeetingClientController(Interface):
    def __init__(self, iots=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0, iot=None, *args, **kwargs):
        super(MeetingClientController, self).__init__(iots=iots, iot=iot, uncertaintyInMilliseconds=uncertaintyInMilliseconds)

        # Needs special discovery logic
        # Need to add another structure for meeting.  See https://developer.amazon.com/docs/device-apis/alexa-meetingclientcontroller.html#properties payload details
        # Uses generic response with no context object

class PercentageController(Interface):
    def __init__(self, iots=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0, iot=None, *args, **kwargs):
        super(PercentageController, self).__init__(iots=iots, iot=iot, uncertaintyInMilliseconds=uncertaintyInMilliseconds)
        self.properties = \
            Interface.Properties(self.interface, [ Interface.Property('percentage')], \
                proactivelyReported=proactivelyReported, retrievable=retrievable)

    def SetPercentage(self, request):
        self._setdirective(request, 'percentage', 'percentage', range(101))

    def AdjustPercentage(self, request):
        self._adjustdirective(request, 'percentage', 'percentageDelta', range(101))

class PlaybackController(Interface):
    def __init__(self, iots=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0, iot=None, *args, **kwargs):
        super(PlaybackController, self).__init__(iots=iots, iot=iot, uncertaintyInMilliseconds=uncertaintyInMilliseconds)

        # Requires special discovery logic
        # Basicallly receives player state events and needs to command that action for the device
        # Response is just a generic message.  Weirdly the example shows a context but the properties are empty.

class PowerController(Interface):
    def __init__(self, iots=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0, iot=None, *args, **kwargs):
        super(PowerController, self).__init__(iots=iots, iot=iot, uncertaintyInMilliseconds=uncertaintyInMilliseconds)
        self.properties = \
            Interface.Properties(self.interface, [ Interface.Property('powerState')], \
                proactivelyReported=proactivelyReported, retrievable=retrievable)

    def TurnOn(self, request):
        self['powerState'] = ('ON', get_utc_timestamp(), self.uncertaintyInMilliseconds)

    def TurnOff(self, request):
        self['powerState'] = ('OFF', get_utc_timestamp(), self.uncertaintyInMilliseconds)

class PowerLevelController(Interface):
    def __init__(self, iots=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0, iot=None, *args, **kwargs):
        super(PowerLevelController, self).__init__(iots=iots, iot=iot, uncertaintyInMilliseconds=uncertaintyInMilliseconds)
        self.properties = \
            Interface.Properties(self.interface, [ Interface.Property('powerLevel')], \
                proactivelyReported=proactivelyReported, retrievable=retrievable)

    def SetPowerLevel(self, request):
        self._setdirective(request, 'powerLevel', 'powerLevel', range(101))

    def AdjustPowerLevel(self, request):
        self._adjustdirective(request, 'powerLevel', 'powerLevelDelta', range(101))

class SceneController(Interface):
    def __init__(self, iots=None, proactivelyReported=False, supportsDeactivation=False, iot=None, *args, **kwargs):
        super(SceneController, self).__init__(iots=iots, iot=iot)
        self.proactivelyReported = proactivelyReported
        self.supportsDeactivation = supportsDeactivation

    @property
    def jsonDiscover(self):
        return { 'type':'AlexaInterface', 'interface':self.interface, 'version': self.version, 'supportsDeactivation': self.supportsDeactivation, 'proactivelyReported': self.proactivelyReported }

class StepSpeaker(Interface):
    def __init__(self, iots=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0, iot=None, *args, **kwargs):
        super(StepSpeaker, self).__init__(iots=iots, iot=iot, uncertaintyInMilliseconds=uncertaintyInMilliseconds)

    # Assumes that iot['volume'] is used to tell the speaker how much to increase or decrease the volume by
    def AdjustVolume(self, request):
        if self.iot:
            v = self.iot['volume']+request.payload['volumeSteps']
            validRange = range(101)
            v = v if v in validRange else validRange[0] if v < validRange[0] else validRange[-1]
            self.iot['volume'] = v

    def SetMute(self, request):
        if self.iot:
            self.iot['muted'] = request.payload['mute']

class Speaker(Interface):
    def __init__(self, iots=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0, iot=None, *args, **kwargs):
        super(Speaker, self).__init__(iots=iots, iot=iot, uncertaintyInMilliseconds=uncertaintyInMilliseconds)
        self.properties = \
            Interface.Properties(self.interface, [ Interface.Property('volume'), Interface.Property('muted') ], \
                proactivelyReported=proactivelyReported, retrievable=retrievable)

    def SetVolume(self, request):
        self._setdirective(request, 'volume', 'volume', range(101))

    def AdjustVolume(self, request):
        self._adjustdirective(request, 'volume', 'volume', range(101))

    def SetMute(self, request):
        self['muted'] = (request.payload['mute'], get_utc_timestamp(), self.uncertaintyInMilliseconds)


class TemperatureSensor(Interface):
    def __init__(self, iots=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0, iot=None, *args, **kwargs):
        super(TemperatureSensor, self).__init__(iots=iots, iot=iot, uncertaintyInMilliseconds=uncertaintyInMilliseconds)
        self.properties = \
            Interface.Properties(self.interface, [ Interface.Property('temperature') ], \
                proactivelyReported=proactivelyReported, retrievable=retrievable)

class ThermostatController(Interface):
    def __init__(self, iots=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0, iot=None, thermostatType='single', *args, **kwargs):
        super(ThermostatController, self).__init__(iots=iots, iot=iot, uncertaintyInMilliseconds=uncertaintyInMilliseconds)
        prop_list = [ Interface.Property('thermostatMode') ]
        if thermostatType.lower() == 'single':
            prop_list.append( Interface.Property('targetSetpoint'))
        elif thermostatType.lower() == 'dual':
            prop_list.append( Interface.Property('lowerSetpoint'))
            prop_list.append( Interface.Property('upperSetpoint'))
        else:
            prop_list.append( Interface.Property('targetSetpoint'))
            prop_list.append( Interface.Property('lowerSetpoint'))
            prop_list.append( Interface.Property('upperSetpoint'))

        self.properties = \
            Interface.Properties(self.interface, prop_list, \
                proactivelyReported=proactivelyReported, retrievable=retrievable)

    def SetTargetTemperature(self, request):
        if 'targetSetpoint' in request.payload:
            self['targetSetpoint'] = (request.payload['targetSetpoint'], get_utc_timestamp(), self.uncertaintyInMilliseconds)
        if 'lowerSetpoint' in request.payload:
            self['lowerSetpoint'] = (request.payload['lowerSetpoint'], get_utc_timestamp(), self.uncertaintyInMilliseconds)
        if 'upperSetpoint' in request.payload:
            self['upperSetpoint'] = (request.payload['upperSetpoint'], get_utc_timestamp(), self.uncertaintyInMilliseconds)

    # Documentation only shows targetSetpoint being adjust.  Not 100% sure what to do with dual mode thermostats
    # Also not sure what range to enforce
    def AdjustTargetTemperature(self, request):
        tsp = Temperature(request.payload['targetSetpointDelta'])
        tsp.value = self['targetSetpoint'].value + tsp.value
        self['targetSetpoint'] = (tsp, get_utc_timestamp(), self.uncertaintyInMilliseconds)

    def SetThermostatMode(self, request):
        tm = ThermostatMode(request.payload['thermostatMode'])
        self['thermostatMode'] = (tm, get_utc_timestamp(), self.uncertaintyInMilliseconds)

class ThermostatControllerSingle(ThermostatController):
    def __init__(self, iots=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0, iot=None, *args, **kwargs):
        self.interface = 'Alexa.'+'ThermostatController'
        super(ThermostatControllerSingle, self).__init__(iots=iots, iot=iot, proactivelyReported=proactivelyReported, retrievable=retrievable, uncertaintyInMilliseconds=uncertaintyInMilliseconds, thermostatType='single')


class ThermostatControllerDual(ThermostatController):
    def __init__(self, iots=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0, iot=None, *args, **kwargs):
        self.interface = 'Alexa.'+'ThermostatController'
        super(ThermostatControllerDual, self).__init__(iots=iots, iot=iot, proactivelyReported=proactivelyReported, retrievable=retrievable, uncertaintyInMilliseconds=uncertaintyInMilliseconds, thermostatType='dual')

class ThermostatControllerTriple(ThermostatController):
    def __init__(self, iots=None, proactivelyReported=False, retrievable=False, uncertaintyInMilliseconds=0, iot=None, *args, **kwargs):
        self.interface = 'Alexa.'+'ThermostatController'
        super(ThermostatControllerTriple, self).__init__(iots=iots, iot=iot, proactivelyReported=proactivelyReported, retrievable=retrievable, uncertaintyInMilliseconds=uncertaintyInMilliseconds, thermostatType='triple')



def getInterfaceClass(interface):
    if interface[0:6] == 'Alexa.':
        interface = interface[6:]
    ret = {
        'BrightnessController': BrightnessController,
        'Calendar': Calendar,
        'CameraStreamController': CameraStreamController,
        'ChannelController': ChannelController,
        'ColorController': ColorController,
        'ColorTemperatureController': ColorTemperatureController,
        'EndpointHealth': EndpointHealth,
        'InputController': InputController,
        'LockController': LockController,
        'MeetingClientController': MeetingClientController,
        'PercentageController': PercentageController,
        'PlaybackController': PlaybackController,
        'PowerController': PowerController,
        'PowerLevelController': PowerLevelController,
        'SceneController': SceneController,
        'StepSpeaker': StepSpeaker,
        'Speaker': Speaker,
        'TemperatureSensor': TemperatureSensor,
        'ThermostatController': ThermostatController
    }.get(interface, None)
    if ret:
        return ret
    raise INVALID_DIRECTIVE('{0} is not a valid interface'.format(interface))
