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

def run( configs, live=False, specific_day=None, cash=25000, commission=0.01 ):
    ''' main event loop 

        if 'live' mode is False, we're testing and running against previously recorded data.
        The 'specific_day' argument allows to run against a specific pre-recorded day. By default, all data is replayed
    '''
    if not live:
        interval=0  # in test mode, no need to sleep, just run
        gen_test_data = partial( gen_csv_data, specific_day=specific_day ) # pass the specific_day argument to the coroutine
        dataProvider=gen_test_data
    else:
        interval=1, # in live mode, how many minutes to sleep between requesting next data point
        dataProvider=gen_time_series

    pnl = Pnl()
    pnl.initialize( configs, cash, commission )

    strategies = [ Strategy( config, dataProvider, pnl, live=live ) for config in configs ]

    while True:
        active_strategies = [ strategy for strategy in strategies if strategy.active ]
        if not active_strategies:
            logging.debug( 'All Done!' )
            logging.info( pnl.get_report() )
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
    run( configs, live = False, specific_day = None )