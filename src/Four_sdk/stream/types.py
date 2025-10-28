from enum import Enum
from typing import List,Dict,Optional,Any

class EventType(Enum):
    """
        Event Type For Streaming 
    """
    MANAGER_1_CREATE = "TokenCreate(address,address,uint256,string,string,uint256,uint256)"
    MANAGER_2_CREATE = "TokenCreate(address,address,uint256,string,string,uint256,uint256,uint256)"

    MANAGER_1_BUY = "TokenPurchase(address,address,uint256,uint256)"
    MANAGER_2_BUY = "TokenPurchase(address,address,uint256,uint256,uint256,uint256,uint256,uint256)"

    MANAGER_1_SELL = "TokenSale(address,address,uint256,uint256)"
    MANAGER_2_SELL = "TokenSale(address,address,uint256,uint256,uint256,uint256,uint256,uint256)"

    v2_SWAP = "Swap(address,uint256,uint256,uint256,uint256,address)"
    v3_SWAP = "Swap(address,address,int256,int256,uint160,uint128,int24,uint128,uint128"