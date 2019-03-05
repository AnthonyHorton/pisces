import argparse
import datetime
import platform
import os

import yaml
from flask import Flask, render_template, current_app, Blueprint

from pisces import __version__


route_blueprint = Blueprint('route_blueprint', __name__)


def load_config():
    my_path = os.path.dirname(__file__)
    config_path = os.path.join(my_path, "../config.yaml")
    with open(config_path) as config_file:
        config = yaml.load(config_file)
    return config


def get_temperatures(sensors):
    temperatures = {}
    for name, device in sensors.items():
        with open(device) as sensor_device:
            raw_data = sensor_device.read()
        _, _, string_temp = raw_data.rpartition('=')
        temperature = float(string_temp) / 1000
        temperatures[name] = "{:2.1f}".format(temperature)
    return temperatures


def create_app(sensors):
    app = Flask(__name__)
    app.config['sensors'] = sensors
    app.register_blueprint(route_blueprint)
    return app


@route_blueprint.route('/')
def index():
    host = platform.node()
    now = datetime.datetime.now()
    time_string = now.strftime("%Y-%m-%d %H:%M")
    temperatures = get_temperatures(current_app.config['sensors'])
    template_data = {'version': __version__,
                     'host': host,
                     'time': time_string,
                     **temperatures}
    return render_template('index.html', **template_data)


if __name__ == '__main__':
    config = load_config()
    host = config.get("host")
    temperature_sensors = config.get("temperature_sensors")
    app = create_app(temperature_sensors)
    app.run(host=host, debug=True)


