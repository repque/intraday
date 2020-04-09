import csv
import datetime

from   core import Point
from   custom import get_data_point

def gen_time_series( symbol=None ):
    ''' generate time-series of prices '''
    while True:
        time_stamp, price = get_data_point( symbol )
        yield Point( time_stamp=time_stamp, price=price )

def gen_csv_data( symbol=None ):
    with open( '.\\data\\' + symbol + '.csv', 'r') as f:
        reader = csv.reader( f )
        for row in reader:
            time_stamp = datetime.datetime.strptime( row[1] + ' ' + row[2], '%Y%m%d %H%M%S' )
            price = float( row[3] )
            yield Point( time_stamp=time_stamp, price=price )