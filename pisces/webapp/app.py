import argparse
import datetime
import platform

from flask import Flask, render_template

from pisces import __version__

app = Flask(__name__)

@app.route('/')
def index():
    host = platform.node()
    now = datetime.datetime.now()
    time_string = now.strftime("%Y-%m-%d %H:%M")
    template_data = {'version': __version__,
                     'host': host,
                     'time': time_string}
    return render_template('index.html', **template_data)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("host")
    args = parser.parse_args()
    app.run(host=args.host, debug=True)


