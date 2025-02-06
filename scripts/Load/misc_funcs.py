from brownie import (accounts, interface, network, config, Contract,
                    MyMath, 
                    MliquidityMiner,
                    MERC20,
                    MPoolAddress,
                    MCallbackValidation,
                    MUniswapFactory,
                    MUniswapFactoryII,
                    MNonfungiblePositionManager,
                    MNonfungiblePositionManagerII,
                    MSwapper,
                    MSwapRouter
                    )
import sys, os
import time, datetime
import math
import pandas as pd
import numpy as np
from scripts.Load.Dicts import NETWORK_TO_RATE_DICT, NETWORK_SYMS

#------------------------- ACCOUNT/ CONTRACTS
if True:
    
    # load account
    def get_accounts(option):
        if option == 0:
            return accounts.add(config["wallets"]["EXPLOR_key"])
        if option == 1:
            return accounts.add(config["wallets"]["GOOG_key"])

    MOCK_CONTRACTS = {
                        # uniswap v3 libraries
                        'MPoolAddress'       : MPoolAddress,
                        'MCallbackValidation': MCallbackValidation,
                        # uniswap v3-core/ periphery mocks
                        'MFactory'           : MUniswapFactory,
                        'MFactoryII'         : MUniswapFactoryII,
                        'MNonfungiblePositionManager'  : MNonfungiblePositionManager,
                        'MNonfungiblePositionManagerII': MNonfungiblePositionManagerII,
                        'MSwapRouter'        : MSwapRouter,
                        # my mocks
                        'MliquidityMiner'    : MliquidityMiner,
                        #'MLiquidityStaker'   : MLiquidityStaker,
                        'MSwapper'           : MSwapper,
                        # misc testing
                        'MyMath'   : MyMath}
    
    def get_contract_from_abi(contract_name):
        # get contract on active network
        contract_type    = MOCK_CONTRACTS[contract_name]
        contract_address = config["networks"][network.show_active()][contract_name]
        contract = Contract.from_abi(
            contract_type._name, contract_address, contract_type.abi)
        return contract
    
    def getV3Contracts(option): 
        # 1 :: NPM Manager
        # 2 :: Router
        # 3 :: Factory
        if option == 1:
            NFPM   = interface.IV3NPMManager(config["networks"][network.show_active()]['MNonfungiblePositionManager'])
            NFPMII = interface.IV3NPMManager(config["networks"][network.show_active()]['MNonfungiblePositionManagerII'])
            return NFPM, NFPMII
        if option == 2:
            return interface.IV3Router(config["networks"][network.show_active()]['MSwapRouter'])
        if option == 3:
            factory   = interface.IV3Factory(config["networks"][network.show_active()]['MFactory'])
            factoryII = interface.IV3Factory(config["networks"][network.show_active()]['MFactoryII'])
            return factory, factoryII
        

#------------------------- ERC20 TOKEN FUNCTIONS
if True:
    
    # my mock ERC20
    def getMERC20(ERC0_name): 
        return interface.myERC20(config["networks"][network.show_active()]['tokens'][ERC0_name])


    # get token balnce of address.
    def get_Token_bal(Token, address_, _str, PRINT):
        Token_balance = Token.balanceOf(address_)
        if PRINT:
            print(f'   {_str} {Token.symbol()} bal: {Token_balance*1e-18} wei')
        return Token_balance

    
    # approve a contract to spent amount of token
    def approve_contract_spender(amount, token, contract, account):
        _allowed = token.allowance(account.address, contract.address)

        # if _allowed amount is less than desired amount, approve
        if _allowed < 0.95*amount:
            print(f'\napproving {contract._name} for {amount*1e-18} {token.symbol()}...')
            time.sleep(2)
            # approve(address spender, uint256 amount) 
            tx = token.approve(contract.address,
                                    amount,
                                    {"from": account})
            tx.wait(1)
            _allowed = token.allowance(account.address, contract.address)
        print(f'\n{contract._name} allowance over my {token.symbol()} tokens: {_allowed*1e-18}')
        return _allowed

# ------------------------ LiquidityMiner 

