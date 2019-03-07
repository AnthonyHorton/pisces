import logging
import time
import math
from collections import OrderedDict
from multiprocessing import Process, Event


from pisces.base import PiscesBase


class TemperatureSensors(PiscesBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data_logger = logging.getLogger('data')
        self._log_interval = int(self.config['temperature_sensors']['log_interval'])
        if self._log_interval < 1:
            msg = "Temperature sensor 'log_interval' must be integer > 0."
            self.logger.error(msg)
            raise ValueError(msg)
        self._log_file = self.config['logging']['handlers']['data']['filename']
        self._stop_event = Event()
        self._stop_event.set()
        self.logger.debug("Temperature sensors initialised.")

    def get_temperatures(self):
        temperatures = OrderedDict()
        for name, device in self.config['temperature_sensors']['devices'].items():
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

    def start_logging(self):
        if not self._stop_event.is_set():
            self.logger.warning("Temperature logging already running.")
        else:
            self._stop_event.clear()
            self._logger = Process(target=self._log_temperatures, daemon=True)
            self._logger.start()

    def stop_logging(self):
        if self._stop_event.is_set():
            self.logger.warning("Temperature logging not running.")
        else:
            self._stop_event.set()
            self._logger.join(timeout=5)
            if self._logger.exitcode is None:
                self._logger.terminate()
                if self._logger.exitcode is None:
                    self.temperature_logger.kill()

    def _log_temperatures(self):
        self.logger.info("Logging temperatures to {}".format(self._log_file))
        while not self._stop_event.is_set():
            temperatures = self.get_temperatures()
            data_string = " ".join(("{:2.3f}".format(T) for T in temperatures.values()))
            self.data_logger.info(data_string)
            for i in range(self._log_interval):
                if self._stop_event.is_set():
                    break
                time.sleep(1)
        self.logger.info("Logging stopped.")
