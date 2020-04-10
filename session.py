from td.client import TDClient
import settings.appconfig as set
from utils import Singleton

class Session ( Singleton ):
    
    session = TDClient()

    def login( self ):
        ''' login to TD account '''
        TDSession = TDClient(account_number = set.td['account_number'],
                             account_password = '',
                             consumer_id = set.td['consumer_id'],
                             redirect_uri = set.td['redirect_uri'])
        session = TDSession.login()        
