import datetime
import platform
from multiprocessing import Process

from flask import Flask, render_template, current_app, Blueprint

from pisces import __version__
from pisces.base import PiscesBase

route_blueprint = Blueprint('route_blueprint', __name__)


class WebApp(PiscesBase):
    def __init__(self, temperature_sensors, **kwargs):
        super().__init__(**kwargs)
        self.app = self.create_app()
        self.app_process = None
        self.logger.debug("Web app initialised")

    def create_app(self):
        app = Flask(__name__)
        app.register_blueprint(route_blueprint)
        return app

    @route_blueprint.route('/')
    def index():
        temperatures = self.temperature_sensors.get_temperatures()
        temp_strings = {n: "{:2.1f}".format(t) for n, t in temperatures.items()}
        now = datetime.datetime.now()
        time_string = now.strftime("%Y-%m-%d %H:%M")

        template_data = {'interval': self.config['webapp']['refresh_interval'],
                         'version': __version__,
                         'host': platform.node(),
                         'time': time_string,
                         **temp_strings}

        return render_template('index.html', **template_data)

    def start(self):
        if self.app_process and self.app_process.is_alive():
            self.logger.warning("Web app already running.")
        else:
            self.app_process = Process(target=self.app.run,
                                       kwargs={'host': self.config['webapp']['host'],
                                               'debug': True,
                                               'use_reloader': False},
                                       daemon=True)
        self.logger.debug("Web app started")

    def stop(self):
        if self.app_process and not self.app_process.is_alive():
            self.logger.warning("Webapp not running.")
        else:
            self.app_process.terminate()
            if self.app_process.exitcode is None:
                self.app_process.kill()
            self.logger.debug("Web app stopped.")
