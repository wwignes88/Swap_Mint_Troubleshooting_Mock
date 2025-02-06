from brownie import network, config


TICK_SPACINGS = {
    500  : 10,
    3000 : 60
}

#===================== NETWORK DICTIONARIES

# list of live/ test nets
LIVE_ENVS = ['eth-main',
             'avax_main',
             'arbitrum_main',
             'bnb_main',
             'base_main',
             'blast_main',
             'celo_main',
             'ethereum_main',
             'optimism_main',
             'polygon_main',
             'worldchain',
             'zksync',
             'zora',
             ]
TEST_ENVS = ['polygon-amoy']

# map network to currency symbol
NETWORK_SYMS ={'arbitrum-main': 'ARB',
               'arbitrum-sepolia': 'ARB'}






#___________PRICE FEED ADDRESSES__________________

# chainlink rates. from: https://docs.chain.link/data-feeds/price-feeds/addresses

arbitrum_sepolia_feeds = {
            'ARB_USD' : '0xD1092a65338d049DB68D7Be6bD89d17a0929945e'
}


# mainnet feeds
arbitrum_main_feeds = {
            'ARB_USD' : '0xb2A824043730FE05F3DA2efaFa1CBbe83fa548D6',
            'ETH_USD' : '0x639Fe6ab55C921f74e7fac1ee960C0B6293ba612'
}
avax_main_feeds = {}
base_main_feeds = {}
blast_main_feeds = {}
celo_main_feeds = {}

optimism_main_feeds = {}
polygon_main_feeds = {           
           'native_usd': '0x001382149eBa3441043c1c66972b4772963f5D43', # matic_usd
           'btc_usd'   : '0xe7656e23fE8077D438aEfbec2fAbDf2D8e070C4f',
           'dai_usd'   : '0x1896522f28bF5912dbA483AC38D7eE4c920fDB6E',
           'WETH_usd'  : '0xF0d50568e3A7e8259E16663972b11910F89BD8e7',
           'eur_usd'   : '0xa73B1C149CB4a0bf27e36dE347CBcfbe88F65DB2',
           'link_matic': '0x408D97c89c141e60872C0835e18Dd1E670CD8781',
           'LINK_usd'  : '0xc2e2848e28B9fE430Ab44F55a8437a33802a219C',
           'SAND_usd'  : '0xeA8C8E97681863FF3cbb685e3854461976EBd895',
           'sol_usd'   : '0xF8e2648F3F157D972198479D5C7f0D721657Af67',
           'usdc_usd'  : '0x1b8739bB4CdF0089d07097A9Ae5Bd274b29C6F16',
           'usdt_usd'  : '0x3aC23DcB4eCfcBd24579e1f34542524d0E4eDeA8'}
worldchain_feeds = {}
zksync_feeds = {}
zora_feeds = {}

ethereum_main_feeds = {
    'LINK_ETH': "0xDC530D9457755926550b59e8ECcdaE7624181557",
    'LINK_USD': "0x2c1d072e956AFFC0D435Cb7AC38EF18d24d9127c",
    'ETH_USD': "0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419"
}

NETWORK_TO_RATE_DICT = {'eth-main': ethereum_main_feeds,
                        'arbitrum-main': arbitrum_main_feeds,
                        'avax-main': avax_main_feeds,
                        'base-main': base_main_feeds,
                        'blast-main': blast_main_feeds,
                        'celo-main': celo_main_feeds,
                        'ethereum-main': ethereum_main_feeds,
                        'optimism-main': optimism_main_feeds,
                        'polygon-main': polygon_main_feeds,
                        'worldchain': worldchain_feeds,
                        'zksync': zksync_feeds,
                        'zora': zora_feeds
                        }

