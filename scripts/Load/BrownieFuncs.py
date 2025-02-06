

from brownie import (accounts, interface, network, config, Contract)
import shutil, os, sys, binascii
from brownie.network.event import EventWatcher
from scripts.Load.misc_funcs import get_accounts, getV3Contracts
#---------------------  DEPLOYMENT; UPDATE CONFIG  ADDRESSES

def UpdateConfigAdresses(Contract, str_):

    NETWORK = network.show_active()
    _dir = os.getcwd() ; #(f'current dir: {_dir}')
    _config = _dir + '\\brownie-config.yaml' ; 
    print(f'\nre-writing {_config}\n')
    dummy_file    = _config + '.bak'
    
    with open(_config, 'r') as read_obj, open(dummy_file, 'w') as write_obj:
        
        READ_LINES = read_obj.readlines() # file to be read
        data = []
        i = 0
        while i < len(READ_LINES):
            line = READ_LINES[i]
            data.append(line)
            if NETWORK+':' in line:
                j = i+1; kill = False
                while kill == False:
                    line = READ_LINES[j]
                    if ' '+str_ in line:
                        line = F'    {str_}: "{Contract.address}"\n'
                        kill = True
                    data.append(line)
                
                    j += 1
                i=j-1
            i += 1
            

        #write new file:
        i = 0
        while i < len(data):
            write_obj.write(data[i]) # this is 'a' object
            i += 1

    # replace current file with new debugging file
    try:
        os.remove(_config)
        os.rename(dummy_file, _config)
        # shutil.move(dummy_file, _config)
        print('config file updated w/ deployment addresses\n\n')
    except:
        print('\n !! could not delete config file. delete brownie-config.yaml and \
            rename the .bak file.')

#--------------------- GAS CONTROLS

# set gas controls 
# * even if set_gas_limit==False, user will be warned with an input statement in the case that 
# gas price exceeds 30 gwei
gas_controls = True 
def gas_controls(account, set_gas_limit, Priority_fee):
    print(f'\n--- GAS CONTROL CHECK:')
    GasBal = account.balance()
    print(f'   GasBal      : {GasBal*1e-18}')
    
    ALCHEMY_MAINNET = 'https://eth-mainnet.g.alchemy.com/v2/OeVRTKqUBtFwUKVXZnZC8z7Wjwvftb71'
    from web3 import Web3
    w3 = Web3(Web3.HTTPProvider(ALCHEMY_MAINNET))

    gas_price    = w3.eth.gas_price  # current gas price [wei]
    print(f'   gas_price   : {int(gas_price*1e-9) } gwei')
    priority_fee = network.priority_fee(f"{Priority_fee} gwei")
    total_fee    = gas_price + priority_fee

    # set gas limit
    if set_gas_limit:
        max_cost  = 0.2*1e18    # enter desired max cost [wei]
        gas_limit = int(max_cost/total_fee) # [wei]
        network.gas_limit(gas_limit)
        print(f'   gas_limit   : {gas_limit}')
    # network.max_fee(gas_limit)

    if priority_fee:
        print(f'   priority fee: {network.priority_fee()*1e-9} gwei')

    if gas_price*1e-9 > 40:
        input('   gas fee is high. proceed?')


    # calculations:
    #  gas cost  = gas_used  * gas_price
    #  max cost  = gas_limit * gas_price

    # *example:
        # Gas price: 30.000000015 gwei   Gas limit: 5677256   Nonce: 7
        # ... Block: 45169776   Gas used: 5161142 (90.91%)
    print(' ')

    return GasBal



    print(f'\n--- GAS CONTROL CHECK:')
    GasBal = account.balance()
    print(f'   GasBal      : {GasBal*1e-18}')
    
    ALCHEMY_MAINNET = 'https://eth-mainnet.g.alchemy.com/v2/OeVRTKqUBtFwUKVXZnZC8z7Wjwvftb71'

    from web3 import Web3
    w3 = Web3(Web3.HTTPProvider(ALCHEMY_MAINNET))

    gas_price    = w3.eth.gas_price  # current gas price [wei]
    print(f'   gas_price   : {int(gas_price*1e-9) } gwei')
    priority_fee = network.priority_fee(f"{Priority_fee} gwei")
    total_fee    = gas_price + priority_fee

    # set gas limit
    if set_gas_limit:
        max_cost  = 0.2*1e18    # enter desired max cost [wei]
        gas_limit = int(max_cost/total_fee) # [wei]
        network.gas_limit(gas_limit)
        print(f'   gas_limit   : {gas_limit}')
    # network.max_fee(gas_limit)

    if priority_fee:
        print(f'   priority fee: {network.priority_fee()*1e-9} gwei')

    if gas_price*1e-9 > 40:
        input('   gas fee is high. proceed?')


    # calculations:
    #  gas cost  = gas_used  * gas_price
    #  max cost  = gas_limit * gas_price

    # *example:
        # Gas price: 30.000000015 gwei   Gas limit: 5677256   Nonce: 7
        # ... Block: 45169776   Gas used: 5161142 (90.91%)
    print(' ')

    return GasBal



