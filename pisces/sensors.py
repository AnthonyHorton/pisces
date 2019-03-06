def get_temperatures(sensors):
    temperatures = {}
    for name, device in sensors.items():
        with open(device) as sensor_device:
            raw_data = sensor_device.read()
        _, _, string_temp = raw_data.rpartition('=')
        temperatures[name] = float(string_temp) / 1000
    return temperatures
