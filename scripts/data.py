from scripts.Load.misc_funcs import ( 
    getPoolFromTokenPair,
    get_accounts,
    findBitPos,
    MIN_TICK, MAX_TICK,
    network
    )

from scripts.Load.positionPlottingFuncs import(
    updateTicksInfoFile,
    plotTickValues,
    updateNFPMPositionsFile,
    updatePoolPositionsFile,
    plotNFTPosition
)
from scripts.Load.BrownieFuncs import gas_controls, config, listenForEvent
import sys, time


#                   __________SELECTION___________

# 1  : update pool tick info 
# 2  : update NFTPM position info
# 3  : plot pool tick info
# 4  : plot NFTPM position
# 5  : PLOT NFTPM position + ticks 

# 100 : convert an amount of one currency to units of another currency (and vice-versa)

OPTIONS = [0]

def main():

    NETWORK  = network.show_active()z

    # load pool parameters
    # even if plotting these values need to be entered to construct poolName.
      #  ta = 'link'   tb = 'sand'  tc = 'weth'
    t0 = 'link' ;  t1 = 'sand' ; unlock_pool = True  ; fee = 500  
    poolName = f'{t0}'+'_'+f'{t1}' + '_' + NETWORK + '_'+str(fee)

    # options 0-2 require connecting to the network. 
    # don't load pool if not needed.
    network_options = [1,2]
    if set(network_options) & set(OPTIONS):
        
        account  = get_accounts(0) # 0 = explorer account, 1 = google chrome account
        acct_bal = gas_controls(account, set_gas_limit=False, Priority_fee=25)

        # load pool
        pool, poolIIAddress, liquidity, tick_spacing, token0, token1, slot0 = getPoolFromTokenPair(
            t0, t1, fee, account, unlock_pool)

        tick0 = slot0['tick'] ;
        print(f'\nloaded {poolName} pool. tick0 = {tick0}')
        print(f'   slot0 [unlocked: {slot0["unlocked"]}]')
        print(f'   tick0        = {tick0},    compressed = {tick0/tick_spacing}')
        print(f'   slot0.pX96   = {slot0["sqrtPriceX96"]}')
        print(f'   tick_spacing = {tick_spacing}')
        print(f'   liquidity    = {liquidity}')
        print(f'   fee          = {fee}')

        #pool Address: 0xc9537E0507F9396c4161532Cbcf928D94275E6BC
        #poolII Address: 0x17C7eFCEdC9Bc9662948AC45c274Cc0E440bFaFa
    
    #______________[1]UPDATE TICK INFO DATA FILE____________
    if 1 in OPTIONS:
        """
        NOTES:
            * ticks.update only called when adding/ decreasing liquidity [this initializes a tick]
            * ticks.cross only called when swapping and if step.initialized == True [if the tick being crossed
              has been initialized]. This value comes from 
            TickBitmap.nextInitializedTickWithinOneWord(...), Consequently, if the tick bieng crossed isn't initialized,
            none of the ticks parameters will be altered.

             ----->>> so we only need to worry about ticks which have been initialized <<-------

             the following algorithm uses the tickBitmap mapping of the pool contract and the library
             TickBitmap.sol's logic* to find initialized ticks. This is much more efficient than querying every
             possible tick!!

             *see README file for an overview of this logic
        """ 
        
        print(f'\n    ________Updating Ticks data for {t0}_{t1}...')

        #        _______PARAM INPUTS________

        queryAllWords    = False  # query all possible word positions
        word_positions   = []     # if above is False, set list of word positions to be queried, or leave blank if words have already been queried.
        # * example:
        #       word_positions   = [-10,-,9,-8,-,...,8,9,10] 
        queriedWordsDict = {}     # leave blank if queryAllWords is set to True. 
        # use if the word positions have already been queried and the value of words in these positions are known. 
        # dictionary should have the structure {word_position : word_value}
        # * example:
        #     queriedWordsDict = {    
        #           -58:2305843009213693952, 
        #            57: 50216813883093446110686315385661331328818843555712276103168
        #           } 

        if queryAllWords:
            # first search down to minimum possible word for ticks which have been 'flipped'. 
            # Then search up to maximum possible word. Make a list of all flipped words. Later, we expand the words
            # into bits [there are 256 bits per word].  This will tell us which [compressed] tick values to get more 
            # detailed info on. 
            # overall, this is more efficient than simply going through all possible tick values. 
            MIN_WORD_POS = int((MIN_TICK/tick_spacing)/256 - 1) ; print(f'\nMIN_WORD: {MIN_WORD_POS}')
            MAX_WORD_POS = -MIN_WORD_POS                        ; print(f'MAX_WORD: {MAX_WORD_POS}')
            wordsToQueryList = np.arrange([MIN_WORD_POS, MAX_WORD_POS, 1])

        # query pool.tickBitmap for target word Position values.
        if len(wordsToQueryList) > 0:
            queriedWordsDict = {}
            print(f'\nfinding non-zero words...')
            for i in wordsToQueryList:
                tickBit = pool.tickBitmap(i)
                if tickBit != 0:
                    queriedWordsDict[i] = int(tickBit) ; input(f'   word {i}: {tickBit}, {type(tickBit)}')
                print(f'{i} = 0')
                i += 1

        # find initialized tick values
        print(f'\nexamining word values to find initialized ticks ...')
        ticks_to_query = []
        for wordPos, WordValue in queriedWordsDict.items():
               tick = findBitPos(wordPos, WordValue, tick_spacing, False)
               ticks_to_query.append(tick)

        # append tick0
        ticks_to_query.append(tick0)

        updateTicksInfoFile(
            pool, 
            poolName, 
            tick0, 
            ticks_to_query, 
            tick_spacing)

    #______________[2]UPDATE POSITION INFO_______________
    if 2 in OPTIONS:
        updateNFPMPositionsFile(account, poolName)
        updatePoolPositionsFile(account, poolName, pool) # redeploy liquid/ mint, then try

    #______________[3]PLOT TICK INFO_________________
    if 3 in OPTIONS:
        keyList   = {
            'liquidityGross': ['blue', 0.5],
            'liquidityNet': ['green', 0.5]
        }
        tick_margin = 10000 
        bar_width   = 1000
        plotTickValues(keyList, poolName, tick_margin, bar_width, True)

    #______________[4]PLOT NFT POSITION__________________
    if 4 in OPTIONS:

        tokenIds = [1,2]
        tick_margin = 10000
        NFTPlotKeyList = {
            'liquidity': ['blue', 0.5],
            'feeGrowthIn': ['green', 0.5],
            'feeGrowthOut': ['red', 0.5],
            'token0Owed': ['black', 0.5],
            'token1Owed': ['gray', 0.5]
        }
        plotNFTPosition(NFTPlotKeyList, tokenIds, tick_margin, poolName, True)

    #______________[5]PLOT NFT+TICKS POSITION____________
    if 5 in OPTIONS:
        from plotly.subplots import make_subplots
        import plotly.offline as pyo
        
        #------------- CREATE TICK GRAPH
        keyList   = {
            'liquidityGross': ['blue', 0.8],
            'liquidityNet': ['blue', 0.1]
        }
        tick_margin = 10000 
        bar_width   = 1000
        tick_fig    = plotTickValues(keyList, poolName, tick_margin, bar_width, False)
        


        #------------- CREATE NFT GRAPH

        tokenIds = [1,2]
        tick_margin = 10000
        NFTPlotKeyList = {
            'liquidity': ['blue', 0.5],
            'feeGrowthIn': ['green', 0.5],
            'feeGrowthOut': ['red', 0.5],
            'token0Owed': ['black', 0.5],
            'token1Owed': ['gray', 0.5]
        }
        NFPM_figs = plotNFTPosition(NFTPlotKeyList, tokenIds, tick_margin, poolName, False)

        #------------ MAKE COMBINED FIGURE:
        figList = NFPM_figs + [tick_fig]
        # Use make_subplots to combine figures
        fig_combined = make_subplots(rows=len(tokenIds)+1, cols=1, shared_xaxes=True)

        # Add individual figures as subplots
        for i, f in enumerate(figList):
            for trace in f.data:
                fig_combined.add_trace(trace, row=i+1, col=1)
            if i < len(figList)-1:
                fig_combined.update_yaxes(
                    title_text=f"Token ID: {tokenIds[i]}",  # Customize label as needed
                    row=i+1,
                    col=1
                )
            if i == len(figList)-1:
                fig_combined.update_yaxes(
                    title_text=f"pool ticks",  # Customize label as needed
                    row=i+1,
                    col=1
                )
        fig_combined.update_layout(
            title ='ticks + NFPM positions',
            barmode='group',
            bargap=0.0,
            bargroupgap=0
        )

        # check if plot already exists. crete if not. override if so.
        plot_file_path = f'data//plots//tick_and_NFPM_positions//{poolName}.html'
        pyo.plot(fig_combined, filename=plot_file_path)
    