#--------------------- EVENT LISTENING
# create a dictionary which maps addresses of interest to some readable symbol.
# detected [emitted] addresses can then be converted to this symbol rather than 
# printing off the detected hexidecimal address value.
# map token address to token names
tokens_dict = config['networks'][network.show_active()]['tokens']
addresses_dict = {}
for name in tokens_dict:
    addresses_dict[tokens_dict[name]] = name

# map deployed contract/ account addresses to a recognizable name
contractToSymDict = {
            config["networks"][network.show_active()]['MNonfungiblePositionManager']: "NFPM",
            config["networks"][network.show_active()]['MNonfungiblePositionManagerII']: "NFPMII",
            config["networks"][network.show_active()]['MliquidityMiner']: "MLiquid Miner",
            config["networks"][network.show_active()]['MSwapper']: "MSwapper",
            get_accounts(0): "my Explorer acct.",
            get_accounts(1): "my Google acct."
            }
addresses_dict.update(contractToSymDict)

# update listening dict with other values of interest. 
def update_listening_dict(_key, _value):
    addresses_dict[_key] = _value

# get the events from a brownie transaction
def getEvents(tx):
    print(f"\nEVENTS")
    tx_events  = tx.events

    for i, (event, eventDict) in enumerate(tx_events.items()):
        print(f"\n-----[{i}] {event}:") #.upper()
        if event ==  '(unknown)':
            pass
        else:
            EventDict = dict(eventDict)
            for j, (param, value) in enumerate(EventDict.items()):
                print(f"      {param} : {value}")


# EVENT WATCHER
def resetEventWatcher():
     EventWatcher.reset()
def stopEventWatcher(Wait):
     EventWatcher.stop(Wait)
     
def listenForEvent(eventList, _repeat):
    watcher = EventWatcher() 
    watcher.reset()
    #watcher._start_watch()
    
    for contract_event_pair in eventList:
        CONTRACT  = contract_event_pair[0]
        # add/replace the watched contract to dictionary
        contractToSymDict.update({CONTRACT.address: CONTRACT._name})
        event_str = contract_event_pair[1]
        watcher.add_event_callback(event  = CONTRACT.events[event_str],
                                callback = callbackFunc, 
                                delay    = 0.1, 
                                repeat   = _repeat)
        print(f'   *added {event_str} event to watch list.')

def callbackFunc(event):

    event_name = event.event
    args_dict = event.args  # Accessing the 'args' AttributeDict
    print(f'\n[emitted] {event.event} :')
    for key, value in args_dict.items():
        isListedAddress = value in addresses_dict
        if isListedAddress:
            print(f'   {key}: {addresses_dict[value]}')
        if isListedAddress == False:
            print(f"   {key}: {value}")


                
        


def CallbackResponse():

    print('\nresponding....')