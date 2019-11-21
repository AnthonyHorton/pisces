import os
import os.path
from glob import glob
import subprocess
import signal
from warnings import warn
from datetime import datetime

import yaml
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure


def load_config(config_path, path_root=None):
    if not os.path.isabs(config_path) and path_root:
        config_path = os.path.join(path_root, config_path)

    try:
        with open(config_path) as config_file:
            config = yaml.load(config_file)
    except OSError as err:
        msg = "Error opening config {}: {}".format(config_path, err)
        raise OSError(msg)
    except yaml.YAMLError as err:
        msg = "Error loading config {}: {}".format(config_path, err)
        raise yaml.YAMLError(msg)

    return config


def get_last_n_lines(filename, n_lines=1, max_line_size=120):
    """Get the last n lines of a text file without reading it all.

    Args:
        filename (str): path to the text file
        n_lines (int, optional): number of lines from the end of the file to
            return, default 1.
        max_line_size (int, optional): maximum number of bytes per
            line of the file. Default 120.

    Returns:
        list: list of newline terminates strings comprising the last n lines
            of the file.

    Raises:
        ValueError: invalid values for n_lines or max_line_size (must be
            positive integers).
        OSError: filename does not exist or is inaccessible

    Notes:
        n_lines * max_line_size will be read from the end of the file. If this
        section of the file contains at least n_lines lines the last n_lines
        will be returned. If fewer lines are found then the amount of the file
        read will be increased by max_line_size and it will try again, until
        either n_lines are found or the whole file has been read.
    """
    if int(n_lines) < 1:
        msg = "n_lines must be a positive integer, got {}".format(n_lines)
        raise ValueError(msg)
    if int(max_line_size) < 1:
        msg = "max_line_size must be a positive integer, got {}".format(n_lines)
        raise ValueError(msg)

    n_lines = int(n_lines)
    max_line_size = int(max_line_size)
    buffer_size = n_lines * max_line_size
    file_size = os.path.getsize(filename)

    lines = []
    while len(lines) < n_lines:
        with open(filename) as f:
            if file_size > buffer_size:
                f.seek(file_size - buffer_size)
            lines = f.readlines()
        if buffer_size >= file_size:
            break
        else:
            buffer_size += max_line_size

    return lines[-n_lines:]


def read_log(filename, n_lines=1, max_line_size=120):
    log_names = ('log_time',
                 'water_temp',
                 'water_temp_status',
                 'air_temp',
                 'water_level',
                 'water_level_status',
                 'overflow',
                 'lights_auto',
                 'lights_enabled',
                 'fan_auto',
                 'fan_enabled',
                 'pump_auto',
                 'pump_enabled')
    log_dtypes = (datetime,
                  np.float,
                  'U4',
                  np.float,
                  np.float,
                  'U4',
                  np.bool,
                  np.bool,
                  np.bool,
                  np.bool,
                  np.bool,
                  np.bool,
                  np.bool)
    time_converter = lambda t: datetime.strptime(t.decode(), "%Y-%m-%dT%H:%M:%S%z")
    bool_converter = lambda b: bool(int(b))

    log_lines = get_last_n_lines(filename, n_lines, max_line_size)
    if len(log_lines) < n_lines:
        # Not enough lines in the current temperature log file. Look for next oldest one and get more lines from that.
        old_log_files = glob("{}.20*".format(filename))
        if old_log_files:
            # Found some older logs. Sort newest first.
            old_log_files.sort(reverse=True)
            # Get lines from old log files until we have n lines.
            for old_log_file in old_log_files:
                old_lines = get_last_n_lines(old_log_file, n_lines - len(log_lines), max_line_size)
                log_lines = old_lines + log_lines
                if len(log_lines) >= n_lines:
                    break

    log_data = np.genfromtxt(log_lines,
                             names=log_names,
                             dtype=log_dtypes,
                             converters={'log_time': time_converter,
                                         'overflow': bool_converter,
                                         'lights_auto': bool_converter,
                                         'lights_enabled': bool_converter,
                                         'fan_auto': bool_converter,
                                         'fan_enabled': bool_converter,
                                         'pump_auto': bool_converter,
                                         'pump_enabled': bool_converter},
                             filling_values=np.nan)

    if n_lines == 1:
        # Structured 1D arrays with 1 element lose their shape,
        # preventing access to values via sa[field_name][0].
        # Need to give it its shape back to allow access in the
        # same way as multi-element structured arrays.
        log_data = log_data.reshape((1,))
    return log_data


def plot_log(log_filename='data/pisces.dat',
             log_interval=300,
             filename_root='pisces/static/temperature',
             temp_limits = [23, 28],
             target_limits = [25, 26],
             duration=24):
    for old_plot in glob("{}_*.png".format(filename_root)):
        os.unlink(old_plot)
    log_data = read_log(log_filename, n_lines=(duration * 3600 / log_interval))
    fig = Figure()
    FigureCanvas(fig)
    fig.set_size_inches(12, 8)
    ax = fig.add_subplot(1, 1, 1)
    ax.fill_between(log_data['log_time'], target_limits[0], target_limits[1], color='g', alpha=0.3)
    ax.plot(log_data['log_time'], log_data['water_temp'], 'b-', label='Water temperature')
    ax.plot(log_data['log_time'], log_data['air_temp'], 'c-', label='Air temperature')
    fan_on_times = log_data['log_time'][log_data['fan_enabled'] == True]
    ax.plot(fan_on_times, temp_limits[1] * np.ones(fan_on_times.shape),
               'yo', label='Cooling fan on')
    lights_on_times = log_data['log_time'][log_data['lights_enabled'] == True]
    ax.plot(lights_on_times, temp_limits[0] * np.ones(lights_on_times.shape),
            'go', label='Lights on')
    ax.legend(loc=0)
    ax.set_xlim(log_data['log_time'].min(), log_data['log_time'].max())
    ax.set_ylabel('Temperature / degC')
    ax.set_ylim(*temp_limits)
    ax.set_title("Temperatures over {} hours up to {}".format(duration, log_data[-1]['log_time']))
    fig.tight_layout()
    fig.savefig("{}_{}.png".format(filename_root,
                                   log_data[-1]['log_time'].strftime('%Y-%m-%dT%H:%M:%S%z')),
                transparent=False)
    fig.clf()
    del fig


def end_process(proc):
    """Makes absolutely sure that a process is definitely well and truly dead.

    Args:
        proc (subprocess.Popen): Popen object for the process
    """
    expected_return = 0
    if proc.poll() is None:
        # I'm not dead!
        expected_return = -signal.SIGINT
        proc.send_signal(signal.SIGINT)
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired as err:
            warn("Timeout waiting for {} to exit!".format(proc.pid))
            if proc.poll() is None:
                # I'm getting better!
                warn("Sending SIGTERM to {}...".format(proc.pid))
                expected_return = -signal.SIGTERM
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired as err:
                    warn("Timeout waiting for {} to terminate!".format(proc.pid))
                    if proc.poll() is None:
                        # I feel fine!
                        warn("Sending SIGKILL to {}...".format(proc.pid))
                        expected_return = -signal.SIGKILL
                        proc.kill()
                        try:
                            proc.wait(timeout=10)
                        except subprocess.TimeoutExpired as err:
                            warn("Timeout waiting for {} to die! Giving up".format(proc.pid))
                            raise err
    else:
        warn("Process {} already exited!".format(proc.pid))

    if proc.returncode != expected_return:
        warn("Expected return code {} from {}, got {}!".format(expected_return,
                                                               proc.pid,
                                                               proc.returncode))
    return proc.returncode
