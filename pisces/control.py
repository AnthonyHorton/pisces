import time
from multiprocessing import Process, Event

from gpiozero import DigitalOutputDevice, LED

from pisces.base import PiscesBase


class TemperatureControl(PiscesBase):
    def __init__(self, pisces_core, **kwargs):
        super().__init__(**kwargs)
        self._core = pisces_core

        self._loop_interval = int(self.config['temperature_control']['loop_interval'])
        if self._loop_interval < 1:
            msg = "Temperature control 'loop_interval' must be integer > 0."
            self.logger.critical(msg)
            raise ValueError(msg)

        self._target_max = float(self.config['temperature_control']['target_max'])
        self._target_min = float(self.config['temperature_control']['target_min'])
        if self._target_max <= self._target_min:
            msg = "Temperature control 'target_min' must be <= 'target_max'."
            self.logger.critical(msg)
            raise ValueError(msg)

        self._hysteresis = float(self.config['temperature_control']['hysteresis'])
        if self._hysteresis < 0:
            msg = "Temperature control 'hysteresis' must be > 0."
            self.logger.critical(msg)
            raise ValueError(msg)
        elif self._hysteresis > (self._target_max - self._target_min):
            msg = "Temperature control 'hysteresis' must be < ('target_max' - 'target_min')."
            self.logger.critical(msg)
            raise ValueError(msg)

        self._leds = {}
        for key, value in self.config['temperature_control'].items():
            if key.endswith('_led'):
                self._leds[key] = LED(int(value), initial_value=None)

        cooling_output = self.config['temperature_control'].get('cooling')
        if cooling_output:
            self._cooler = DigitalOutputDevice(int(cooling_output), initial_value=None)
        else:
            self._cooler = None

        self._stop_event = Event()
        self._stop_event.set()

        self.logger.debug("Temperature control initialised.")

    @property
    def cooler_on(self):
        if not self._cooler or not self._cooler.value:
            return False
        else:
            return True

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
        temperatures = self._core.current_temperatures
        if temperatures['water_temp'] > self._target_max:
            self._set_leds({'cold_led': False,
                            'good_led': False,
                            'hot_led': True})
        elif temperatures['water_temp'] < self._target_min:
            self._set_leds({'cold_led': True,
                            'good_led': False,
                            'hot_led': False})
        else:
            self._set_leds({'cold_led': False,
                            'good_led': True,
                            'hot_led': False})

        if self._cooler:
            if self._cooler.value:
                if temperatures['water_temp'] < (self._target_max - self._hysteresis):
                    self._cooler.off()
                    self.logger.info("Cooling turned off.")
            else:
                if temperatures['water_temp'] > self._target_max:
                    self._cooler.on()
                    self.logger.info("Cooling turned on.")

    def _set_leds(self, settings):
        for led_name, led_setting in settings.items():
            if led_setting:
                self._leds[led_name].on()
            else:
                self._leds[led_name].off()
