import unittest

import datetime
from   core import Config, Point, Trade
from   positions import Pnl, Position
from   signals import Signal

class TestPositions(unittest.TestCase):

    def test_pnl_singleton( self ):
        p1 = Pnl()
        p2 = Pnl()
        self.assertEqual( p1, p2 )
        self.assertEqual( id(p1), id(p2) )

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
        self.assertEqual( 0, pos.qty )
        self.assertEqual( 0, pos.starting_equity )

        point = Point(time_stamp=datetime.datetime.now(), price=100.00)
        pnl.market_data_update( symbol, point )
        self.assertEqual( 0, pos.mtm_pl )
        
        signal = Signal( point, desc='Test Signal' )
        signal.symbol = symbol
        signal.is_entry = True

        pnl.handle_fill( Trade( signal, 10, 100.00 ) )

        pnl.market_data_update( symbol, Point(time_stamp=datetime.datetime.now(), price=99.50) )
        self.assertEqual( 10, pos.qty )
        self.assertEqual( -5.00, pos.mtm_pl )

        pnl.market_data_update( symbol, Point(time_stamp=datetime.datetime.now(), price=100.00) )
        self.assertEqual( 10, pos.qty )
        self.assertEqual( 0.00, pos.mtm_pl )

        pnl.market_data_update( symbol, Point(time_stamp=datetime.datetime.now(), price=102.00) )
        self.assertEqual( 10, pos.qty )
        self.assertEqual( 20.00, pos.mtm_pl )

    def test_available_cash( self ):
        symbol = 'T1'
        config1 = Config( symbol=symbol, equity_pct=0.50, 
                entry_rules=[], 
                exit_rules =[] )
        pnl = Pnl()
        pnl.initialize( [config1], 2000, 0.01 )

        self.assertIn( symbol, pnl.positions )
        self.assertEqual( 2000, pnl.available_cash )

        pos = pnl.positions[symbol]

        point = Point(time_stamp=datetime.datetime.now(), price=100.00)

        signal = Signal( point, desc='Test Signal' )
        signal.symbol = symbol
        signal.is_entry = True

        # entry trade reduces available cash
        pnl.handle_fill( Trade( signal, 5, 100.00 ) )
        self.assertEqual( 1500, pnl.available_cash )

        # exit trade returns available cash
        signal.is_entry = False
        pnl.handle_fill( Trade( signal, 5, 110.00 ) )
        self.assertEqual( 2050, pnl.available_cash )

    def test_realized_pnl( self ):
        symbol = 'T1'
        config1 = Config( symbol=symbol, equity_pct=0.50, 
                entry_rules=[], 
                exit_rules =[] )
        pnl = Pnl()
        pnl.initialize( [config1], 2000, 0.01 )

        self.assertIn( symbol, pnl.positions )
        self.assertEqual( 2000, pnl.available_cash )

        pos = pnl.positions[symbol]

        point = Point(time_stamp=datetime.datetime.now(), price=100.00)

        signal = Signal( point, desc='Test Signal' )
        signal.symbol = symbol
        signal.is_entry = True

        # entry trade doesn't impact realized_pnl
        pnl.handle_fill( Trade( signal, 10, 100.00 ) )
        self.assertEqual( 0, pos.realized_pl )

        # exit trade impacts realized pnl
        signal.is_entry = False
        pnl.handle_fill( Trade( signal, 10, 98.00 ) )
        self.assertEqual( -20, pos.realized_pl )

        # another entry trade, realized_pl stays the same 
        signal.is_entry = True
        pnl.handle_fill( Trade( signal, 20, 100.00 ) )
        self.assertEqual( -20, pos.realized_pl )

        # exit trade causes realized pnl to aggregate
        signal.is_entry = False
        pnl.handle_fill( Trade( signal, 20, 110.00 ) )
        self.assertEqual( 180, pos.realized_pl )

    def test_get_commissions( self ):
        symbol = 'T1'
        config1 = Config( symbol=symbol, equity_pct=0.50, 
                entry_rules=[], 
                exit_rules =[] )
        pnl = Pnl()
        pnl.initialize( [config1], 2000, 0.01 )

        pos = pnl.positions[symbol]

        point = Point(time_stamp=datetime.datetime.now(), price=100.00)

        signal = Signal( point, desc='Test Signal' )
        signal.symbol = symbol

        for _ in range( 0, 10 ):
            # entry trade 
            signal.is_entry = True
            pnl.handle_fill( Trade( signal, 10, 100.00 ) )

            # exit trade 
            signal.is_entry = False
            pnl.handle_fill( Trade( signal, 10, 100.00 ) )

        # 20 trades total, 1 cent per share commission rate, 10 shares traded per each trade = 200 cents total commissions
        self.assertEqual( 2.00, pnl.get_commissions() )

    def test_get_pnl( self ):
        symbol = 'T1'
        config1 = Config( symbol=symbol, equity_pct=0.50, 
                entry_rules=[], 
                exit_rules =[] )
        pnl = Pnl()
        pnl.initialize( [config1], 2000, 0.01 )

        pos = pnl.positions[symbol]

        point = Point(time_stamp=datetime.datetime.now(), price=100.00)

        signal = Signal( point, desc='Test Signal' )
        signal.symbol = symbol

        for _ in range( 0, 10 ):
            # entry trade 
            signal.is_entry = True
            pnl.handle_fill( Trade( signal, 10, 100.00 ) )

            # exit trade 
            signal.is_entry = False
            pnl.handle_fill( Trade( signal, 10, 101.00 ) )

        # 10 round-trips, 10.0 profit per = 100 realized_pl
        self.assertEqual( 100.00, pos.realized_pl )

        # book some unrealized pnl too
        signal.is_entry = True
        pnl.handle_fill( Trade( signal, 10, 100.00 ) )

        # market moved - mtm pnl is now 3 x 10 = 30
        pnl.market_data_update( symbol, Point(time_stamp=datetime.datetime.now(), price=103.00) )
        self.assertEqual( 30.00, pos.mtm_pl )

        # assert the total pnl
        self.assertEqual( 130.00, pnl.get_pnl() )

    def test_get_report( self ):
        symbol1 = 'T1'
        config1 = Config( symbol=symbol1, equity_pct=0.50, 
                entry_rules=[], 
                exit_rules =[] )

        symbol2 = 'T2'
        config2 = Config( symbol=symbol2, equity_pct=0.50, 
                entry_rules=[], 
                exit_rules =[] )

        pnl = Pnl()
        pnl.initialize( [config1, config2], 2000, 0.10 )

        point1 = Point(time_stamp=datetime.datetime.now(), price=100.00)

        signal1 = Signal( point1, desc='Test Signal 1' )
        signal1.symbol = symbol1        

        point2 = Point(time_stamp=datetime.datetime.now(), price=200.00)

        signal2 = Signal( point2, desc='Test Signal 2' )
        signal2.symbol = symbol2

        # entry trades 
        signal1.is_entry = True
        pnl.handle_fill( Trade( signal1, 10, 100.00 ) )

        signal2.is_entry = True
        pnl.handle_fill( Trade( signal2, 10, 200.00 ) )

        # exit trades
        signal1.is_entry = False
        pnl.handle_fill( Trade( signal1, 10, 110.00 ) ) # we made 10 on symbol1

        signal2.is_entry = False
        pnl.handle_fill( Trade( signal2, 10, 180.00 ) ) # we lost 20 on symbol2

        report = pnl.get_report()

        self.assertEqual( 2000, report.starting_equity )
        self.assertEqual( 1896, report.ending_equity )
        self.assertEqual( -104, report.net )
        self.assertEqual( -4, report.total_commissions )
        self.assertEqual( -100, report.total_pl )

if __name__ == '__main__':
    unittest.main()