"""
Historical event indexer for bonding curve events
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from web3 import AsyncWeb3, AsyncHTTPProvider
from eth_abi import decode

from ...constants import CONTRACTS
from ..types import EventType


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s : %(message)s"
)


class CurveIndexer:
    """Index historical bonding curve events"""
    
    def __init__(self, rpc_url: str):
        """Initialize indexer with RPC endpoint
        
        Args:
            rpc_url: HTTP RPC endpoint URL
        """
        self.w3 = AsyncWeb3(AsyncHTTPProvider(rpc_url))
        self.curve_address = CONTRACTS["tokenManager2"]
        
        # Pre-calculate topic hashes for all event types
        self.event_topics = {
            event_type: self.w3.keccak(text=event_type.value)
            for event_type in EventType
        }

    
    async def fetch_events(
        self,
        from_block: int,
        to_block: int,
        event_types: Optional[List[EventType]] = None,
        token_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetch historical curve events
        
        Args:
            from_block: Starting block number
            to_block: Ending block number
            event_types: List of EventType to fetch (default: all)
            token_filter: Filter by token address (optional)
            
        Returns:
            List of parsed events
        """
        # Default to all event types if not specified
        if event_types is None:
            event_types = list(EventType)
        
        # Build event topics from EventType enum
        event_topic_hashes = []
        for event_type in event_types:
            if event_type in self.event_topics:
                event_topic_hashes.append("0x" + self.event_topics[event_type].hex())
        
        
        # Build topics array
        topics = [event_topic_hashes]  # First topic is event signature
        
        # Add token filter if specified (token is second indexed parameter)
        if token_filter:
            # Token is the second indexed parameter (after trader)
            # Convert address to 32-byte padded format for topics
            token_address = self.w3.to_checksum_address(token_filter)
            # Pad address to 32 bytes (addresses are 20 bytes, need to pad left with zeros)
            padded_token = "0x" + token_address[2:].lower().rjust(64, '0')
            topics.append(None)  # Skip trader (first indexed)
            topics.append(padded_token)
        
        # Scan in chunks to avoid API limits
        chunk_size = 1000
        all_events = []
        current_block = from_block
        
        while current_block <= to_block:
            chunk_end = min(current_block + chunk_size - 1, to_block)
            
            try:
                # Create filter parameters
                filter_params = {
                    "address": self.curve_address,
                    "topics": topics,
                    "fromBlock": current_block,
                    "toBlock": chunk_end
                }
                
                # Get logs
                logs = await self.w3.eth.get_logs(filter_params)
                
                
                # Parse events
                for log in logs:
                    event = await self._parse_event(log)
                    if event:
                        all_events.append(event)
                
                current_block = chunk_end + 1
                
            except Exception as e:
                # Reduce chunk size on error
                if chunk_size > 100:
                    chunk_size = chunk_size // 2
                    continue
                else:
                    raise e
        
        return all_events
    
    
    async def _parse_event(self, log: Dict) -> Optional[Dict[str, Any]]:
        """Parse a log entry into an event"""
        try:
            # Get event type from topic
            topic0 = log['topics'][0]
            if isinstance(topic0, bytes):
                topic0_hex = topic0.hex()
            else:
                topic0_hex = topic0
            
            # Find matching event type
            event_name = None
            for event_type, topic_hash in self.event_topics.items():
                if topic0_hex == topic_hash.hex():
                    event_name = event_type.name
                    break
            
            if not event_name:
                return None
            
            
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
                "creator": self.w3.to_checksum_address(creator),
                "token": self.w3.to_checksum_address(token),
                # "name": name,
                # "symbol": symbol,
                "totalSupply": totalSupply,
                'launchTime':launchTime,
                'launchFee':launchFee
            }
            
        except Exception as e:
            return None

    async def get_block_number(self) -> int:
        return await self.w3.eth.get_block_number()