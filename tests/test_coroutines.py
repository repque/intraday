import datetime
import unittest

from core import Point
from coroutines import initial_breakout, stop_loss, stop_profit, time_based, all_conditions

class TestCoroutines(unittest.TestCase):

    def _next_point( self, p, dt=None, df=None ):
        ''' helper function to generate data points for testing '''
        if dt is None:
            dt = self.dt

        point = Point( dt, p )
        self.dt = dt + datetime.timedelta(minutes=1)
        return (point, df)

    def setUp( self ):
        self.dt = datetime.datetime( 2020, 4, 6, 9, 30 )

    def test_initial_breakout( self ):
        cr = initial_breakout( 3 )

        # set initial range
        cr.send( self._next_point( 50.00 ) )
        cr.send( self._next_point( 50.25 ) )
        cr.send( self._next_point( 50.10 ) )

        # no breakout
        for p in (50.05, 50.00, 50.25, 49.00):
            signal = cr.send( self._next_point( p ) )
            self.assertIsNone( signal )

        # breakout
        signal = cr.send( self._next_point( 50.26 ) )
        self.assertIsNotNone( signal )

        # no breakout
        signal = cr.send( self._next_point( 50.25 ) )
        self.assertIsNone( signal )

        # current code doesn't allow re-triggering ...
        for p in ( 51.00, 52.00, 53.00, 54.00, 55.00 ):
            signal = cr.send( self._next_point( 50.27 ) )
            self.assertIsNone( signal )

        # if we get to the next day, the coroutine should reset and start working again
        self.dt = datetime.datetime( 2020, 4, 7, 9, 30 )

        # set initial range
        cr.send( self._next_point( 50.00 ) )
        cr.send( self._next_point( 50.25 ) )
        cr.send( self._next_point( 50.10 ) )

        # no breakout
        for p in (50.05, 50.00, 50.25, 49.00):
            signal = cr.send( self._next_point( p ) )
            self.assertIsNone( signal )

        # breakout
        signal = cr.send( self._next_point( 50.26 ) )
        self.assertIsNotNone( signal )

    def test_stop_loss( self ):
        cr = stop_loss( 0.01 )

        # send first point to set the stop level
        cr.send( self._next_point( 100.00 ) )

        # no level breached
        for p in ( 100.00, 100.50, 102.00, 99.00 ):
            signal = cr.send( self._next_point( p ) )
            self.assertIsNone( signal )

        # stop triggered
        signal = cr.send( self._next_point( 98.99 ) )
        self.assertIsNotNone( signal )

        # stop should not be triggered again!
        signal = cr.send( self._next_point( 98.99 ) )
        self.assertIsNone( signal )

    def test_stop_profit( self ):
        cr = stop_profit( 0.01 )

        # send first point to set the stop level
        cr.send( self._next_point( 100.00 ) )

        # no level breached
        for p in ( 100.00, 100.50, 98.00, 101.00 ):
            signal = cr.send( self._next_point( p ) )
            self.assertIsNone( signal )

        # stop triggered
        signal = cr.send( self._next_point( 101.01 ) )
        self.assertIsNotNone( signal )

        # stop should not be triggered again!
        signal = cr.send( self._next_point( 101.01 ) )
        self.assertIsNone( signal )

    def test_time_based( self ):
        cr = time_based( 9, 34 )

        # no signal
        for p in ( 100.00, 100.50, 102.00, 99.00 ):
            signal = cr.send( self._next_point( p ) )
            self.assertIsNone( signal )

        # time triggered
        signal = cr.send( self._next_point( 99.50 ) )
        self.assertIsNotNone( signal )

        # no more triggerring because we're matching exactly
        signal = cr.send( self._next_point( 99.50 ) )
        self.assertIsNone( signal )

    def test_and_logic( self ):
        cr = all_conditions( [initial_breakout( 3, repeat=True ), initial_breakout( 4, repeat=True )] )

        # set initial range
        cr.send( self._next_point( 50.00 ) )
        cr.send( self._next_point( 50.25 ) )
        cr.send( self._next_point( 50.10 ) )

        # now 4th bar exceeds 3-bar range, so the first coroutine would trigger, but the second hasn't, so AND condition is not met
        signal = cr.send( self._next_point( 50.27 ) )
        self.assertIsNone( signal )

        # no signal
        signal = cr.send( self._next_point( 50.26 ) )
        self.assertIsNone( signal )

        # both conditions satisfied - signal raised
        signal = cr.send( self._next_point( 50.28 ) )
        self.assertIsNotNone( signal )

if __name__ == '__main__':
    unittest.main()