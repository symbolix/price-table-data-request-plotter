# Global Imports
import pandas as pd
from bokeh.models import CustomJS

# Local Imports
from os import sys
from os import path

# A crude solution, but should be fixed eventually.
# 'scope' is '<PROJECT_ROOT>'
#       for example: /home/me/dev/my-project
# WARNING: This hack is required to import the local modules from within the current module depth.
scope = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))
sys.path.append(scope)

from coreglobals import get_global_property
from coreglobals import set_global_property
import tools.utils as utils
import tools.indicators as indicators

# from, import * guard.
__all__ = ['my_public_method', 'get_raw_data']

# @pubic function my_public_method() {{{1


def my_public_method():
    """
    A test public method.
    """

    # Test if we have access to the global properties.
    NAMESPACE = get_global_property('APP_NAME') + "." + __name__
    print('{}: Module accessed.'.format(NAMESPACE))
# }}}1

# @public function get_raw_data(source_file, field) {{{1


def get_raw_data(source_file, field):
    """
    Import a dataFrame from a *.csv file.
    """

    # DataSet Import
    df = utils.IO.import_csv_data(source_file)

    # Query a filed such as 'BTC/EUR'
    pair_df = df.loc[df.pair == field].copy()
    # pair_df.drop(['pair'], axis=1, inplace=True)

    # After isolating the required data slice for the pair field, we need to reset the index.
    # Since the pairs are sequentially stored, once a specific pair is removed there will be
    # a gap in the index. For example:
    #   The 'EUR' field is stored from 0 to 287 and the 'USD' field is stored from 288 to 576
    #   within the dataframe. Once the 'EUR' field is removed, the index for the remaining field
    #   needs to be reset.
    pair_df.reset_index(drop=True, inplace=True)

    cols = list(pair_df)
    cols.insert(0, cols.pop(cols.index('date')))

    pair_df = pair_df.loc[:, cols]

    # Return the final data-frame.
    return pair_df
# }}}1

# @public function get_data_container(dataFrame, MA, MACD, drop_last=True) {{{1


