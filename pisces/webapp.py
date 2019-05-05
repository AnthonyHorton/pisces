import datetime
import platform
import os

from gpiozero import DigitalOutputDevice
from flask import Flask, render_template, current_app

from pisces.base import PiscesBase
from pisces.utils import load_config, read_log


app = Flask(__name__)


@app.route('/')
def index():
    version = current_app.config['version']
    hostname = platform.node()
    data_file = current_app.config['pisces_config']['logging']['handlers']['data']['filename']
    last_reading = read_log(data_file)[0]
    last_reading_datetime = last_reading['log_time']
    now = datetime.datetime.now(tz=last_reading_datetime.tzinfo)
    time_string = now.strftime("%Y-%m-%d %H:%M")
    last_reading_age = (now - last_reading_datetime).total_seconds()
    if last_reading_age > current_app.config['pisces_config']['temperature_sensors']['log_interval']:
        last_colour = 'w3-red'
    else:
        last_colour = 'w3-green'
    last_mins = last_reading_age // 60

    target_max = current_app.config['pisces_config']['temperature_control']['target_max']
    target_min = current_app.config['pisces_config']['temperature_control']['target_min']

    if last_reading['water_temp'] > target_max:
        water_colour = 'w3-red'
    elif last_reading['water_temp'] < target_min:
        water_colour = 'w3-blue'
    else:
        water_colour = 'w3-green'

    if last_reading['air_temp'] > target_max:
        air_colour = 'w3-red'
    elif last_reading['air_temp'] < target_min:
        air_colour = 'w3-blue'
    else:
        air_colour = 'w3-green'

    if last_reading['cooler_on']:
        cooling_status = 'On'
        cooling_colour = 'w3-yellow'
    else:
        cooling_status = 'Off'
        cooling_colour = 'w3-black'

    if last_reading['lights_on']:
        lights_status = 'On'
        lights_colour = 'w3-green'
    else:
        lights_status = 'Off'
        lights_colour = 'w3-black'

    refresh_interval = current_app.config['pisces_config']['webapp']['refresh_interval']
    template_data = {'version': version,
                     'hostname': hostname,
                     'time': time_string,
                     'last_time': last_reading['log_time'],
                     'last_colour': last_colour,
                     'last_mins': last_mins,
                     'water_temp': last_reading['water_temp'],
                     'water_colour': water_colour,
                     'air_temp': last_reading['air_temp'],
                     'air_colour': air_colour,
                     'cooling_status': cooling_status,
                     'cooling_colour': cooling_colour,
                     'lights_status': lights_status,
                     'lights_colour': lights_colour,
                     'refresh_interval': refresh_interval}
    return render_template('index.html', **template_data)


if __name__ == '__main__':
    pb = PiscesBase()
    host = pb.config['webapp']['host']
    app.config['pisces_config'] = pb.config
    app.config['version'] = pb.__version__
    app.run(host=host, debug=True)
