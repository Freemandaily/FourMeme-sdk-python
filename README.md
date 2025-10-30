# FourMeme-sdk-python


A full-featured Python SDK for seamless interaction with Four.Meme ecosystem contracts on the Bsc blockchain — supporting bonding-curve trading, DEX execution, and real-time on-chain event streaming


## Features

- 🚀 **Trading**: Execute buy/sell operations on bonding curves with slippage protection
- 💰 **Token Operations**: ERC-20 token interactions (balance, approve, transfer)
- 📊 **Bonding Curves**: Query curve parameters and check liquidity status
- 🔄 **Real-time Streaming**: Monitor bonding curve and DEX events via WebSocket with token filtering
- 📚 **Historical Indexing**: Fetch and analyze past events with CurveIndexer and DexIndexer
- ⚡ **Async/Await**: Fully asynchronous design for high performance

## Installation
install from source:

```bash
git clone https://github.com/Freemandaily/FourMeme-sdk-python
cd FourMeme-sdk-python

pip install -e .
```

## Quick Start
```python
import asyncio
from Four-sdk import Trade, BuyParams, calculate_slippage, parseMon

async def main():
    # Initialize trade client
    https_url =  'https://public-bsc-mainnet.fastnode.io'
    private_key = 'Your_Private_Key
    trade = Trade(rpc_url=https_url, private_key=private_key)

    # Get quote for buying tokens
    token = "0x1cF0A038015D108f4Adc6Db09e14ed8c783B4444"
    amount_in = parseMon(1)  # 1 Bnb
    quote = await trade.get_amount_out(token, amount_in, is_buy=True)

    # Execute buy with slippage protection
    params = BuyParams(
        token=token,
        to=trade.address,
        amount_in=amount_in,
        amount_out_min=calculate_slippage(quote.amount, 5)  # 5% slippage tolerance
    )
    tx_hash = await trade.buy(params, quote.router)
    reciept = await trade.wait_for_transaction(tx_hash, timeout=60)
    print(f"Transaction: {tx_hash}")

asyncio.run(main())
```

## Core Modules

### 🚀 Trading

Execute trades on bonding curves with automatic routing:

```python
from Four-sdk import Trade, BuyParams, SellParams, calculate_slippage

trade = Trade(rpc_url, private_key)

# Get quotes
buy_quote = await trade.get_amount_out(token, bnb_amount, is_buy=True)
sell_quote = await trade.get_amount_out(token, token_amount, is_buy=False)

# Buy tokens
buy_params = BuyParams(
    token=token,
    to=wallet_address,
    amount_in=bnb_amount,
    amount_out_min=calculate_slippage(buy_quote.amount, 5),
    deadline=None  
)
tx = await trade.buy(buy_params, buy_quote.router)

# Sell tokens
sell_params = SellParams(
    token=token,
    to=wallet_address,
    amount_in=token_amount,
    amount_out_min=calculate_slippage(sell_quote.amount, 5),
    deadline=None
)
tx = await trade.sell(sell_params, sell_quote.router)

# Wait for transaction
receipt = await trade.wait_for_transaction(tx, timeout=60)
```

### 💰 Token Operations

Interact with ERC-20 tokens:

```python
from Four-sdk import Token

token = Token(rpc_url, private_key)

# Get token metadata
metadata = await token.get_metadata(token_address)
print(f"Token: {metadata['name']} ({metadata['symbol']})")
print(f"Decimals: {metadata['decimals']}")
print(f"Total Supply: {metadata['totalSupply']}")

# Check balances
balance = await token.get_balance(token_address)
balance = await token.get_balance(token_address, owner_address)  # Check other address

# Check allowance
allowance = await token.get_allowance(token_address, spender_address)

# Approve tokens
tx = await token.approve(token_address, spender_address, amount)

# Transfer tokens
tx = await token.transfer(token_address, recipient_address, amount)

# Smart approval (only approves if needed)
tx = await token.check_and_approve(token_address, spender_address, required_amount)
```


