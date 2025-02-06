
from scripts.Load.misc_funcs import (  
    sys,
    time,
    getPoolFromTokenPair,
    get_contract_from_abi,
    approve_contract_spender,
    get_accounts,
    get_Token_bal,
    checkPriceLimit,
    getMERC20,
    p_from_x96,
    tick_at_sqrt,
    MIN_SQRT_RATIO, MAX_SQRT_RATIO)
from scripts.Load.BrownieFuncs import gas_controls, listenForEvent, getEvents, update_listening_dict

# load contracts/ accounts/ gas control check
router    = get_contract_from_abi('MSwapRouter')
swapper   = get_contract_from_abi('MSwapper')
account  = get_accounts(0) # 0 = explorer account, 1 = google chrome account
acct_bal = gas_controls(account, set_gas_limit=False, Priority_fee=25)



def swap_():

    print('\n_______________singleSwap.py_______________\n')

    #    ============ SET PARAMETERS ===============
    
    # load pool parameters
    # Choose tokens to swap (determines what pool to load, not what token is tokenIn/Out)
    # *the pool assigns token0 as the token with the lower address (token0<token1--see re-order tokens below)
    ta, tb              = 'sand', 'weth'   # choose token names (e.g. 'link', 'weth' -- should match token entires in config file)
    fee = 500 ; unlock_pool = True # initialize pool if it is locked
        
    # event listening
    listenForSpecificEvents = True # if False will instead print tx.events (in a readable format)
    listenForRepeats        = False # listen for repeated emits
    # if not troubleshooting, can either 
    #           A) attempt full transaction [option 0] or
    #           B) bypass state-changes and emit events of interest [options 20-23] 
    singleSwapOption = 0   
                                # 0 : no revert: attempt full transaction
                                # >20 : bypass callback payment and other state-changing lines in router/ pool contracts,
                                #       but emit misc. payment amounts/ parameters
                                    # 20: router callback pay parameters

                                # *Remaining options deal with events emitted in the while loop of the pool::swap(..) function
                                    # 21: (step.tickNext, 
                                    #      state.amountSpecifiedRemaining, 
                                    #      state.amountCalculated) [in while loop]  
                                    #     + swap amounts [after while loop]
                                    # 22: (step.tickNext, 
                                    #      state.sqrtPriceX96, 
                                    #      state.sqrtPriceNextX96,
                                    #      step.sqrtPriceTartgetX96) [in while loop]
                                    #     + swap amounts [after while loop]
                                    # 23:  (step.tickNext, 
                                    #      step.amountIn, 
                                    #      step.amountOut, 
                                    #      step.feeAmount) [in while loop]
                                    #     + swap amounts [after while loop]
                                    
    # troubleshooting        
    TroubleshootRange  = False 
    rangeOptionStart   = 6;  rangeOptionEnd = 12 # set option range if troubleshoot == True
        # for troubleshooting; set option parameter value(s) to trigger a revert statement
        # at a specified location in the call. This lets you know [about] where
        # the call is reverting.

        # [CONTRACT] :: [FUNCTION] [OPTION VALUE(S)]
        # Swapper :: swapExact 1-2 [ not relevant to single swaps :: see multiHopSwap.py]
            #    ---- 3-5 not implemented ----
            # Router :: exactInputInternal 5 
                # pool :: swap          6-8    
                    # pool :: RouterPaymentCallback   9  
                        # router :: uniswapV3SwapCallback   10-11  
                        #                                   * 20  bypasses payment in callback. listen for pay amounts 
        

    # swap parameters
    InputSwap           = True      # True = exactInputSingle, False = exactOutputSingle
                                    # * the differenc has nothing to do with the direction of swap!
    zeroForOne          = False     # swap direction: True: swap token0 for token1. False: opposite.
    sqrtPriceLimitX96   = 0
            # [see below...or router] sqrtPriceLimitX96 == 0
            #    ? (zeroForOne ? TickMath.MIN_SQRT_RATIO + 1 : TickMath.MAX_SQRT_RATIO - 1)
            #    : sqrtPriceLimitX96,

    approvalAmount    = 50*1e18 # approve Router to spend approvalFactor*amountSpecified
    𐤃deadline         = 40 # additional seconds added to block.timestamp() for deadline [see deadline below]
    recipient         = account.address
    amount            = 0.3*1e18 # swap amount
    amountMinMax      = 0
    
    #            ============================================

    # load pool
    pool, poolIIAddress, liquidity, tick_spacing, token0, token1, slot0 = getPoolFromTokenPair(
        ta, tb, fee, account, unlock_pool)

    if liquidity == 0:
        print(f'\n!!! this pool has 0 liquidity. pool.swap(...)::computeSwapStep(...) will calculate zero values for amountIn/Out')
        input(f'liquidity = {liquidity}')

    # re-order tokens so that router calculatese zeroForOne same as we have chosen our zeroForOne value.
    # *the pool assigns token0 as the token with the lower address (token0<token1-
    if zeroForOne:
        tokenIn,tokenOut = token0,token1
    if zeroForOne==False:
        tokenIn,tokenOut = token1,token0

    # approve router to take account funds
    approve_contract_spender(approvalAmount, tokenIn, router, account)

    # event listener
    if listenForSpecificEvents and TroubleshootRange==False:
        update_listening_dict(pool.address, 'pool')
        eventOptions = {0:[], # attempt full transaction -- can add events to listen for if desired.
                        20:  [[router, "SwapCallback"]], # swap pay amounts/ router callback payment parameters
                        # *remaining options are in/ after while loop in pool::swap(...) function which 
                        # calculates amounts to send to router for payment in callback function
                        21: [[pool,"SteppedAmounts"], # Swap amounts + detailed step calculations of amount0/1 [or remaining/ calculated] calculated in while loop
                                [pool,"SwapAmounts"]],
                        22: [[pool,"SteppedPrices"], # Swap amounts + detailed step calculations of prices in while loop
                                [pool,"SwapAmounts"]],
                        23: [[pool,"SwapStepAmounts"], # Swap amounts + detailed step calculations of amountIn/Out in while loop
                                [pool,"SwapAmounts"]]
                            }
        eventList = eventOptions[singleSwapOption]
        listenForEvent(eventList, listenForRepeats)
        
    # set sqrtPriceLimitX96 to min/max (see router :: exactOutputInternal)
    if sqrtPriceLimitX96==0:
        if zeroForOne:
            sqrtPriceLimitX96 = MIN_SQRT_RATIO+1
        if zeroForOne==False:
            sqrtPriceLimitX96 = MAX_SQRT_RATIO-1

    print(F'\nswap parameters:')
    print(f'    tokenIn   : {tokenIn.symbol()}')
    print(f'    tokenOut  : {tokenOut.symbol()}')
    print(f'    zeroForOne: {zeroForOne} ')
    print(f'    𐤃deadline : {𐤃deadline}')

    print(F'\npool state:')
    print(f'    slot0.tick         = {slot0["tick"]}')
    print(f'    slot0.sqrtPriceX96 = {slot0["sqrtPriceX96"]} ')
    print(f'    sqrtPriceLimitX96  = {sqrtPriceLimitX96} ')
    print(f'    pool liquidity     = {liquidity}\n')

    # *Check priceLimit is valid.
    checkPriceLimit(sqrtPriceLimitX96, zeroForOne, slot0)

    # Get Inital Balances
    balIn0  = get_Token_bal(tokenIn, account.address, 'my [In] ',  True)
    balOut0 = get_Token_bal(tokenOut, account.address, 'my [Out]', True)
    
    # set parameters for Exact Input/ Output swaps
    deadline          = swapper._blockTimestamp() + 𐤃deadline
    ExactSingleParams = (
        tokenIn.address,       # tokenIn
        tokenOut.address,      # tokenOut
        fee,   
        recipient,     # recipient
        deadline,      # deadline
        amount,        # amount In/Out
        amountMinMax,  # amount Out/In Minimum
        sqrtPriceLimitX96 # sqrtPriceLimitX96
    )
    
    # troubleshooting single swaps
    if TroubleshootRange:
        
        revert_option = rangeOptionStart 
        while revert_option <= rangeOptionEnd:
            try: 
                if InputSwap:
                    print(F'\n------exact single in swap ({revert_option})')
                    tx = router.exactInputSingle(
                                    ExactSingleParams,
                                    revert_option, 
                                    {"from": account})

                if InputSwap==False:
                    print(F'\n------exact single out swap ({revert_option})')
                    tx = router.exactOutputSingle(
                                    ExactSingleParams,
                                    revert_option, 
                                    {"from": account})
                tx.wait(1)
            except Exception as e:
                print(f'    swap{revert_option} failed {e}')
            revert_option += 1
            time.sleep(2)

        
        #-----------------------------------------------
        
    if TroubleshootRange == False:   
            
        # Execute exact single swap
        if InputSwap:
            print(f'\nswapping [single input, amount = {amount*1e-18}]...')
            tx = router.exactInputSingle(
                            ExactSingleParams,
                            singleSwapOption, 
                            {"from": account})

        if InputSwap==False:
            print(f'\nswapping [single output, amount = {amount*1e-18}]...')
            tx = router.exactOutputSingle(
                            ExactSingleParams,
                            singleSwapOption, 
                            {"from": account})
        
        tx.wait(1)

        # if not listenForSpecificEvents, get whatever tx events emitted.
        if listenForSpecificEvents == False:
            getEvents(tx)

    # calculate change in balances           
    get𐤃s = True 
    if get𐤃s:
        print('\n')
        balIn1  = get_Token_bal(tokenIn, account.address, 'my [In] ',  True)
        𐤃In     = balIn1 - balIn0 
        print(f'          𐤃In  = {𐤃In*1e-18} Wei')

        balOut1 = get_Token_bal(tokenOut, account.address, 'my [Out]', True)
        𐤃Out    = balOut1 - balOut0 
        print(f'          𐤃Out = {𐤃Out*1e-18} Wei')
    


def main():
    swap_()
    print('\n=============== end swap.py =====================\n')

