from pisces.control import ClosedLoopBase
from pisces.sensors import TemperatureSensors

class TemperatureControl(ClosedLoopBase):
    def __init__(self, pisces_core, **kwargs):
        kwargs.update({'name': 'temperature_control',
                       'output_name': 'fan'})
        super().__init__(pisces_core, **kwargs)
        self._sensors = TemperatureSensors(**kwargs)

        self.logger.info("Temperature control initialised.")
        self.start_monitoring()

    def __del__(self):
        self.stop_monitoring()

    def _update(self):
        self._status.update(self._sensors.temperatures)
        if self._status['water_temp'] > self._target_max:
            self._status['water_temp_status'] = 'HIGH'
        elif self._status['water_temp'] < self._target_min:
            self._status['water_temp_status'] = 'LOW'
        else:
            self._status['water_temp_status'] = 'OK'

        if self.is_auto:
            if self.is_on and self._status['water_temp'] < (self._target_max - self._hysteresis):
                self.off()
            elif not self.is_on and self._status['water_temp'] > self._target_max:
                self.on()
            else:
                self._update_status()
        else:
            self._update_status()
