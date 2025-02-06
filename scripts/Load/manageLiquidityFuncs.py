from scripts.Load.misc_funcs import (
    approve_contract_spender,
    getV3Contracts,
    getPoolFromTokenPair,
    get_contract_from_abi, 
    getTickInfo,
    get_NPM_position,
    get_pool_position,
    getMERC20,
    get_pool_position,
    MIN_TICK, MAX_TICK,
    network)
from scripts.Load.BrownieFuncs import gas_controls, config
import numpy as np
import pandas as pd
import os
import plotly.graph_objs as go
#import plotly.express as px
import plotly.offline as pyo
from plotly.subplots import make_subplots
import time, sys
from pathlib import Path
import os.path

"""
functions related to researching pools/ positions to mint. in liquidityMinting.py the user makes a selection:

    #                   __________SELECTION___________
    # 0  : mint a position
    # 1  : update pool tick info 
    # 2  : plot pool tick info

    # 3  : update NFT position info
    # 4  : plot NFT position
    # 5  : PLOT NFT position + ticks 

    # 100 : convert an config["networks"][network.show_active()]['MNonfungiblePositionManager']amount of one currency to units of another currency (and vice-versa)

    OPTIONS = [0]

here functions 1-5 and are defined.

"""

#       ==============================================
#                UPDATE TICK INFO TABLE 
#       ==============================================
def updateTicksInfoFile(
        pool, 
        poolName, 
        tick0, 
        initializedTicks, 
        tick_spacing):

    print('\n---------updateTicksInfoFile:')

    # column headers 
    _headers = np.array([
        'tick',
        'liquidityGross',
        'liquidityNet',
        'feeGrowthOut0',
        'feeGrowthOut1',
        'tickCumulativeOut',
        'secsPerLiquidity',
        'secsOut',
        'initialized'
    ])   
    
    # append tick0 if desired to update slot0.tick

    # create tick data
    tickData = _headers
    i = 0
    for tick in initializedTicks:
        tickInfo = getTickInfo(pool, tick, False)
        time.sleep(0.5)
        tickRow         = np.array([tick])
        stepInitialized = tickInfo['initialized']
        print(f'\n----tick: {tick} [{stepInitialized}]]')
        for key, value in tickInfo.items():
            print(f'   {key}: {value}')
            tickRow = np.append(tickRow, value)
        #print(f'   tickRow: {tickRow}')
        if i == 0:
            tickData = tickRow
        if i > 0:
            tickData = np.vstack([tickData,tickRow])  
        i += 1

    data_file_path = f'data//poolTickData//{poolName}.csv'
    # check if file path exists.
    dfExists = os.path.exists(data_file_path)
    df = pd.DataFrame(tickData , columns=_headers) 
    print(f'\nsaving df: \n{df}...')
    df.to_csv(data_file_path, index=False)  # Set index=False to omit writing row numbers


