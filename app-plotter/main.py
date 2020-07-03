# Global Imports
from functools import partial
import os
import pandas as pd
import numpy as np
import datetime

# Bokeh Imports
from bokeh import __version__ as bokeh_version
from bokeh.layouts import row, column, layout
from bokeh.models import ColumnDataSource, Select, Range1d, TableColumn, DataTable
from bokeh.plotting import curdoc, figure
from bokeh.models import Button, HoverTool, DatetimeTickFormatter
from bokeh.models.tools import WheelZoomTool, PanTool, CrosshairTool, BoxZoomTool, ResetTool, SaveTool, BoxSelectTool
from bokeh.models.widgets.tables import DateFormatter
from bokeh.models.callbacks import CustomJS
from bokeh import events

# Local Imports
from coreglobals import get_global_property
from coreglobals import set_global_property
import tools.utils as utils
import tools.indicators as indicators
import tools.wrappers as wrappers
from tools.timezones import ZonesList as tzl
from tools.container import MyUpdater

# Prototype Usage
'''
# Pubic method(s) on the `core` section of the module are accessible directly.
foo.my_public_method()

# Public method(s) on the `movingaverages` section of the module are accessible through
# an extra namespace.
foo.BAR.my_public_method()
'''

# Globals
# Setup initial global propery.
set_global_property('APP_NAME', 'app-plotter')

REL_DATA_PATH = 'data'
RAW_CSV_FILE = 'data_{}.csv'
OS_SEPARATOR = '/'
PROJECT_ROOT_SEARCH_DEPTH = 0
EPOCH = datetime.datetime.utcfromtimestamp(0)

# Bokeh canvas width.
PLOT_WIDTH = 900

# Indicator Configuration
MACD_FAST_LENGTH = 13
MACD_SLOW_LENGTH = 30
MACD_SIGNAL_LENGTH = 9
SMA_FAST_LENGTH = 13
SMA_SLOW_LENGTH = 30
EMA_FAST_LENGTH = 13
EMA_SLOW_LENGTH = 30

# Drop-down menu components.
timezone_labels = ['({}) {}'.format(zone[0], zone[1]) for zone in tzl]
timezone_signatures = [zone[2] for zone in tzl]
timezone_lookup = {k: v for k, v in zip(timezone_labels, timezone_signatures)}

# Construct the path required for the local data access.
current_file_path_list = os.path.join(os.path.dirname(__file__)).split(OS_SEPARATOR)
project_root_path_list = current_file_path_list[:len(current_file_path_list) - PROJECT_ROOT_SEARCH_DEPTH]
project_root_path = (OS_SEPARATOR).join(project_root_path_list)
full_csv_data_file_path = '{}/{}/{}'.format(project_root_path, REL_DATA_PATH, RAW_CSV_FILE)

# Data Container
source = ColumnDataSource(dict(
    index=[],
    time=[],
    open=[],
    high=[],
    low=[],
    close=[],
    candle_wick_color=[],
    candle_body_fill_color=[],
    candle_body_line_color=[],
    candle_bound_min=[],
    candle_bound_max=[],
    ma_slow=[],
    ma_fast=[],
    macd=[],
    macds=[],
    macdh=[],
    macd_bound_min=[],
    macd_bound_max=[],
    volume=[],
    volume_bound_min=[],
    volume_bound_max=[],
    signature=[],
    bar_width=[]
))

# ;----------;
# ; PLOT (1) ;
# ;----------;
# {{{1
tooltips_top = [
    ('open', '@open{0.2f}'),
    ('high', '@high{0.2f}'),
    ('low', '@low{0.2f}'),
    ('close', '@close{0.2f}'),
    ('ma-slow', '@ma_slow{0.2f}'),
    ('ma-fast', '@ma_fast{0.2f}'),
    ('time', '@time{%F %T}')
]

box_zoom = BoxZoomTool()
pan_tool = PanTool(dimensions='width')
wheel_zoom = WheelZoomTool()
reset_tool = ResetTool()
crosshair = CrosshairTool()
save = SaveTool()
hover_tool = HoverTool(
    tooltips=tooltips_top,
    formatters={'@time': 'datetime'}
)
box_selection = BoxSelectTool()

