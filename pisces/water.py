from gpiozero import DigitalInputDevice

from pisces.control import ClosedLoopBase
from pisces.sensors import WaterLevelSensor

class WaterControl(ClosedLoopBase):
    def __init__(self, pisces_core, **kwargs):
        kwargs.update({'name': 'water_control',
                       'output_name': 'pump'})
        super().__init__(pisces_core, **kwargs)
        self._sensors = WaterLevelSensor(**kwargs)

        overflow_pin = self.config[self._name]['overflow']
        self._overflow = DigitalInputDevice(int(overflow_pin), bounce_time=1)
        self._overflow.when_deactivated = self._overflow_detected  # Overflow sensor goes low when overflow detected.
        self._overflow.when_activated = self._overflow_ended  # Overflow sensor goes high when there's no overflow.
        self._status['overflow'] = self._overflow.is_active

        self.logger.debug("Water control initialised.")
        self.start_monitoring()

    def __del__(self):
        self.stop_monitoring()

    def _update(self):
        self._status['water_level'] = self._sensors.water_level
        if self._status['water_level'] > self._target_max:
            self._status['water_level_status'] = 'HIGH'
        elif self._status['water_level'] < self._target_min:
            self._status['water_level_status'] = 'LOW'
        else:
            self._status['water_level_status'] = 'OK'

        if self.is_auto:
            if self.is_on and self._status['water_level'] > (self._target_min + self._hysteresis):
                self.off()
            elif not self.is_on and self._status['water_level'] < self._target_min:
                self.on()
            else:
                self._update_status()
        else:
            self._update_status()

    def _overflow_detected(self):
        self.logger.warning("Overflow detected! Water pump inhibited.")
        self._status['overflow'] = True
        self._update_status()

    def _overflow_ended(self):
        self.logger.info("Overflow ended.")
        self._status['overflow'] = False
        self._update_status()
