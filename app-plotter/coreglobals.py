_data = {
    'APP_NAME': None,
    'APP_MAJOR_VERSION': '0',
    'APP_MINOR_VERSION': '1',
    'APP_DEV_VERSION': '1',
    'PROCESS_ID': None,
    'REQUIRED_VERBOSITY_DEPTH': 1,
    'CURRENT_VERBOSITY_LEVEL': 0,
    'LOG_FILE_ABSOLUTE_PATH': None,
    'APP_VERSION': '0.0.0'
}


def get_global_property(key):
    return '{}'.format(_data[key])


def set_global_property(key, value):
    _data[key] = value


def module_test():
    print('Module accessed.')


_data['APP_VERSION'] = '{}.{}.{}'.format(
    _data['APP_MAJOR_VERSION'],
    _data['APP_MINOR_VERSION'],
    _data['APP_DEV_VERSION'])

# vim: ts=4 ft=python nowrap fdm=marker
