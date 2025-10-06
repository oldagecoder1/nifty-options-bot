# Trading Phases Guide - KiteConnect Integration

## 🎯 Overview

The bot supports **3 independent trading phases**:

| Phase | Data Source | Order Execution | Use Case |
|-------|-------------|-----------------|----------|
| **Phase 1** | Mock/Simulated | Paper Trading | Test strategy logic |
| **Phase 2** | KiteConnect Real-time | Paper Trading | Test with live market data |
| **Phase 3** | KiteConnect Real-time | Real Orders (AlgoTest) | Live trading |

---

## 🔧 Setup for Each Phase

### Phase 1: Mock Data + Paper Trading

**Purpose:** Test the strategy logic without any external dependencies

**Configuration:**
```bash
# .env file
TRADING_PHASE=1

# No broker credentials needed for Phase 1
# KITE_API_KEY=  (not required)
# KITE_ACCESS_TOKEN=  (not required)
```

**What Happens:**
- ✅ Uses simulated/mock market data
- ✅ Simulates order placement (paper trading)
- ✅ All strategy logic executes normally
- ✅ Generates trade logs in CSV
- ✅ No network calls to broker or order platform

**Run:**
```bash
python main.py
```

**Output:**
```
📊 NIFTY OPTIONS TRADING BOT - CONFIGURATION
Mode: 📝 PHASE 1: Mock Data + Paper Trading
Using Real Data: ❌ No (Mock)
Live Orders: 📝 No (Paper)
```

---

### Phase 2: KiteConnect Real Data + Paper Trading

**Purpose:** Test with live market data but no real orders

**Prerequisites:**
1. Zerodha trading account
2. KiteConnect API subscription (₹2000/month)
3. Access token (generated daily)

**Configuration:**
```bash
# .env file
TRADING_PHASE=2

# KiteConnect credentials
KITE_API_KEY=your_api_key_here
KITE_API_SECRET=your_api_secret_here
KITE_ACCESS_TOKEN=your_access_token_here
```

**Getting KiteConnect Credentials:**

1. **Sign up for Kite Connect:**
   - Visit: https://kite.trade/
   - Go to "Create new app"
   - Get API Key and API Secret

2. **Generate Access Token (Daily):**

```python
# generate_access_token.py
from kiteconnect import KiteConnect

kite = KiteConnect(api_key="your_api_key")

# Step 1: Get login URL
print("Login URL:", kite.login_url())

# Step 2: Open URL in browser, login, copy the request_token from redirect URL

# Step 3: Generate session
request_token = "paste_request_token_here"
data = kite.generate_session(request_token, api_secret="your_api_secret")

print("Access Token:", data["access_token"])
# Copy this token to .env file
```

**What Happens:**
- ✅ Connects to KiteConnect WebSocket
- ✅ Receives real-time tick data
- ✅ Fetches real historical candles
- ✅ Executes strategy with live market data
- ✅ Simulates orders (paper trading - no real orders)
- ✅ Generates trade logs

**Run:**
```bash
python main.py
```

**Output:**
```
📊 NIFTY OPTIONS TRADING BOT - CONFIGURATION
Mode: 📊 PHASE 2: KiteConnect Data + Paper Trading
Using Real Data: ✅ Yes
Live Orders: 📝 No (Paper)

✅ Connected to KiteConnect - User: Your Name
🔗 KiteConnect WebSocket started
Subscribed to 3 instruments
```

---

### Phase 3: KiteConnect Real Data + Live Orders

**Purpose:** Live trading with real money

**Prerequisites:**
1. Everything from Phase 2
2. AlgoTest account and API credentials
3. Thorough testing in Phase 1 & 2