def get_LMiner_Deposit(tokenId, liquidity_contract, PRINT):
    deposit = liquidity_contract.getDeposit(tokenId)
    deposit_dict = {
        'owner': deposit[0],
        'liquidity': deposit[1],
        'token0_sym': deposit[2],
        'token1_sym': deposit[3]
    }
    if PRINT:
        print(f'\nLiquidityMiner deposit [tokenId = {tokenId}]:')
        print(f'   owner     : {deposit[0]}')
        print(f'   liquidity : {deposit[1]}')
        Token0    =    getMERC20(deposit[2])
        Token1    =    getMERC20(deposit[3])
        print(f'   token0    : {Token0.symbol()}')
        print(f'   token1    : {Token1.symbol()}')

    return deposit_dict
                
# ------------------------- UNISWAP 
if True:

    # find nearest tick which is divisible by tick_spacing so that tick%tick_spacing == 0
    def find_modulo_zero_tick(tick, tick_spacing, spread, round_up):
        if round_up:
            tick_compressed = math.ceil(tick/tick_spacing)
            modulo_tick     = tick_compressed + spread*tick_spacing
        if round_up==False:
            tick_compressed = math.floor(tick/tick_spacing)
            modulo_tick     = tick_compressed - spread*tick_spacing
        _tick = modulo_tick*tick_spacing
        return int(_tick)

    # get tick info
    def getTickInfo(V3Pool_contract, tick_, PRINT):
        vals          = V3Pool_contract.ticks(tick_)
        params        = {}
        liqGross      = vals[0]; params['liquidityGross'] = liqGross
        liqNet        = vals[1]; params['liquidityNet'] = liqNet
        feeGrowthOut0 = vals[2]; params['feeGrowthOut0'] = feeGrowthOut0
        feeGrowthOut1 = vals[3]; params['feeGrowthOut1'] = feeGrowthOut1
        tickCumOut    = vals[4]; params['tickCumulativeOut'] = tickCumOut
        secsPerLiq    = vals[5]; params['secsPerLiquidity'] = secsPerLiq
        secsOut       = vals[6]; params['secsOut'] = secsOut
        initialized   = vals[7]; params['initialized'] = initialized

        if PRINT:
            for key, value in params.items():
                print(f'   {key}: {value}')
        return params


    # get position from ERC721 manager (nonfungiblePositionManger) of a given [minted] tokenId
    def get_NPM_position(tokenId, account, PRINT):
        NFPM, NFPMII  = getV3Contracts(1)
        vals          = NFPMII.positions(tokenId,  {"from": account})
        params        = {}
        nonce         = vals[0]; params['nonce']        = nonce
        operator      = vals[1]; params['operator']     = operator
        token0        = vals[2]; params['token0']       = token0 #getMERC20(token0)
        token1        = vals[3]; params['token1']       = token1 #getMERC20(token1)
        fee           = vals[4]; params['fee']          = fee
        tickLow       = vals[5]; params['tickLow']      = tickLow
        tickHigh      = vals[6]; params['tickHigh']     = tickHigh
        liquidity     = vals[7]; params['liquidity']    = liquidity
        feeGrowthIn   = vals[8]; params['feeGrowthIn']  = feeGrowthIn
        feeGrowthOut  = vals[9]; params['feeGrowthOut'] = feeGrowthOut
        token0Owed    = vals[10]; params['token0Owed']  = token0Owed
        token1Owed    = vals[11]; params['token1Owed']  = token1Owed

        token_names = {}
        if PRINT:
            TOKENS = ["token0", "token1"]
            print(f'\nNFT POSITION:')
            for key, value in params.items():
                if key in TOKENS:
                    token = interface.myERC20(value)
                    Symbol = token.symbol()
                    print(f'   {key}: {Symbol}')
                    token_names[key+'_name'] = Symbol.lower()
                if key not in TOKENS:
                    print(f'   {key}: {value}')
        
        params.update(token_names)
        return params


    # get position from ERC721 manager (nonfungiblePositionManger) of a given [minted] tokenId
    def get_pool_position(
            account,
            pool,
            liquid, # as in liquidityMiner
            tickLow, 
            tickHigh, 
            PRINT): 

        # assuming the pool still recognized NFPM II as the owner [default when minting]. change if not.
        owner = config["networks"][network.show_active()]['MNonfungiblePositionManagerII']
        pool_pos = pool.getPoolPosition(owner, tickLow, tickHigh) 

        # instead of the easy way, we can also get the pool position by calculating the corresponsing pool key. 
        # with modification to the _updatePosition function of the pool contract, this approach also enables us
        # to view ALL minted/ modified positions to the pool [see commented out lines below]

        get_position_by_key = True
        if get_position_by_key:

            pool_position_key = liquid.compute(
                owner, 
                tickLow, 
                tickHigh)
            print(F'\npool_position_key: {pool_position_key} ')
            print(F'owner: {owner}')

            pool_key_pos = pool.positions(pool_position_key) 
            print(f'\n [KEY position]:\n {pool_key_pos}')

            # if for any reason we want to see ALL positions [the key and owner] *this is unique to MOCK -- not a part of V3 protocol.
            # allKeys = pool.getKeys()     ; print(F'\nall keys: {allKeys}')
            # allOwners = pool.getOwners() ; print(F'allOwners: {allOwners}')

        pool_pos_dict = {'liquidity': pool_pos[0],
                            'fg_in_last_0': pool_pos[1],
                            'fg_in_last_1': pool_pos[2],
                            'tokensOwed0': pool_pos[3],
                            'tokensOwed1': pool_pos[4]}

        if PRINT:
            print(f'\npool position:\n {pool_pos}')
            for key, value in pool_pos_dict.items():
                print(f'   {key}: {value}')
               
         
        return pool_pos_dict
    
    
    # get slot0 of pool
    def getslot0(V3Pool_contract, PRINT):
        params = {}
        slot0_ = V3Pool_contract.slot0()
        sqrtPriceX96 = slot0_[0]
        params['sqrtPriceX96'] = sqrtPriceX96
        tick = slot0_[1]; 
        params['tick'] =  tick
        observationIndex = slot0_[2]; 
        params['observationIndex'] =  observationIndex
        obsCard = slot0_[3]; 
        params['obsCard'] =  obsCard
        obsCardNext = slot0_[4]; 
        params['obsCardNext'] =  obsCardNext
        feeProtocol = slot0_[5]; 
        params['feeProtocol'] =  feeProtocol
        unlocked = slot0_[6]; 
        params['unlocked'] =  unlocked
        
        
        if PRINT:
            print(f'\n   slot0:')
            print(f'      Tick0    : {tick}')
            print(f'      p_X96    : {sqrtPriceX96}')
            print(f'      obs.Ind.     : {observationIndex}')
            print(f'      obs.Card.    : {obsCard}')
            print(f'      obs.Card.Next: {obsCardNext}')
            print(f'      feeProt.     : {feeProtocol}')
            #print(f'    unlocked     : {unlocked}')
            
        return params

    # load uniswapV3Pool. will create and initialize pool if needed.


    def deployPool(token0_address, token1_address, fee, account):

        factory, factoryII = getV3Contracts(3)

        pool_addr    = factory.getPool(token0_address, token1_address, fee)
        pool_addrII  = factoryII.getPoolII(token0_address, token1_address, fee, {'from':account})  

        tx = factory.createPool(token0_address, token1_address, fee, {'from':account})
        tx.wait(1)
        pool_addr = factory.getPool(token0_address, token1_address, fee, {'from':account})

        txII = factoryII.createPoolII(token0_address, token1_address, fee, {'from':account})
        txII.wait(1)
        pool_addrII = factoryII.getPoolII(token0_address, token1_address, fee, {'from':account})

        # check that MPoolAddress.sol library is accurately calculating the pool address
        # this is vital to a number of processes/ function in the uniswap V3 protocol, 
        # so it is worth checking, although it need not be checked EVERY time a pool 
        # gets loaded, so can be set to False after a couple checks that its working.

        checkAddressComputed = True
        if checkAddressComputed:
            pool_address_computer = get_contract_from_abi('MPoolAddress')
            poolAddress = pool_address_computer.computePoolAddress(
                            factory.address, 
                            token0_address,
                            token1_address,
                            fee)
            
            poolIIAddress = pool_address_computer.computePoolAddressII(
                            factoryII.address, 
                            token0_address,
                            token1_address,
                            fee)

            if pool_addr != poolAddress or poolIIAddress != pool_addrII:
                print(f'\n    [LoadPool] :: !!! pool address calculation error !!! ')
                print(f'      pool_addr  : {pool_addr}')
                print(f'         *computed pool   : {poolAddress}')
                print(f'      pool_addrII: {pool_addrII}')
                print(f'         *computed poolII : {poolIIAddress}')
                print(f'\n*      factory    : {factory.address}')
                print(f'*      factoryII  : {factoryII.address}')           
            
                sys.exit(0)
            print(f'   pool Address: {poolAddress}')
            print(f'   poolII Address: {poolIIAddress}')
            print('    these addresses have been reproduced [calculated] successfully by MPoolAddress.sol library:)')
                
        return pool_addr



    # get pool from tokens [get from address not implemented for Mock protocol]
    def getPoolFromTokenPair(t0, t1, fee, account, UNLOCK, PRINT):
        t0=t0.lower() ; t1=t1.lower()
        token0_address = config["networks"][network.show_active()]['tokens'][t0]
        token1_address = config["networks"][network.show_active()]['tokens'][t1]

        factory, factoryII = getV3Contracts(3)

        poolAddress    = factory.getPool(token0_address, token1_address, fee, {'from':account})
        poolIIAddress  = factoryII.getPoolII(token0_address, token1_address, fee, {'from':account})
        #print(f'\n   poolAddress   : {poolAddress}')
        #print(f'   poolIIAddress : {poolIIAddress}')
        
        if '0000' in poolAddress or '0000' in poolIIAddress: 
            deploy = input(f'{t0}/{t1} pool not deployed. Deploy pools? ["y" = yes, any other key = no]\n')
            if deploy == 'y':
                poolAddress = deployPool(token0_address, token1_address, fee, account)
            if deploy != 'y':
                sys.exit(0)
            liquidity = 0
        
        pool  = interface.IV3Pool(poolAddress)
        token0       = interface.myERC20(str(pool.token0()))
        token1       = interface.myERC20(str(pool.token1()))
        liquidity    = pool.liquidity()
        tick_spacing = int(pool.tickSpacing())

        slot0 = getslot0(pool, False)
        # initialize pool if needed
        if slot0['unlocked'] == False and UNLOCK:
            p = input(f'pool locked. set pool price [{token0.symbol()}/{token1.symbol()}] p =')
            p0_X96 = p_to_x96(float(p))
            print(f'\n   initializing w/ price p = {p0_X96} ')  
            tx     = pool.initialize(p0_X96, {"from": account})
            tx.wait(1)
            slot0 = getslot0(pool, False)

        if PRINT:
            print(f'\nloaded {t0}/{t1}_{fee} pool.')
            print(f'   slot0 unlocked = {slot0["unlocked"]}')
            tick0 = slot0["tick"]
            print(f'   tick0          = {tick0},    compressed = {tick0/tick_spacing}')
            print(f'   slot0.pX96     = {slot0["sqrtPriceX96"]}')
            print(f'   tick_spacing   = {tick_spacing}')
            print(f'   liquidity      = {liquidity}')
            print(f'   fee            = {fee}\n')
        return pool, poolIIAddress, liquidity, tick_spacing, token0, token1, slot0


