from __future__ import print_function
import datetime
import logging
import settings.appconfig as config
from   session import Session
import time
from   td.orders import Order, OrderLeg
import td.enums

def get_session( force_login = False ):
    s = Session()
    if s.session is None or force_login:
        s.login()
    return s.session

def get_data_point( symbol ):
    ''' Pull current data point here from data provider for the symbol '''    
    for i in range(0,5):
        while True:            
            try:
                session = get_session()
                # get real data here
                price = session.get_quotes(instruments=symbol)[symbol]['lastPrice']
                time_stamp = datetime.datetime.now()
                logging.debug( 'Get Quote from API for {}: {},{}'.format( symbol, str(price), str(time_stamp) ) )
        
                return time_stamp, price
            except Exception as ex:                
                logging.error( 'Exception: {}'.format ( str(ex) ) )                              
                time.sleep(1)
                session = get_session( force_login = True )
                continue
            break

def submit_order( symbol, qty, is_entry ):
    ''' Place order through TD API '''
    
    session = get_session()
    account_id = config.td['account_id']
    fill_price = 0
    
    logging.debug( 'Executing signal: {},{},{}'.format( symbol, qty, is_entry ) )
    send_order = config.td['live_orders']
    instruction = 'buy' if is_entry else 'sell'
    logging.debug( 'Executing signal: {} {} {}'.format( instruction, qty, symbol ) )

    new_order = Order()
    new_order.order_type(order_type = td.enums.ORDER_TYPE.MARKET)
    new_order.order_session(session = td.enums.ORDER_SESSION.NORMAL)
    new_order.order_duration(duration = td.enums.DURATION.DAY)
    new_order.order_strategy_type(order_strategy_type = td.enums.ORDER_STRATEGY_TYPE.SINGLE)

    new_order_leg = OrderLeg()
    if ( is_entry ):
        new_order_leg.order_leg_instruction(instruction = td.enums.ORDER_INSTRUCTIONS.BUY)
    else:
        new_order_leg.order_leg_instruction(instruction = td.enums.ORDER_INSTRUCTIONS.SELL)

    new_order_leg.order_leg_asset(asset_type = td.enums.ORDER_ASSET_TYPE.EQUITY, symbol = symbol)
    new_order_leg.order_leg_quantity_type(quantity_type = td.enums.QUANTITY_TYPE.SHARES)
    new_order_leg.order_leg_quantity(quantity=int(qty))
    new_order.add_order_leg(order_leg = new_order_leg)
    if (send_order):
        session.place_order(account = account_id, order= new_order)
        fill_price = get_filled_price(account_id,symbol)    
    else:
        print('Instruction = {}, Symbol = {}'.format(instruction, symbol))

    return fill_price

def get_filled_price (account, symbol):
    ''' Find latest filled order for symbol '''
    session = get_session()
    time.sleep(2)
    today = datetime.date.today()
    # Get all today's fulfilled orders
    orders = session.get_orders_query(account = account, from_entered_time = today, to_entered_time = today, status = 'FILLED')
    # Get last filled order for symbol
    last_symbol_order = [i for i in orders if i['orderLegCollection'][0]['instrument']['symbol'] == symbol][-1]        
    fill_price = last_symbol_order['orderActivityCollection'][0]['executionLegs'][0]['price']
     
    # don't need this
    #fill_time = last_symbol_order['orderActivityCollection'][0]['executionLegs'][0]['time']
    #time_stamp = datetime.datetime.strptime( fill_time, '%Y-%m-%dT%H:%M:%S+0000' )

    return fill_price