tools_top = [
    box_zoom,
    pan_tool,
    wheel_zoom,
    reset_tool,
    crosshair,
    save,
    hover_tool,
    box_selection
]

p1 = figure(plot_width=PLOT_WIDTH,
            plot_height=340,
            tools=tools_top,
            x_axis_type='datetime',
            sizing_mode='stretch_width',
            tooltips=tooltips_top,
            active_drag=pan_tool,
            active_scroll=wheel_zoom,
            active_inspect=None,
            y_axis_location="right")

# Price Line
# p1.line(x='time', y='close', alpha=0.5, line_width=1, color='navy', source=source)

# MA Slow
p1.line(x='time', y='ma_slow', color='#6cbf40', source=source)

# MA Fast
p1.line(x='time', y='ma_fast', color='#5740bf', source=source)

# Plot Candlesticks (bokeh-candlestick)
# Wicks (High/Low)
p1.segment(x0='time', y0='high', x1='time', y1='low', source=source, color='candle_wick_color')

# Open and close
p1.vbar(x='time', width='bar_width', top='open', bottom='close', source=source,
        fill_color='candle_body_fill_color', line_color='candle_body_line_color', line_width=0.1)

p1.xaxis.formatter = DatetimeTickFormatter(
    days=["%m/%d %H:%M"],
    months=["%m/%d %H:%M"],
    hours=["%m/%d %H:%M"],
    minutes=["%m/%d %H:%M"]
)

p1.y_range = Range1d(0, 1)
p1.x_range = Range1d(0, 1)
# }}}1

# ;----------;
# ; PLOT (2) ;
# ;----------;
# {{{1
tooltips_bottom = [
    ('histogram', '@macdh{0.2f}'),
    ('signal', '@macds{0.2f}'),
    ('macd', '@macd{0.2f}'),
    ('time', '@time{%F}')
]

hover_tool_bottom = HoverTool(
    tooltips=tooltips_bottom,
    formatters={'@time': 'datetime'}
)

tools_bottom = [
    hover_tool_bottom,
]

p2 = figure(plot_width=PLOT_WIDTH,
            plot_height=140,
            tools=tools_bottom,
            x_range=p1.x_range,
            x_axis_type='datetime',
            sizing_mode='stretch_width',
            y_axis_location='right')

# MACD Line (blue)
p2.line(x='time', y='macd', color='#33C9FF', source=source)

# MACD Signal (orange): macds
p2.line(x='time', y='macds', color='#FF5733', source=source)

# MACD Histogram: macdh
p2.vbar(x='time', bottom=0, top='macdh', width='bar_width', fill_color='#000000', alpha=1, source=source)

p2.xaxis.formatter = DatetimeTickFormatter(
    days=["%m/%d/%Y %H:%M"],
    months=["%m/%d/%Y %H:%M"],
    hours=["%m/%d/%Y %H:%M"],
    minutes=["%m/%d/%Y %H:%M"]
)

p2.y_range = Range1d(0, 1)
# }}}1

# ;----------;
# ; PLOT (3) ;
# ;----------;
# {{{1
tooltips_mid = [
    ('volume', '@volume{0.2f}'),
    ('time', '@time{%F}')
]

hover_tool_mid = HoverTool(
    tooltips=tooltips_mid,
    formatters={'@time': 'datetime'}
)

tools_mid = [
    hover_tool_mid,
]

p3 = figure(plot_width=PLOT_WIDTH,
            plot_height=140,
            tools=tools_mid,
            x_range=p1.x_range,
            x_axis_type='datetime',
            sizing_mode='stretch_width',
            y_axis_location='right')

# Volume Bars
p3.vbar(x='time', bottom=0, top='volume', width='bar_width', fill_color='#000000', alpha=1, source=source)

p3.xaxis.formatter = DatetimeTickFormatter(
    days=["%m/%d/%Y %H:%M"],
    months=["%m/%d/%Y %H:%M"],
    hours=["%m/%d/%Y %H:%M"],
    minutes=["%m/%d/%Y %H:%M"]
)

p3.y_range = Range1d(0, 1000)
# }}}1

