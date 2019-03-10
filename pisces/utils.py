import os
import os.path
import subprocess
import signal
from warnings import warn

import yaml

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
