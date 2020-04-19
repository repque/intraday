import custom
import unittest
import settings.appconfig as config
import logging
import td.enums
import td.client
from td.orders import Order, OrderLeg
from   session import Session
from unittest import TestCase, mock

class TestCustom(unittest.TestCase):

    def test_get_data_point( self ):
            symbol = 'FAS'        
            time_stamp, price = custom.get_data_point( symbol )
        
            self.assertIsNotNone(time_stamp)
            self.assertIsNotNone(price)
            self.assertGreater(price, 0)

    def test_submit_order_not_live( self ):
        send_order = config.td['live_orders']
        if not(send_order):
            symbol = 'FAS'        
            qty = 1
            is_entry = True

            fill_price = custom.submit_order( symbol, qty, is_entry )                    
            self.assertEqual(fill_price, 0)
            
    def test_submit_order_live(self):
        try:
            send_order = config.td['live_orders']
            if (send_order):
                symbol = 'FAS'        
                qty = 1
                is_entry = True

                session = Session().session
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
                send_order = config.td['live_orders']

                with unittest.mock.patch('td.client') as mocked_td:                    
                    mocked_td.TDClient().place_order(account = account_id, order= new_order)
                    mocked_td.TDClient().place_order.assert_called_once()
        except Exception as ex:                
            print(str(ex))            
        
if __name__ == '__main__':
    unittest.main()