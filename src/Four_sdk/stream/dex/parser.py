"""
Common event parser for DEX swap events
"""

from typing import Optional, Dict, Any
from web3 import Web3
from eth_abi import decode


def parse_swap_event(log: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parse DEX Swap event log
    
    Args:
        log: Web3 log dict
    
    Returns:
        Parsed event dict with DexSwapEvent structure
    """
    try:
        topics = log.get("topics", [])
        if len(topics) < 3:
            return None
        
        # sender. Note : This is not the trader 
        sender = topics[1].hex()

        # Parse non-indexed parameters (data)
        data_bytes = log.get("data")
        if not data_bytes:
            return None
        
        # Decode: [amount0, amount1, sqrtPriceX96, liquidity, tick]
        amount0In, amount1In, amount0Out, amount1Out  = decode(
            ['uint256', 'uint256', 'uint256', 'uint256'],
            data_bytes
        )
        if amount0In or amount1In:
            if amount1In:
                price = amount1In / amount0Out
            else:
                price = amount1Out / amount0In
        
        

        # Get pool address
        pool_address = log.get("address")
        if hasattr(pool_address, 'hex'):
            pool_address = "0x" + pool_address.hex()
        elif not pool_address.startswith('0x'):
            pool_address = '0x' + pool_address
        
        return {
            "eventName": "Swap",
            "transactionHash": "0x"+ str(log.get("transactionHash").hex()),
            "pool": Web3.to_checksum_address(pool_address),
            "sender": Web3.to_checksum_address("0x" + sender[24:]),
            "amount0In": amount0In,
            "amount1In": amount1In,
            "amount0Out": amount0Out,
            "amount1Out": amount1Out,
            "price":price
        }
        
    except Exception  as e:
        return None