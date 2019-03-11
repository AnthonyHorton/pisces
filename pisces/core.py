from multiprocessing import Process, Event
import subprocess

from pisces.base import PiscesBase
from pisces.sensors import TemperatureSensors
from pisces.control import TemperatureControl
from pisces.utils import end_process

class Pisces(PiscesBase):
    """Main class for the aquarium control system.

    Stuff.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs) # Load config and configure logging
        self.logger.info("Pisces v{}".format(self.__version__))
        if 'temperature_sensors' in self.config:
            self.temperature_sensors = TemperatureSensors()
            if 'temperature_control' in self.config:
                self.temperature_control = TemperatureControl(self.temperature_sensors)
            if 'webapp' in self.config:
                self.webapp_process = None
        self.start_all()

    def __del__(self):
        self.stop_all()

    def start_all(self):
        if 'temperature_sensors' in self.config:
            self.start_logging()
            if 'temperature_control' in self.config:
                self.start_control()
            if 'webapp' in self.config:
                self.start_webapp()

    def stop_all(self):
        if 'temperature_sensors' in self.config:
            self.temperature_sensors.stop_logging()
            if 'temperature_control' in self.config:
                self.stop_control()
            if 'webapp' in self.config:
                self.stop_webapp()
            
    def start_logging(self):
        if 'temperature_sensors' in self.config:
            self.temperature_sensors.start_logging()
        else:
            self.logger.error("No temperature sensors configured.")

    def stop_logging(self):
        if 'temperature_sensors' in self.config:
            self.temperature_sensors.stop_logging()
        else:
            self.logger.error("No temperature sensors configured.")

    def start_control(self):
        if 'temperature_control' in self.config:
            self.temperature_control.start_control()
        else:
            self.logger.error("No temperature control configured.")

    def stop_control(self):
        if 'temperature_control' in self.config:
            self.temperature_control.stop_control()
        else:
            self.logger.error("No temperature control configured.")

    def start_webapp(self):
        if 'webapp' in self.config:
            if self.webapp_process is None:
                webapp_cmds = ('python', 'pisces/webapp.py')
                self.webapp_process = subprocess.Popen(webapp_cmds)
                self.logger.info("Web app started.")
            else:
                self.logger.warning("Web app already running.")
        else:
            self.logger.error("Web app not configured.")

    def stop_webapp(self):
        if 'webapp' in self.config:
            if self.webapp_process is not None:
                exit_code = end_process(self.webapp_process)
                self.logger.info("Web app stopped ()".format(exit_code))
                self.webapp_process = None
            else:
                self.logger.warning("Web app not running.")
        else:
            self.logger.error("Web app not configured.")
