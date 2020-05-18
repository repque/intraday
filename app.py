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

def run( configs, live=False, specific_day=None, cash=25000, commission=0, interval=1, daily_charts=True, charts_folder='.\\charts\\testing' ):
    ''' main event loop 

        if 'live' mode is False, we're testing and running against previously recorded data.
        The 'specific_day' argument allows to run against a specific pre-recorded day. By default, all data is replayed
    '''
    if not live:
        interval = 0 # no need to sleep when testing
        gen_test_data = partial( gen_csv_data, specific_day=specific_day ) # pass the specific_day argument to the coroutine
        dataProvider=gen_test_data
    else:
        dataProvider=gen_time_series

    pnl = Pnl()
    pnl.initialize( configs, cash, commission )

    strategies = [ Strategy( config, dataProvider, pnl, live=live ) for config in configs ]

    while True:
        active_strategies = [ strategy for strategy in strategies if strategy.active ]
        if not active_strategies:
            logging.debug( 'All Done!' )
            logging.info( pnl.get_report() )
            utils.plot( pnl, daily_charts, specific_day is None, charts_folder )
            break # we're done
        
        for strategy in active_strategies:
            signal = strategy.tick()
            if signal:
                trade = execute_signal( signal )
                if trade:
                    pnl.handle_fill( trade )

                
        time.sleep( interval * 60 )

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
    live = False
    specific_day = None #datetime.datetime( 2020, 4, 1 )
    day_by_day = True #Change if you want to process whole set instead of day by day

    if not(live):
        charts_folder = '.\\charts\\testing'
        if not(specific_day):
            if (day_by_day):
                #Process one day at a time, export and combine charts                
                df = pd.read_csv('.\\data\\' + configs[0].symbol + '.csv', header=None, index_col=0)
                df.index = pd.to_datetime(df.index, format='%Y-%m-%d %H:%M:%S')
                df['date'] = df.index.date     
                dates = df['date'].unique()
                for specific_day in dates:
                    run( configs, live, specific_day = datetime.datetime.combine(specific_day, datetime.datetime.min.time()), daily_charts = True, charts_folder = charts_folder )
                    if len(configs) > 1:
                        utils.combine_charts(charts_folder, combine_pattern = specific_day)                    
                for eachconfig in configs:
                    utils.combine_charts(charts_folder, combine_pattern = eachconfig.symbol)
            else:
                #Process whole set of days at once
                run( configs, live, specific_day = None, daily_charts = True, charts_folder = charts_folder )
        else:
            #Process for specific day
            run( configs, live, specific_day = specific_day, daily_charts = True, charts_folder = charts_folder )
    else:
        #Run live
        charts_folder = '.\\charts\\live'
        run( configs, live, specific_day = None, daily_charts = True, charts_folder = charts_folder )