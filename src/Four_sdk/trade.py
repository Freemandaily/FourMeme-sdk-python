import time
from typing import Dict,List,Optional,Any

from web3 import AsyncWeb3,Web3,AsyncHTTPProvider
from eth_utils import function_signature_to_4byte_selector,to_checksum_address
from eth_account import Account
from eth_abi import encode
from web3.types import TxParams, Wei

from .types import CurveData,BuyParams,SellParams,QuoteResult
from .constants import CONTRACTS,CHAIN_ID,WBNB,DEFAULT_DEADLINE_SECONDS 
from .Utils import load_abis

def _cs(addr:str)-> str:
    return to_checksum_address(addr)

class Trade:

    def __init__(self,rpc_url:str, private_key:str|None=None):
        self.w3 = AsyncWeb3(AsyncHTTPProvider(rpc_url))
        self.account = Account.from_key(private_key)
        self.address: str = self.account.address
        self.chain_id = CHAIN_ID

        abis = load_abis()
        self.tokenManagerHelper = self.w3.eth.contract(
            address=_cs(CONTRACTS['tokenManagerHelper']),
            abi=abis['tokenManagerHelper']
        )
        self.pancakeRouter_address = CONTRACTS['pancakeRouter']
        self.pancakeRouter = self.w3.eth.contract(
            address=_cs(self.pancakeRouter_address),
            abi=abis['pancakeRouter']
        )

        self.buy_sel =  function_signature_to_4byte_selector(
            "buyTokenAMAP(address,uint256,uint256)"
        )

        self.sell_sel = function_signature_to_4byte_selector(
            "sellToken(address,uint256)"
        )

        self.pancake_buy_sel = function_signature_to_4byte_selector(
            "swapExactETHForTokens(uint256,address[],address,uint256)"
        )
        self.pancake_sell_sel = function_signature_to_4byte_selector(
            "swapExactTokensForETH(uint256,uint256,address[],address,uint256)"
        )

    async def get_curves(self, token: str) -> CurveData:
        
        try:
            data = await self.tokenManagerHelper.functions.getTokenInfo(_cs(token)).call()
            return CurveData(
                token_manager=data[1],
                quote=data[2],
                reserve=int(data[9]),
                max_reserve=int(data[10]),
                liquidity_added=data[11]
            )
        except Exception as e:
            raise RuntimeError(f"Failed to get curve data: {e}")
    

    async def _send_transaction(self, to: str, calldata: bytes, *, value: int = 0, nonce: int = None, gas: int = None, gas_price: int = None) -> str:
        try:
            # Get current gas price and nonce
            if gas_price is None:
                # gas_price = int(await self.w3.eth.gas_price)
                base_gas_price = 100_000_000
                gas_price = base_gas_price * 1


            if nonce is None:
                nonce = await self.w3.eth.get_transaction_count(self.address, "pending")
            
            # Build transaction
            tx: TxParams = {
                "from": self.address,
                "to": _cs(to),
                "data": "0x" + calldata.hex(),
                "value": Wei(value),
                "chainId": self.chain_id,
                "nonce": nonce,
                "gasPrice": Wei(gas_price),
            }
            if gas is None:
                estimated_gas = await self.w3.eth.estimate_gas(tx)
                tx["gas"] = int(estimated_gas * 1.2)  # 20% buffer
            
            # Sign and send transaction
            signed = self.account.sign_transaction(tx)
            raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
            tx_hash = await self.w3.eth.send_raw_transaction(raw)
            return tx_hash.hex()
            
        except Exception as e:
            raise RuntimeError(f"Transaction failed: {e}")


    async def get_amount_out(self, token: str, amount_in: int, is_buy: bool) -> QuoteResult:
        try:
            """
                Check If the token has migrated or Not 
                Then fetch the amount out for the token sale/buy
            """
            result_for_liquidity = await self.tokenManagerHelper.functions.getTokenInfo(
                    _cs(token)
                ).call()
            is_liquidity = result_for_liquidity[11]
            if not is_liquidity:
                if is_buy:
                    result = await self.tokenManagerHelper.functions.tryBuy(
                        _cs(token), 0, int(amount_in)
                    ).call()

                    if not result:
                        return None
                    router = result[0]
                    amount_out = result[2]
                else:
                    result = await self.tokenManagerHelper.functions.trySell(
                        _cs(token), int(amount_in)
                    ).call()

                    if not result:
                        return None
                    router = result[0]
                    amount_out = result[2]
            else:
                result = await self.pancakeRouter.functions.getAmountsOut(
                    int(amount_in),
                    [_cs(WBNB), _cs(token)]
                ).call()
                router = self.pancakeRouter_address
                amount_out = result[1]

            return QuoteResult(
                router=_cs(router),
                amount=int(amount_out)
            )
        except Exception as e:
            raise RuntimeError(f"Failed to get amount out: {e}")


    async def buy(self, params: SellParams, router_addr: str) -> str:
        nonce = params.nonce
        gas = params.gas
        gas_price = params.gas_price
        
       
        
        # Encode buy parameters
        if _cs(router_addr) != _cs(self.pancakeRouter_address):
            encoded_params = encode(
                ["address","uint256","uint256"],
                [
                    _cs(params.token),
                    int(params.amount_in),
                    int(params.amount_out_min)
                ],
            )
            call_data = self.buy_sel + encoded_params
        else:
             # Set deadline if not provided
            deadline = (
                int(time.time()) + DEFAULT_DEADLINE_SECONDS 
                if params.deadline is None 
                else int(params.deadline)
            )
            encoded_params = encode(
                ["uint256","address[]","address","uint256"],
                [
                    int(params.amount_out_min),
                    [_cs(WBNB), _cs(params.token)],
                    _cs(params.to),
                    deadline
                ]
            )
            call_data = self.pancake_buy_sel + encoded_params

        
        # Send transaction
        return await self._send_transaction(
            router_addr, 
            # self.buy_sel + encoded_params,
            call_data,
            value=int(params.amount_in),
            nonce=nonce,
            gas=gas,
            gas_price=gas_price
        )
    

    async def sell(self, params: BuyParams, router_addr: str) -> str:
        nonce = params.nonce
        gas = params.gas
        gas_price = params.gas_price
        
       
        
        # Encode buy parameters
        if _cs(router_addr) != _cs(self.pancakeRouter_address):
            encoded_params = encode(
                ["address","uint256"],
                [
                    _cs(params.token),
                    int(params.amount_in)
                ]
            )
            call_data = self.sell_sel + encoded_params
        else:
             # Set deadline if not provided
            deadline = (
                int(time.time()) + DEFAULT_DEADLINE_SECONDS 
                if params.deadline is None 
                else int(params.deadline)
            )
            encoded_params = encode(
                ["uint256","uint256","address[]","address","uint256"],
                [
                    int(params.amount_in),
                    # int(params.amount_out_min),
                    0,
                    [_cs(params.token),_cs(WBNB)],
                    _cs(params.to),
                    deadline
                ]
            )
            call_data = self.pancake_sell_sel + encoded_params

        
        # Send transaction
        return await self._send_transaction(
            router_addr, 
            # self.buy_sel + encoded_params,
            call_data,
            nonce=nonce,
            gas=gas,
            gas_price=gas_price
        )
    
    async def wait_for_transaction(self, tx_hash: str, timeout: int = 60) -> Dict[str, Any]:
        try:
            receipt = await self.w3.eth.wait_for_transaction_receipt(
                tx_hash, 
                timeout=timeout
            )
            return dict(receipt)
        except Exception as e:
            raise RuntimeError(f"Failed to get transaction receipt: {e}")
