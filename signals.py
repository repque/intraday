class Signal( object ):
    
    def __init__( self, point=None, desc=None ):
        self.point      = point
        self.desc       = desc
        self.equity_pct = 0
        self.is_entry   = False
        self.symbol     = None
        
    def __repr__(self):
        return "<{klass} {attrs}>".format(
            klass=self.__class__.__name__,
            attrs=" ".join("{}={!r}".format(k, v) for k, v in self.__dict__.items()),
            )