### 📊 Bonding Curve Data

Query bonding curve information:

```python

# Get curve reserves
curve_data = await trade.get_curves(token_address)
print(f"Reserve BnB: {curve_data.reserve}")
print(f"Max Reserve Needed: {curve_data.max_reserve}")

# Check if Liquidity has been added to the token
print(f"Liquidity Added: {curve_data.liquidity_added}")

# Get amount needed for specific output
quote = await trade.get_amount_in(token_address, desired_output, is_buy=True)
```



### 🔄 Real-time Event Streaming

Monitor events in real-time using WebSocket connections:

#### Curve Events Stream

```python
from Four-sdk import CurveStream, EventType, CurveEvent

# Initialize stream
stream = CurveStream(ws_url)

# Subscribe to specific events
stream.subscribe([EventType.MANAGER_2_BUY])  # Only BUY events
stream.subscribe([EventType.MANAGER_2_SELL])  # Only SELL events
stream.subscribe([EventType.MANAGER_2_BUY, EventType.MANAGER_2_SELL])  # Both
stream.subscribe()  # All events (default)

# Filter by token addresses (optional)
stream.subscribe(
    [EventType.MANAGER_2_BUY, EventType.MANAGER_2_SELL],
    token_addresses=["0x1234...", "0x5678..."]  # Only events from these tokens
)

# Process events with typed async iterator
event: CurveEvent
async for event in stream.events():
    print(f"Event: {event['eventName']}")      # "BUY" or "SELL"
    print(f"Trader: {event['trader']}")        # Buyer/Seller address
    print(f"Token: {event['token']}")          # Token address
    print(f"Amount: {event['amount']}")   # amount bought /sold
    print(f"Cost: {event['cost']}") # Bnb Spent/ Bought
    price(f"Price: {event["price"]}")
    print(f"Tx: {event['transactionHash']}")
```

#### DEX Swap Events Stream

```python
from Four-sdk import DexStream, DexSwapEvent

# Initialize stream
stream = DexStream(ws_url)

# Subscribe to tokens (automatically finds pools)
stream.subscribe_tokens("0x1234...")  # Single token
stream.subscribe_tokens(["0x1234...", "0x5678..."])  # Multiple tokens

# Process swap events with typed iterator
event: DexSwapEvent
async for event in stream.events():
    print(f"Event: {event['eventName']}")
    print(f"Pool: {event['pool']}")
    print(f"Sender: {event['sender']}")
    print(f"Amount0In: {event['amount0In']}")
    print(f"amount1In: {event['amount1In']}")
    print(f"amount0Ou: {event["amount0Out"]}")
    print(f"amount1Out: {event["amount1Out"]}")
    print(f"Price : {event['price']}")
    print(f"Tx: {event['transactionHash']}")
```


### 📚 Historical Event Indexing

Index historical blockchain events for analysis:

#### Curve Indexer

```python
from Four-sdk import CurveIndexer, EventType

# Initialize indexer
indexer = CurveIndexer(rpc_url)

# Get current block number
latest_block = await indexer.get_block_number()
from_block = latest_block - 1000  # Last 1000 blocks

# Fetch all events
all_events = await indexer.fetch_events(from_block, latest_block)

# Filter by event types (Bonding Token Creation)
trade_events = await indexer.fetch_events(
    from_block,
    latest_block,
    event_types=[EventType.MANAGER_2_CREATE]
)

```


## API Reference

### Trade Class

```python
trade = Trade(rpc_url: str, private_key: str)
```

#### Methods

- `async get_amount_out(token: str, amount_in: int, is_buy: bool) -> QuoteResult`

  - Get expected output amount for a trade
  - Returns `QuoteResult` with `router` address and `amount`

- `async get_amount_in(token: str, amount_out: int, is_buy: bool) -> QuoteResult`

  - Get required input amount for desired output
  - Returns `QuoteResult` with `router` address and `amount`

