// SPDX-License-Identifier: GPL-2.0-or-later
pragma solidity >=0.5.0;
pragma abicoder v2;

import '@uniswap/v3-core/contracts/interfaces/IUniswapV3Factory.sol';
import '@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol';
import '@uniswap/v3-core/contracts/libraries/Position.sol';

// this interface is NOT inherited by contract. It IS used to load pool in scripts.
interface IV3Pool is IUniswapV3Pool{

    function getPoolPosition(
        address owner,
        int24 tickLower,
        int24 tickUpper
    ) external view  returns(Position.Info memory position);

    function positions(bytes32 key) external override view returns (
        uint128 liquidity,
        uint256 feeGrowthInside0LastX128,
        uint256 feeGrowthInside1LastX128,
        uint128 tokensOwed0,
        uint128 tokensOwed1);
    function getKeys() external view returns (bytes32[] memory);
    function getOwners() external view returns (address[] memory);


    // option 50
    event SwapAmounts(
        bool firstPool,
        address indexed sender,
        address recipient,
        bool zeroForOne,
        int256 amount0,
        int256 amount1
    );
    // option 51
    // option 51
    event SteppedAmounts(
        int24 indexed tickNext,
        int256 state_amountSpecifiedRemaining,
        int256 state_amountCalculated
    );
    // option 52
    event SteppedPrices(
        int24 indexed tickNext,
        uint160 state_sqrtPriceX96,
        uint256 step_sqrtPriceNextX96,
        uint256 step_sqrtPriceTargetX96,
        uint160 sqrtPriceLimitX96
    );
    // option 53
    event SwapStepAmounts(
        int24 indexed tickNext,
        uint256 step_amountIn,
        uint256 step_amountOut,
        uint256 step_feeAmount
    );
    // option 53
    event modifyAmounts(
        int128 liquidityDelta,
        int256 amount0,
        int256 amount1
    );
    
}
interface IV3Factory is IUniswapV3Factory{
    function getPool(
        address tokenA,
        address tokenB,
        uint24 fee
    ) external view override returns (address pool);
    function getPoolII(
        address tokenA,
        address tokenB,
        uint24 fee
    ) external view  returns (address pool);
    function createPoolII( 
        address tokenA,
        address tokenB,
        uint24 fee
    ) external returns (address pool);
    
}


