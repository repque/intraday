import collections
import csv
from   datetime import datetime
import functools
import pandas as pd
import plotly.graph_objects as go
import os

class memoized(object):
   '''Decorator. Caches a function's return value each time it is called.
      If called later with the same arguments, the cached value is returned
      (not reevaluated).
   '''
   def __init__(self, func):
      self.func = func
      self.cache = {}
   def __call__(self, *args):
      if not isinstance(args, collections.Hashable):
         # uncacheable. a list, for instance.
         # better to not cache than blow up.
         return self.func(*args)
      if args in self.cache:
         return self.cache[args]
      else:
         value = self.func(*args)
         self.cache[args] = value
         return value
   def __repr__(self):
      '''Return the function's docstring.'''
      return self.func.__doc__
   def __get__(self, obj, objtype):
      '''Support instance methods.'''
      return functools.partial(self.__call__, obj)

class Singleton( object ):
    def __new__(cls, *args, **kwds):
        it = cls.__dict__.get("__it__")
        if it is not None:
            return it
        cls.__it__ = it = object.__new__(cls)
        it.init(*args, **kwds)
        return it
    def init(self, *args, **kwds):
        pass

@memoized
def save_point( symbol, point ):
    with open( '.\\data\\' + symbol + '.csv', 'a', newline='') as f:
        writer = csv.writer( f )
        writer.writerow( point )

def plot( pnl, live, is_multiday ):
    ''' Plot buys and sells for each each position, if running for a single day.
        If running in live mode, saves the images, otherwise just generates and shows them.
        If testing using multiple days, displays equity curve (TODO)
    '''
    if not is_multiday:
        for symbol, position in pnl.positions.items():
            if position.buys:
                df = pd.DataFrame.from_records( position.all_points, index='time_stamp', columns=['time_stamp', 'price'] )                
                plot_day( symbol, position.buys[-1], df, position.buys, position.sells, position.realized_pl + position.mtm_pl, position.total_qty, save=live )

def plot_day( symbol, date, df, buys, sells, pnl, qty, save=True ):
    ''' Creates a plot of day's prices with both buy and sell markers.

        Arguments:
        ---------
            date  - string representation of the day
            df    - dataframw of prices, indexed by timestamps
            buys  - list of timestamps where buy trades were executed
            sells - list of timestamps where sell trades were executed
            save  - boolean which specifies whether to save the image to a file (default), or show it on the screen
    '''
    date = datetime.strptime( date, '%Y-%m-%d %H:%M:%S' ).date() # convert from string to datetime

    df_buys = df[df.index.isin(buys)]
    df_sells = df[df.index.isin(sells)]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_buys.index, y=df_buys['price'],
                        mode='markers',
                        marker_symbol=[5, 'triangle-up'],
                        marker_size=15,
                        name='Buy',
                        marker=dict(color='green')))
    fig.add_trace(go.Scatter(x=df_sells.index, y=df_sells['price'],
                        mode='markers',
                        name='Sell',
                        marker_symbol=[6, 'triangle-down'],
                        marker_size=15,
                        marker=dict(color='red')))
    fig.add_trace(go.Scatter(x=df.index, y=df['price'],
                        mode='lines',
                        name='Prices',
                        line=dict(color='rgb(107,105,172)')))

    fig.update_layout(
        title="{}    Date: {}, PnL: ${}, Size: {}".format( symbol, date, int(pnl), int(qty) ),
        xaxis_title="Time",
        yaxis_title="Price",
        showlegend=False
    )
    
    if (save):
        directory = '.\\charts'
        if not os.path.exists(directory):
            os.makedirs(directory)
        filename =  directory + '\\{}_{}.html'.format(date, symbol)
        fig.write_html(filename)
    else:
        fig.show()        