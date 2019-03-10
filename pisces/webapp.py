import datetime
import platform
import os

from flask import Flask, render_template, current_app

from pisces.base import PiscesBase
from pisces.utils import load_config
from pisces.sensors import read_log


app = Flask(__name__)


@app.route('/')
def index():
    version = current_app.config['version']
    hostname = platform.node()
    now = datetime.datetime.now()
    time_string = now.strftime("%Y-%m-%d %H:%M")
    data_file = current_app.config['pisces_config']['logging']['handlers']['data']['filename']
    last_reading = read_log(data_file)[0]
    refresh_interval = current_app.config['pisces_config']['webapp']['refresh_interval']
    template_data = {'version': version,
                     'hostname': hostname,
                     'time': time_string,
                     'last_time': last_reading['log_time'].time(),
                     'water_temp': last_reading['water_temp'],
                     'air_temp': last_reading['air_temp'],
                     'refresh_interval': refresh_interval}
    return render_template('index.html', **template_data)


if __name__ == '__main__':
    pb = PiscesBase()
    host = pb.config['webapp']['host']
    app.config['pisces_config'] = pb.config
    app.config['version'] = pb.__version__
    app.run(host=host, debug=True)
