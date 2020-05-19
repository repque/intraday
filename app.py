from __future__ import print_function

import datetime
from   functools import partial
import logging
import logging.config
import time

from   core import Config, Strategy, execute_signal
from   coroutines import initial_breakout, time_based, stop_loss, stop_profit
from   data_providers import gen_csv_data, gen_time_series
from   positions import Pnl
import utils
import pandas as pd

def run( configs, live=False, specific_day=None, cash=25000, commission=0, interval=1, save_charts=True ):
    ''' main event loop 

        if 'live' mode is False, we're testing and running against previously recorded data.
        The 'specific_day' argument allows to run against a specific pre-recorded day. By default, all data is replayed
    '''
    if not live:
        interval = 0 # no need to sleep when testing
        gen_test_data = partial( gen_csv_data, specific_day=specific_day ) # pass the specific_day argument to the coroutine
        dataProvider=gen_test_data
        charts_folder='.\\charts\\testing'
    else:
        dataProvider=gen_time_series
        charts_folder = '.\\charts\\live'

    pnl = Pnl()
    pnl.initialize( configs, cash, commission )

    strategies = [ Strategy( config, dataProvider, pnl, live=live ) for config in configs ]

    while True:
        active_strategies = [ strategy for strategy in strategies if strategy.active ]
        if not active_strategies:
            logging.debug( 'All Done!' )
            logging.info( pnl.get_report() )
            utils.plot( pnl, save_charts, specific_day is None, charts_folder )
            break # we're done
        
        for strategy in active_strategies:
            signal = strategy.tick()
            if signal:
                trade = execute_signal( signal )
                if trade:
                    pnl.handle_fill( trade )

                
        time.sleep( interval * 60 )

def run_dates (configs, save_charts):
    '''Process one day at a time, export and combine charts'''
    charts_folder='.\\charts\\testing' 
    dates = get_dates( configs[0].symbol )
    for specific_day in dates:
        run( configs, live = False, specific_day = datetime.datetime.combine(specific_day, datetime.datetime.min.time()), save_charts = save_charts )
        if (len(configs)) > 1 & save_charts:
            utils.combine_charts(charts_folder, combine_pattern = specific_day)                    
    if (save_charts):
        for eachconfig in configs:
            utils.combine_charts(charts_folder, combine_pattern = eachconfig.symbol)

def get_dates (symbol):
    '''Get unique dates from symbol CSV'''
    df = pd.read_csv('.\\data\\' + symbol + '.csv', header=None, index_col=0)
    df.index = pd.to_datetime(df.index, format='%Y-%m-%d %H:%M:%S')
    df['date'] = df.index.date     
    return df['date'].unique()
          
if __name__ == '__main__':
    # init logging
    logging.config.fileConfig(".\\settings\\logging.conf")

    config1 = Config( symbol='IVV', equity_pct=0.50, 
                 entry_rules=[initial_breakout(45)], 
                 exit_rules =[time_based(14,15), 
                              stop_loss(0.02), 
                              stop_profit(0.02)] )

    configs = [config1]

    # to replay specific day, set the argument to datetime instance:
    # for example: specific_day = datetime.datetime( 2020, 4, 2 )
    #run( configs, live = False, specific_day = datetime.datetime( 2020, 4, 2 ), save_charts = True )
    run_dates (configs, save_charts = True)