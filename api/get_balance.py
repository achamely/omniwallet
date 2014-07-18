import urlparse
import os, sys
import json, bitcoinrpc
tools_dir = os.environ.get('TOOLSDIR')
lib_path = os.path.abspath(tools_dir)
sys.path.append(lib_path)
from msc_apps import *
from debug import *

data_dir_root = os.environ.get('DATADIR')
TIMEOUT='timeout -s 9 60 '
conn=getRPCconn()

# Get the Mastercoin balances.  Not that this is also creating the default balance
# object, and should run before all the other currency checks.
def get_rpcmsc_balances( addr ):

    #address_data=[]
    address_data = json.load(conn.getallbalancesforaddress_MP(addr))
    balance_data = address_data[ 'result' ]

    # Once the data's been loaded, remove the BTC entry since we're going to
    #    use sx's BTC balances directly.
    for i in xrange(0,len( balance_data )):
      balance_data[i][ 'divisible' ] = False
      if balance_data[ i ][ 'propertyid' ] == 0:
        balance_data.pop( i )
	break
      else:
        if type(balance_data[i]['balance']) != type(0): #if not int convert (divisible property)
            balance_data[ i ][ 'divisible' ] = True
            balance_data[ i ][ 'balance' ] = int( round( float( balance_data[ i ][ 'balance' ]) * 100000000 ))

    for i in xrange( 0, len( balance_data )):
      if balance_data[ i ][ 'balance' ] == '0.0':
        balance_data.pop( i )

    #print_debug("got here", 5)
    print address_data
    return ( address_data, None )


def get_msc_balances( addr ):
  filename = data_dir_root + '/www/addr/' + addr + '.json'

  if not os.path.exists(filename):
    return ( None, '{ "status": "NOT FOUND: ' + filename + '" }' )

  with open(filename, 'r') as f:
    address_data = json.load(f)
    # Once the data's been loaded, remove the BTC entry since we're going to 
    #    use sx's BTC balances directly.
    balance_data = address_data[ 'balance' ]
    for i in xrange(0,len( balance_data )):
      balance_data[i][ 'divisible' ] = False
      if balance_data[ i ][ 'symbol' ] == 'BTC':
        balance_data.pop( i )
        break
      else:
        if type(balance_data[i]['value']) != type(0): #if not int convert (divisible property)
            balance_data[ i ][ 'divisible' ] = True
            balance_data[ i ][ 'value' ] = int( round( float( balance_data[ i ][ 'value' ]) * 100000000 ))

    for i in xrange( 0, len( balance_data )):
      if balance_data[ i ][ 'value' ] == '0.0':
        balance_data.pop( i )

  #print_debug("got here", 5)

  return ( address_data, None )

# Get the Bitcoin balances - this is a different format from the MSC one above.
def get_btc_balances( addr ):
  balances = { 'symbol': 'BTC', 'divisible': True }
  out, err = run_command(TIMEOUT+ 'sx balance -j ' + addr )
  if err != None:
    return None, err
  elif out == '':
    return None, 'No bitcoin balance available.  Invalid address?: ' + addr
  else:
    try:
        balances[ 'value' ] = int( json.loads( out )[0][ 'paid' ])
    except ValueError:
        balances[ 'value' ] = int(-666)

  return ( [ balances ], None )

def get_balance_response(request_dict):
  import re
  try:
      addrs_list=request_dict['addr']
  except KeyError:
      return (None, 'no address in dictionary')
      
  if len(addrs_list)!=1:
      return response(none, 'no single address')
  addr=addrs_list[0]

  addr = re.sub(r'\W+', '', addr) #check alphanumeric

  address_data, err = get_msc_balances( addr )
  if err != None:
    address_data = {}
    address_data[ 'address' ] = addr
    address_data[ 'balance' ] = []

  bitcoin_balances, err = get_btc_balances( addr )
 
  if err == None:
    for i in xrange(0,len( bitcoin_balances )):
      address_data[ 'balance' ].append( bitcoin_balances[i] )

  #test_bal, err = get_rpcmsc_balances ( addr )
  #print ("testdata",test_bal," realdata", address_data)

  return (json.dumps( address_data ), None)

def get_balance_handler(environ, start_response):
  return general_handler(environ, start_response, get_balance_response)

