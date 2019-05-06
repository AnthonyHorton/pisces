from datetime import datetime, time

from gpiozero import DigitalOutputDevice, TimeOfDay, Button

from pisces.base import PiscesBase


class LightsControl(PiscesBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._output = DigitalOutputDevice(int(self.config['lights']['output']), initial_value=None)
        self._time_on = datetime.strptime(self.config['lights']['time_on'],
                                          "%H:%M").time()
        self._time_off = datetime.strptime(self.config['lights']['time_off'],
                                           "%H:%M").time()
        self._update_timer()

        button_pin = self.config['lights'].get('button')
        if button_pin:
            self._button = Button(int(button_pin))
            self._button.when_pressed = self._button_callback
        else:
            self._button = None

        self.logger.debug("Lights control initialised.")

    @property
    def is_on(self):
        return bool(self._output.value)

    @property
    def time_on(self):
        return self._time_on

    @time_on.setter
    def time_on(self, on_time):
        if not isinstance(on_time, time):
            on_time = datetime.strptime(on_time, "%H:%M").time()
        self._time_on = on_time
        self._update_timer()

    @property
    def time_off(self):
        return self._time_off

    @time_off.setter
    def time_off(self, off_time):
        if not isinstance(off_time, time):
            off_time = datetime.strptime(off_time, "%H:%M").time()
        self._time_on = on_time
        self._update_timer()

    @property
    def timer_on(self):
        return self._output.source is not None

    def on(self):
        self._output.on()

    def off(self):
        self._output.off()

    def start_timer(self):
        if self.timer_on:
            self.logger.warning("Lights timer already running.")
        else:
            self._output.source = self._timer
            self._output.source_delay = 60  # Check timer once per minute
            self.logger.info("Lights timer started.")

    def stop_timer(self):
        if not self.timer_on:
            self.logger.warning("Lights timer not running.")
        else:
            self._output.source = None
            self.logger.info("Lights timer stopped.")

    def toggle_timer(self):
        if self.timer_on:
            self.stop_timer()
        else:
            self.start_timer()

    def _update_timer(self):
        self._timer = TimeOfDay(self._time_on, self._time_off, utc=False)  # Work in local time

    def _button_callback(self):
        # Button press toggles both light status & timer status so that the time doesn't
        # revert the lights status within the following minute. This does require the user to
        # remember to press the button a second time to restore the timer.
        self.toggle_timer()
        self._output.toggle()
        self.logger.debug("Button pressed - Lights on: {}, Timer on: {}".format(self.is_on,
                                                                                self.timer_on))
