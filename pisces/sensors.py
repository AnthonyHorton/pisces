import math
from collections import OrderedDict

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
        for name, device in self.config['temperature_control']['devices'].items():
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
        self.logger.debug("Water level sensors initialised.")