#       ==============================================
#                         PLOT TICKS
#       ==============================================
def plotTickValues(keysList, poolName, tick_margin, bar_width, PLOT):
    PRINT = False
    print('\n\n________________plotTickValues________________')

    # *tickInfo.csv always updates all key values.
    data_file_path = f'data//poolTickData//{poolName}.csv'
    plot_file_path = f'data//plots//TickPlots//{poolName}.html'

    file_exists = os.path.exists(data_file_path)
    if file_exists == False:
        print(f'\n{poolName} data file does not exist.')
        sys.exit(0)
        
    df        = pd.read_csv(data_file_path) ;  L = len(df) #; print(f'L: {L}')
    df        = df.set_index('tick')
    allTicks  = df.index.to_numpy()
    keys      = df.columns.to_numpy() # label of values to plot
    
    # initizlie figure
    fig = go.Figure()
    
    # ------------------------ get tick0 row
    print(f'\ndf: \n{df}')
    
    tick0DF  = df[::-1].iloc[0:1]
    tick0    = allTicks[-1] # tick0 is always the last row of the data file
    print(f'\ntick0DF: \n{tick0DF}')
    print(f'tick0 = {tick0}')
    custom_data    = tick0DF  #  <<------------ this loop covers only tick0!!

    already_shown_in_key_list = []
    # start plot with tick0 trace
    for key in keys:
        if key in keysList:
            keyValues = tick0DF[key].values

            fig.add_trace(go.Bar(
                x=[tick0], 
                y=keyValues,
                width=bar_width,
                offset=bar_width,
                name='tick0 '+key,
                marker=dict(
                    color='black',  # Base color
                    pattern=dict(
                        shape="x",  # Pattern shape (e.g., '/', '\\', 'x', '.', etc.)
                        size=10,  # Size of the pattern
                        solidity=0.5  # Opacity of the pattern (0 = transparent, 1 = solid)
                    )
                ),
                opacity = 0.5,
                showlegend=True,
                customdata=custom_data,
                hovertemplate=
                '<b>tick: %{x}</b><br>' +
                'liquidityGross: %{customdata[0]}<br>' +
                'liquidityNet: %{customdata[1]}<br>' +
                'feeGrowthOut0: %{customdata[2]}<br>' +
                'feeGrowthOut1: %{customdata[3]}<br>' +
                'tickCumulativeOut: %{customdata[4]}<br>' +
                'secsPerLiquidity: %{customdata[5]}<br>' +
                'secsOut: %{customdata[6]}<br>' +
                'initialized: %{customdata[7]}<br>'
            ))

    #   ________ Create tick [not tick0] fig ________
    """-----------------------------------------------------
        now we repeat the process to add a traces which cover 
        the rest of the ticks. It seems innefficient, but it
        is a result of how we've chosen to save our dataframe; 
        because we do not distinguish tick0's row by anythin other
        than the convention it is the first row, there is no dictionary
        key value which would identify it, and the loop which 
        creates traces to add depends on the column keys, not 
        row indices or tick values.
    """

    dfMain  = df.iloc[0:L-1]   ;  print(f'\ndfMain: \n{dfMain}')
    ticks   = dfMain.index.to_numpy()
    # Create customdata for hover info
    custom_data = dfMain # <<----------------- this loop covers the rest of the [initialized] ticks

    for key in keys:
        if key in keysList:
            keyValues = dfMain[key].values
            # default values
            show_legend = False ; _color = 'black'

            if key in keysList:
                mapped_array = keysList[key]
                _color = mapped_array[0]
                _opacity = mapped_array[1]
                show_legend = True
                    
            fig.add_trace(go.Bar(
                x=ticks, 
                y=keyValues,
                width = bar_width,
                offset=100,
                marker_color = _color,
                opacity=_opacity,
                customdata=custom_data,
                showlegend=show_legend, 
                name = key,
                hovertemplate=
                '<b>tick: %{x}</b><br>' +
                'liquidityGross: %{customdata[0]}<br>' +
                'liquidityNet: %{customdata[1]}<br>' +
                'feeGrowthOut0: %{customdata[2]}<br>' +
                'feeGrowthOut1: %{customdata[3]}<br>' +
                'tickCumulativeOut: %{customdata[4]}<br>' +
                'secsPerLiquidity: %{customdata[5]}<br>' +
                'secsOut: %{customdata[6]}<br>' +
                'initialized: %{customdata[7]}<br>'
            ))
            
    #     _________ PLOT _____________

    # if only plotting pool ticks, PLOT = True. When plotting pool ticks
    # + NFT positions, PLOT = False.
    if PLOT:
        fig.update_layout(
            title ='title',
            barmode='group',
            bargap=0.0,
            bargroupgap=0
        )

        min_tick = np.min(allTicks) 
        min_tick = min_tick - tick_margin

        max_tick = np.max(allTicks)
        max_tick = max_tick + tick_margin

        fig.update_xaxes(range=[min_tick, max_tick])
    
        # check if plot already exists. crete if not. override if so.

        pyo.plot(fig, filename=plot_file_path)
    
    return fig


