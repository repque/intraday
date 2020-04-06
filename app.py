from __future__ import print_function

import logging
import logging.config

from   core import Config, run
from   coroutines import initial_breakout, time_based, stop_loss, stop_profit
from   backtest import gen_csv_data

if __name__ == '__main__':
    # init logging
    logging.config.fileConfig("logging.conf")

    config1 = Config( symbol='IVV', equity_pct=0.10, 
                 entry_rules=[initial_breakout(45)], 
                 exit_rules =[time_based(14,15), 
                              stop_loss(0.02), 
                              stop_profit(0.02)] )

    configs = [config1]

    run( configs, interval=0, dataProvider=gen_csv_data )