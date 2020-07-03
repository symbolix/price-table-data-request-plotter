# Global Imports
import pandas as pd
import numpy as np

# Local Imports
from os import sys
from os import path

scope = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))
sys.path.append(scope)

from coreglobals import get_global_property
from coreglobals import set_global_property

# from, import * guard.
__all__ = ['MovingAverage']


def my_public_method():
    # Test if we have access to the global properties.
    NAMESPACE = get_global_property('APP_NAME') + "." + __name__
    print('{}: Module accessed.'.format(NAMESPACE))


def sma(values, window):
    input_arr_length = len(values)

    weights = np.repeat(1.0, window) / window
    smas = np.convolve(values, weights, 'valid')

    result_arr_length = len(smas)

    first_value = smas[0]

    # print('\ninput_arr_length: {}, result_arr_length: {}, first_value: {}'
    #       .format(input_arr_length, result_arr_length, first_value)
    #       )

    # DEBUG
    # smas_length, smas_tail = len(smas), smas[-10:]

    # print('[PRE] smas_length: {}, smas_tail: {}'.format(smas_length, smas_tail))

    # input_arr_length = 287, result_arr_length = 258, range[258:286]
    fill_array = np.full((1, (input_arr_length - result_arr_length)), first_value)
    smas = np.append(fill_array, smas)

    # DEBUG
    # smas_length, smas_tail = len(smas), smas[-10:]
    # print('[POST] smas_length: {}, smas_tail: {}\n'.format(smas_length, smas_tail))

    return smas


def ema(values, window):
    # Temporary DataFrame container.
    tmp_df = pd.DataFrame({'values': values})
    tmp_df['results'] = tmp_df['values'].ewm(span=window, adjust=False).mean()

    return tmp_df['results']


class MovingAverage:
    # Emulate a secondary name-space in-order to utilise the following usage:
    #   indicators.MA.sma()
    #   indicators.MA.my_public_method()
    #   etc.

    sma = sma
    ema = ema
    my_public_method = my_public_method


# vim: ts=4 ft=python nowrap fdm=marker