#       ==============================================
#                  UPDATE NFT POSITION INFO 
#       ==============================================
def updateNFPMPositionsFile(account, poolName):
    liquid  = get_contract_from_abi('MliquidityMiner')
    NFPM    = getV3Contracts(1)

    #---------------- GET TOKEN ID's
    mytokenIds     = liquid.getTokenIds(account.address)
    print(f'mytokenIds: {mytokenIds}')

    if len(mytokenIds) == 0:
        print(f'\nno liquidity positions minted.')
        sys.exit(0)
    
    #---------------- UPDATE NFTPositions.cvs
    # create dataFrame
    data = np.array([
        'tokenId',
        'nonce',
        'operator',
        'token0SYM',
        'token1SYM',
        'fee',
        'tickLow',
        'tickHigh',
        'liquidity',
        'feeGrowthIn',
        'feeGrowthOut',
        'token0Owed',
        'token1Owed'
    ])

    mytokenIds = [2] #  <<<---------------- xxx
    
    for tokenId in mytokenIds:
        print(f'\n----POSITION {tokenId} INFO:')
        NFTRow = np.array([tokenId])
        
        NFTposition   = get_NPM_position(tokenId, account, True)
        for key, value in NFTposition.items():
            print(f'   {key}: {value}')
            NFTRow = np.append(NFTRow, value)

    
    data = np.vstack([data,NFTRow])  
      
    # save dataFram to .csv file
    data_file_path = f'data//NFPM_positions/{poolName}.csv'      
    df = pd.DataFrame(data[1:] , columns=data[0]) 
    print(f'\nsaving df: \n{df}...')
    time.sleep(2)
    # save df to .csv
    df.to_csv(data_file_path, index=False)  # Set index=False to omit writing row numbers
    df = df.set_index('tokenId')
    print(f'\nsaved df: \n{df}...')


#       ==============================================
#                UPDATE POOL POSITION INFO
#       ==============================================
def updatePoolPositionsFile(account, poolName, pool):
    liquid  = get_contract_from_abi('MliquidityMiner')

    #---------------- GET TOKEN ID's
    mytokenIds     = liquid.getTokenIds(account.address)
    print(f'mytokenIds: {mytokenIds}')

    if len(mytokenIds) == 0:
        print(f'\nno liquidity positions minted.')
        sys.exit(0)
    
    #---------------- UPDATE NFTPositions.cvs
    # create dataFrame
    data = np.array([
        'tokenId',
        'liquidity',
        'feeGrowthIn0',
        'feeGrowthIn1',
        'token0Owed',
        'token1Owed'
    ])

    
    for tokenId in mytokenIds:
        print(f'\n----POSITION {tokenId} INFO:')
        
        # get corresponding NFT position and some params
        NFTposition = get_NPM_position(tokenId, account, False)
        token0 = NFTposition['token0']  ; token1 = NFTposition['token1'] 
        TH     = NFTposition['tickHigh']; TL    = NFTposition['tickLow']
        fee    = NFTposition['fee']
        

        # get pool position
        PoolPosition = get_pool_position(account, pool, liquid, TL, TH, True)
        
        # construct the row for tokenId
        POOLRow = np.array([tokenId])
        for key, value in PoolPosition.items():
            #print(f'   {key}: {value}')
            POOLRow = np.append(POOLRow, value)
    
        data = np.vstack([data,POOLRow])  
      
    
    # save dataFram to .csv file
    data_file_path = f'data//pool_positions//{poolName}.csv'      
    df = pd.DataFrame(data[1:] , columns=data[0]) 
    print(f'\nsaving df: \n{df}...')
    time.sleep(2)
    # save df to .csv
    df.to_csv(data_file_path, index=False)  # Set index=False to omit writing row numbers
    df = df.set_index('tokenId')
    print(f'\nsaved df: \n{df}...')


