
// SPDX-License-Identifier: GPL-2.0-or-later
pragma solidity >=0.7.5;
pragma abicoder v2;

interface IswapCallback{ 

    struct SwapCallbackData {
        bytes path;
        address payer;
        int8 Ropt;
        bool exactInput;
        bool firstPool;
    }


    event PathPool( bool hasMultiplePools,
                        bytes pathBytes,
                        int8 Option
                    ); 
}