// SPDX-License-Identifier: GPL-2.0-or-later
pragma solidity =0.7.6;
pragma abicoder v2;

import '@uniswap/v3-periphery/contracts/libraries/TransferHelper.sol';
import '@v3PeripheryMOCKS/libraries/MTransferHelper.sol';
import '@v3PeripheryMOCKS/interfaces/IMSwapRouter.sol';
import '@uniswap/v3-periphery/contracts/libraries/Path.sol';


contract MSwapper {
    using Path for bytes;
    IMSwapRouter public immutable swapRouter;
    constructor(IMSwapRouter _swapRouter) {
                    swapRouter = _swapRouter;
    }

    function MultiHop_Input(uint256 amountIn,
                            uint256 transferAmount,
                            uint256 amountOutMin,
                            address tokenA,
                            address tokenB,
                            address tokenC,
                            address transferToken,
                            uint24 feeA,
                            uint24 feeB,
                            int8 option
                            ) external returns (uint256 amountOut) {

            // Transfer `amountIn` of tokenA to this contract.
        if (option <= 19){
            MTransferHelper.safeTransferFrom(transferToken, msg.sender, address(this), transferAmount);
            if (option == 1){ revert("[Swapper :: MultiHop_Input] safeTransfered");}

            // Approve the router to spend tokenA.
            MTransferHelper.safeApprove(transferToken, address(swapRouter), transferAmount);
            if (option == 2){ revert("[Swapper :: MultiHop_Input] safeApproved");}
        }
        bytes memory PATH = abi.encodePacked(tokenA, feeA, tokenB, feeB, tokenC);
        
        IMSwapRouter.ExactInputParams memory params =
            IMSwapRouter.ExactInputParams({
                path: PATH,
                recipient: msg.sender,
                deadline: block.timestamp,
                amountIn: amountIn,
                amountOutMinimum: amountOutMin,
                option: option
            });
                // Executes the swap.
        amountOut = swapRouter.exactInput(params);
    }

    function MultiHop_Output(uint256 amountOut,
                            uint256 transferAmount,
                            uint256 amountInMax,
                            address tokenA,
                            address tokenB,
                            address tokenC,
                            address transferToken,
                            uint24 feeA,
                            uint24 feeB,
                            int8 option
                            ) external returns (uint256 amountIn) {
        
        if (option <= 19) {
            // Transfer `amountIn` of tokenA to this contract.
            MTransferHelper.safeTransferFrom(transferToken, msg.sender, address(this), amountOut);
            if (option == 1){ revert("[Swapper :: MultiHop_Output] safeTransfered");}

            // Approve the router to spend tokenA.
            MTransferHelper.safeApprove(transferToken, address(swapRouter), amountOut);
            if (option == 2){ revert("[Swapper :: MultiHop_Output] safeApproved"); }
        }

        bytes memory PATH = abi.encodePacked(tokenC, feeB, tokenB, feeA, tokenA);
        
        IMSwapRouter.ExactOutputParams memory params =
            IMSwapRouter.ExactOutputParams({
                path: PATH,
                recipient: msg.sender, 
                deadline: block.timestamp,
                amountOut: amountOut,
                amountInMaximum: amountInMax,
                option: option
            });
                // Executes the swap.
        amountIn = swapRouter.exactOutput(params);
    }

    function tokenOrder(address tokenA, address tokenB) public view returns(bool zeroForOne){
        zeroForOne = tokenA < tokenB;
    }

    function _blockTimestamp() public view virtual returns (uint256) {
        return block.timestamp; // truncation is desired
    }

}