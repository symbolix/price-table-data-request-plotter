# Global Imports
import pandas as pd

# Local Imports
from os import sys
from os import path

scope = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))
sys.path.append(scope)

from coreglobals import get_global_property
from coreglobals import set_global_property

# module_test()

# from, import * guard.
__all__ = ['InputOutput']


def my_public_method():
    # Test if we have access to the global properties.
    NAMESPACE = get_global_property('APP_NAME') + "." + __name__
    print('{}: Module accessed.'.format(NAMESPACE))


def import_csv_data(csv_file):
    print('SOURCE\t: {}\nTASK\t: {}'.format(csv_file, 'Import dataset from CSV.'))

    df = pd.read_csv(csv_file)

    # new_df = df[['created_date', 'client_name', 'amount']].copy()
    df['time'] = pd.to_datetime(df['timestamp'], unit='s')
    df.rename(columns={'time': 'date'}, inplace=True)

    return df


class InputOutput:
    # Emulate a secondary name-space in-order to utilise the following usage:
    #   indicators.IO.sma()
    #   indicators.IO.my_public_method()
    #   etc.

    import_csv_data = import_csv_data
    my_public_method = my_public_method

# vim: ts=4 ft=python nowrap fdm=marker
