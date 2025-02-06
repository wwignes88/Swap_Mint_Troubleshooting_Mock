from scripts.Load.misc_funcs import ( 
    getPoolFromTokenPair,
    approve_contract_spender,
    get_contract_from_abi, 
    get_NPM_position,
    find_modulo_zero_tick,
    get_accounts,
    get_Token_bal,
    CurrencyConvert,
    sqrtPatTick,
    network
    )


from scripts.Load.BrownieFuncs import gas_controls, config, listenForEvent
import sys, time

liquid = get_contract_from_abi('MliquidityMiner')
account  = get_accounts(0) # 0 = explorer account, 1 = google chrome account
acct_bal = gas_controls(account, set_gas_limit=False, Priority_fee=25)
NETWORK  = network.show_active()

#                   __________SELECTION___________
# 1   : mint a position
# 2   : add liquidity
# 100 : convert an amount of one currency to units of another currency (and vice-versa)

OPTIONS = [0]

def main():

    

    
    #______________[0]MINT_____________
    if 1 in OPTIONS:
        print(f'\n__________ Mint liquidity position __________')

        # _______________ set params _________________

        # load pool parameters
        t0 = 'link' ;  t1 = 'weth' ; unlock_pool = True  ; fee = 500  

        # set amounts to mint in liquidity position
        x = 5*1e18
        y = 5*1e18

        # find nearest tick to tick0 which is an even multiple of tick_spacing.
        tickLowJump = 3; tickLow_upDown = False # [jump down 3 compressed tick values form tick0]
        tickHighJump = 4; tickHigh_upDown = True # [jump up 4 compressed tick values form tick0]

        predict_liquidity_amounts = True

        # troubleshooting parameters
        troubleshoot    = False 
        revert_option_start  = 8   ; revert_option_max = 9
        single_revert_option = 0
        # transaction will revert at a specified point for each option in a while loop
        # which utilizes the try/except method.

        listenToEvents  = False # same as setting troublshooting option > 50.
            #                      troubleshooting/ minting will be bypassed.  mint function will be 
            #                       executed while bypassing state-changes, but events are still emited.
            #                       event listener will be set up to detec these events (see below)

            # CONTRACT :: FUNCTION :: OPTIONS
            # LMiner :: mintNewPosition 1-2
            #       MNonfung   :: 
            #         MNonfungII   :: 3-4 
            #           MLmanager :: addLiquidity 5
            #               poolII :: mintII
            #                   pool :: _modify   21-22
            #                   pool :: _update   31-34
            #               poolII :: mintII  7                     
            #                   MLmanager :: uniswapV3MintCallback 8-9
            #       >> ERC721 mint
            #       MNonfung   :: mint 10
            #           MNonfungII :: mappoolkey 11-12
            # LMiner :: mintNewPosition 13-15

            # emits [revert option > 50] 
            #   * run the mint function without making any state changes. emits [e.g. payment amounts in callback]
            #     will still be emitted, and selecting this option will trigger an event listener to pick these up.
        #  __________________________________________

        # load pool
        pool, poolIIAddress, liquidity, tick_spacing, token0, token1, slot0 = getPoolFromTokenPair(
            t0, t1, fee, account, unlock_pool, True)
        tick0 = slot0['tick'] 

        tickLow   = find_modulo_zero_tick(tick0, tick_spacing, tickLowJump , tickLow_upDown) # find nearest 
        tickHigh  = find_modulo_zero_tick(tick0, tick_spacing, tickHighJump, tickHigh_upDown)
        print(f'\n   tickLow : {tickLow} [{tickLow/tick_spacing}]')
        print(f'   tickHigh: {tickHigh} [{tickHigh/tick_spacing}]')


        #  ------------- ERC20 bals/ mint if needed

        myBalance0 = get_Token_bal(token0, account.address, 'my', True)
        myBalance1 = get_Token_bal(token1, account.address, 'my', True)

        if myBalance0*1e-18 < 20:
            print(f'\nminting 100 {token0.symbol()}...')
            tx = token0.mint(100*1e18, account.address, {'from':account}) 
            tx.wait(1)
            myBalance0 = get_Token_bal(token0, account.address, 'my', True)

        if myBalance1*1e-18 < 20:
            print(f'\nminting 100 {token1.symbol()}...')
            tx = token1.mint(100*1e18, account.address, {'from': account}) 
            tx.wait(1) 
            myBalance1 = get_Token_bal(token1, account.address, 'my', True)


        # -------------- predict L for amounts
        # calculate liquidity for x,y amounts then exit
        predict_liquidity_amounts = False
        if predict_liquidity_amounts:

            #sqrtRatioX96_0  = liquid.sqrtPatTick(tick0)    ; print(f'\np0X96: {sqrtRatioX96_0}')
            sqrtRatioX96_0  = sqrtPatTick(tick0)           ; #print(f'p0X96: {sqrtRatioX96_0}')
            
            #sqrtRatioX96_Low  = liquid.sqrtPatTick(tickLow)   ; print(f'\npLX96: {sqrtRatioX96_Low}')
            sqrtRatioX96_Low  = sqrtPatTick(tickLow)          ; #print(f'pLX96: {sqrtRatioX96_Low}')

            #sqrtRatioX96_High = liquid.sqrtPatTick(tickHigh)  ; print(f'\npHX96: {sqrtRatioX96_High}')
            sqrtRatioX96_High = sqrtPatTick(tickHigh)         ; #print(f'pHX96: {sqrtRatioX96_High}')
            
            liquidity_for_amounts = liquid.LiquidityForAmounts(
                sqrtRatioX96_0,
                sqrtRatioX96_Low,
                sqrtRatioX96_High,
                x,
                y
            )
            print(f'\nprojected liquidity for amounts: {liquidity_for_amounts*1e-18} [x1e18] ')
            if liquidity_for_amounts == 0:
                print(f'\attempting to mint zero liquidity (must be non-zero)')
                sys.exit(0)

        # --------------- approvals
        print(F'\nApprovals:')
        # approve liquid.sol to transfer my tokens to itself (see mintNewPosition function).
        L_x_allowed = approve_contract_spender(x*5, token0, liquid, account)
        L_y_allowed = approve_contract_spender(y*5, token1, liquid, account)

        # mint params
        mintParams = (
            token0,
            token1,
            x,
            y,
            0, # Amount0Min
            0, # Amount1Min
            tickLow,
            tickHigh,
            fee
                )

        if listenToEvents:
            print(f'\n----------- listening for events...')
            single_revert_option  = 50 # int8 variables used to bypass state changing events
            troubleshoot = False
            NFPM_II    = get_contract_from_abi('MNonfungiblePositionManagerII')
            listenForEvent([[NFPM_II,"MintPayAmounts"]])

        if troubleshoot == False:
            print(f'\n----------- minting liquidity position...')
            tx = liquid.mintNewPosition(
                                    mintParams,
                                    single_revert_option,
                                    {'from': account}
                                )
            tx.wait(1)
            print(f'\n*minted L = {pool.liquidity()} to {t0}/{t1} pool [{pool.address}]')
            mytokenIds = liquid.getTokenIds(account.address)
            print(f'my tokensIds: {mytokenIds}')
            # *minted L = 1065171336027520928 to link/sand pool [0xaeE68F0ed1fB160E569f7Aba68765983f20628A4]
            # my tokensIds: (1,)

        if troubleshoot:
            revert_option = revert_option_start 
            while revert_option <= revert_option_max:
                try:
                    print(f'\n_____ minting liquidity position [troubleshoot option {revert_option}]')
                    tx = liquid.mintNewPosition(
                                            mintParams,
                                            revert_option,
                                            {'from': account}
                                        )
                    tx.wait(1)
                except Exception as e:
                    print(f'    mint{revert_option} failed {e}')

                revert_option += 1
            sys.exit(0)

        time.sleep(2)


    #______________[1]Add liquidity____________
    if 2 in OPTIONS:
        mytokenIds = liquid.getTokenIds(account.address)
        print(f'my tokensIds: {mytokenIds}')

        tokenId = mytokenIds[2]
        myPosition = get_NPM_position(tokenId, account, True)
    

        # load pool
        t0 = myPosition['token0_name'] ;  t1 = myPosition['token1_name']  
        fee = myPosition['fee'] 
        pool, poolIIAddress, liquidity, tick_spacing, token0, token1, slot0 = getPoolFromTokenPair(
            t0, t1, fee, account, False, True)
        tick0 =  slot0['tick']

        tL = myPosition['tickLow'] ; tH = myPosition['tickHigh']
        if tick0 <= tL or tick0 > tH:
            print(f' !! Warning !! this will not add liquidity to pool.')
            sys.exit(0)

        add_amount_0 = 1*1e18
        add_amount_1 = 1*1e18

        tx = liquid.increaseL(tokenId, add_amount_0, add_amount_1, 0, {"from": account})
        tx.wait

        time.sleep(1)
        print(f'   pool liquidity: {pool.liquidity()}')



    #______________[100]PRICE CONVERSION_________________
    if 100 in OPTIONS:
        print(f'\n[100] Price conversion:')
        fromSymbol = 'LINK'
        toSymbol   = 'ETH'
        A_to_B     = False  # True: convert LINK to ETH, False: convert ETH to LINK
        Amount     = 0.0063968*1e18 
        
        CurrencyConvert(
            Amount, 
            fromSymbol, 
            toSymbol,
            A_to_B
        )