def get_data_container(dataFrame, MA=None, MACD=None, drop_last=True):
    """
    A wrapper used to populate a data frame container.

    :param dataFrame (``Pandas Object``): A partially populated pandas dataFrame.
    :param MA (``MA configuration dict``): Configuration object for the MA indicator.
    :param MACD (``MACD configuration dict``): Configuration object for the MACD indicator.
    :param drop_last (``Boolean``): A boolean flag to force a drop on the last element
                                    within the incoming dataFrame.
    """

    if MA is None:
        # Default MA configuration.
        MA = {'type': 'SMA', 'slow_period': 30, 'fast_period': 13}

    if MACD is None:
        # Default MACD configuration.
        MACD = {'slow_period': 30, 'fast_period': 13, 'signal_period': 9}

    local_df = dataFrame.copy()

    if drop_last:
        # Last row contains data from the current 5min. We should not be using the data from the last
        # row since the candle has not closed yet, and the values are likely to keep changing.
        local_df = local_df[:-1]

    x = local_df['close'].values

    if MA['type'] == 'SMA':
        # Calculate the Simple Moving Average slots.

        # local_df['sma_slow'] = local_df['close'].copy().rolling(SMA_SLOW_LENGTH).mean()
        ma_slow = indicators.MA.sma(x, MA['slow_period'])

        # local_df['sma_fast'] = local_df['close'].copy().rolling(SMA_FAST_LENGTH).mean()
        ma_fast = indicators.MA.sma(x, MA['fast_period'])

    elif MA['type'] == 'EMA':
        # Calculate the Exponential Moving Average slots.

        # ema_slow = local_df['close'].ewm(span=EMA_SLOW_LENGTH, adjust=False).mean()
        ma_slow = indicators.MA.ema(x, MA['slow_period'])

        # ema_fast = local_df['close'].ewm(span=EMA_FAST_LENGTH, adjust=False).mean()
        ma_fast = indicators.MA.ema(x, MA['fast_period'])
    else:
        raise Exception('MA configuration error!')

    # Add the MA components to the data-frame.
    local_df['ma_slow'] = ma_slow
    local_df['ma_fast'] = ma_fast

    # Add OHLC bounds
    # These bounds are used to re-fit the y-scale so that all candlesticks are visible within in the current window.
    local_df['candle_bound_min'] = local_df['low']
    local_df['candle_bound_max'] = local_df['high']

    # Calculate and store MACD series.
    macd_fast_ma = indicators.MA.ema(x, MACD['fast_period'])
    macd_slow_ma = indicators.MA.ema(x, MACD['slow_period'])

    macd = macd_fast_ma - macd_slow_ma
    macd_df = pd.DataFrame({"macd": macd})

    # Calculate and store MACD signal and histogram series.
    macd_df['signal'] = macd_df['macd'].ewm(span=MACD['signal_period'], adjust=False).mean()
    macd_df['histogram'] = macd_df['macd'] - macd_df['signal']

    # Calculate and store MACD bounds.
    macd_df['bound_min'] = macd_df.min(axis=1)
    macd_df['bound_max'] = macd_df.max(axis=1)

    local_df['macd'] = macd_df[['macd']]
    local_df['macds'] = macd_df['signal']
    local_df['macdh'] = macd_df['histogram']
    local_df['macd_bound_min'] = macd_df['bound_min']
    local_df['macd_bound_max'] = macd_df['bound_max']

    # Volume Bounds
    local_df['volume_bound_min'] = 0
    local_df['volume_bound_max'] = local_df['volume']

    # LIMITS
    volume_min_limit = local_df['volume_bound_min'].min()
    volume_max_limit = local_df['volume_bound_max'].max()

    macd_min_limit = local_df['macd_bound_min'].min()
    macd_max_limit = local_df['macd_bound_max'].max()

    candles_min_limit = local_df['candle_bound_min'].min()
    candles_max_limit = local_df['candle_bound_max'].max()

    limits = dict(volume_max_limit=volume_max_limit,
                  volume_min_limit=volume_min_limit,
                  macd_min_limit=macd_min_limit,
                  macd_max_limit=macd_max_limit,
                  candles_min_limit=candles_min_limit,
                  candles_max_limit=candles_max_limit)

    return (local_df, limits)
# }}}1

# @public function callback_on_interaction_range_fit(range, sourcem name, target) {{{1


def callback_on_interaction_range_fit(range, source, name='top', target='candle'):
    """
    A callback factory for the CustomJS model.

    :param range (``bokeh range object``): The plot axis object.
    :param source (``ColumnDataSource object ``): Data container.
    :param name (``string``): Name signature for internal identification.
    :param target (``string``): Source to access bounds.
    """
    code = '''
           // Reset previous delayed process.
           clearTimeout(window._autoscale_timeout_''' + name + '''_plot);

           var index = source.data.time,
               target = target,
               low = source.data.''' + target + '''_bound_min,
               high = source.data.''' + target + '''_bound_max,
               start = cb_obj.start,
               end = cb_obj.end,
               min = Infinity,
               max = -Infinity;

           for (var i=0; i < index.length; ++i) {
               if (start <= index[i] && index[i] <= end) {
                   max = Math.max(high[i], max);
                   min = Math.min(low[i], min);
               }
           }

           //console.log(`[''' + name + '''_plot] x_start: ${start}, x_end: ${end}`);
           //console.log(`[''' + name + '''_plot] y_min: ${min}, y_max: ${max}`);

           // New delayed process.
           // Here, 'range' refers to the Y-Range.
           window._autoscale_timeout_''' + name + '''_plot = setTimeout(function() {
               var pad = (max - min) * .05;
               // WARNING: We DO NOT want the lower limit padding on the volume plot.
               if(target === 'volume'){
                    range.start = min;
               }else{
                    range.start = min - pad;
               }
               range.end = max + pad;
           });
        '''
    return CustomJS(args={'range': range, 'source': source, 'target': target}, code=code)
