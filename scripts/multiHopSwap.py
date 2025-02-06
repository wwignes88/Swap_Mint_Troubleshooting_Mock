
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
#acct_bal = gas_controls(account, set_gas_limit=False, Priority_fee=25)


def swap_():

    print('\n_______________multiHopSwap.py_______________\n')

#    ============ SET PARAMETERS ===============

    # load pool paramaters
    # Choose tokens to swap (determines what pools to load, not what token is tokenIn/Out)
    # poolA = ta/tb pool. poolB = tb/tc pool
    ta = 'link' 
    tb = 'weth' 
    tc = 'sand'
    feeA = 500 ; feeB = 500

    # if not troubleshooting, can either 
    #           A) attempt full transaction [multiSwapOption = 0] or
    #           B) bypass state-changes and listen for emitted events of interest [multiSwapOption = [20-23]] 
    
    # event listening (see multiSwapOption below for options list)
    listenForSpecificEvents = True  # if False will instead print tx.events (in a readable format)
    listenForRepeats        = False # listen for repeated emits
    listenToFirstPool       = True
    
    multiSwapOption = 20   
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

    # troubleshooting  (listenForSpecificEvents == False)      
    TroubleshootRange  = True 
    rangeOptionStart   = 13;  rangeOptionEnd = 15 # set option range if troubleshoot == True
        # for troubleshooting; set option parameter value(s) to trigger a revert statement
        # at a specified location in the call. This lets you know [about] where
        # the call is reverting.

        #  the following is a list of troubleshooting options
        #   [CONTRACT] :: [FUNCTION] [OPTION VALUE(S)]
        #   Swapper :: swapExact 1-2 [ not relevant to single swaps :: see multiHop swap (option 2)]
                # Router :: exactInputInternal 3 
                    # pool :: swap          4-5                         ... second swap: 10-11
                        # pool :: RouterPaymentCallback   6             ... second swap: 12
                            # router :: uniswapV3SwapCallback   7-8     ... second swap: 13-14

                    
    # swap parameters
    InputSwap           = False      # True = swapper.MultiHop_Input, False = swapper.MultiHop_Output
                                    # * the differenc has nothing to do with the direction of swap!
    zeroForOne          = False     # swap direction: True: swap token0 for token1. False: opposite.
    sqrtPriceLimitX96   = 0
            # [see below...or router] sqrtPriceLimitX96 == 0
            #    ? (zeroForOne ? TickMath.MIN_SQRT_RATIO + 1 : TickMath.MAX_SQRT_RATIO - 1)
            #    : sqrtPriceLimitX96,

    𐤃deadline           = 40 # additional seconds added to block.timestamp() for deadline [see deadline below]
    recipient           = account.address
    amountIn  = 0.05*1e18 ; amountOutMin =  0             # InputSwap = True
    amountOut = 0.01*1e18 ; amountInMax  = 10*amountOut   # InputSwap = False
    
    #            ============================================
    t0 = 'link' ;  t1 = 'sand' ; unlock_pool = True  ; fee = 500  
    # only need pools for event listening. but it helps check liquidity is non-zero as well. 
    poolA, poolIIA_address, liquidityA, tick_spacingA, token0A, token1A, slot0A = getPoolFromTokenPair(
        ta, tb, feeA, account, False, True)
    
    poolB, poolIIB_address, liquidityB, tick_spacingB, token0B, token1B, slot0B = getPoolFromTokenPair(
        tb, tc, feeB, account, False, True)


    if liquidityA == 0 or liquidityB == 0:
        print(f'\n!!! one or both of these pools have 0 liquidity. ')
            # pool.swap(...)::computeSwapStep(...) will calculate zero values for amountIn/Out')
        print(f'    {ta}/{tb}, feeA = {feeA} : liquidityA = {liquidityA}')
        print(f'     poolA: {poolA.address}')
        print(f'    {tb}/{tc}, feeB = {feeB} : liquidityB = {liquidityB}\n')
        print(f'     poolB: {poolB.address}')
        sys.exit(0)

    # load tokens directly instead of relying on pool because its too much of a hastle to account for ordering.
    # in the multihop case zeroForOne=token0<token1 value is so much our our concern anyway.
    tokenA = getMERC20(ta) ; balA_0  = get_Token_bal(tokenA, account.address, f'my {ta} ',  True)
    tokenB = getMERC20(tb) ; balB_0  = get_Token_bal(tokenB, account.address, f'my {tb} ',  True)
    tokenC = getMERC20(tc) ; balC_0  = get_Token_bal(tokenC, account.address, f'my {tc} ',  True)

    # ******
    test = False
    if test:
        print(f'\n   tokenA: {tokenA.symbol()}')
        print(f'   tokenB: {tokenB.symbol()}')
        print(f'   tokenC: {tokenC.symbol()}')

        test_option = 12
        (hasMultiPool, swapPath, tokenIn, tokenOut, fee, zeroForOne, poolAddress) = router.pathSwapParams(
            feeA, feeB, tokenA, tokenB, tokenC, test_option
        )


        """
            ta = 'link' 
            tb = 'sand' 
            tc = 'weth'

        link = "0xf4447503eb3a9E9574627B01D38956C140fd42dC"
        sand = "0x84362d16D098c509e77029E0D4A6175B1A483b3e"
        weth = "0x98cf8300719ae8362D2f2ec4959D9d5191c4Ce03"

        poolA       : 0xaeE68F0ed1fB160E569f7Aba68765983f20628A4 [link/sand]
        poolB       : 0xB8680b3E8b3C408373eC02D29811Ed5ABE8Fd2Bf [weth/sand]
            link/sand : 0xaeE68F0ed1fB160E569f7Aba68765983f20628A4
            weth/sand : 0xB8680b3E8b3C408373eC02D29811Ed5ABE8Fd2Bf
            xx weth/link : 0xefDc4dfAb80A51e51288ebD7D35655BF6e5a9551
            

        weth : "0x98cf8300719ae8362D2f2ec4959D9d5191c4Ce03"
        sand : "0x84362d16D098c509e77029E0D4A6175B1A483b3e"
        link : "0xf4447503eb3a9E9574627B01D38956C140fd42dC"

        A:
           hasMultiPool: True
                                                               sand |      |                                    link|     |weth
            swapPath    : 0x84362d16d098c509e77029e0d4a6175b1a483b3e|000bb8|f4447503eb3a9e9574627b01d38956c140fd42dc|000bb8|98cf8300719ae8362d2f2ec4959d9d5191c4ce03
            tokenIn     : sand
            tokenOut    : link
            fee         : 3000
            zeroForOne  : True
            poolAddress : poolA [link/sand]

        B:
            hasMultiPool: False
                                                                link|      |weth
            swapPath    : 0xf4447503eb3a9e9574627b01d38956c140fd42dc|000bb8|98cf8300719ae8362d2f2ec4959d9d5191c4ce03
            tokenIn     : link
            tokenOut    : weth
            fee         : 3000
            zeroForOne  : False
            poolAddress : 0xefDc4dfAb80A51e51288ebD7D35655BF6e5a9551 [weth/link]


        """
        print(f'\ntest:')
        print(f'   hasMultiPool: {hasMultiPool}')
        print(f'   swapPath    : {swapPath}')
        print(f'   tokenIn     : {tokenIn}')
        print(f'   tokenOut    : {tokenOut}')
        print(f'   fee         : {fee}')
        print(f'   zeroForOne  : {zeroForOne}')
        print(f'   poolAddress : {poolAddress}')


        print(f'\n  ')
        print(f'   poolA : {poolA.address}')
        print(f'   poolB : {poolB.address}')
        print(f'   in/out : {router.getPool(tokenIn, tokenOut, fee)}')


        sys.exit(0)
    #--------------------

    # adjust parameters to be in line with In/Out swap.
    if InputSwap:
        amount = amountIn
        inOut_str = 'input swap'
        transferAmount = amountIn
        transferToken = tokenB
    if InputSwap==False:
        amount = amountOut
        inOut_str = 'output swap'
        transferAmount = amountOut*5 # <<<------- need to calculate this
        transferToken  = tokenA

    """
    print(F' exactOut: {ta})
    ta = 'link' 
    tb = 'weth' 
    tc = 'sand'
        [emitted] SwapCallback :
        tokenIn: weth
        tokenOut: sand
        amountToPay: 33530275869035671
        isExactInput: False
        sender: poolB
        payer: MSwapper

        [emitted] SwapCallback :
        tokenIn: sand
        tokenOut: link
        amountToPay: 10118689508701058
        isExactInput: False
        sender: poolA
        payer: MSwapper
    """
    # approve MSwapper.sol to takeapprovalAmount transferToken 
    approve_contract_spender(transferAmount, transferToken, swapper, account)

    # event listener
    if listenForSpecificEvents and TroubleshootRange == False:
        
        if listenToFirstPool:
            watchPool   = poolA
        if listenToFirstPool==False:
            watchPool   = poolB
            
        update_listening_dict(poolA.address, 'poolA')
        update_listening_dict(poolB.address, 'poolB')
        eventOptions = {0:[], # attempt full transaction -- can add events to listen for if desired.
                        20:  [[router, "SwapCallback"],
                              [router, "exactInInternal"]], # swap pay amounts/ router callback payment parameters
                        # *remaining options are in/ after while loop in pool::swap(...) function which 
                        # calculates amounts to send to router for payment in callback function
                        21: [[watchPool,"SteppedAmounts"], # Swap amounts + detailed step calculations of amount0/1 [or remaining/ calculated] calculated in while loop
                            [watchPool,"SwapAmounts"]],
                        22: [[watchPool,"SteppedPrices"], # Swap amounts + detailed step calculations of prices in while loop
                            [watchPool,"SwapAmounts"]],
                        23: [[watchPool,"SwapStepAmounts"], # Swap amounts + detailed step calculations of amountIn/Out [from computeSwapStep] in while loop
                            [watchPool,"SwapAmounts"]]
                            }
        eventList = eventOptions[multiSwapOption]
        listenForEvent(eventList, listenForRepeats)


    print(F'\nswap parameters:')
    print(f'    tokenA   : {ta}')
    print(f'    tokeB    : {tb}')
    print(f'    tokeC    : {tc}')
    print(f'    amount   : {amount*1e-18}')
    print(f'    in/Out   : {inOut_str}')

    # troubleshooting single swaps
    if TroubleshootRange:
        increment = 1
        if rangeOptionStart < 0:
            increment = -1
        revert_option = rangeOptionStart 
        while abs(revert_option) <= abs(rangeOptionEnd):
            try: 
                if InputSwap:
                    print(F'\n------MultiHop_Input ({revert_option})')
                    tx = swapper.MultiHop_Input(
                                    amountIn,
                                    transferAmount,
                                    amountOutMin, 
                                    tokenA.address,
                                    tokenB.address,
                                    tokenC.address,
                                    transferToken.address,
                                    feeA,
                                    feeB,
                                    revert_option,
                                    {"from": account})

                if InputSwap==False:
                    print(F'\n------MultiHop_Output ({revert_option})')
                    tx = swapper.MultiHop_Output(
                                    amountOut,
                                    transferAmount,
                                    amountInMax, 
                                    tokenA.address,
                                    tokenB.address,
                                    tokenC.address,
                                    transferToken.address,
                                    feeA,
                                    feeB,
                                    revert_option,
                                    {"from": account})
                tx.wait(1)
            except Exception as e:
                print(f'    swap{revert_option} failed {e}')
            revert_option += increment
            time.sleep(2)

        
        #-----------------------------------------------
        
    if TroubleshootRange == False:   

        if InputSwap:
            print(F'\n------MultiHop_Input ')
            tx = swapper.MultiHop_Input(
                            amountIn,
                            amountOutMin, 
                            tokenA.address,
                            tokenB.address,
                            tokenC.address,
                            transferToken.address,
                            multiSwapOption,
                            {"from": account})

        if InputSwap==False:
            print(F'\n------MultiHop_Output')
            tx = swapper.MultiHop_Output(
                            amountOut,
                            amountInMax, 
                            tokenA.address,
                            tokenB.address,
                            tokenC.address,
                            transferToken.address,
                            feeA,
                            feeB,
                            multiSwapOption,
                            {"from": account})

        tx.wait(1)

        # if not listenForSpecificEvents, get whatever tx events emitted.
        if listenForSpecificEvents == False:
            getEvents(tx)

    # calculate change in balances           
    get𐤃s = True 
    if get𐤃s:
        print('\n')
        balA_1 = get_Token_bal(tokenA, account.address, f'my {ta} ',  True)
        balB_1 = get_Token_bal(tokenB, account.address, f'my {tb} ',  True)
        balC_1 = get_Token_bal(tokenC, account.address, f'my {tc} ',  True)
        𐤃A   = balA_1 - balA_0 ; print(f'          𐤃A  = {𐤃A*1e-18} Wei')
        𐤃B   = balB_1 - balB_0 ; print(f'          𐤃B  = {𐤃B*1e-18} Wei')
        𐤃C   = balC_1 - balC_0 ; print(f'          𐤃C  = {𐤃C*1e-18} Wei')




def main():
    swap_()
    print('\n=============== end swap.py =====================\n')