**Configuration:**
```bash
# .env file
TRADING_PHASE=3

# KiteConnect credentials
KITE_API_KEY=your_api_key_here
KITE_API_SECRET=your_api_secret_here
KITE_ACCESS_TOKEN=your_access_token_here

# AlgoTest credentials
ALGOTEST_API_KEY=your_algotest_key
ALGOTEST_API_SECRET=your_algotest_secret
ALGOTEST_BASE_URL=https://api.algotest.in/v1
```

**What Happens:**
- ✅ Connects to KiteConnect WebSocket
- ✅ Receives real-time tick data
- ✅ Executes strategy with live market data
- 🔴 **Places REAL orders via AlgoTest**
- 🔴 **Real money at risk**
- ✅ Generates trade logs

**Run:**
```bash
python main.py
```

**Output:**
```
📊 NIFTY OPTIONS TRADING BOT - CONFIGURATION
Mode: 🔴 PHASE 3: KiteConnect Data + LIVE Trading
Using Real Data: ✅ Yes
Live Orders: 🔴 YES

✅ Connected to KiteConnect - User: Your Name
🔗 KiteConnect WebSocket started
🔴 PHASE 3: Placing REAL orders
```

---

## 📋 Step-by-Step Setup

### Step 1: Install KiteConnect

```bash
pip install kiteconnect
```

### Step 2: Download Instrument Tokens

Create a script to download Nifty option instruments:

```python
# download_instruments.py
from kiteconnect import KiteConnect
import pandas as pd

kite = KiteConnect(api_key="your_api_key")
kite.set_access_token("your_access_token")

# Get all NFO instruments (Nifty options)
instruments = kite.instruments("NFO")

# Filter for NIFTY options
nifty_options = [
    inst for inst in instruments 
    if inst['name'] == 'NIFTY' and inst['instrument_type'] in ['CE', 'PE']
]

# Convert to DataFrame
df = pd.DataFrame(nifty_options)

# Map to our format
df_mapped = pd.DataFrame({
    'symbol': df['tradingsymbol'],
    'token': df['instrument_token'],
    'strike': df['strike'],
    'expiry': df['expiry'],
    'option_type': df['instrument_type'],
    'lot_size': df['lot_size']
})

# Save to CSV
df_mapped.to_csv('data/instruments.csv', index=False)
print(f"Saved {len(df_mapped)} instruments to data/instruments.csv")
```

Run it:
```bash
python download_instruments.py
```

### Step 3: Generate Access Token Daily

**Important:** KiteConnect access token expires every day. You need to generate it daily.

**Option A: Manual (via browser)**
```python
# get_token.py
from kiteconnect import KiteConnect

api_key = "your_api_key"
kite = KiteConnect(api_key=api_key)

# Print login URL
print("Open this URL in browser:")
print(kite.login_url())
print("\nAfter login, copy the 'request_token' from URL and paste below:")
```

**Option B: Automated (using Selenium - advanced)**
```python
# auto_login.py (requires selenium)
from kiteconnect import KiteConnect
from selenium import webdriver
import time

# This automates the login flow
# See KiteConnect docs for complete implementation
```

### Step 4: Configure .env

```bash
# Start with Phase 1
TRADING_PHASE=1

# When ready for Phase 2, add:
KITE_API_KEY=your_key
KITE_ACCESS_TOKEN=your_token

# When ready for Phase 3, add:
ALGOTEST_API_KEY=your_algotest_key
```

### Step 5: Test Each Phase

**Phase 1 - Logic Testing:**
```bash
TRADING_PHASE=1 python main.py
```
- Verify strategy logic works
- Check entry/exit conditions
- Review trade logs

**Phase 2 - Live Data Testing:**
```bash
TRADING_PHASE=2 python main.py
```
- Verify KiteConnect connection
- Check WebSocket tick data
- Monitor strategy with real market
- Still paper trading (safe)

**Phase 3 - Live Trading:**
```bash
TRADING_PHASE=3 python main.py
```
- ⚠️ **REAL MONEY**
- Start with 1 lot only
- Monitor actively

---

## 🔍 Verification Commands

### Check Current Phase

