from multiprocessing import Process, Event

from pisces import __version__
from pisces.base import PiscesBase
from pisces.sensors import TemperatureSensors
from pisces.app import WebApp

class Pisces(PiscesBase):
    """Main class for the aquarium control system.

    Stuff.
    """
    def __init__(self, *kwargs):
        super().__init__(*kwargs) # Load config and configure logging
        self.logger.info("Pisces v{}".format(__version__))
        if 'temperature_sensors' in self.config:
            self.temperature_sensors = TemperatureSensors()
            if 'webapp' in self.config:
                self.webapp = WebApp(self.temperature_sensors)

    def __del__(self):
        self.stop_all()

    def start_all(self):
        if 'temperature_sensors' in self.config:
            self.temperature_sensors.start_logging()
            if 'webapp' in self.config:            
                self.webapp.start()

    def stop_all(self):
        if 'temperature_sensors' in self.config:
            self.temperature_sensors.stop_logging()
            if 'webapp' in self.config:  
                self.webapp.stop()
