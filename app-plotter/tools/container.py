# Global Imports
from bokeh.models import ColumnDataSource
from bokeh import events
import types
import datetime
from dateutil.parser import parse
from pytz import timezone
import numpy as np
import pandas as pd
import pytz

# Local Imports
from os import sys
from os import path

# A crude solution, but should be fixed eventually.
# 'scope' is '<PROJECT_ROOT>/<APP_ROOT>'
#       for example: /home/me/dev/my-project/my-bokeh-app
# WARNING: This hack is required to import the local modules from within the current module depth.
scope = path.dirname(path.dirname(path.abspath(__file__)))
sys.path.append(scope)

import tools.wrappers as wrappers
from coreglobals import get_global_property
from coreglobals import set_global_property
import tools.utils as utils
import tools.indicators as indicators
from tools.timezones import ZonesList as tzl

# from, import * guard.
__all__ = ['my_public_method']

# Private properties related to timezoned.
__timezone_labels = ['({}) {}'.format(zone[0], zone[1]) for zone in tzl]
__timezone_signatures = [zone[2] for zone in tzl]

# Module Globals
TIMEZONE_LOOKUP = {k: v for k, v in zip(__timezone_labels, __timezone_signatures)}
EPOCH = datetime.datetime.utcfromtimestamp(0)

# Colour scheme for increasing and descending candles
INCREASING_COLOR = '#30A092'
DECREASING_COLOR = '#DC5B55'

# @pubic function my_public_method() {{{1


def my_public_method():
    """
    A test public method.
    """

    # Test if we have access to the global properties.
    NAMESPACE = get_global_property('APP_NAME') + "." + __name__
    print('{}: Module accessed.'.format(NAMESPACE))
# }}}1


