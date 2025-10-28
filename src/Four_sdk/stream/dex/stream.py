import asyncio
import json
import os
from typing import List, AsyncIterator, Optional, Dict, Any
from web3 import AsyncWeb3,AsyncHTTPProvider, WebSocketProvider, Web3

from .parser import parse_swap_event
from ..types import EventType
from ...Utils import load_abis
from ...constants import CONTRACTS,WBNB



class DexStream:
    def __init__(self,http_url:str, ws_url: str):
        self.ws_url = ws_url
        self.w3 = AsyncWeb3(AsyncHTTPProvider(http_url))
        self.token_addresses: List[str] = []
        self.pool_addresses: List[str] = []
        self._subscription_id: Optional[str] = None
        self.event_types: List[EventType] = []
        
    def subscribe_tokens(self, token_addresses, event_types: List[EventType] = None):
        """Set which tokens to monitor (will find pools automatically)"""
        # Handle both single string and list of strings
        if isinstance(token_addresses, str):
            token_addresses = [token_addresses]
        self.token_addresses = [Web3.to_checksum_address(addr) for addr in token_addresses]
        if event_types is None:
            event_types = [EventType.v2_SWAP]
        self.event_types = event_types
        
    async def _discover_pools(self, w3: AsyncWeb3) -> List[str]:
        """Discover V3 pools for configured tokens"""
        if not self.token_addresses:
            return []
        
        abis = load_abis()
        # Loading Factory contract
        factory = w3.eth.contract(
            address=Web3.to_checksum_address(CONTRACTS["v2_factory"]),
            abi=abis['v2_factory']
        )
        
        wbnb = Web3.to_checksum_address(WBNB)
        pools = []
        
        for token in self.token_addresses:
            if token.lower() == wbnb.lower():
                continue
            
            try:
                # Sort tokens for pool address calculation
                token0, token1 = (token, wbnb) if token.lower() < wbnb.lower() else (wbnb, token)
                
                # Get pool address 
                pool_address = await factory.functions.getPair(
                    token0,
                    token1
                ).call()
                
                if pool_address and pool_address != "0x0000000000000000000000000000000000000000":
                    pools.append(pool_address)
                    pass
            except Exception as e:
                pass
        
        return pools
    


    async def events(self) -> AsyncIterator[Dict[str, Any]]:
        """Async iterator that yields parsed swap events"""
        # Connect
        async with AsyncWeb3(WebSocketProvider(self.ws_url)) as w3:
            self.w3 = w3
            # Discover pools
            self.pool_addresses = await self._discover_pools(self.w3)
            
            if not self.pool_addresses:
                return 
            
            # Swap event signature
            swap_topic = Web3.keccak(text=EventType.v2_SWAP.value)
            
            # Create filter
            filter_params = {
                "address": self.pool_addresses,  # Multiple pool addresses
                "topics": [[swap_topic]]  # Just swap events
            }
            
            # Subscribe
            self._subscription_id = await self.w3.eth.subscribe("logs", filter_params)
            
            # Process events
            async for payload in self.w3.socket.process_subscriptions():
                if payload.get("subscription") != self._subscription_id:
                    continue
                    
                log = payload.get("result")
                if not log:
                    continue
                
                # Parse and yield event
                event = parse_swap_event(log)
                if event:
                    yield event
