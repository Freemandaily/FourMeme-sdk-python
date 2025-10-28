from dataclasses import dataclass
from typing import Optional

@dataclass
class CurveData:
    token_manager :str
    quote:str
    reserve:int
    max_reserve:int
    liquidity_added:bool


@dataclass
class BuyParams:
    """Parameters for buy transaction."""
    token: str
    amount_in: int
    amount_out_min: int
    to: str
    nonce: Optional[int] = None
    gas: Optional[int] = None
    gas_price: Optional[int] = None
    deadline: Optional[int] = None


@dataclass
class SellParams:
    """Parameters for sell transaction."""
    token: str
    amount_in: int
    amount_out_min: int
    to: str
    nonce: Optional[int] = None
    gas: Optional[int] = None
    gas_price: Optional[int] = None
    deadline: Optional[int] = None


@dataclass
class QuoteResult:
    """Result from quote functions."""
    router: str
    amount: int

@dataclass
class TokenMetadata:
    """Token metadata information."""
    name: str
    symbol: str
    decimals: int
    total_supply: int
    address: str


