from __future__ import print_function
import datetime
import logging
import settings.appconfig as config
import session as s
import time
from td.orders import Order, OrderLeg
from td.enums import ORDER_SESSION, DURATION, ORDER_INSTRUCTIONS, ORDER_ASSET_TYPE, ORDER_STRATEGY_TYPE, ORDER_TYPE, QUANTITY_TYPE


def get_data_point( symbol ):
    ''' Pull current data point here from data provider for the symbol '''    
    for i in range(0,5):
        while True:            
            try:
                session_object = s.Session()
                session = session_object.session
                # get real data here
                price = session.get_quotes(instruments=symbol)[symbol]['lastPrice']
                time_stamp = datetime.datetime.now()
                logging.debug( 'Get Quote from API for {}: {},{}'.format( symbol, str(price), str(time_stamp) ) )
        
                return time_stamp, price
            except Exception as ex:                
                logging.error( 'Exception: {}'.format ( str(ex) ) )                              
                time.sleep(1)
                session_object.login()
                session = session_object.session
                continue
            break

def submit_order( symbol, qty, is_entry ):
    
    ''' Place order through TD API '''
    session = s.Session().session
    account_id = config.td['account_id']
    fill_price = 0
    
    logging.debug( 'Executing signal: {},{},{}'.format( symbol, qty, is_entry ) )
    send_order = config.td['live_orders']
    instruction = 'buy' if is_entry else 'sell'

    new_order = Order()
    new_order.order_type(order_type = ORDER_TYPE.MARKET)
    new_order.order_session(session = ORDER_SESSION.NORMAL)
    new_order.order_duration(duration = DURATION.DAY)
    new_order.order_strategy_type(order_strategy_type = ORDER_STRATEGY_TYPE.SINGLE)

    new_order_leg = OrderLeg()
    if (instruction == 'buy'):
        new_order_leg.order_leg_instruction(instruction = ORDER_INSTRUCTIONS.BUY)
    else:
        new_order_leg.order_leg_instruction(instruction = ORDER_INSTRUCTIONS.SELL)

    new_order_leg.order_leg_asset(asset_type = ORDER_ASSET_TYPE.EQUITY, symbol = symbol)
    new_order_leg.order_leg_quantity_type(quantity_type = QUANTITY_TYPE.SHARES)
    new_order_leg.order_leg_quantity(quantity=int(qty))
    new_order.add_order_leg(order_leg = new_order_leg)
    if (send_order):
        session.place_order(account = account_id, order= new_order)
        fill_price, time_stamp = get_filled_price(account_id,symbol)    
    else:
        print('Instruction = {}, Symbol = {}'.format(instruction, symbol))

    return fill_price

def get_filled_price (account, symbol):

    ''' Find latest filled order for symbol '''
    session = s.Session().session
    time.sleep(2)
    today = datetime.date.today()
    # Get all today's fulfilled orders
    orders = session.get_orders_query(account = account_id, from_entered_time = today, to_entered_time = today, status = 'FILLED')
    # Get last filled order for symbol
    last_symbol_order = [i for i in orders if i['orderLegCollection'][0]['instrument']['symbol'] == symbol][-1]        
    fill_price = last_symbol_order['orderActivityCollection'][0]['executionLegs'][0]['price']
    fill_time = last_symbol_order['orderActivityCollection'][0]['executionLegs'][0]['time']
    time_stamp = datetime.datetime.strptime( fill_time, '%Y-%m-%dT%H:%M:%S+0000' )

    return fill_price, time_stamp