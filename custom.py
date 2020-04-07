from __future__ import print_function
import datetime
import logging

from   core import Trade
from   positions import Pnl

def get_data_point( symbol ):
    ''' TODO: pull current data point here from your data provider for the symbol '''
    
    # get real data here
    price      = 50
    time_stamp = datetime.datetime.now() # IMPORTANT - time stamp has to increase on subsequent calls, going from 9:30 to 16:00
    
    return time_stamp, price

def execute_signal( signal ):
    ''' TODO: submit signal for execution and record completion '''

    pnl = Pnl()
    if signal.is_entry:
        needed_cash = pnl.starting_equity * signal.equity_pct
        if needed_cash > pnl.available_cash:
            logging.warn( 'Not enough cash to open position for {}: need: {}, have:{}. Skipping signal ...', signal.symbol, needed_cash, pnl.available_cash )
            return None

        qty = needed_cash // signal.point.price
        qty = qty - qty % 10
    else:
        position = pnl.positions[ signal.symbol ]
        qty = position.qty
        
    logging.debug( 'Executing signal: {}'.format( signal ) )

    price = signal.point.price # TODO: change this to the actual fill price

    return Trade( signal, qty, price )