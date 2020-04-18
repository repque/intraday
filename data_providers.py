import csv
import datetime

from   core import Point
from   custom import get_data_point

def gen_time_series( symbol=None ):
    ''' generate time-series of prices '''
    while True:
        time_stamp, price = get_data_point( symbol )
        yield Point( time_stamp=time_stamp, price=price )

def gen_csv_data( symbol=None, specific_day=None ):
    with open( '.\\data\\' + symbol + '.csv', 'r') as f:
        reader = csv.reader( f )
        for row in reader:
            time_stamp = datetime.datetime.strptime( row[0], '%Y-%m-%d %H:%M:%S' )
            if specific_day and specific_day.date() != time_stamp.date():
                continue
            price = float( row[1] )
            yield Point( time_stamp=time_stamp, price=price )