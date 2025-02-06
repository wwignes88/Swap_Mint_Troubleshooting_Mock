import time
from scripts.Load.misc_funcs import get_accounts, get_contract_from_abi, sys
from scripts.Load.BrownieFuncs import UpdateConfigAdresses, gas_controls
from brownie import (accounts, interface, network, config, Contract,
                    # V3-CORE/ PERIPERY MOCKS
                    MUniswapFactory, 
                    MUniswapFactoryII, 
                    MNonfungiblePositionManager,
                    MNonfungiblePositionManagerII,
                    MSwapRouter,
                    # UNISWAP LIBRARIES:
                    MCallbackValidation,
                    PoolHashGenerator, 
                    PoolIIHashGenerator,
                    MPoolAddress,
                    MTransferHelper,
                    # ZEPPELIN MOCKS
                    MERC20,
                    # MY CONTRACTS
                    MSwapper,
                    MliquidityMiner,
                    # MLiquidityStaker,
                    # TESTING
                    MyMath
                    )

# account  : 0x588c3e4FA14b43fdB25D9C2a4247b3F2ba76aAce # Goog
# accountII: 0x6dFa1b0235f1150008B23B2D918F87D4775fBba9 # explorer

def deploy():
    print('\n=============== deploy =====================\n')

    # load account
    account = get_accounts(0) 
    acct_bal = gas_controls(account, set_gas_limit=False, Priority_fee=25)

    # 0 ERC20 Tokens
    # 1 V3 Periphery Libraries
    # 2 V3 Core Contraacts
    # 3 Swapper contract
    # 4 Liquidity Miner contract
    deployments = [3]

    # ERC20s
    if 0 in deployments:
        print('\ndeploying ERC20...')
        
        token_list = ['mockToken0','mockToken1']
        for token_name in token_list:
            symbol    = token_name.upper()
            print(f'\n   deploying {symbol} ...')
            mockERC20 =  MERC20.deploy(token_name,
                                        symbol,
                                        {"from": account})
            
            UpdateConfigAdresses(mockERC20, token_name)

            tx = mockERC20.mint(100*1e18, account.address, {'from':account}) 
            tx.wait(1)

        sys.exit(0)

    # UNISWAP libraries
    if 1 in deployments:

        #---------- deploy TransferHelper library
        deploy_MTransferHelper = False
        if deploy_MTransferHelper:
            transfer_helper = MTransferHelper.deploy({"from": account})
            UpdateConfigAdresses(transfer_helper, 'MTransferHelper')
            
        #---------- deploy hashPoolCreationCode
        deploy_PoolHashGenerators = False
        if deploy_PoolHashGenerators:
        
            hash_generator = PoolHashGenerator.deploy({"from": account})
            UpdateConfigAdresses(hash_generator, 'PoolHashGenerator')
            POOL_INIT_CODE_HASH = hash_generator.hashPoolCode()

            hash_generatorII = PoolIIHashGenerator.deploy({"from": account})
            UpdateConfigAdresses(hash_generatorII, 'PoolIIHashGenerator')
            POOL_INIT_CODE_HASHII = hash_generatorII.hashPoolCodeII()

            print(f'\n***POOL_INIT_CODE_HASH: \n    {POOL_INIT_CODE_HASH}\n\n')
            print(f'***POOL_INIT_CODE_HASHII: \n    {POOL_INIT_CODE_HASHII}\n')
                
            print("""
            ***update MPoolAddress.sol library with POOL_INIT_CODE_HASH/ POOL_INIT_CODE_HASHII values, 
                save it, THEN continue with deployments of libraries [next deployment should be MPoolAddress.sol 
                which will use the INIT_CODE_HASH values to compute pool addresses.] 
                
                Also make sure to set above deployments [transferHelter and hash generators] to "False" in deploy.py. 
                
                Finally, check config file to ensure deployed addresses match above values [they should have updated automatically].
                """)
            sys.exit(0)
            
        #---------- deploy ComputePoolAddress library
        deploy_MPoolAddress = True
        if deploy_MPoolAddress:
            pool_address_computer = MPoolAddress.deploy({"from": account})
            UpdateConfigAdresses(pool_address_computer, 'MPoolAddress')
   
        deploy_callbackValidation = True # uses MPoolAddress 
        if deploy_callbackValidation:
            callbackVal = MCallbackValidation.deploy({"from": account})
            UpdateConfigAdresses(callbackVal, 'MCallbackValidation')

        print(f'\n   V3 LIBRARIES DEPLOYED.\n')
        sys.exit(0)
        #----------------------------------------------------------
        
    # core/ periphery uniswap mock contracts
    if 2 in deployments:

        #---------- deploy mock factory

        deploy_MFactory = False
        if deploy_MFactory:
            print('\ndeploying factory MOCK...')
            factory =  MUniswapFactory.deploy({"from": account})
            UpdateConfigAdresses(factory, 'MFactory')
            time.sleep(3)
            factoryAddress = factory.address
        if not deploy_MFactory:
            factoryAddress = config["networks"][network.show_active()]['MFactory']

        deploy_MFactoryII = False
        if deploy_MFactoryII:
            print('\ndeploying factoryII MOCK...')
            factoryII =  MUniswapFactoryII.deploy({"from": account})
            UpdateConfigAdresses(factoryII, 'MFactoryII')
            time.sleep(3)
            factoryAddressII = factoryII.address
        if not deploy_MFactoryII:
            factoryAddressII = config["networks"][network.show_active()]['MFactoryII']
            
        #---------- deploy mock non-fungible position manager 
        deploy_MNonfungible = False
        if deploy_MNonfungible:
            print('\ndeploying  nonFungible MOCKS...')
            weth9 = config["networks"][network.show_active()]['tokens']['weth']
            # not utilized unless interested in URI...I'm not, so enter any address
            tokenDescriptor = account.address # ???
            
            deployFungII = True 
            if deployFungII:
                ERC721managerII = MNonfungiblePositionManagerII.deploy(
                                        factoryAddress,
                                        factoryAddressII,
                                        weth9,
                                        {'from': account})
                UpdateConfigAdresses(ERC721managerII, 'MNonfungiblePositionManagerII')
                time.sleep(2)
            
            deployFung = True 
            if deployFung:
                if deployFungII:
                    ERC721managerIIAddress = ERC721managerII.address
                if not deployFungII:
                    ERC721managerIIAddress = config["networks"][network.show_active()]['MNonfungiblePositionManagerII']

                ERC721manager   = MNonfungiblePositionManager.deploy(
                                        ERC721managerIIAddress,
                                        tokenDescriptor,
                                        {'from': account})
                UpdateConfigAdresses(ERC721manager, 'MNonfungiblePositionManager')
        
        #---------- deploy mock SwapRouter
        deploy_MSwapRouter = True
        if deploy_MSwapRouter:

            print('\ndeploying  swap router MOCK...')
            weth9   = config["networks"][network.show_active()]['tokens']['weth']
            
            # not utilized unless interested in URI...I'm not, so enter any address
            tokenDescriptor = account.address 
            swap_router     = MSwapRouter.deploy(
                                    factoryAddress,
                                    weth9,
                                    {'from': account})
            UpdateConfigAdresses(swap_router, 'MSwapRouter')
            routerAddress = swap_router.address

        print(f'\n   V3-CORE DEPLOYED.\n')
        sys.exit(0)
        #----------------------------------------------------------
    
    # Swapper
    if 3 in deployments:
        router  = get_contract_from_abi('MSwapRouter')
        print('\ndeploying swapper...')
        swapper = MSwapper.deploy(router, 
                                {"from": account})
        
        UpdateConfigAdresses(swapper, 'MSwapper')

    # Liquidity Miner
    if 4 in deployments:
        ERC721manager = config["networks"][network.show_active()]['MNonfungiblePositionManager']
        ERC721managerII = config["networks"][network.show_active()]['MNonfungiblePositionManagerII']
        print('\ndeploying Liquidity Miner...')
        liquidMOCK = MliquidityMiner.deploy(ERC721manager,
                                            ERC721managerII,
                                            {"from": account})
        UpdateConfigAdresses(liquidMOCK, 'MliquidityMiner')



def main():
    deploy()