#       ==============================================
#                   PLOT NFT POSITION
#       ==============================================
def plotNFTPosition(keysList, tokenIds, tick_margin, poolName, PLOT):
    
    PRINT = False

    print('\n---------plotNFTPosition------------')
    ticks   = []
    figList = []
    already_shown_in_key_list = []
    for tokenId in tokenIds:

        data_file_path = f'data//NFPM_positions//{poolName}.csv'
        df        = pd.read_csv(data_file_path)
        unique_token_ids = df['tokenId'].unique()
        keys      = df.columns.to_numpy()
        dfIndexed = df.set_index('tokenId')
        
        print(f'dfIndexed: \nm{dfIndexed}')
        TL = dfIndexed.loc[tokenId, 'tickLow'] 
        TH = dfIndexed.loc[tokenId, 'tickHigh']
        if TL not in ticks:
            ticks.append(TL)
        if TH not in ticks:
            ticks.append(TH)

        ΔT = TH-TL ; BarSpacing = ΔT/len(keysList)

        # Create customdata for hover info
        # locate what row number tokenId corresponds to
        rowNum = dfIndexed.index.get_loc(tokenId)
        # create new single row dataframe
        custom_dataT = df.loc[rowNum].to_frame()
        custom_data  = custom_dataT.transpose()
        fig = go.Figure()

        plotValues    = np.array([])
        plotHeaders   = np.array([])
        barPositions  = np.array([])
        i = 0.5
        for key in keys:
            if key in keysList:
                keyValue = dfIndexed.loc[tokenId, key]
                
                # default values
                show_legend = False ; color = 'black'

                if key in keysList:
                    mapped_array = keysList[key]
                    _color = mapped_array[0]
                    _opacity = mapped_array[1]
                    show_legend = True
                    # show in legen? not if we've already done so!
                    if key in already_shown_in_key_list:
                        show_legend = False
                    already_shown_in_key_list.append(key)


                i += 1
            
                # Add traces
                fig.add_trace(go.Bar(
                    x=[TL+BarSpacing*i], 
                    y=[keyValue],
                    text=key,       # Text to appear on each bar
                    textposition = 'auto',  # Position of the text
                    #width= 10000,
                    #offset=_offset,
                    marker_color = [_color],
                    opacity=_opacity,
                    customdata=custom_data,
                    showlegend=show_legend,  # Disable legend for this trace,
                    name = key,
                    hovertemplate=
                    'tokenId: %{customdata[0]}<br>' +
                    'nonce: %{customdata[1]}<br>' +
                    'operator: %{customdata[2]}<br>' +
                    'token0SYM: %{customdata[3]}<br>' +
                    'token1SYM: %{customdata[4]}<br>' +
                    'fee: %{customdata[5]}<br>' +
                    'tickLow: %{customdata[6]}<br>' +
                    'tickHigh: %{customdata[7]}<br>' +
                    'liquidity: %{customdata[8]}<br>' +
                    'feeGrowthIn: %{customdata[9]}<br>' +
                    'feeGrowthOut: %{customdata[10]}<br>' 
                ))


        figList.append(fig)
        
    if PLOT:
        # Step 3: Use make_subplots to combine figures
        fig_combined = make_subplots(rows=len(figList), cols=1, shared_xaxes=True)

        # Step 4: Add individual figures as subplots
        for i, f in enumerate(figList):
            for trace in f.data:
                fig_combined.add_trace(trace, row=i+1, col=1)
            # Add labels for each subplot
            fig_combined.update_yaxes(
                title_text=f"Token ID: {tokenIds[i]}",  # Customize label as needed
                row=i+1,
                col=1
            )

        tickArray = np.array(ticks)
        min_tick  = np.min(tickArray) - tick_margin
        max_tick  = np.max(tickArray) + tick_margin

        print(f'max_tick: {max_tick}')
        print(f'min_tick: {min_tick}')
        fig_combined.update_xaxes(range=[min_tick, max_tick])

        fig_combined.update_layout(
            title='NFPM positions',
            barmode='group',
            bargap=0.0,
            bargroupgap=0,
            showlegend=True  # Ensure legend is displayed
        )
        
        # check if plot already exists. crete if not. override if so.
        plot_file_path = f'data//plots//NFPM_positions//{poolName}.html'
        pyo.plot(fig_combined, filename=plot_file_path)
    
    return figList