class MyUpdater(object):
    # These are the core class attributes required to store the critial data at class level.
    __data_df = []
    __limits = []
    __serialized_plots = []
    __original_date_df = []
    timedelta = 0
    __states = {
        'timezone': {
            'signature': {
                'previous': None,
                'current': None
            },
            'zone': {
                'previous': None,
                'current': None
            },
        },
        'timerange': {
            'candlestick': {
                'previous': {'start': None, 'end': None},
                'current': {'start': None, 'end': None}
            },
        }
    }

    # Contructor
    def __init__(self, plots={}, widgets={}, configs={}, file=None, source=None):

        self.plots = plots
        self.widgets = widgets
        self.configs = configs
        self.file = file
        self.source = source

        # Populate class attributes at initialisation.
        self.__populate_data_storage(self.file)

        # Plot references are stored at initialisation stage and are persistent per instance.
        self.__serialized_plots = self.plots

        # Rest Time
        self.__states['timezone']['signature']['current'] = '(Exchange) Exchange'
        self.__original_date_df = self.__data_df[['date']]

    # Private Method
    def __get_raw_data(self, file):

        local_df = wrappers.get_raw_data(
            source_file=file,
            field='{}/{}'.format(self.widgets['asset'].value, self.widgets['pair'].value)
        )
        return local_df

    # Private Method
    def __populate_data_storage(self, file):
        # Internally adapt the file name to support one of the timeframe: 5m, 15m, 1h, 4h, 1d
        file_signature = file.format(self.widgets['timeframe'].value.lower())
        raw_df = self.__get_raw_data(file_signature)

        # Get a fresh snapshot of the data and the limits.
        # (DEBUG) print('{}\n{}\n{}'.format('+' * 80, self.configs['ma'], '+' * 80))
        (self.__data_df,
         self.__limits) = wrappers.get_data_container(raw_df, MA=self.configs['ma'],
                                                      MACD=self.configs['macd'], drop_last=True)

    # Private Method
    def __convert_timeframe(self):
        lookup = {
            '5m': 5,
            '15m': 15,
            '1h': 60,
            '4h': 240,
            '1D': 1440,
        }
        minutes = lookup[self.widgets['timeframe'].value]

        # Percent of the width.
        bar_padding = 20

        # Final width.
        # 1 sec = 1000 milliseconds
        # 1 min = 60 seconds
        return (minutes * 60 * 1000) - ((minutes * 60 * 1000) * ((bar_padding / 100) * 2))

    def __call__(self, task=None, cb=None, timeframe=None, active=False, axis_reset=False):

        # DEBUG
        print('__task__: {}'.format(task))

        # Unpack the plots.
        _p1 = self.__serialized_plots['candlestick']['plot']
        _p2 = self.__serialized_plots['macd']['plot']
        _p3 = self.__serialized_plots['volume']['plot']

        # Handle States (Part 1 of 2)

        # Backup the 'current' timezone signature as 'previous', then update the 'current' timezone
        # signature with the value supplied by the live widget.
        self.__states['timezone']['signature']['previous'] = self.__states['timezone']['signature']['current']
        self.__states['timezone']['signature']['current'] = self.widgets['timezone'].value

        # ACTIVE {{{2
        if active:
            # If this is an 'ACTIVE' call, we need to perform a hot reload.
            # This process will update the data stored inside the '__data_df' and '__limits'
            # containers. These are class level attributes and should be accessible by every
            # instance of the 'Updater' class.
            self.__populate_data_storage(self.file)

            # Rest TimeZone
            self.__original_date_df = self.__data_df[['date']]

            if self.__states['timezone']['signature']['current'] is None:
                self.__states['timezone']['signature']['current'] = '(Exchange) Exchange'
            else:
                self.__states['timezone']['signature']['previous'] = self.__states['timezone']['signature']['current']
                self.__states['timezone']['signature']['current'] = self.widgets['timezone'].value
        # }}}2

        # Unpack limits from the class storage.
        (volume_lower_limit,
         volume_upper_limit,
         candlestick_lower_limit,
         candlestick_upper_limit,
         macd_lower_limit,
         macd_upper_limit) = wrappers.get_limits(self.__limits, padding_scale=0.05)

        # TIMEZONE {{{2

        # Update timezone state.
        print(';--- [TIMEZONE] --- (START) ---')

        previous_timezone_signature = self.__states['timezone']['signature']['previous']
        current_timezone_signature = self.__states['timezone']['signature']['current']

        print('[update:{:<19}] <previous_signature: {}>, <current_signature: {}>'.format(
            'TIMEZONE_SIGNATURES', previous_timezone_signature, current_timezone_signature))

        # Timezone Lookup
        previous_timezone_zone = TIMEZONE_LOOKUP[previous_timezone_signature]
        current_timezone_zone = TIMEZONE_LOOKUP[current_timezone_signature]

        print('[update:{:<19}] <previous_zone: {}>, <current_zone: {}>'.format(
            'TIMEZONE_ZONES', previous_timezone_zone, current_timezone_zone))

        print('[update:{:<19}] <signature: {}>, <zone: {}>'.format(
            'REQUEST', current_timezone_signature, current_timezone_zone))

        # Handle any new timezone requests.
        # First we need to reset to the original 'Exchange' zone (UTC+00:00).
        # In order to avoid time-delta calculations required to revert back to the original
        # exchange date-time, we are simply swapping the initial date-time state here.
        self.__data_df['date'] = self.__original_date_df

        if previous_timezone_signature != current_timezone_signature:
            previous_key_time = self.__original_date_df['date'].iloc[0].tz_localize("UTC").tz_convert(previous_timezone_zone).tz_localize(None)
            prev_kt = previous_key_time.replace(tzinfo=None).to_pydatetime()
            print('[DEBUG] (previous_timezone_signature != current_timezone_signature) prev: {}'.format(prev_kt))

            print('[DEBUG] (previous_timezone_signature != current_timezone_signature) New timezone set.')
            # ... then switch to the new timezone and update the dataframe.
            self.__data_df['date'] = self.__data_df['date'].dt.tz_localize("UTC").dt.tz_convert(current_timezone_zone).dt.tz_localize(None)

            current_key_time = self.__data_df['date'].iloc[0]
            curr_kt = current_key_time.replace(tzinfo=None).to_pydatetime()
            print('[DEBUG] (previous_timezone_signature != current_timezone_signature) curr: {}'.format(curr_kt))

            time_delta = (curr_kt - prev_kt)

            td = time_delta.total_seconds() * 1000
            MyUpdater.timedelta = td

            if axis_reset:
                print('[DEBUG] (previous_timezone_signature != current_timezone_signature) Incoming time-delta is zero.')
                td = 0
                MyUpdater.timedelta = td

            print('[DEBUG] (previous_timezone_signature != current_timezone_signature) time_delta (milliseconds): {}'.format(td))
        else:
            # This is for conditions where we change other data fields, but the time-zone stays
            # the same. Also when we are running for the first time.
            print('[DEBUG] (previous_timezone_signature == current_timezone_signature) Incoming time-delta is zero.')
            td = 0
            MyUpdater.timedelta = td
            print('[DEBUG] (previous_timezone_signature == current_timezone_signature) Timezone set.')

            # Transform the exchange timezone to the current timezone.
            self.__data_df['date'] = self.__data_df['date'].dt.tz_localize("UTC").dt.tz_convert(current_timezone_zone).dt.tz_localize(None)

            print('[DEBUG] (previous_timezone_signature == current_timezone_signature) time_delta (milliseconds): {}'.format(td))

        print(';--- [TIMEZONE] --- (_END_) ---')
        # }}}2

        # Extra data fields.
        self.__data_df['candle_color'] = INCREASING_COLOR
        self.__data_df.loc[self.__data_df.close < self.__data_df.open, 'candle_color'] = DECREASING_COLOR

        # Handle wrangle callbacks.
        if cb is not None:
            print('[DEBUG] Callback:Handler -> {}'.format(cb.__name__))
            cb(self.widgets['mavg'], self.configs['ma'], self.__data_df)

        # Handle States (Part 2 of 2) -- NEEDS TO HAPPEN AFTER THE TIMEZONE REQUEST

        # Backup the 'current' timerange as 'previous', then update the 'current' with the live range value.
        self.__states['timerange']['candlestick']['previous']['start'] = self.__states['timerange']['candlestick']['current']['start']
        self.__states['timerange']['candlestick']['previous']['end'] = self.__states['timerange']['candlestick']['current']['end']
        self.__states['timerange']['candlestick']['current']['start'] = _p1.x_range.start
        self.__states['timerange']['candlestick']['current']['end'] = _p1.x_range.end

        # Just initialize the raw time-ranges. These values are provided by the initial plot
        # configuration and are place holders. Actual range vlues will be set later.
        print(';--- INIT_TIME-RANGE --- (START) ---')
        timerange_start = self.__states['timerange']['candlestick']['current']['start']
        timerange_end = self.__states['timerange']['candlestick']['current']['end']
        print('[DEBUG] timerange_start: {}, timerange_end: {}'.format(timerange_start, timerange_end))
        print('[DEBUG] plotrange_start: {}, plotrange_end: {}'.format(_p1.x_range.start, _p1.x_range.end))
        print(';--- INIT_TIME-RANGE --- ( END ) ---')

        # Serialize Limits
        serialized_limits = {}

        # We need to construct a matching dictionary. This will be merged into the
        # serialized plot structure.
        # {
        #   candlestick: [lower_limit, upper_limit],
        #   volume: [lower_limit, upper_limit],
        #   macd: [lower_limit, upper_limit]
        # }

        for key, value in self.__serialized_plots.items():
            serialized_limits[key] = {'limits': [eval('{}_{}_{}'.format(key, value['limits'][0], 'limit')), eval('{}_{}_{}'.format(key, value['limits'][1], 'limit'))]}

        # This is usually when we run for the first time.
        if axis_reset:
            # AXIS RESET {{{2
            print(';--- [AXIS_RESET] --- (START) ---')

            # When resetting, we realy on the range(s) provided within the dataframe.
            timerange_end = ((self.__data_df['date'].iat[-1] - EPOCH).total_seconds() * 1000)
            timerange_start = ((self.__data_df['date'].iloc[0] - EPOCH).total_seconds() * 1000)

            # Then merge serialized objects, merge and set the plot properties.
            # WARNING: The limit values used at this stage will include the padding margins.
            for key, val in self.__serialized_plots.items():
                # iterate over plots (p1, p2, p3 etc.)
                plot = val['plot']

                # Setup the vertical limits (Y-axis).
                print('[update:{:<18}] ({}), {}, <{}>'.format(
                    'RANGE', 'y', key, serialized_limits[key]['limits']))

                plot.y_range.update(
                    start=serialized_limits[key]['limits'][0],
                    end=serialized_limits[key]['limits'][1])

            # Setup the horizontal limits (X-axis) on the first plot.
            # Other plots are already linked to p1's x-axis.
            print('[update:{:<18}] ({}), <{}>'.format(
                'RANGE', 'x', [timerange_start, timerange_end]))

            _p1.x_range.update(start=timerange_start, end=timerange_end)

            # Update class state container.
            self.__states['timerange']['candlestick']['current']['start'] = timerange_start
            self.__states['timerange']['candlestick']['current']['end'] = timerange_end

            print(';--- [AXIS_RESET] --- (_END_) ---')
            # }}}2
        else:
            # AXIS SET {{{2
            print(';--- [AXIS_SET] --- (START) ---')
            # *** WARNING: Fix the "MA out of sync on pair change" issue! ***
            # *** WARNING: Fix the "Reset button will not reset in a different time-zone" issue! ***
            if td != 0:
                print('[DEBUG] Apply time-delta correction.')
                a = timerange_start + td
                b = timerange_end + td

                _p1.x_range.update(start=a, end=b)

                # Done? Reset td?
                print('[DEBUG] Reset time-delta.')
                td = 0
                MyUpdater.timedelta = td

            print(';--- [AXIS_SET] --- (_END_) ---')
            # }}}2

        # Override p1 (Candlestick).
        _p1_text_label = 'Candlestick Bars, {}, {}/{}, {}'
        _p1_title_text = _p1_text_label.format(
            self.widgets['mavg'].value, self.widgets['asset'].value,
            self.widgets['pair'].value, self.widgets['timeframe'].value)
        _p1.title.text = _p1_title_text

        # Override p2 (MACD).
        _p2_text_label = 'MACD ({}, {}, {})'
        _p2_title_text = _p2_text_label.format(
            self.configs['macd']['fast_period'], self.configs['macd']['slow_period'],
            self.configs['macd']['signal_period'])
        _p2.title.text = _p2_title_text

        # Override p3 (Volume).
        _p3_text_label = '{}'
        _p3_title_text = _p3_text_label.format('Volume')
        _p3.title.text = _p3_title_text

        # Provide the dynamic bar width.
        self.__data_df['bar_width'] = self.__convert_timeframe()

        # Create a new data-container.
        new_data = dict(
            index=self.__data_df.index,
            time=self.__data_df.date,
            open=self.__data_df.open,
            high=self.__data_df.high,
            low=self.__data_df.low,
            close=self.__data_df.close,
            candle_wick_color=self.__data_df.candle_color,
            candle_body_fill_color=self.__data_df.candle_color,
            candle_body_line_color=self.__data_df.candle_color,
            candle_bound_min=self.__data_df.candle_bound_min,
            candle_bound_max=self.__data_df.candle_bound_max,
            ma_slow=self.__data_df.ma_slow,
            ma_fast=self.__data_df.ma_fast,
            macd=self.__data_df.macd,
            macds=self.__data_df.macds,
            macdh=self.__data_df.macdh,
            macd_bound_min=self.__data_df.macd_bound_min,
            macd_bound_max=self.__data_df.macd_bound_max,
            volume=self.__data_df.volume,
            volume_bound_min=self.__data_df.volume_bound_min,
            volume_bound_max=self.__data_df.volume_bound_max,
            signature=self.__data_df.pair,
            bar_width=self.__data_df.bar_width
        )

        # Swap the current data with the new data.
        self.source.data = new_data

    def __str__(self):
        x = self.__limits
        header = '{:<60}\n'.format('=' * 60)
        rows = '{:<10} {:<30} {:<20}'.format('Index', 'Key', 'Value')

        for i, (k, v) in enumerate(x.items()):
            rows += '\n' + '{:<10} {:<30} {:<20}'.format(i, k, v)

        pandas_info = '\n' + str(self.__data_df.describe())
        separator = '\n{:<60}'.format('-' * 60)
        footer = '\n{:<60}'.format('=' * 60)

        table = header + rows + separator + pandas_info + footer
        return table


if __name__ == "__main__":
    pass

# vim: ts=4 ft=python nowrap fdm=marker
