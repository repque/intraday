from   collections import namedtuple
import logging

from   signals import Signal
from   utils import Singleton

PnlReport = namedtuple('PnlReport', 'starting_equity ending_equity net total_pl total_commissions')


class Position( object ):
    ''' Position per instrument '''
    def __init__( self, commission ):
        self.commission = commission
        self.total_commissions = 0.0
        self.realized_pl = 0.0

        self.qty = 0
        self.starting_equity = 0

    def handle_fill( self, trade ):
        self.total_commissions += trade.qty * self.commission

        if trade.is_entry:
            self.qty = trade.qty
            self.starting_equity = trade.qty * trade.price
        else:
            self.realized_pl += trade.qty * trade.price - self.starting_equity
            self.qty = 0 # no partial trades allowed

    def market_data_update( self, point ):
        ''' keep track of mtm pl when position is open '''
        if self.qty:
            self.mtm_pl = self.qty * point.price - self.starting_equity
        else:
            self.mtm_pl = 0.0

class Pnl( Singleton ):
    ''' Keeps track of total pnl '''
    def initialize( self, configs, cash, commission ):
        self.starting_equity = cash
        self.current_equity  = cash
        self.available_cash  = cash
        self.positions = { config.symbol: Position( commission ) for config in configs }

    def market_data_update( self, symbol, point ):
        position = self.positions[ symbol ]
        position.market_data_update( point )

    def handle_fill( self, trade ):
        position = self.positions[ trade.symbol ]
        position.handle_fill( trade )

        if trade.is_entry:
            self.available_cash -= trade.qty * trade.price 
        else:
            self.available_cash += trade.qty * trade.price 

    def get_report( self ):
        pnl = self.get_pnl()
        commissions = self.get_commissions()
        net = pnl - commissions;
        self.current_equity += net

        # current_equity and net include commissions impact, pnl doesn't
        return PnlReport( int(self.starting_equity), int(self.current_equity), int(net), int(pnl), int(-commissions) )

    def get_pnl( self ):
        return sum( position.realized_pl + position.mtm_pl for position in self.positions.values() )

    def get_commissions( self ):
        return sum( position.total_commissions for position in self.positions.values() )
