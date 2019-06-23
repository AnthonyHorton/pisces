import time
from multiprocessing import Process, Event

from gpiozero import DigitalOutputDevice, Button

from pisces.base import PiscesBase
from pisces.sensors import SensorsBase as Sensors


class SubcomponentBase(PiscesBase):
    def __init__(self, pisces_core, **kwargs):
        super().__init__(**kwargs)
        self._core = pisces_core
        self._name = kwargs['name']

    def _update(self):
        """This is the method that should do something useful."""
        raise NotImplementedError


class ControlBase(SubcomponentBase):
    def __init__(self, pisces_core, **kwargs):
        super().__init__(pisces_core, **kwargs)
        self._output_name = kwargs['output_name']
        
        self._output = DigitalOutputDevice(int(self.config[self._name][self._output_name]),
                                           initial_value=None)
        self._status = {'{}_auto'.format(self._output_name): False,
                        '{}_enabled'.format(self._output_name): self._output.is_active}

        button_pin = self.config[self._name].get('button')
        if button_pin:
            self._button = Button(int(button_pin), bounce_time=0.1)
            self._button.when_pressed = self._button_callback
        else:
            self._button = None

    @property
    def status(self):
        return self._status

    @property
    def is_on(self):
        return self._output.is_active

    @property
    def is_auto(self):
        return self._status['{}_auto'.format(self._output_name)]

    def on(self):
        self._output.on()
        self.logger.debug("{} turned on.".format(self._output_name))
        self._update_status()

    def off(self):
        self._output.off()
        self.logger.debug("{} turned off.".format(self._output_name))
        self._update_status()

    def toggle(self):
        self._output.toggle()
        self.logger.debug("{} toggled.".format(self._output_name))
        self._update_status()
    
    def auto_on(self):
        if self.is_auto:
            self.logger.warning("{} already in automatic mode.".format(self._output_name))
        else:
            self._status['{}_auto'.format(self._output_name)] = True
            self.logger.info("{} in automatic mode.".format(self._output_name))
            # Force an update to make sure outputs are immediately put in correct state.
            self._update()

    def auto_off(self):
        if not self.is_auto:
            self.logger.warning("{} already in manual mode.".format(self._output_name))
        else:
            self._status['{}_auto'.format(self._output_name)] = False
            self.logger.info("{} in manual mode.".format(self._output_name))
            self._update_status()

    def _button_callback(self):
        # Button press cycles through automatic, manual on, manual off states.
        if self.is_auto:
            # In auto, next state is manual on.
            self.auto_off()
            self.on()
        elif self.is_on:
            # In manual on, next state is manual off
            self.off()
        else:
            # In manual off, next state is automatic.
            self.auto_on()

    def _update_status(self):
        self._status['{}_enabled'.format(self._output_name)] = self._output.is_active
        self._core.update_status(self._status)


class PollingBase(SubcomponentBase):
    def __init__(self, pisces_core, **kwargs):
        super().__init__(pisces_core, **kwargs)

        self._loop_interval = int(self.config[self._name]['loop_interval'])
        if self._loop_interval < 1:
            msg = "Temperature control 'loop_interval' must be integer > 0."
            self.logger.critical(msg)
            raise ValueError(msg)

        self._stop_event = Event()
        self._stop_event.set()
        
    def start_monitoring(self):
        if not self._stop_event.is_set():
            self.logger.warning("{} already running.".format(self._name))
        else:
            self._stop_event.clear()
            self._controller = Process(target=self._monitor, daemon=True)
            self._controller.start()

    def stop_monitoring(self):
        if self._stop_event.is_set():
            self.logger.warning("{} not running.".format(self._name))
        else:
            self._stop_event.set()
            self._controller.join(timeout=5)
            if self._controller.exitcode is None:
                self._controller.terminate()
                if self._controller.exitcode is None:
                    self._controller.kill()

    def _monitor(self):
        self.logger.info("{} starting.".format(self._name))
        while not self._stop_event.is_set():
            self._update()
            for i in range(self._loop_interval):
                if self._stop_event.is_set():
                    break
                time.sleep(1)
        self.logger.info("{} stopped.".format(self._name))




class ClosedLoopBase(ControlBase, PollingBase):
    def __init__(self, pisces_core, **kwargs):
        super().__init__(pisces_core, **kwargs)
        self._sensors = Sensors(**kwargs)

        self._target_max = float(self.config[self._name]['target_max'])
        self._target_min = float(self.config[self._name]['target_min'])
        if self._target_max <= self._target_min:
            msg = "{} 'target_min' must be <= 'target_max'.".format(self._name)
            self.logger.critical(msg)
            raise ValueError(msg)

        self._hysteresis = float(self.config[self._name]['hysteresis'])
        if self._hysteresis < 0:
            msg = "{} 'hysteresis' must be > 0.".format(self.name)
            self.logger.critical(msg)
            raise ValueError(msg)
        elif self._hysteresis > (self._target_max - self._target_min):
            msg = "{} 'hysteresis' must be < ('target_max' - 'target_min').".format(self._name)
            self.logger.critical(msg)
            raise ValueError(msg)
