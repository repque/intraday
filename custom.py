from __future__ import print_function
import datetime
import logging


def get_data_point( symbol ):
    ''' TODO: pull current data point here from your data provider for the symbol '''
    
    # get real data here
    price      = 50
    time_stamp = datetime.datetime.now() # IMPORTANT - time stamp has to increase on subsequent calls, going from 9:30 to 16:00
    
    return time_stamp, price

def submit_order( symbol, qty, is_entry ):
    ''' TODO: submit order to the broker API for execution, and return fill price 
        If 'is_entry' is True - Buy to Open, else - Sell to Close
    '''
    return 0