```python
python -c "from config.settings import settings; settings.print_config()"
```

### Test KiteConnect Connection (Phase 2/3)

```python
# test_kite.py
from kiteconnect import KiteConnect
from config.settings import settings

kite = KiteConnect(api_key=settings.KITE_API_KEY)
kite.set_access_token(settings.KITE_ACCESS_TOKEN)

# Test connection
profile = kite.profile()
print(f"✅ Connected as: {profile['user_name']}")
print(f"Email: {profile['email']}")

# Test LTP fetch
ltp = kite.ltp(["NSE:NIFTY 50"])
print(f"Nifty LTP: {ltp}")
```

### Test WebSocket (Phase 2/3)

```python
# test_websocket.py
from kiteconnect import KiteTicker
from config.settings import settings

kws = KiteTicker(
    api_key=settings.KITE_API_KEY,
    access_token=settings.KITE_ACCESS_TOKEN
)

def on_ticks(ws, ticks):
    print("Tick received:", ticks)

def on_connect(ws, response):
    print("Connected!")
    # Subscribe to Nifty 50
    ws.subscribe([256265])
    ws.set_mode(ws.MODE_FULL, [256265])

kws.on_ticks = on_ticks
kws.on_connect = on_connect
kws.connect()
```

---

## 📊 Data Flow by Phase

### Phase 1: Mock Flow
```
Mock Data Generator
    ↓
Strategy Logic
    ↓
Paper Trade Logger
    ↓
CSV File
```

### Phase 2: Real Data + Paper
```
KiteConnect WebSocket (Real-time ticks)
    ↓
Strategy Logic
    ↓
Paper Trade Logger
    ↓
CSV File
```

### Phase 3: Real Data + Live Orders
```
KiteConnect WebSocket (Real-time ticks)
    ↓
Strategy Logic
    ↓
AlgoTest API (Real orders)
    ↓
Trade Confirmation
    ↓
CSV File + Live P&L
```

---

## 🐛 Troubleshooting

### Phase 2/3 Issues

**"Token expired" error:**
```bash
# Access token expires daily - regenerate it
python get_token.py
# Update .env with new token
```

**"Connection refused" on WebSocket:**
```bash
# Check if access token is valid
# Verify API key and secret
# Check internet connection
```

**"Instrument not found":**
```bash
# Re-download instruments.csv
python download_instruments.py
```

**WebSocket disconnects:**
```python
# The bot will show:
# "WebSocket closed: code - reason"
# It should reconnect automatically
# If not, restart the bot
```

---

## 📁 Additional Files Needed

### 1. Token Generator Script

Create `generate_token.py`:

```python
"""Generate KiteConnect access token"""
from kiteconnect import KiteConnect
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('KITE_API_KEY')
api_secret = os.getenv('KITE_API_SECRET')

kite = KiteConnect(api_key=api_key)

# Step 1: Get login URL
print("\n" + "="*60)
print("KITECONNECT ACCESS TOKEN GENERATOR")
print("="*60)
print("\n1. Open this URL in your browser:")
print(f"\n{kite.login_url()}\n")
print("2. Login with your Zerodha credentials")
print("3. You'll be redirected to a URL like:")
print("   http://127.0.0.1/?request_token=XXXXX&action=login&status=success")
print("\n4. Copy the 'request_token' value (XXXXX part) and paste below:")

request_token = input("\nEnter request_token: ").strip()

# Generate session
try:
    data = kite.generate_session(request_token, api_secret=api_secret)
    access_token = data["access_token"]
    
    print("\n" + "="*60)
    print("✅ ACCESS TOKEN GENERATED SUCCESSFULLY!")
    print("="*60)
    print(f"\nAccess Token: {access_token}")
    print("\nAdd this to your .env file:")
    print(f"KITE_ACCESS_TOKEN={access_token}")
    print("\n⚠️  Note: This token expires at the end of the day.")
    print("    You need to regenerate it daily.")
    print("="*60 + "\n")
    
except Exception as e:
    print(f"\n❌ Error: {e}\n")
```

