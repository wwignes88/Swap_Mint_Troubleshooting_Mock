// SPDX-License-Identifier: GPL-2.0-or-later
pragma solidity 0.7.6;
pragma abicoder v2;

// my contracts
import '@v3PeripheryMOCKS/MNonfungiblePositionManager.sol';
import '@v3PeripheryMOCKS/MNonfungiblePositionManagerII.sol';
import '@v3PeripheryMOCKS/interfaces/IMNonfungiblePositionManager.sol';
import '@v3PeripheryMOCKS/interfaces/IMNonfungiblePositionManagerII.sol';
import '@v3PeripheryMOCKS/interfaces/IStructs.sol';
import '@v3PeripheryMOCKS/MNonfungiblePositionManagerII.sol';
import '@v3PeripheryMOCKS/libraries/MTransferHelper.sol';
import '@v3CoreMOCKS/interfaces/IUniswapV3Pool.sol';

import '@uniswap/v3-core/contracts/libraries/SafeCast.sol';
import '@uniswap/v3-core/contracts/libraries/SqrtPriceMath.sol';
import '@uniswap/v3-core/contracts/libraries/TickMath.sol';
import '@openzeppelin/contracts/token/ERC721/IERC721Receiver.sol';
import '@uniswap/v3-periphery/contracts/libraries/LiquidityAmounts.sol';

import "@openzeppelin/contracts/utils/Address.sol";


