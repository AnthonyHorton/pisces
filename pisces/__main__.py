import os
import datetime
import time
import yaml
from multiprocessing import Process

from dateutil.tz import tzlocal


from pisces import sensors
from pisces import app


def load_config():
    my_path = os.path.dirname(__file__)
    config_path = os.path.join(my_path, "../config.yaml")
    with open(config_path) as config_file:
        config = yaml.load(config_file)
    return config


def log_temperature(config):
    temperatures = sensors.get_temperatures(config['sensors'])
    now = datetime.datetime.now(tz=tzlocal())
    log_name = config['logging']['log_file']
    log_line = "{} {:2.3f} {:2.3f}\n".format(now.isoformat(timespec='seconds'),
                                             temperatures['water_temp'],
                                             temperatures['air_temp'])
    with open(log_name, mode='at') as log_file:
        log_file.write(log_line)
    print("Logged to {}: {}".format(log_name, log_line.rstrip()))


def log_temperatures(config):
    log_file = config['logging']['log_file']
    interval = config['logging']['interval']
    print("Starting temperature logging: log file {}, interval {}s".format(log_file, interval))
    while True:
        log_temperature(config)
        time.sleep(interval)


if __name__ == "__main__":
    config = load_config()
    log_process = Process(target=log_temperatures,
                          args=(config,),
                          daemon=True)
    log_process.start()
    app.run(config)
