from __future__ import print_function

import logging
import logging.config
import time
import session as s

from   core import Config, Strategy, execute_signal
from   coroutines import initial_breakout, time_based, stop_loss, stop_profit
from   data_providers import gen_csv_data, gen_time_series
from   positions import Pnl

def run( configs, interval=1, dataProvider=gen_time_series, cash=9000, commission=0.00 ):
    ''' main event loop 

        interval is in minutes, it defines how long to wait before requesting next data point, for testing set it to 0
        dataProvider is a generator function which generates data points for the symbol

    '''
    session = s.Session()
    session.login()
    pnl = Pnl()
    pnl.initialize( configs, cash, commission )

    strategies = [ Strategy( config, dataProvider, pnl ) for config in configs ]

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

    config1 = Config( symbol='FAS', equity_pct=0.50, 
                 entry_rules=[initial_breakout(1)], 
                 exit_rules =[time_based(14,15), 
                              stop_loss(0.02), 
                              stop_profit(0.04)] )

    config2 = Config( symbol='FAZ', equity_pct=0.50, 
                 entry_rules=[initial_breakout(1)], 
                 exit_rules =[time_based(14,15), 
                              stop_loss(0.02), 
                              stop_profit(0.04)] )

    configs = [config1,config2]

    run( configs, interval=1, dataProvider=gen_time_series )