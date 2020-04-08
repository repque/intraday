from __future__ import print_function
from   collections import namedtuple
import datetime
import logging
import time

from   coroutines import time_based
from   custom import submit_order
from   positions import Pnl

Point = namedtuple( 'Point', ['time_stamp', 'price'] )


class Strategy( object ):
    
    def __init__( self, config, dataProvider, pnl ):
        self.time_series = dataProvider( config.symbol )
        self.config      = config
        self.in_position = False
        self.active      = True
        self.eod_exit    = time_based( 15, 59 ) # end-of-day exit hard-coded rule
        self.pnl         = pnl

    def tick( self ):
        ''' get the next data point and process it '''
        try:
            point = next( self.time_series )
            
            # skip after-market data
            if point.time_stamp.hour > 15:
                return None

            # default exit at eod, if still in position
            eod_exit = self.eod_exit.send( point )
            if eod_exit and self.in_position:
                self.in_position = False
                return eod_exit
            
            # apply entry/exit rules
            if self.in_position:
                signal = self.config.run_exit_rules( point )
            else:
                signal = self.config.run_entry_rules( point )
            
            # if signal is generated - return it for execution    
            if signal:
                self.in_position = signal.is_entry                
                return signal 
            
            # track mtm pnl in response to market data changes
            self.pnl.market_data_update( self.config.symbol, point )

        except StopIteration:
            self.active = False
            logging.debug('{} finished.'.format ( self.config.symbol ) )

        except Exception as ex:
            # if any exception has occured, the strategy is inactivated
            self.active = False
            logging.error( '{} setting active to False.'.format ( self.config.symbol ) )


class Config( object ):
    
    def __init__( self, symbol, equity_pct, entry_rules, exit_rules ):
        self.equity_pct  = equity_pct
        self.entry_rules = entry_rules
        self.exit_rules  = exit_rules
        self.symbol      = symbol
        
    def run_exit_rules( self, point ):
        for func in self.exit_rules:
            result = func.send( point )
            if result: # if any exit rule matches
                result.is_entry = False
                result.symbol   = self.symbol
                return result
        
    def run_entry_rules( self, point ):
        for func in self.entry_rules:
            result = func.send( point )
            if result: # if any entry rule matches
                result.is_entry = True
                result.symbol   = self.symbol
                result.equity_pct = self.equity_pct
                return result

class Trade( object ):
    
    def __init__( self, signal, qty, price ):
        self.symbol     = signal.symbol
        self.qty        = qty
        self.price      = price
        self.is_entry   = signal.is_entry
        
    def __repr__(self):
        return "<{klass} {attrs}>".format(
            klass=self.__class__.__name__,
            attrs=" ".join("{}={!r}".format(k, v) for k, v in self.__dict__.items()),
            )

def execute_signal( signal ):
    ''' submit signal for execution and record completion '''

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

    fill_price = submit_order( signal.symbol, qty, signal.is_entry )

    return Trade( signal, qty, fill_price or signal.point.price )