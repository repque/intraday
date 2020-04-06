from __future__ import print_function

import datetime
import six
from   signals import Signal

def coroutine(func):
    ''' Decorator for coroutines to prime them '''
    def start(*args,**kwargs):
        cr = func(*args,**kwargs)
        six.next( cr )
        return cr
    return start

@coroutine
def time_based( hour, minute ):
    ''' Raise signal when the timestamp of an incoming price point matches the passed in hour/minute '''
    while True:
        point = (yield) 
        if point.time_stamp.hour == hour and point.time_stamp.minute == minute:
            yield Signal( point=point, desc='hour: {}, minute: {}'.format( hour, minute ) )

@coroutine
def initial_breakout( period_length ):
    ''' Collect max prices during period length. Then, compare incoming price points to max, 
        and generate signal if there's breakout.
    '''
    counter = 0
    max_price = 0
    start_time = datetime.datetime( 2020, 4, 5, 9, 30 ) # date doesn't matter
    while True:
        point = (yield)
        if counter < period_length:
            if point.time_stamp.time() <= ( start_time + datetime.timedelta( minutes=period_length ) ).time():
                counter += 1
                max_price = max( max_price, point.price )
        else:
            if point.price > max_price:
                signal = Signal( point=point, desc='break out' )
                # reset
                counter = 0
                max_price = 0

                yield signal
            
@coroutine
def stop_loss( percent ):
    ''' Raises signal when the price break below trigger level, which identified by % below initial price '''
    initial_price = 0
    trigger_level = 0
    while True:
        point = (yield) 
        if initial_price == 0:
            initial_price = point.price
            trigger_level = initial_price - initial_price * percent
        else:
            if point.price < trigger_level:
                signal = Signal( point=point, desc='loss exit: broke below {}'.format( trigger_level ) )
                # reset
                trigger_level = 0
                initial_price = 0

                yield signal
            
@coroutine
def stop_profit( percent ):
    ''' Raises signal when the price break above trigger level, which identified by % above initial price '''
    initial_price = 0
    trigger_level = 0
    while True:
        point = (yield) 
        if initial_price == 0:
            initial_price = point.price
            trigger_level = initial_price + initial_price * percent
        else:
            if point.price > trigger_level:
                signal = Signal( point=point, desc='profit exit: broke above {}'.format( trigger_level ) )
                # reset
                trigger_level = 0
                initial_price = 0

                yield signal      
                