# ------------------ UNISWAP : Math
if True:
    from decimal import Decimal
    MIN_TICK = -887272
    MAX_TICK = -MIN_TICK
    MIN_SQRT_RATIO = 4295128739
    MAX_SQRT_RATIO = 1461446703485210103287273052203988822378723970342
    Q96  = 2**24 # = 79228162514264337593543950336 # see LiquidityAmounts.sol in v3-periphery
    Q128 = 2**32


    # see tickBitMap.sol library -- maps the initialized ticks, and this makes finding them much more efficent.
    def findBitPos(word_position, word_value, tick_spacing, PRINT):

        binary_word = bin(word_value)[2:].zfill(256)  # Strip '0b' and pad to 256 bits
        if PRINT:
            print(f"\n   word position {word_position} = {word_value}")
            print(f"            = {binary_word} ")

        if word_value == 0:
            print(f'\nno active bits [no ticks initialized]')
            return -1  # No active bits

        # Find the position of the first active bit
        bit_position = 0
        while word_value > 0:
            if word_value & 1:  # Check if the least significant bit is set
                flipMask    = 1 << bit_position
                flipMaskBin = bin(flipMask)[2:].zfill(256) 
                tick= (word_position*256 + bit_position) * tick_spacing
                if PRINT:
                    print(f'   bit position: {bit_position}')
                    print(f'   1 << bitPos = {flipMask}')
                    print(f"            = {flipMaskBin}")
                    #print(f"   XOR      = {0 ^ flipMaskBin}")
                print(f'   tick = {tick} is active.')
                return tick
            word_value >>= 1  # Shift right by one bit
            bit_position += 1
        
        input(f'\n [problem] no active bits.')
        return  -1

    # convert p to sqrtPX96
    def p_to_x96(p):
        pX96 = math.sqrt(p)*(2**96)
        return pX96

    # get sqrtPX96 value at tick
    def sqrtPatTick(tick):
        p = 1.0001**tick
        return p_to_x96(p)
    
    # convert pX96 to p
    def p_from_x96(pX96):
        rootP = pX96/(2**96)
        p = rootP**2
        return p
    
    # check sqrtpX96 values don't pass max/min values
    def SQRT_RATIO_CHECK(root_pX96):
        if root_pX96 <  MIN_SQRT_RATIO:
            raise Exception("root_pX96 <  MIN_SQRT_RATIO")
        if root_pX96 >  MAX_SQRT_RATIO:
            raise Exception("root_pX96 >  MAX_SQRT_RATIO")
    
    # check ticks to surposs max/min values
    def TICK_CHECK(tick):
        if abs(tick) <  MIN_TICK:
            raise Exception(f"abs(tick) = {tick} <  MIN_TICK")

    # get corresponding tick at sqprtX96 value
    def tick_at_sqrt(root_pX96, PRINT):
        SQRT_RATIO_CHECK(root_pX96)
        p = ( root_pX96/(2**96) )**2
        tick = int(math.log(p)/math.log(1.0001))
        TICK_CHECK(root_pX96)
        if PRINT:
            print(f'\nprice/tick at sqrtPX96 = {root_pX96}:')
            print(f'   price = {p}')
            print(f'   tick  = {tick}')
        return p,tick

    def checkPriceLimit(sqrtPriceLimitX96, ZeroForOne, slot0):
        tickLimit = tick_at_sqrt(sqrtPriceLimitX96, False)
        p0 = slot0["sqrtPriceX96"]
        if ZeroForOne:
            if sqrtPriceLimitX96 >= p0 or  sqrtPriceLimitX96 <= MIN_SQRT_RATIO:
                print(f'   REQUIRED: pLimit < p0 & pLimit > pMin')
                print(f'      sqrtPriceLimitX96 = {sqrtPriceLimitX96} ')
                print(f'      p0                = {p0}')
                print(f'      tickLimit         = {tickLimit}')
                sys.exit(0)
        if ZeroForOne == False:
            if sqrtPriceLimitX96 <= p0 or  sqrtPriceLimitX96 >= MAX_SQRT_RATIO:
                print(f'   REQUIRED: pLimit > p0 & pLimit < pMax')
                print(f'      sqrtPriceLimitX96 = {sqrtPriceLimitX96} ')
                print(f'      p0                = {p0}')
                print(f'      tickLimit         = {tickLimit}')
                sys.exit(0)

    """ 
        find liquidity for amounts or amounts for liqudity
        * see liquidityAmounts.sol library in V3 periphery.
        * these functions have been relegated to liquidityMiner.sol contract

        def liquidity_for_amounts(my_math_contract, tick0, tickLow, tickHigh, x, y):
            # x, y - amount 0/1 in wei
            print(f'\nLIQUIDITY FOR AMOUNTS:')
            print(f'   x = {x*1e-18} wei')
            print(f'   y = {y*1e-18} wei')

            p0 = my_math_contract.sqrtPatTick(tick0) 
            pA = my_math_contract.sqrtPatTick(tickLow) 
            pB = my_math_contract.sqrtPatTick(tickHigh)    
            print(f'   p0X96 : {p0} [{p_from_x96(p0)}]')
            print(f'   pAX96 : {pA} [{p_from_x96(pA)}]')
            print(f'   pBX96 : {pB} [{p_from_x96(pB)}]')
            
            LForAmounts = my_math_contract.LForAmounts(p0,pA,pB,x,y)
            print(f'   LForAmounts: {LForAmounts} Wei\n')
            
            return LForAmounts

        def amounts_for_liquidity(my_math_contract, tick0, tickLow, tickHigh, L):
            # x, y - amount 0/1 in wei
            print(f'\nAMOUNTS FOR LIQUIDITY:')
            print(f'   L = {L*1e-18} wei')

            p0 = my_math_contract.sqrtPatTick(tick0) 
            pA = my_math_contract.sqrtPatTick(tickLow) 
            pB = my_math_contract.sqrtPatTick(tickHigh)    
            print(f'   p0X96 : {p0} [{p_from_x96(p0)}]')
            print(f'   pAX96 : {pA} [{p_from_x96(pA)}]')
            print(f'   pBX96 : {pB} [{p_from_x96(pB)}]')
            
            (x,y) = my_math_contract.getAmountsForLiquidity(p0,pA,pB,L)
            print(f'   x: {x*1e-18} Wei')
            print(f'   y: {y*1e-18} Wei')
            
            return x,y
    """
