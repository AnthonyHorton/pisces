import time
from subprocess import Process, Event

from gpiozero import DigitalOutputDevice, LED

from pisces.base import PiscesBase


class TemperatureControl(PiscesBase):
    def __init__(self, temperature_sensors, **kwargs):
        super().__init__(**kwargs)
        self._temperature_sensors = temperature_sensors
        self._loop_interval = int(self.config['temperature_control']['loop_interval'])
        if self._loop_inteval < 1:
            msg = "Temperature control 'loop_interval' must be integer > 0."
            self.logger.error(msg)
            raise ValueError(msg)
        self._stop_event = Event()
        self._stop_event.set()
        self.logger.debug("Temperature control initialised.")

    def start_control(self):
        if not self._stop_event.is_set():
            self.logger.warning("Temperature control already running.")
        else:
            self._stop_event.clear()
            self._controller = Process(target=self._control_temperature, daemon=True)
            self._controller.start()

    def stop_control(self):
        if self._stop_event.is_set():
            self.logger.warning("Temperature control not running.")
        else:
            self._stop_event.set()
            self._controller.join(timeout=5)
            if self._controller.exitcode is None:
                self._controller.terminate()
                if self._controller.exitcode is None:
                    self._controller.kill()

    def _control_temperature(self):
        self.logger.info("Temperature control starting.")
        while not self._stop_event.is_set():
            self._update()
            for i in range(self._loop_interval):
                if self._stop_event.is_set():
                    break
                time.sleep(1)
        self.logger.info("Temperature control stopped.")
        
    def _update(self):
        temperatures = self.temperature_sensors.get_temperatures()
        if temperatures['water_temp'] > self.config['temperature_control']['target_max']:
            self._set_leds({'cold_led': False,
                            'good_led': False,
                            'hot_led': True})
        elif temperatures['water_temp'] < self.config['temperature_control']['target_min']:
            self._set_leds({'cold_led': True,
                            'good_led': False,
                            'hot_led': False})
        else:
            self._set_leds({'cold_led': False,
                            'good_led': True,
                            'hot_led': False})

        cooling_ouput = self.config['temperature_control'].get('cooling')
        if cooling_output:
            with DigitalOutputDevice(cooling_output, initial_value=None) as cooling_device:
                if cooling_device.value:
                    if temperatures['water_temp'] < (self.config['temperature_control']['target_max'] - /
                        self.config['temperature_control']['hysteresis']):
                        cooling_device.off()
                else:
                    if temperatures['water_temp'] > self.config['temperature_control']['target_max']:
                        cooling_device.on()

    def _set_leds(self, settings):
        for led_name, led_setting in settings.items():
            with LED(self.config['temperature_control'].get(led_name), initial_value=None) as led_device:
                if led_setting:
                     led_device.on()
                else:
                     led_device.off()
