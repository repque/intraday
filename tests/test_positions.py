import unittest

import datetime
from   core import Config, Point, Trade
from   positions import Pnl, Position
from   signals import Signal

class TestPositions(unittest.TestCase):

    def test_pnl_singleton( self ):
        p1 = Pnl()
        p2 = Pnl()
        self.assertEquals( p1, p2 )
        self.assertEquals( id(p1), id(p2) )

    def test_pnl_initialize( self ):
        config1 = Config( symbol='T1', equity_pct=0.50, 
                entry_rules=[], 
                exit_rules =[] )
        p = Pnl()
        p.initialize( [config1], 100, 0.01 )
        self.assertIn( 'T1', p.positions )
        self.assertTrue( isinstance( p.positions['T1'], Position ) )
        self.assertEqual( 100, p.available_cash )
        self.assertEqual( 100, p.current_equity )

    def test_market_data_update( self ):
        symbol = 'T1'
        config1 = Config( symbol=symbol, equity_pct=0.50, 
                entry_rules=[], 
                exit_rules =[] )
        pnl = Pnl()
        pnl.initialize( [config1], 2000, 0.01 )

        self.assertIn( symbol, pnl.positions )

        pos = pnl.positions[symbol]
        self.assertEquals( 0, pos.qty )
        self.assertEqual( 0, pos.starting_equity )

        point = Point(time_stamp=datetime.datetime.now(), price=100.00)
        pnl.market_data_update( symbol, point )
        self.assertEquals( 0, pos.mtm_pl )
        
        signal = Signal( point, desc='Test Signal' )
        signal.symbol = symbol
        signal.is_entry = True

        pnl.handle_fill( Trade( signal, 10, 100.00 ) )

        pnl.market_data_update( symbol, Point(time_stamp=datetime.datetime.now(), price=99.50) )
        self.assertEquals( 10, pos.qty )
        self.assertEquals( -5.00, pos.mtm_pl )

        pnl.market_data_update( symbol, Point(time_stamp=datetime.datetime.now(), price=100.00) )
        self.assertEquals( 10, pos.qty )
        self.assertEquals( 0.00, pos.mtm_pl )

        pnl.market_data_update( symbol, Point(time_stamp=datetime.datetime.now(), price=102.00) )
        self.assertEquals( 10, pos.qty )
        self.assertEquals( 20.00, pos.mtm_pl )

    def test_available_cash( self ):
        symbol = 'T1'
        config1 = Config( symbol=symbol, equity_pct=0.50, 
                entry_rules=[], 
                exit_rules =[] )
        pnl = Pnl()
        pnl.initialize( [config1], 2000, 0.01 )

        self.assertIn( symbol, pnl.positions )
        self.assertEquals( 2000, pnl.available_cash )

        pos = pnl.positions[symbol]

        point = Point(time_stamp=datetime.datetime.now(), price=100.00)

        signal = Signal( point, desc='Test Signal' )
        signal.symbol = symbol
        signal.is_entry = True

        # entry trade reduces available cash
        pnl.handle_fill( Trade( signal, 5, 100.00 ) )
        self.assertEquals( 1500, pnl.available_cash )

        # exit trade returns available cash
        signal.is_entry = False
        pnl.handle_fill( Trade( signal, 5, 110.00 ) )
        self.assertEquals( 2050, pnl.available_cash )

if __name__ == '__main__':
    unittest.main()