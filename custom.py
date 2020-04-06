from __future__ import print_function
import datetime
import logging

def get_data_point( symbol ):
    ''' TODO: pull current data point here from your data provider for the symbol '''
    
    # get real data here
    price      = 50
    time_stamp = datetime.datetime.now() # IMPORTANT - time stamp has to increase on subsequent calls, going from 9:30 to 16:00
    
    return time_stamp, price

def execute_signal( signal ):
    ''' TODO: submit signal for execution and record completion '''
    logging.debug( 'Executing signal: {}'.format( signal ) )