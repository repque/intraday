
class Signal( object ):
    
    def __init__( self, point, desc, is_entry=True, equity_pct=0, symbol=None ):
        self.symbol     = symbol
        self.point      = point
        self.desc       = desc
        self.is_entry   = is_entry
        self.equity_pct = equity_pct
        
    def __repr__(self):
        return "<{klass} {attrs}>".format(
            klass=self.__class__.__name__,
            attrs=" ".join("{}={!r}".format(k, v) for k, v in self.__dict__.items()),
            )