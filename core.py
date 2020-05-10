from __future__ import print_function
from   collections import namedtuple
import datetime
import logging
import time

from   coroutines import time_based
from   custom import submit_order
from   positions import Pnl
import utils 
import pandas as pd

Point = namedtuple( 'Point', ['time_stamp', 'price'] )


class Strategy( object ):
    
    def __init__( self, config, dataProvider, pnl, live=False ):
        self.time_series = dataProvider( config.symbol )
        self.config      = config
        self.in_position = False
        self.active      = True
        self.eod_exit    = time_based( 15, 59 ) # end-of-day exit hard-coded rule
        self.pnl         = pnl
        self.live        = live # are we running in Live mode or in Test mode?
        self.all_points  = []

        # these could come from config eventually
        start_hour = 9
        start_minute = 30

        end_hour = 16
        end_minute = 0

        # convert to minutes
        self.start_time = int(start_hour)*60 + int(start_minute)
        self.end_time   = int(end_hour)*60   + int(end_minute)

    def tick( self ):
        ''' get the next data point and process it '''
        try:
            point = next( self.time_series )

            # skip pre-market and after-market data
            current_time =  point.time_stamp.hour*60 + point.time_stamp.minute

            if  current_time < self.start_time or current_time >= self.end_time:
                return None

            self.all_points.append( point )
            df = pd.DataFrame( self.all_points, columns=Point._fields )

            if self.live:
                utils.save_point( self.config.symbol, point )
            
            # track mtm pnl in response to market data changes
            self.pnl.market_data_update( self.config.symbol, point )

            # default exit at eod, if still in position
            eod_exit = self.eod_exit.send( (point, df) )
            if eod_exit and self.in_position:
                self.in_position = False
                return eod_exit
            
            # apply entry/exit rules
            if self.in_position:
                signal = self.config.run_exit_rules( point, df )
            else:
                signal = self.config.run_entry_rules( point, df )
            
            # if signal is generated - return it for execution    
            if signal:
                self.in_position = signal.is_entry                
                return signal 

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
        
    def run_exit_rules( self, point, df ):
        for func in self.exit_rules:
            result = func.send( (point, df) )
            if result: # if any exit rule matches
                result.is_entry = False
                result.symbol   = self.symbol
                return result
        
    def run_entry_rules( self, point, df ):
        for func in self.entry_rules:
            result = func.send( (point, df) )
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
        self.time_stamp = signal.point.time_stamp # making an assumption here that the fill is isntant, but it's ok for now
        
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