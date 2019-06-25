import math
from collections import OrderedDict

import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

from pisces.base import PiscesBase


class SensorsBase(PiscesBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class TemperatureSensors(SensorsBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger.debug("Temperature sensors initialised.")

    @property
    def temperatures(self):
        return self._get_temperatures()

    def _get_temperatures(self):
        temperatures = OrderedDict()
        for name, device in self.config['temperature_control']['temperature_sensors'].items():
            try:
                with open(device) as sensor_device:
                    raw_data = sensor_device.read()
            except OSError as err:
                msg = "Error opening '{}' sensor {}: {}".format(name, device, err)
                self.logger.error(msg)
                temperatures[name] = math.nan
            except Exception as error:
                msg = "Error reading '{}' sensor {}: {}".format(name, device, err)
                self.logger.error(msg)
                temperatures[name] = math.nan
            else:
                _, _, string_temp = raw_data.rpartition('=')
                temperatures[name] = float(string_temp) / 1000

        return temperatures


class WaterLevelSensor(SensorsBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._gain = int(self.config['water_control']['water_level_sensor']['gain'])
        
        try:
            # Create the I2C interface.
            i2c = busio.I2C(board.SCL, board.SDA)
            # Create the interface to the ADC.
            self._adc = ADS.ADS1115(i2c)
            # Create different analogue input channel.
            self._channel = AnalogIn(self._adc, ADS.P0, ADS.P1)
            # Set analogue gain
            self._adc.gain = self._gain
        except Exception as err:
            self._initialised = False
            self.logger.error("Error initialising water level sensor: {}".format(err))
        else:
            self._initialised = True
            self.logger.debug("Water level sensors initialised.")

    @property
    def value(self):
        return self._channel.value

    @property
    def voltage(self):
        return self._channel.voltage

    @property
    def water_level(self):
        # Placeholder to check stability
        discards = 10
        readings = 20
        for i in range(discards):
            _ = self.voltage
        voltage = 0
        for i in range(readings):
            voltage += self.voltage
        voltage /= readings
        return voltage * 100.0
