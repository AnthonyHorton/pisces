import datetime
import platform

from flask import Flask, render_template, current_app, Blueprint

from pisces import __version__
from pisces import sensors


route_blueprint = Blueprint('route_blueprint', __name__)


def create_app(config):
    app = Flask(__name__)
    app.config.update(config)
    app.register_blueprint(route_blueprint)
    return app


@route_blueprint.route('/')
def index():
    temperatures = sensors.get_temperatures(current_app.config['sensors'])
    temp_strings = {n: "{:2.1f}".format(t) for n, t in temperatures.items()}
    now = datetime.datetime.now()
    time_string = now.strftime("%Y-%m-%d %H:%M")

    template_data = {'interval': current_app.config['webapp']['interval'],
                     'version': __version__,
                     'host': platform.node(),
                     'time': time_string,
                     **temp_strings}

    return render_template('index.html', **template_data)

def run(config):
    host = config['webapp']['host']
    app = create_app(config)
    app.run(host=host, debug=True, use_reloader=False)
