A mock of the UniswapV3 protocol with emphasis on troubleshooting failed swap(...) or mint(...) transactions. This troubleshooting functionality is accomplished by incorporating a uint8 variable called 'revert_option' or simply 'option' into the mint(...) and swap(...) [and related] functions. This variable will trigger an intential revert statement placed in various locations throughout the call. For example, at the beginning of the _modifyPosition(...) function in the pool contract we have,

    if (option == 21){ revert(" --- [_mod]  21 ");}

Placing similar intentional revert statements throughout the call allows users to pinpoint where in the call their calls are reverting. For multi-hop swaps the revert statement takes the form of a function [revertOption(...)] which has an additional boolean input that identifies whether it is the first or second pool (users don't input the boolean value though -- see whitepaper). 

Eth-brownie -- a python based  smart contract development toolchain -- is presumed in the scripts. The V4 mock, if and when I get to it, will be written in Rust.

The first thing a user might notice is there are not one but two pool contracts, two NonfungbiblePositionManager (NFPM) contracts, and two Factory contracts. The reason for this is because adding in troubleshooting functionality caused the already packed contracts to pass the EIP-170 byte limit. This project was NOT designed wtih an aim to optimize the overall design. Neither was security given much consideration. In fact, to reduce the byte-size of some of the contracts certain security features found in the UniswapV3 protocol were stripped out. Beyond this, the contracts ARE designed to realistically emulate the uniswapV3 protocol. 
