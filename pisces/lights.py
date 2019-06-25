from datetime import datetime, time

from gpiozero import TimeOfDay

from pisces.control import ControlBase, PollingBase


class LightsControl(ControlBase, PollingBase):
    def __init__(self, pisces_core, **kwargs):
        kwargs.update({'name': 'lights_control',
                       'output_name': 'lights'})
        super().__init__(pisces_core, **kwargs)
 
        self._time_on = datetime.strptime(self.config['lights_control']['time_on'],
                                          "%H:%M").time()
        self._time_off = datetime.strptime(self.config['lights_control']['time_off'],
                                           "%H:%M").time()
        self._update_timer()

        self.logger.info("Lights control initialised.")
        self.start_monitoring()

    def __del__(self):
        self.stop_monitoring()

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
        self._time_off = off_time
        self._update_timer()

    def _update_timer(self):
        self._timer = TimeOfDay(self.time_on, self.time_off, utc=False)  # Work in local time
        self.logger.info("Light timer set - On: {}, Off: {}.".format(self.time_on.strftime("%H:%M"),   
                                                                     self.time_off.strftime("%H:%M")))
        # Force an lights update to make sure they're now in sync with the timer.
        self._update()

    def _update(self):
        if self.is_auto:
            if self._timer.is_active and not self.is_on:
                self.on()
            elif self.is_on and not self._timer.is_active:
                self.off()