### 2. Instrument Downloader

Create `download_instruments.py`:

```python
"""Download Nifty option instruments from KiteConnect"""
from kiteconnect import KiteConnect
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

kite = KiteConnect(api_key=os.getenv('KITE_API_KEY'))
kite.set_access_token(os.getenv('KITE_ACCESS_TOKEN'))

print("Downloading instruments from KiteConnect...")

# Get all NFO instruments
instruments = kite.instruments("NFO")

# Filter for NIFTY options only
nifty_options = [
    inst for inst in instruments 
    if inst['name'] == 'NIFTY' and inst['instrument_type'] in ['CE', 'PE']
]

print(f"Found {len(nifty_options)} NIFTY options")

# Also get Nifty index
nifty_index = [
    inst for inst in kite.instruments("NSE")
    if inst['tradingsymbol'] == 'NIFTY 50'
]

# Combine
all_instruments = nifty_index + nifty_options

# Convert to our format
df_mapped = pd.DataFrame({
    'symbol': [inst['tradingsymbol'] for inst in all_instruments],
    'token': [inst['instrument_token'] for inst in all_instruments],
    'strike': [inst.get('strike', 0) for inst in all_instruments],
    'expiry': [inst.get('expiry', datetime.now().date()) for inst in all_instruments],
    'option_type': [inst.get('instrument_type', 'INDEX') for inst in all_instruments],
    'lot_size': [inst['lot_size'] for inst in all_instruments]
})

# Save to CSV
output_path = 'data/instruments.csv'
df_mapped.to_csv(output_path, index=False)

print(f"✅ Saved {len(df_mapped)} instruments to {output_path}")
print("\nSample data:")
print(df_mapped.head(10))
```

---

## ⚠️ Important Notes

### Phase 2 & 3 Requirements

1. **Daily Token Generation**
   - Access token expires daily at market close
   - Run `generate_token.py` every morning before market
   - Update `.env` with new token

2. **Instrument Data**
   - Download fresh instruments weekly (expiries change)
   - Run `download_instruments.py` weekly

3. **WebSocket Stability**
   - Keep stable internet connection
   - WebSocket may disconnect - bot should handle reconnection
   - Monitor logs for connection issues

4. **Rate Limits**
   - KiteConnect has API rate limits
   - WebSocket is recommended for real-time data
   - Avoid excessive historical data calls

### Phase 3 Specific

1. **AlgoTest Integration**
   - Contact AlgoTest for API documentation
   - Test with small amounts first
   - Verify order confirmation logic

2. **Risk Management**
   - Start with 1 lot only
   - Monitor actively during first week
   - Set conservative `DAILY_LOSS_LIMIT`

3. **Order Validation**
   - Check order status after placement
   - Reconcile bot positions with broker
   - Handle partial fills

---

## 🚀 Quick Start Commands

**Phase 1 (Mock):**
```bash
# Set phase
echo "TRADING_PHASE=1" >> .env

# Run
python main.py
```

**Phase 2 (Real Data):**
```bash
# Generate token
python generate_token.py

# Download instruments
python download_instruments.py

# Set phase
echo "TRADING_PHASE=2" >> .env

# Run
python main.py
```

**Phase 3 (Live):**
```bash
# Ensure Phase 2 works well first!
# Add AlgoTest credentials to .env
# Set phase
echo "TRADING_PHASE=3" >> .env

# Run with caution
python main.py
```

---

## 📈 Progression Path

1. **Week 1-2:** Phase 1 - Understand strategy logic
2. **Week 3-4:** Phase 2 - Test with live market data
3. **Week 5+:** Phase 3 - Live trading (if confident)

**Never skip Phase 2!** Testing with real market data but paper orders is crucial.

---

Good luck! 🚀📈