contract MliquidityMiner is IERC721Receiver{
    using Address for address;
    using SafeCast for uint256;
    using SafeCast for int256;

    // VARIABLES
        MNonfungiblePositionManager public immutable nonfungiblePositionManager;
        MNonfungiblePositionManagerII public immutable nonfungiblePositionManagerII;

        /// @notice Represents the deposit of an NFT
        struct Deposit {
            address owner;
            uint128 liquidity;
            address token0;
            address token1;
        }

        mapping (address => uint256[]) public tokenOwnership;

        /// @dev deposits[tokenId] => Deposit
        mapping(uint256 => Deposit) public deposits;


        constructor( 
                    MNonfungiblePositionManager _nonfungiblePositionManager,
                    MNonfungiblePositionManagerII _nonfungiblePositionManagerII
        ){
                nonfungiblePositionManager = _nonfungiblePositionManager;
                nonfungiblePositionManagerII = _nonfungiblePositionManagerII;
        }
    //

    // Implementing `onERC721Received` so this contract can receive custody of erc721 tokens
    function onERC721Received(
        address operator,
        address,
        uint256 tokenId,
        bytes calldata
     ) external override returns (bytes4) {
        // get position information

        _createDeposit(operator, tokenId);

        return this.onERC721Received.selector;
    }

    function _createDeposit(address owner, uint256 tokenId) internal {
        (, , address token0, address token1, , , , uint128 liquidity, , , , ) =
            nonfungiblePositionManagerII.positions(tokenId);

        // set the owner and data for position
        // operator is msg.sender
        deposits[tokenId] = Deposit({owner: owner, liquidity: liquidity, token0: token0, token1: token1});
    }

    // set/ get min mint amounts
    uint256 Amount0Min;
    uint256 Amount1Min;
    function setMinMintAmounts(uint256 amount0Min, uint256 amount1Min) external {
        Amount0Min = amount0Min;
        Amount1Min = amount1Min;
    }
    function getMinMintAmounts() external view returns (uint256 _Amount0Min, uint256 _Amount1Min){
        _Amount0Min = Amount0Min;
        _Amount1Min = Amount1Min;
    }

    //require(amount0 >= myMintParams.Amount0Min && amount1 >= myMintParams.Amount1Min, 'Price slippage check');
    struct myMintParams{
        address tokenA;
        address tokenB;
        uint256 amount0ToMint;
        uint256 amount1ToMint;
        uint256 Amount0Min;
        uint256 Amount1Min;
        int24 tickLower;
        int24 tickUpper;
        uint24 poolFee;
    }

    /// mint
            // revert_option input is for troubleshooting; triggers 'if' statements that hold 
            // revert conditions if option == [some number]
            // this lets the user know how far / where the transaction made it successfully.
    function mintNewPosition(
                myMintParams memory _params,
                int8 option)
            external
            returns (
                uint256 tokenId,
                uint128 liquidity,
                uint256 amount0,
                uint256 amount1
            ){ 

            MTransferHelper.safeTransferFrom(
                                    _params.tokenA,
                                    msg.sender,       // from
                                    address(this),    // to
                                    _params.amount0ToMint);
                if (option == 1){revert("transfered tokenA to liquid");}
            MTransferHelper.safeTransferFrom(
                                    _params.tokenB, 
                                    msg.sender, 
                                    address(this), 
                                    _params.amount1ToMint);
                if (option == 2){revert("transfered tokenB to liquid");}
            MTransferHelper.safeApprove(_params.tokenA, address(nonfungiblePositionManagerII), _params.amount0ToMint);
                if (option == 3){ revert( "approved nonfungII for amount0" ); }
            MTransferHelper.safeApprove(_params.tokenB, address(nonfungiblePositionManagerII), _params.amount1ToMint);
                if (option == 4){ revert( "approved nonfungII for amount1" ); }
        
            IStructs.MintParams memory params =
                IStructs.MintParams({
                    token0        : _params.tokenA,
                    token1        : _params.tokenB,
                    fee           : _params.poolFee,
                    tickLower     : _params.tickLower,
                    tickUpper     : _params.tickUpper,
                    amount0Desired: _params.amount0ToMint,
                    amount1Desired: _params.amount1ToMint,
                    amount0Min    : Amount0Min,
                    amount1Min    : Amount1Min,
                    recipient     : address(this),
                    deadline      : block.timestamp
            });
            (tokenId, liquidity, amount0, amount1) = nonfungiblePositionManager.mint(params, option);
            require(amount0 >= _params.Amount0Min && amount1 >= _params.Amount1Min, 'Price slippage check');

            if (option == 13){ revert("[MLMiner] 13"); }

            if (option < 50){ 
                tokenOwnership[msg.sender].push(tokenId);
                _createDeposit(msg.sender, tokenId);

                // refunds
                    if (amount0 < _params.amount0ToMint) {
                            //MTransferHelper.safeApprove(_params.tokenA, address(nonfungiblePositionManager), 0);
                            uint256 refund0 = _params.amount0ToMint - amount0;
                            if (option == 14){revert("approved/ transfered something....");}
                            MTransferHelper.safeTransfer(
                                                    _params.tokenA,
                                                    msg.sender,    // to
                                                    refund0);
                        }


                    if (amount1 < _params.amount1ToMint) {
                        //MTransferHelper.safeApprove(_params.tokenB, address(nonfungiblePositionManager), 0);
                        if (option == 15){revert("approved/ transfered something....");}
                        uint256 refund1 = _params.amount1ToMint - amount1;
                        MTransferHelper.safeTransfer(
                                                _params.tokenB,
                                                msg.sender,    // to
                                                refund1);
                    }
            }
    }

    function burnPosition(uint256 tokenId) external{
        address depositOwner = deposits[tokenId].owner;
        require(msg.sender == depositOwner, "dep. owner");
        nonfungiblePositionManager.burn( tokenId);
    }

 
    // decrease liquidity of position by 1/frac 
    function decreaseLiquidity(
        uint256 tokenId, 
        uint8 frac,
        int8 option) external returns (
                        uint256 amount0, 
                        uint256 amount1) {
        require(msg.sender == deposits[tokenId].owner, 'Not the owner');
        (, , , , , , , uint128 liquidity, , , , ) = nonfungiblePositionManagerII.positions(tokenId);
        uint128 L_burn = liquidity / frac;
        IMNonfungiblePositionManagerII.DecreaseLiquidityParams memory params =
            IMNonfungiblePositionManagerII.DecreaseLiquidityParams({
                tokenId: tokenId,
                liquidity: L_burn,
                amount0Min: 0,
                amount1Min: 0,
                deadline: block.timestamp
            });
        (amount0, amount1) = nonfungiblePositionManagerII.decreaseLiquidity(params, option);

    }

    function _sendToOwner(
        uint256 tokenId,
        uint256 amount0,
        uint256 amount1
        ) internal {
        // get owner of contract
        address owner  = deposits[tokenId].owner;
        address token0 = deposits[tokenId].token0;
        address token1 = deposits[tokenId].token1;
        // send collected fees to owner
        MTransferHelper.safeTransfer(token0, owner, amount0);
        MTransferHelper.safeTransfer(token1, owner, amount1);
    }
    
    function increaseL(
        uint256 tokenId,
        uint256 amountAdd0,
        uint256 amountAdd1,
        int8 revert_option
        )
        external
        returns (
            uint128 liquidity,
            uint256 amount0,
            uint256 amount1
        ) {

        MTransferHelper.safeTransferFrom(deposits[tokenId].token0, msg.sender, address(this), amountAdd0);
        MTransferHelper.safeTransferFrom(deposits[tokenId].token1, msg.sender, address(this), amountAdd1);
            if (revert_option == 1){
                revert("transferFrom executed");
            }

        MTransferHelper.safeApprove(deposits[tokenId].token0, address(nonfungiblePositionManagerII), amountAdd0);
        MTransferHelper.safeApprove(deposits[tokenId].token1, address(nonfungiblePositionManagerII), amountAdd1);
            if (revert_option == 2){
                revert("approvals done");
            }

        IMNonfungiblePositionManagerII.IncreaseLiquidityParams memory params = IMNonfungiblePositionManagerII.IncreaseLiquidityParams({
            tokenId: tokenId,
            amount0Desired: amountAdd0,
            amount1Desired: amountAdd1,
            amount0Min: 0,
            amount1Min: 0,
            deadline: block.timestamp
        });

        (liquidity, amount0, amount1) = nonfungiblePositionManagerII.increaseLiquidity(params, revert_option);

    }

    function collectFees(
        uint256 tokenId, 
        uint128 _amount0Max,
        uint128 _amount1Max,
        int8 revert_option) public returns (uint256 amount0, uint256 amount1) {
        // Caller must own the ERC721 position, meaning it must be a deposit

        // set amount0Max and amount1Max to uint256.max to collect all fees
        // alternatively can set recipient to msg.sender and avoid another transaction in `sendToOwner`
        IMNonfungiblePositionManagerII.CollectParams memory params =
            IMNonfungiblePositionManagerII.CollectParams({
                tokenId: tokenId,
                recipient: address(this),
                amount0Max: _amount0Max,
                amount1Max: _amount1Max
        });

        (amount0, amount1) = nonfungiblePositionManagerII.collect(params, revert_option);
        if (revert_option == 1){revert("nonfung collect");}
        // send collected feed back to owner
        _sendToOwner(tokenId, amount0, amount1);
    }

    /// @notice Transfers the NFT to the owner
    function retrieveNFT(uint256 tokenId) external {
        // must be the owner of the NFT
        require(msg.sender == deposits[tokenId].owner, 'Not the owner');
        // transfer ownership to original owner
        nonfungiblePositionManager.safeTransferFrom(address(this), msg.sender, tokenId);
        //remove information related to tokenId
        delete deposits[tokenId];
    }

    /*
    function transferToStaker(
            address from,
            address staker, 
            uint256 tokenId,
            address deposit_EOA_operator
        ) public {
            require(deposits[tokenId].owner == msg.sender , "only token minter");
            // send 'to' address as encoded data for 'onERC721Received'
            // which will set 'to' as owner of the deposit
            bytes memory _data = abi.encode(deposit_EOA_operator);
            nonfungiblePositionManager.safeTransferFrom(from, staker, tokenId, _data);
    }
    */

    //========== MY FUNCTIONS
    // NFT functions
        // get tokenIds of owner
        function getTokenIds(address tokenOwner) external view returns (uint256[] memory) {
            return tokenOwnership[tokenOwner];
        }

        // count tokens held by owner
        function getTokenCount(address account) external view returns (uint256) {
            return tokenOwnership[account].length;
        }

        // retrieve deposit
        function getDeposit(uint256 tokenId) public view returns (Deposit memory) {
            return deposits[tokenId];
        }
    //


// ===================================================
// =================== liquidioty math ===============
// ===================================================


    // see PositionKey.sol library in v3-periphery.
    function compute(
        address owner,
        int24 tickLower,
        int24 tickUpper
    ) external pure returns (bytes32) {
        return keccak256(abi.encodePacked(owner, tickLower, tickUpper));
    }

    //* See LiquidityMath.sol library
    uint256 public constant Q96 = 0x1000000000000000000000000;
    uint256 public constant Q128 = 0x100000000000000000000000000000000;
    function toUint128(uint256 x) private pure returns (uint128 y) {
        require((y = uint128(x)) == x);
    }

    function sqrtPatTick(int24 tick_) external pure returns (uint160 sqrtPriceX96_){
        sqrtPriceX96_ = TickMath.getSqrtRatioAtTick( tick_);
    }

    function tickAtSqrt(uint160 sqrtPriceX96_) external pure returns (int24 tick_){
        tick_ = TickMath.getTickAtSqrtRatio( sqrtPriceX96_);
    }

    // see LForZero [below]
    function MulDiv(
        uint256 a,
        uint256 b,
        uint256 denominator
        ) public pure returns (uint256 result) {
        // 512-bit multiply [prod1 prod0] = a * b
        // Compute the product mod 2**256 and mod 2**256 - 1
        // then use the Chinese Remainder Theorem to reconstruct
        // the 512 bit result. The result is stored in two 256
        // variables such that product = prod1 * 2**256 + prod0
        uint256 prod0; // Least significant 256 bits of the product
        uint256 prod1; // Most significant 256 bits of the product
        assembly {
            let mm := mulmod(a, b, not(0))
            prod0 := mul(a, b)
            prod1 := sub(sub(mm, prod0), lt(mm, prod0))
        }

        // Handle non-overflow cases, 256 by 256 division
        if (prod1 == 0) {
            require(denominator > 0);
            assembly {
                result := div(prod0, denominator)
            }
            return result;
        }

        // Make sure the result is less than 2**256.
        // Also prevents denominator == 0
        require(denominator > prod1);

        ///////////////////////////////////////////////
        // 512 by 256 division.
        ///////////////////////////////////////////////

        // Make division exact by subtracting the remainder from [prod1 prod0]
        // Compute remainder using mulmod
        uint256 remainder;
        assembly {
            remainder := mulmod(a, b, denominator)
        }
        // Subtract 256 bit number from 512 bit number
        assembly {
            prod1 := sub(prod1, gt(remainder, prod0))
            prod0 := sub(prod0, remainder)
        }

        // Factor powers of two out of denominator
        // Compute largest power of two divisor of denominator.
        // Always >= 1.
        uint256 twos = -denominator & denominator;
        // Divide denominator by power of two
        assembly {
            denominator := div(denominator, twos)
        }

        // Divide [prod1 prod0] by the factors of two
        assembly {
            prod0 := div(prod0, twos)
        }
        // Shift in bits from prod1 into prod0. For this we need
        // to flip `twos` such that it is 2**256 / twos.
        // If twos is zero, then it becomes one
        assembly {
            twos := add(div(sub(0, twos), twos), 1)
        }
        prod0 |= prod1 * twos;

        // Invert denominator mod 2**256
        // Now that denominator is an odd number, it has an inverse
        // modulo 2**256 such that denominator * inv = 1 mod 2**256.
        // Compute the inverse by starting with a seed that is correct
        // correct for four bits. That is, denominator * inv = 1 mod 2**4
        uint256 inv = (3 * denominator) ^ 2;
        // Now use Newton-Raphson iteration to improve the precision.
        // Thanks to Hensel's lifting lemma, this also works in modular
        // arithmetic, doubling the correct bits in each step.
        inv *= 2 - denominator * inv; // inverse mod 2**8
        inv *= 2 - denominator * inv; // inverse mod 2**16
        inv *= 2 - denominator * inv; // inverse mod 2**32
        inv *= 2 - denominator * inv; // inverse mod 2**64
        inv *= 2 - denominator * inv; // inverse mod 2**128
        inv *= 2 - denominator * inv; // inverse mod 2**256

        // Because the division is now exact we can divide by multiplying
        // with the modular inverse of denominator. This will give us the
        // correct result modulo 2**256. Since the precoditions guarantee
        // that the outcome is less than 2**256, this is the final result.
        // We don't need to compute the high bits of the result and prod1
        // is no longer required.
        result = prod0 * inv;
        return result;
    }


    // LIQUIDITY FOR AMOUNTS
        // see LiquidityAmounts.sol and LiquidityManager :: addLiquidity in v3-periphery 
        // Calculates amount0 * (sqrt(upper) * sqrt(lower)) / (sqrt(upper) - sqrt(lower))
    function LForZero(
            uint160 sqrtRatioAX96,
            uint160 sqrtRatioBX96,
            uint256 amount0
        ) public pure returns (uint256 intermediate, uint256 lIQUIDITY, uint128 liquidity) {
            if (sqrtRatioAX96 > sqrtRatioBX96) (sqrtRatioAX96, sqrtRatioBX96) = (sqrtRatioBX96, sqrtRatioAX96);
            intermediate = MulDiv(sqrtRatioAX96, sqrtRatioBX96, Q96);
            lIQUIDITY = MulDiv(amount0, intermediate, sqrtRatioBX96 - sqrtRatioAX96);
            liquidity = toUint128(lIQUIDITY);
        }
        // Calculates amount1 / (sqrt(upper) - sqrt(lower)).
        function LForOne(
            uint160 sqrtRatioAX96,
            uint160 sqrtRatioBX96,
            uint256 amount1
        ) public pure  returns (uint128 liquidity) {
            if (sqrtRatioAX96 > sqrtRatioBX96) (sqrtRatioAX96, sqrtRatioBX96) = (sqrtRatioBX96, sqrtRatioAX96);
            return toUint128(MulDiv(amount1, Q96, sqrtRatioBX96 - sqrtRatioAX96));
    }

    function LiquidityForAmounts(
            uint160 sqrtRatioX96,
            uint160 sqrtRatioAX96,
            uint160 sqrtRatioBX96,
            uint256 amount0,
            uint256 amount1
        ) external view returns ( uint128 liquidity ) {
            if (sqrtRatioAX96 > sqrtRatioBX96) (sqrtRatioAX96, sqrtRatioBX96) = (sqrtRatioBX96, sqrtRatioAX96);
            if (sqrtRatioX96 <= sqrtRatioAX96) {
                ( , , liquidity) = LForZero(sqrtRatioAX96, sqrtRatioBX96, amount0);
            } else if (sqrtRatioX96 < sqrtRatioBX96) {
                uint128 liquidity0;
                uint128 liquidity1;
                ( , , liquidity0) = LForZero(sqrtRatioX96, sqrtRatioBX96, amount0);
                liquidity1 = LForOne(sqrtRatioAX96, sqrtRatioX96, amount1);
                liquidity  = liquidity0 < liquidity1 ? liquidity0 : liquidity1;
            } else {
                liquidity = LForOne(sqrtRatioAX96, sqrtRatioBX96, amount1);
            }
    }

    //
    // AMOUNTS FOR LIQUIDITY
    //  Gets the amount0 delta between two prices
    // Calculates liquidity / sqrt(lower) - liquidity / sqrt(upper),
    // i.e. liquidity * (sqrt(upper) - sqrt(lower)) / (sqrt(upper) * sqrt(lower))
    function getAmount0ForLiquidity(
            uint160 sqrtRatioAX96,
            uint160 sqrtRatioBX96,
            uint128 liquidity
        ) public pure returns (uint256 amount0) {
            if (sqrtRatioAX96 > sqrtRatioBX96) (sqrtRatioAX96, sqrtRatioBX96) = (sqrtRatioBX96, sqrtRatioAX96);

            return
                FullMath.mulDiv(
                    uint256(liquidity) << FixedPoint96.RESOLUTION,
                    sqrtRatioBX96 - sqrtRatioAX96,
                    sqrtRatioBX96
                ) / sqrtRatioAX96;
    }

    /// @notice Gets the amount1 delta between two prices
    /// @dev Calculates liquidity * (sqrt(upper) - sqrt(lower))
    function getAmount1ForLiquidity(
            uint160 sqrtRatioAX96,
            uint160 sqrtRatioBX96,
            uint128 liquidity
        ) public pure returns (uint256 amount1) {
            if (sqrtRatioAX96 > sqrtRatioBX96) (sqrtRatioAX96, sqrtRatioBX96) = (sqrtRatioBX96, sqrtRatioAX96);

            return FullMath.mulDiv(liquidity, sqrtRatioBX96 - sqrtRatioAX96, FixedPoint96.Q96);
    }

    function getAmountsForLiquidity(
            uint160 sqrtRatioX96,
            uint160 sqrtRatioAX96,
            uint160 sqrtRatioBX96,
            uint128 liquidity
        ) public pure returns (uint256 amount0, uint256 amount1) {
            if (sqrtRatioAX96 > sqrtRatioBX96) (sqrtRatioAX96, sqrtRatioBX96) = (sqrtRatioBX96, sqrtRatioAX96);

            if (sqrtRatioX96 <= sqrtRatioAX96) {
                amount0 = getAmount0ForLiquidity(sqrtRatioAX96, sqrtRatioBX96, liquidity);
            } else if (sqrtRatioX96 < sqrtRatioBX96) {
                amount0 = getAmount0ForLiquidity(sqrtRatioX96, sqrtRatioBX96, liquidity);
                amount1 = getAmount1ForLiquidity(sqrtRatioAX96, sqrtRatioX96, liquidity);
            } else {
                amount1 = getAmount1ForLiquidity(sqrtRatioAX96, sqrtRatioBX96, liquidity);
            }
    }




}