- `async buy(params: BuyParams, router: str, nonce: int = None, gas: int = None) -> str`

  - Execute buy transaction
  - Returns transaction hash

- `async sell(params: SellParams, router: str, nonce: int = None, gas: int = None) -> str`

  - Execute sell transaction
  - Returns transaction hash


- `async get_curves(token: str) -> CurveData`

  - Get bonding curve reserves
  - Returns `CurveData` with `reserve` 

- `async wait_for_transaction(tx_hash: str, timeout: int = 60) -> Dict`
  - Wait for transaction confirmation


### Token Class

```python
token = Token(rpc_url: str, private_key: str)
```

#### Methods

- `async get_balance(token: str, address: str = None) -> int`

  - Get token balance (defaults to own address)

- `async get_allowance(token: str, spender: str, owner: str = None) -> int`

  - Get approved amount (defaults to own address as owner)

- `async get_metadata(token: str) -> TokenMetadata`

  - Get token metadata (name, symbol, decimals, totalSupply)

- `async approve(token: str, spender: str, amount: int) -> str`

  - Approve tokens for spending

- `async transfer(token: str, to: str, amount: int) -> str`

  - Transfer tokens

- `async check_and_approve(token: str, spender: str, required: int, buffer_percent: float = 10) -> Optional[str]`
  - Smart approval - only approves if current allowance is insufficient

### Stream Classes

#### CurveStream

```python
stream = CurveStream(ws_url: str)
```

- `subscribe(event_types: List[EventType] = None)` - Set events to subscribe to
- `async events() -> AsyncIterator[Dict]` - Async iterator yielding parsed events

#### DexStream

```python
stream = DexStream(ws_url: str)
```

- `subscribe_tokens(token_addresses: Union[str, List[str]])` - Set tokens to monitor
- `async events() -> AsyncIterator[Dict]` - Async iterator yielding swap events




### Utilities

- `calculate_slippage(amount: int, percent: float) -> int`
  - Calculate minimum output amount with slippage tolerance
- `parse(amount: float | str) -> int`
  - Convert Bnb amount to wei (18 decimals)


### Environment Variables

```bash
# Network endpoints
RPC_URL=                                   # HTTP RPC endpoint for Bsc Mainnet
WS_URL=                                    # WebSocket endpoint for real-time event streaming

# Wallet configuration
PRIVATE_KEY=your_private_key_here         # Private key (without 0x prefix)

# Token addresses
TOKEN=0x...                                # Single token address for trading
TOKENS=0x...                               # Multiple token addresses for DEX monitoring (comma-separated)

# Trading parameters
AMOUNT=                                    # Amount in bnb for trading (e.g., 0.1)
SLIPPAGE=                                  # Slippage tolerance percentage (e.g., 5)
```

### Network Information

- **Chain**: Bsc Mainnet
- **Chain ID**: 56
- **Native Token**: BNB
- **Block Explorer**: https://bscscan.com/



All contract addresses are defined in `src/Four-sdk/constants.py`

- **tokenManager1**: `0xEC4549caDcE5DA21Df6E6422d448034B5233bFbC`
- **tokenManager2**: `0x5c952063c7fc8610FFDB798152D69F0B9550762b`
- **tokenManagerHelper**: `0xF251F83e40a78868FcfA3FA4599Dad6494E46034`
- **v2_factory**: `0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73`
- **v3_factory**: `0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865`
- **pancakeRouter**: `0x10ED43C718714eb63d5aA57B78B54704E256024E`


## Requirements

- Python 3.11+
- web3.py >= 7.0.0
- eth-account
- eth-abi
- python-dotenv

## Development

```bash
# Clone the repository
git clone https://github.com/Freemandaily/FourMeme-sdk-python
cd FourMeme-sdk-python


# Install in development mode
pip install -e .
