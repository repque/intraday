from __future__ import print_function
from   collections import namedtuple
import datetime
import logging
import time

from   coroutines import time_based
from   custom import get_data_point, execute_signal


Point = namedtuple( 'Point', ['time_stamp', 'price'] )

def gen_time_series( symbol=None ):
    ''' generate time-series of prices '''
    while True:
        time_stamp, price = get_data_point( symbol )
        yield Point( time_stamp=time_stamp, price=price )

class Strategy( object ):
    
    def __init__( self, config, dataProvider ):
        self.time_series = dataProvider( config.symbol )
        self.config      = config
        self.in_position = False
        self.active      = True
        self.eod_exit    = time_based( 15, 59 ) # end-of-day exit hard-coded rule
        
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
            
        except StopIteration:
            self.active = False
            logging.debug('{} finished.'.format ( self.config.symbol ) )

        except Exception as ex:
            # if any exception has occured, the strategy is inactivated
            self.active = False
            logging.error( '{} setting active to False.'.format ( self.config.symbol ) )


            

def run( configs, interval=1, dataProvider=gen_time_series ):
    ''' main event loop 

        interval is in minutes, it defines how long to wait before requesting next data point, for testing set it to 0
        dataProvider is a generator function which generates data points for the symbol

    '''

    strategies = [ Strategy(config, dataProvider) for config in configs ]
    
    while True:
        active_strategies = [ strategy for strategy in strategies if strategy.active ]
        if not active_strategies:
            logging.debug( 'All Done!' )
            break # we're done
        
        for strategy in active_strategies:
            signal = strategy.tick()
            if signal:
                execute_signal( signal )
                
        time.sleep( interval * 60 )


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