# }}}1

# @public function callback_on_source_change_range_fit(range, sourcem name, target) {{{1


def callback_on_source_change_range_fit(args=dict()):
    """
    A callback factory for the CustomJS model.

    :param range (``bokeh range object``): The plot axis object.
    :param source (``ColumnDataSource object ``): Data container.
    :param name (``string``): Name signature for internal identification.
    :param target (``string``): Source to access bounds.
    """
    code = '''
        // Reset previous delayed process.
        clearTimeout(window.my_autoscale_timeout);

        var index = cb_obj.data.time,
            low = cb_obj.data.candle_bound_min,
            high = cb_obj.data.candle_bound_max,
            start = xr.start,
            end = xr.end,
            min = Infinity,
            max = -Infinity,
            signature = cb_obj.data.signature[0];

        for (var i=0; i < index.length; ++i) {
            if (start <= index[i] && index[i] <= end) {
                max = Math.max(high[i], max);
                min = Math.min(low[i], min);
            }
        }

        //console.log(`[selected_currency_pair: ${signature}] x_start: ${start}, x_end: ${end}`);
        //console.log(`[selected_currency_pair: ${signature}] y_min: ${min}, y_max: ${max}`);

        // New delayed process.
        window.my_autoscale_timeout = setTimeout(function() {
            var pad = (max - min) * .05;
            yr.start = min - pad;
            yr.end = max + pad;
        });
    '''
    return CustomJS(args=args, code=code)
# }}}1

# @public function callback_on_source_change_range_fit2(range, sourcem name, target) {{{1


def callback_on_source_change_range_fit2(args=dict()):
    """
    A callback factory for the CustomJS model.

    :param range (``bokeh range object``): The plot axis object.
    :param source (``ColumnDataSource object ``): Data container.
    :param name (``string``): Name signature for internal identification.
    :param target (``string``): Source to access bounds.
    """
    code = '''
        // Reset previous delayed process.
        clearTimeout(window.my_autoscale_timeout);

        var index = cb_obj.data.time,
        candlestick_low = cb_obj.data.candle_bound_min,
        candlestick_high = cb_obj.data.candle_bound_max,
        candlestick_start = candlestick_xr.start,
        candlestick_end = candlestick_xr.end,
        volume_low = cb_obj.data.volume_bound_min,
        volume_high = cb_obj.data.volume_bound_max,
        volume_start = volume_xr.start,
        volume_end = volume_xr.end,
        macd_low = cb_obj.data.macd_bound_min,
        macd_high = cb_obj.data.macd_bound_max,
        macd_start = macd_xr.start,
        macd_end = macd_xr.end,
        candlestick_min = Infinity,
        candlestick_max = -Infinity,
        volume_min = Infinity,
        volume_max = -Infinity,
        macd_min = Infinity,
        macd_max = -Infinity,
        signature = cb_obj.data.signature[0];

        for (var i=0; i < index.length; ++i) {
            if (candlestick_start <= index[i] && index[i] <= candlestick_end) {
                candlestick_max = Math.max(candlestick_high[i], candlestick_max);
                candlestick_min = Math.min(candlestick_low[i], candlestick_min);
            }

            if (volume_start <= index[i] && index[i] <= volume_end) {
                volume_max = Math.max(volume_high[i], volume_max);
                volume_min = Math.min(volume_low[i], volume_min);
            }

            if (macd_start <= index[i] && index[i] <= macd_end) {
                macd_max = Math.max(macd_high[i], macd_max);
                macd_min = Math.min(macd_low[i], macd_min);
            }
        }

        //console.log(`*[selected_currency_pair: ${signature}] candlestick: x_start: ${candlestick_start}, x_end: ${candlestick_end}`);
        //console.log(`*[selected_currency_pair: ${signature}] candlestick: y_min: ${candlestick_min}, y_max: ${candlestick_max}`);

        //console.log(`*[selected_currency_pair: ${signature}] volume: x_start: ${volume_start}, x_end: ${volume_end}`);
        //console.log(`*[selected_currency_pair: ${signature}] volume: y_min: ${volume_min}, y_max: ${volume_max}`);

        //console.log(`*[selected_currency_pair: ${signature}] macd: x_start: ${macd_start}, x_end: ${macd_end}`);
        //console.log(`*[selected_currency_pair: ${signature}] macd: y_min: ${macd_min}, y_max: ${macd_max}`);

        // New delayed process.
        window.my_autoscale_timeout = setTimeout(function() {
            var candlestick_pad = (candlestick_max - candlestick_min) * .05;
            candlestick_yr.start = candlestick_min - candlestick_pad;
            candlestick_yr.end = candlestick_max + candlestick_pad;

            var volume_pad = (volume_max - volume_min) * .05;
            // WARNING: We DO NOT want the lower limit padding on the volume plot.
            volume_yr.start = volume_min;
            volume_yr.end = volume_max + volume_pad;

            var macd_pad = (macd_max - macd_min) * .05;
            macd_yr.start = macd_min - macd_pad;
            macd_yr.end = macd_max + macd_pad;
        });
    '''
    return CustomJS(args=args, code=code)
