import logging

from pisces.control import PollingBase
from pisces.utils import plot_log

class DataLogger(PollingBase):
    def __init__(self, pisces_core, **kwargs):
        kwargs.update({'name': 'data_logger'})
        super().__init__(pisces_core, **kwargs)
        
        self._data_logger = logging.getLogger('pisces_data')
        self._log_file = self.config['logging']['handlers']['data']['filename']

        self.logger.info("Data logger initialised.")

    def _update(self):
        data = self._core.status
        data_string = "{:2.3f} {:<4} {:2.3f} {:2.1f} {:<4} {:<5} {:<5} {:<5} {:<5} {:<5} {:<5} {:<5}".format(*data.values())
        self._data_logger.info(data_string)
        try:
            plot_log(log_filename=self._log_file,
                     log_interval=self._log_interval,
                     **self.config['temperature_sensors']['plotting'])
        except Exception as err:
            # Don't want any plotting issues to stop data logging. Log the error, then carry on regardless.
            self.logger.error("Error updating temperature plot: {}".format(err))

