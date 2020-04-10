from   td.client import TDClient
import settings.appconfig as config
from   utils import Singleton

class Session ( Singleton ):
    
    session = None

    def login( self ):
        ''' login to TD account '''
        TDSession = TDClient(account_number   = config.td['account_number'],
                             account_password = '',
                             consumer_id      = config.td['consumer_id'],
                             redirect_uri     = config.td['redirect_uri'])
        session = TDSession.login()        
