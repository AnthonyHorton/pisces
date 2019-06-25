import subprocess
import time

from pisces.base import PiscesBase
from pisces.display import Display
from pisces.lights import LightsControl
from pisces.temperature import TemperatureControl
#from pisces.water import WaterControl
from pisces.datalogger import DataLogger
from pisces.utils import end_process

class Pisces(PiscesBase):
    """Main class for the aquarium control system.

    Stuff.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs) # Load config and configure logging
        self.logger.info("Pisces v{}".format(self.__version__))

        self._status = {'water_temp': 99.9,
                        'water_temp_status': 'OK',
                        'air_temp': 99.9,
                        'water_level': 99.9,
                        'water_level_status': 'OK',
                        'overflow': False,
                        'lights_auto': True,
                        'lights_enabled': False,
                        'fan_auto': True,
                        'fan_enabled': False,
                        'pump_auto': True,
                        'pump_enabled': False}

        self._display = Display(self, **kwargs)
        self._lights_control = LightsControl(self, **kwargs)        
        self._temperature_control = TemperatureControl(self, **kwargs)
#        self._water_control = WaterControl(self, **kwargs)
        self._datalogger = DataLogger(self, **kwargs)
        self._webapp_process = None

        self.start_all()

    def __del__(self):
        self.stop_all()

    @property
    def status(self):
        return self._status

    def update_status(self, update):
        self._status.update(update)
        self._display.update()

    def start_all(self):
        self.lights_auto()
        self.fan_auto()
#        self.pump_auto()
        time.sleep(5)  # Give sensors time to get valid readings before logging.
        self.start_logging()
#        self.start_webapp()

    def stop_all(self):
#        self.stop_webapp()
        self.stop_logging()
#        self.pump_manual()
        self.fan_manual()
        self.lights_manual()
        self._display.clear()

    def lights_auto(self):
        self._lights_control.auto_on()

    def lights_manual(self):
        self._lights_control.auto_off()

    def fan_auto(self):
        self._temperature_control.auto_on()

    def fan_manual(self):
        self._temperature_control.auto_off()

    def pump_auto(self):
        self._water_control.auto_on()

    def pump_manual(self):
        self._water_control.auto_off()

    def start_logging(self):
        self._datalogger.start_monitoring()

    def stop_logging(self):
        self._datalogger.stop_monitoring()

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