# }}}1

# @public function get_limits(limits, padding_sca,le) {{{1


def get_limits(limits, padding_scale=0.05):
    # ;------------------;
    # ; Calculate Limits ;
    # ;------------------;

    # Calculate Volume Limits
    volume_upper_limit = limits['volume_max_limit']
    volume_lower_limit = limits['volume_min_limit']

    # We need to clamp the lower limit ...
    volume_lower_limit = max(min(volume_lower_limit, 999999999), 0)

    # Calculate Candlestick Limits
    candlestick_upper_limit = limits['candles_max_limit']
    candlestick_lower_limit = limits['candles_min_limit']

    # Calculate MACD Limits
    macd_upper_limit = limits['macd_max_limit']
    macd_lower_limit = limits['macd_min_limit']

    # ;--------------------;
    # ; Calculate Paddings ;
    # ;--------------------;

    # A bit of padding for the the volume bounds.
    volume_padding = abs(volume_upper_limit - volume_lower_limit) * padding_scale

    # A bit of padding for the the candlestick bounds.
    candlestick_padding = abs(candlestick_upper_limit - candlestick_lower_limit) * padding_scale

    # A bit of padding for the the macd bounds.
    macd_padding = abs(macd_upper_limit - macd_lower_limit) * padding_scale

    print(';\nvolume_upper_limit: {}, volume_lower_limit: {}, volume_padding: {}'.format(
        volume_upper_limit, volume_lower_limit, volume_padding))

    print('candlestick_upper_limit: {}, candlestick_lower_limit: {}, candlestick_padding: {}'.format(
        candlestick_upper_limit, candlestick_lower_limit, candlestick_padding))

    print('macd_upper_limit: {}, macd_lower_limit: {}, macd_padding: {}\n;'.format(
        macd_upper_limit, macd_lower_limit, macd_padding))

    # ;----------------;
    # ; Apply Paddings ;
    # ;----------------;

    volume_upper_limit += volume_padding

    candlestick_upper_limit += candlestick_padding
    candlestick_lower_limit -= candlestick_padding

    macd_upper_limit += macd_padding
    macd_lower_limit -= macd_padding

    return (volume_lower_limit, volume_upper_limit,
            candlestick_lower_limit, candlestick_upper_limit,
            macd_lower_limit, macd_upper_limit)
# }}}1

# vim: ts=4 ft=python nowrap fdm=marker