# ;------------;
# ; Data Table ;
# ;------------;
# {{{1
columns = [TableColumn(field="time",
                       title="Time",
                       formatter=DateFormatter(format="%m/%d/%Y %H:%M")),
           TableColumn(field="open", title="Open"),
           TableColumn(field="high", title="High"),
           TableColumn(field="low", title="Low"),
           TableColumn(field="close", title="Close"),
           TableColumn(field="volume", title="Volume")]
# }}}1

# Intro
print('\nGeneric Python CLI Application | {} | v{}\n'.format(
    get_global_property('APP_NAME'),
    get_global_property('APP_VERSION')))

# Test utilities.
utils.my_public_method()
utils.IO.my_public_method()

# Test indicators.
indicators.my_public_method()
indicators.MA.my_public_method()

print(';\npandas version: {}'.format(pd.__version__))
print('numpy version : {}'.format(np.__version__))
print('bokeh version : {}\n;'.format(bokeh_version))

# ;----;
# ; UI ;
# ;----;
js_debug = """
    var xr_start = plot.x_range.start;
    var xr_end = plot.x_range.end;

    console.log(`[debug] x_window_range_start: ${xr_start}`);
    console.log(`[debug] x_window_range_end: ${xr_end}`);
"""
js_debug_cb = CustomJS(args=dict(plot=p1, source=source), code=js_debug)

button_reload = Button(label="Reload")
button_debug = Button(label="Debug")

button_debug.js_on_click(js_debug_cb)

SMA, EMA = 'SMA (13/30)', 'EMA (13/30)'

mavg = Select(title='Moving Average', value=SMA, options=[SMA, EMA])
timezone = Select(title='Time Zone', value='(UTC+01:00) London', options=timezone_labels)
pair = Select(title='Currency Pair', value='EUR', options=['EUR', 'USD'])
asset = Select(title='Asset', value='BTC',
               options=['BTC', 'ETH', 'ZEC', 'LTC', 'XMR', 'DASH', 'EOS', 'ETC', 'XLM', 'XRP'])
timeframe = Select(title='Timeframe', value='5m', options=['5m', '15m', '1h', '4h', '1D'])

column_mavg = column(mavg, width=130)
column_timezone = column(timezone, width=450)
column_pair = column(pair, width=100)
column_asset = column(asset, width=100)
column_timeframe = column(timeframe, width=100)

inputs = row([column_mavg, column_timezone, column_pair, column_asset, column_timeframe], width=PLOT_WIDTH, height=60)
inputs.sizing_mode = "fixed"

buttons = row([button_reload, button_debug], width=200, height=50)
buttons.sizing_mode = "fixed"

full_table = DataTable(editable=False, columns=columns, source=source, width=PLOT_WIDTH, height=200)

# ;-----------;
# ; Callbacks ;
# ;-----------;

# These callbacks are used to update the y-scale on the plot (name) based on the min/max bounds of the currently
# visible data (target). This provides optimum canvas usage where we have the lowest value at the bottom of the
# chart and the highest value at the top.


def exec_reset():
    # {{{1
    """
    Function that returns a Python callback to reset the plots.
    """
    def python_callback(event):
        print('__RESET__')
        update(task='test:main:reset', timeframe='5m', axis_reset=True, active=False)
    return python_callback
# }}}1


callback_range_top = wrappers.callback_on_interaction_range_fit(
    p1.y_range, source, name='top', target='candle')

callback_range_bottom = wrappers.callback_on_interaction_range_fit(
    p2.y_range, source, name='bottom', target='macd')

callback_range_middle = wrappers.callback_on_interaction_range_fit(
    p3.y_range, source, name='middle', target='volume')

callback_data_update = wrappers.callback_on_source_change_range_fit2(
    args=dict(candlestick_yr=p1.y_range, candlestick_xr=p1.x_range,
              volume_yr=p3.y_range, volume_xr=p3.x_range,
              macd_yr=p2.y_range, macd_xr=p2.x_range))

# Attach callbacks.
p1.x_range.js_on_change('start', callback_range_top)
p2.x_range.js_on_change('start', callback_range_bottom)
p3.x_range.js_on_change('start', callback_range_middle)