#--------------------- CHAINLINK/ CURRENCY CONVERSION
if True:

    # use chainlinks price-feed service to get the current price of an asset
    def getRoundData(rate_sym, roundID): # https://docs.chain.link/data-feeds/historical-data/
        
        print(f'rate_sym: {rate_sym}')
        price_feed_dict = NETWORK_TO_RATE_DICT[network.show_active()]
        #print(f'price_feed_dict: {price_feed_dict}')
        #sys.exit(0)
        price_feed_address = price_feed_dict[rate_sym]
        price_feed = interface.AggregatorV3Interface(price_feed_address)

        if not roundID:
            roundId,answer,startedAt,updatedAt,answeredInRound = price_feed.latestRoundData()
        if roundID:
            roundId,answer,startedAt,updatedAt,answeredInRound = price_feed.getRoundData(roundID)
        # latest rate
        #answer = float(Web3.fromWei(answer, "ether"))*1e10
        answer = answer*1e-18
        return answer

    def CurrencyConvert(
        amount, 
        Asym, 
        Bsym,
        A_to_B
        ):
            AB_sym   = Asym + '_' + Bsym
            AB_rate  = getRoundData(AB_sym, None)

            # calculate converted amount
            if A_to_B:

                # convert B amount to USD
                B_USD_sym = Bsym + '_USD'
                B_USD = getRoundData(B_USD_sym, None)

                B_in_A   = amount*AB_rate
                B_in_USD = B_in_A*B_USD

                print(f'   {AB_sym}  = {AB_rate}:')
                print(f'   {amount*1e-18} {Asym} = {B_in_A*1e-18} {Bsym} ')
                print(f'                                 = {B_in_USD*1e-18} USD ')

                return B_in_A, B_in_USD

            if A_to_B == False:

                # convert A amount to USD
                A_USD_sym = Asym + '_USD'
                A_USD     = getRoundData(A_USD_sym, None)

                BA_rate  = 1/AB_rate ; BA_sym   = Bsym + '_' + Asym
                A_in_B   = amount*BA_rate
                A_in_USD = A_in_B*A_USD

                print(f'   {BA_sym}  = {BA_rate}:')
                print(f'   {amount*1e-18} {Bsym} = {A_in_B*1e-18} {Asym} ')
                print(f'                         = {A_in_USD*1e-18} USD ')
            
                return A_in_B, A_in_USD

    def seconds_to_date(seconds_since_epoch):
        # input: seconds since last epoch. returns date and time format
        return datetime.datetime.fromtimestamp(seconds_since_epoch)

    def date_to_seconds(dateTime):
        # input: datetime.datetime(2023, 9, 1, 12, 30, 0)
        # returns: seconds since last epoch
        return  dateTime.timestamp()

