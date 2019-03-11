import logging
import time
import math
from collections import OrderedDict
from multiprocessing import Process, Event
from datetime import datetime

import numpy as np

from pisces.base import PiscesBase
from pisces.utils import get_last_n_lines


def read_log(filename, n_lines=1, max_line_size=120):
    log_names = ('log_time', 'water_temp', 'air_temp', 'cooler_on')
    log_dtypes = (datetime, np.float, np.float, bool)
    time_converter = lambda t: datetime.strptime(t.decode(), "%Y-%m-%dT%H:%M:%S%z")

    log_lines = get_last_n_lines(filename, n_lines, max_line_size)
    log_data = np.genfromtxt(log_lines,
                             names=log_names,
                             dtype=log_dtypes,
                             converters={'log_time': time_converter})

    if n_lines == 1:
        # Structured 1D arrays with 1 element lose their shape,
        # preventing access to values via sa[field_name][0].
        # Need to give it its shape back to allow access in the
        # same way as multi-element structured arrays.
        log_data = log_data.reshape((1,))
    return log_data
 

class TemperatureSensors(PiscesBase):
    def __init__(self, pisces_core, **kwargs):
        super().__init__(**kwargs)
        self._core = pisces_core
        self.data_logger = logging.getLogger('pisces_data')
        self._log_interval = int(self.config['temperature_sensors']['log_interval'])
        if self._log_interval < 1:
            msg = "Temperature sensor 'log_interval' must be integer > 0."
            self.logger.critical(msg)
            raise ValueError(msg)
        self._log_file = self.config['logging']['handlers']['data']['filename']
        self._stop_event = Event()
        self._stop_event.set()
        self.logger.debug("Temperature sensors initialised.")

    def _get_temperatures(self):
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
                    self._logger.kill()

    def _log_temperatures(self):
        self.logger.info("Logging temperatures to {}".format(self._log_file))
        while not self._stop_event.is_set():
            temperatures = self._get_temperatures()
            data_string = " ".join(("{:2.3f}".format(T) for T in temperatures.values()))
            data_string = "{} {:<5}".format(data_string, str(self._core.cooler_on))
            self.data_logger.info(data_string)
            for i in range(self._log_interval):
                if self._stop_event.is_set():
                    break
                time.sleep(1)
        self.logger.info("Logging stopped.")