source.js_on_change('data', callback_data_update)

p1.on_event(events.Reset, exec_reset())

# ;-----------------------;
# ; Updater Configuration ;
# ;-----------------------;
# Prepare Configurations
# Please note that the 'ref' is a direct reference link to the widget associated with
# the configuration object.
ma_config = dict(
    type=mavg.value.split()[0],
    slow_period=SMA_SLOW_LENGTH if mavg.value == 'SMA' else EMA_SLOW_LENGTH,
    fast_period=SMA_FAST_LENGTH if mavg.value == 'EMA' else EMA_FAST_LENGTH,
)

macd_config = dict(
    slow_period=MACD_SLOW_LENGTH,
    fast_period=MACD_FAST_LENGTH,
    signal_period=MACD_SIGNAL_LENGTH,
)

# Serialize the plot objects so we can match plots to limits.
# This is the way of passing plot objetcs to the Updater instance by reference.
serialized_plots = {
    'candlestick': {
        'plot': p1,
        'limits': ['lower', 'upper']
    },
    'volume': {
        'plot': p3,
        'limits': ['lower', 'upper']
    },
    'macd': {
        'plot': p2,
        'limits': ['lower', 'upper']
    }
}

# Serialize the widget objects.
# This is the way of passing widgets to the Updater instance by reference.
serialized_widgets = {
    'asset': asset,
    'pair': pair,
    'mavg': mavg,
    'timezone': timezone,
    'timeframe': timeframe
}

serialized_configs = {
    'ma': ma_config,
    'macd': macd_config
}

update = MyUpdater(
    plots=serialized_plots,
    widgets=serialized_widgets,
    configs=serialized_configs,
    file=full_csv_data_file_path,
    source=source)


def switch_ma(ref, config, data):
    # {{{1
    '''
    This is a container callback to switch between different type of moving averages.
    The internal task is a passive task, meaning no extra data import stages are needed.
    '''
    print('[DEBUG] Callback:Wrangler -> {}'.format(ref.value))

    x = data['close'].values

    if ref.value.split()[0] == 'SMA':
        # Calculate the Simple Moving Average slots.
        ma_slow = indicators.MA.sma(x, config['slow_period'])
        ma_fast = indicators.MA.sma(x, config['fast_period'])
    elif ref.value.split()[0] == 'EMA':
        # Calculate the Exponential Moving Average slots.
        ma_slow = indicators.MA.ema(x, config['slow_period'])
        ma_fast = indicators.MA.ema(x, config['fast_period'])
    else:
        raise Exception('MA configuration error!')

    # Update the MA components within the data-frame.
    data['ma_slow'] = ma_slow
    data['ma_fast'] = ma_fast
# }}}1


# WARNING: To fix the sync issue between the mavg and pair on pair change, we have to
# pass the 'switch_ma' callback here.
pair.on_change(
    'value', lambda attr, old, new: update(task='test:select:pair', cb=switch_ma, axis_reset=False, active=True))

asset.on_change(
    'value', lambda attr, old, new: update(task='test:select:asset', cb=switch_ma, axis_reset=False, active=True))

mavg.on_change(
    'value', lambda attr, old, new: update(task='test:select:mavg', cb=switch_ma, axis_reset=False, active=False))

timezone.on_change(
    'value', lambda attr, old, new: update(
        task='test:select:timezone', axis_reset=False, active=False))

timeframe.on_change(
    'value', lambda attr, old, new: update(
        task='test:select:timeframe', cb=switch_ma, axis_reset=True, active=True))

button_reload.on_click(partial(update, task='test:reload', cb=switch_ma, axis_reset=True, active=True))

# Providing a timeframe different to the one supplied at instance time will force
# an 'active=True' state.

# ;--------;
# ; Layout ;
# ;--------;

dashboard_layout = layout([
    [inputs],
    [p1],
    [p3],
    [p2],
    [full_table],
    [buttons],
], sizing_mode='stretch_width')

update(task='test:main:init', timeframe='5m', axis_reset=True, active=True)

curdoc().add_root(dashboard_layout)
curdoc().title = "Request Plotter"

# vim: ts=4 ft=python nowrap fdm=marker
