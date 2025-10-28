
import json
import os
from dotenv import load_dotenv
from web3 import AsyncHTTPProvider, AsyncWeb3,Web3

from ..types import QuoteResult
from ..constants import CONTRACTS,WBNB

load_dotenv()

DIR_NAME =  os.path.join(os.path.dirname(__file__), 'ABIS')

def parseMon(amount) -> int:
    return AsyncWeb3.to_wei(amount, "ether")

def _cs(token):
    return Web3.to_checksum_address(token)

# ─────────────────────────────────────
# Slippage utilities
# ─────────────────────────────────────
def calculate_slippage(amount: int, slippage_percent: int = 0) -> int:
    """Calculate minimum output amount with slippage tolerance."""
    if slippage_percent < 0 or slippage_percent > 100:
        raise ValueError("slippage_percent must be between 0 and 100")
    return int(amount * (100 - slippage_percent) / 100)

ABIS = {
    'tokenManager1': 'tokenManager1.json',
    'tokenManager2': 'tokenManager2.json',
    'tokenManagerHelper':'tokenManagerHelper.json',
    'v2_factory':'v2_factory.json',
    'v3_factory':'v3_factory.json',
    'pancakeRouter':"pancakeRouter.json",
    'erc20Abi':'erc20Abi.json'
}

def load_path(path:str):
    if not os.path.exists(path):
        raise FileNotFoundError(f'This Path doesnt Exist {path}')
    
    with open(path, 'r',encoding='utf-8') as file:
        return  json.load(file)

def load_abis():
    abis = {}
    for abi_name, abi_file in ABIS.items():
        abis[abi_name] = load_path(os.path.join(DIR_NAME,abi_file))
    return abis


async def get_amount_out( http_url:str, token: str, amount_in: int, is_buy: bool) -> QuoteResult:
        try:
            """
                Check If the token has migrated or Not 
                Then fetch the amount out for the token sale/buy
            """
            connect = AsyncWeb3(AsyncHTTPProvider(http_url))
            connected = await connect.is_connected()
            if not connected:
                return None
            
            abis = load_abis()
            tokenManagerHelper = connect.eth.contract(address=_cs(CONTRACTS['tokenManagerHelper']),abi=abis['tokenManagerHelper'])
            result_for_liquidity = await tokenManagerHelper.functions.getTokenInfo(
                    _cs(token)
                ).call()
            is_liquidity = result_for_liquidity[11]
            if not is_liquidity:
                if is_buy:
                    result = await tokenManagerHelper.functions.tryBuy(
                        _cs(token), 0, int(amount_in)
                    ).call()

                    if not result:
                        return None
                    router = result[0]
                    amount_out = result[2]
                else:
                    result = await tokenManagerHelper.functions.trySell(
                        _cs(token), int(amount_in)
                    ).call()

                    if not result:
                        return None
                    router = result[0]
                    amount_out = result[2]
            else:
                pancakeRouter_address =  CONTRACTS['pancakeRouter']
                pancakeRouter = connect.eth.contract(
                    address=_cs(pancakeRouter_address),
                    abi=abis['pancakeRouter'])
                result = await pancakeRouter.functions.getAmountsOut(
                    int(amount_in),
                    [_cs(WBNB), _cs(token)]
                ).call()
                router = pancakeRouter_address
                amount_out = result[1]

            return QuoteResult(
                router=_cs(router),
                amount=int(amount_out)
            )
        except Exception as e:
            raise RuntimeError(f"Failed to get amount out: {e}")