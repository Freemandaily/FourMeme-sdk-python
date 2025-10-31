"""
Common event parser for curve events
"""

import token
from typing import Optional, Dict, Any
from web3 import Web3
from eth_abi import decode


def parse_curve_event(log: Dict[str, Any], event_name: str) -> Optional[Dict[str, Any]]:
    """
    Parse Curve event log (BUY/SELL)
    
    Args:
        log: Web3 log dict
        event_name: Event name (e.g., "BUY", "SELL")
    
    Returns:
        Parsed event dict with CurveEvent structure
    """
    try:
        # Parse non-indexed parameters (data)
        data_bytes = log.get("data")
        if not data_bytes:
            return None
        
        data_hex =  log['data'].hex() if hasattr(log['data'],'hex') else log['data']
        if data_hex.startswith('0x'):
            data_hex = data_hex[2:]
            
        # Parse data to get these items
        # token: 0
        # account : 1
        # price: 2
        # amount:3
        # cost: 4
        # fee:5
        # offers:6
        # funds: 7
        datas = [data_hex[i:i+64] for i in range(0, len(data_hex), 64)]
        
        token = "0x" + datas[0][24:]
        account = "0x" + datas[1][24:]
        price = int("0x" + datas[2][24:],16)
        amount = int("0x" + datas[3][24:],16)
        cost = int("0x" + datas[4][24:],16)
        fee = int("0x" + datas[5][24:],16)
        offers = int("0x" + datas[6][24:],16)
        funds = int("0x" + datas[7][24:],16)

        return {
            "eventName": event_name,
            "trader":account,
            "transactionHash": "0x"+str(log.get("transactionHash").hex()),
            "price":price,
            "token": Web3.to_checksum_address(token),
            "amount":amount,
            "cost": cost,
            "fee":fee,
            "offers":offers,
            "funds":funds
        }
        
    except Exception as e:
        return None
    
    
def parse_create_event( log: Dict,event_name:str) -> Optional[Dict[str, Any]]:
    """Parse a log entry into an event"""
    try:
        # Fetch data hex that contain created token Info
        data_hex =  log['data'].hex() if hasattr(log['data'],'hex') else log['data']
        if data_hex.startswith('0x'):
            data_hex = data_hex[2:]


        # Parse This data to get each items
        # 0 = creator
        # 1 = token
        # 2 = requestId
        # 3 = name
        # 4 = symbol
        # 5 = totalSupply
        # 6 = launchTime
        # 7 = launchFee
        datas = [data_hex[i:i+64] for i in range(0, len(data_hex), 64)]
        
        creator = "0x" + datas[0][24:]
        token = "0x" + datas[1][24:]
        requestId = datas[2][24:]
        name = bytes.fromhex(datas[3]).decode('utf-8')
        symbol = bytes.fromhex(datas[4]).decode('utf-8')
        totalSupply = int("0x"+ datas[5],16)
        launchTime =int("0x"+ datas[6],16)
        launchFee = int("0x"+ datas[7],16)

        return {
            "eventName": event_name,
            "creator": log['blockNumber'],
            "transactionHash": (
                log['transactionHash'].hex() 
                if hasattr(log['transactionHash'], 'hex') 
                else log['transactionHash']
            ),
            "creator": Web3.to_checksum_address(creator),
            "token": Web3.to_checksum_address(token),
            # "name": name,
            # "symbol": symbol,
            "totalSupply": totalSupply,
            'launchTime':launchTime,
            'launchFee':launchFee
        }
        
    except Exception as e:
        return None
