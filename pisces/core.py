from multiprocessing import Process, Event
import subprocess

from pisces.base import PiscesBase
from pisces.sensors import TemperatureSensors
from pisces.control import TemperatureControl
from pisces.lights import LightsControl
from pisces.utils import end_process

class Pisces(PiscesBase):
    """Main class for the aquarium control system.

    Stuff.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs) # Load config and configure logging
        self.logger.info("Pisces v{}".format(self.__version__))
        self._temperature_sensors = TemperatureSensors(self)
        self._temperature_control = TemperatureControl(self)
        self._lights_control = LightsControl()
        self._webapp_process = None
        self.start_all()

    def __del__(self):
        self.stop_all()

    @property
    def current_temperatures(self):
        return self._temperature_sensors._get_temperatures()

    @property
    def cooler_on(self):
        return self._temperature_control.cooler_on

    @property
    def lights_on(self):
        return self._lights_control.is_on

    def start_all(self):
        self.start_logging()
        self.start_control()
        self.start_timer()
        self.start_webapp()

    def stop_all(self):
        self.stop_logging()
        self.stop_control()
        self.stop_timer()
        self.stop_webapp()

    def start_logging(self):
        self._temperature_sensors.start_logging()

    def stop_logging(self):
        self._temperature_sensors.stop_logging()

    def start_control(self):
        self._temperature_control.start_control()

    def stop_control(self):
        self._temperature_control.stop_control()

    def start_timer(self):
        self._lights_control.start_timer()

    def stop_timer(self):
        self._lights_control.stop_timer()

    def start_webapp(self):
        if self._webapp_process is None:
            webapp_cmds = ('python', 'pisces/webapp.py')
            self._webapp_process = subprocess.Popen(webapp_cmds)
            self.logger.info("Web app started.")
        else:
            self.logger.warning("Web app already running.")

    def stop_webapp(self):
        if self._webapp_process is not None:
            exit_code = end_process(self._webapp_process)
            self.logger.info("Web app stopped ()".format(exit_code))
            self._webapp_process = None
        else:
            self.logger.warning("Web app not running.")
