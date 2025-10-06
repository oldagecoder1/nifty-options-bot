# KiteConnect Integration - Complete Setup Guide

## 📋 What Changed

I've updated the code to support **3 independent phases** with **KiteConnect integration**:

| What | Changed Files |
|------|---------------|
| Phase configuration | `config/settings.py`, `.env.example` |
| KiteConnect integration | `data/broker_api.py` |
| Phase-aware order execution | `execution/order_manager.py` |
| KiteConnect dependency | `requirements.txt` |
| Helper scripts | `generate_token.py`, `download_instruments.py` |
| Documentation | `PHASE_GUIDE.md`, `KITECONNECT_SETUP.md` |

---

## 🚀 Quick Start

### 1. Update Your Files

Replace these files with the new versions:
- ✅ `config/settings.py` (updated)
- ✅ `data/broker_api.py` (KiteConnect integrated)
- ✅ `execution/order_manager.py` (phase-aware)
- ✅ `.env.example` (with phase config)
- ✅ `requirements.txt` (added kiteconnect)

Add these new files:
- ✅ `generate_token.py` (new)
- ✅ `download_instruments.py` (new)
- ✅ `PHASE_GUIDE.md` (new)
- ✅ `KITECONNECT_SETUP.md` (this file)

### 2. Install KiteConnect

```bash
pip install kiteconnect==4.2.0
```

### 3. Choose Your Phase

Edit `.env`:
```bash
TRADING_PHASE=1  # Start with Phase 1
```

---

## 📊 The 3 Phases

### Phase 1: Mock Data + Paper Trading ✅
**No broker needed - Test strategy logic**

```bash
# .env
TRADING_PHASE=1

# Run
python main.py
```

**What it does:**
- Uses simulated data
- Tests strategy logic
- Paper trading only
- No external dependencies

---

### Phase 2: KiteConnect Data + Paper Trading 📊
**Real market data - Safe testing**

#### Prerequisites:
1. Zerodha trading account
2. KiteConnect API subscription (₹2000/month from https://kite.trade)
3. API Key & Secret from Kite Connect dashboard

#### Setup:

**Step 1: Get KiteConnect credentials**
- Visit: https://kite.trade/
- Create app → Get API Key and Secret
- Add to `.env`:
```bash
KITE_API_KEY=your_api_key
KITE_API_SECRET=your_api_secret
```

**Step 2: Generate access token (daily)**
```bash
python generate_token.py
```
- Opens login URL in instructions
- Login via browser
- Copy request token
- Paste in terminal
- Token added to `.env` automatically

**Step 3: Download instruments**
```bash
python download_instruments.py
```
- Downloads all Nifty options
- Saves to `data/instruments.csv`
- Run weekly for latest expiries

**Step 4: Set phase and run**
```bash
# .env
TRADING_PHASE=2

# Run
python main.py
```

**What it does:**
- ✅ Real KiteConnect WebSocket data
- ✅ Real-time tick updates
- ✅ Actual market prices
- ✅ Strategy executes with live data
- 📝 Still paper trading (safe)

---

### Phase 3: KiteConnect Data + Live Orders 🔴
**REAL MONEY - Live trading**

#### Additional Prerequisites:
1. Everything from Phase 2
2. AlgoTest account & API credentials
3. Thorough testing in Phase 1 & 2

#### Setup:

```bash
# .env
TRADING_PHASE=3

KITE_API_KEY=your_api_key
KITE_ACCESS_TOKEN=your_token

ALGOTEST_API_KEY=your_algotest_key
ALGOTEST_API_SECRET=your_algotest_secret

# Run with CAUTION
python main.py
```

**What it does:**
- ✅ Real KiteConnect data
- 🔴 **REAL orders via AlgoTest**
- 🔴 **REAL money at risk**
- ✅ Full automation

---

## 🔧 Daily Workflow

### Every Trading Day:

**1. Morning Setup (before 9:15 AM)**
```bash
# Generate fresh access token
python generate_token.py

# Verify connection
python -c "from config.settings import settings; settings.print_config()"
```

**2. Run the Bot**
```bash
# Phase 1 (testing)
TRADING_PHASE=1 python main.py

# Phase 2 (live data, paper orders)
TRADING_PHASE=2 python main.py

# Phase 3 (live trading)
TRADING_PHASE=3 python main.py
```

**3. Monitor**
```bash
# Watch logs
tail -f logs/trading.log

# Check trades
cat trades/paper_trades_*.csv
```

---

## 📁 File Structure (Updated)

```
nifty-options-bot/
├── main.py                          # Main bot (phase-aware)
├── run_backtest.py                  # Backtesting
├── requirements.txt                 # ✅ UPDATED (added kiteconnect)
├── .env                            # ✅ UPDATED (phase config)
│
├── generate_token.py               # 🆕 NEW - Generate KiteConnect token
├── download_instruments.py         # 🆕 NEW - Download strike data
│
├── config/
│   ├── __init__.py
│   └── settings.py                 # ✅ UPDATED (phase support)
│
├── data/
│   ├── __init__.py
│   ├── broker_api.py              # ✅ UPDATED (KiteConnect integrated)
│   ├── instruments.py
│   └── instruments.csv            # Will be auto-generated
│
├── strategy/                       # No changes
│   ├── reference_levels.py
│   ├── strike_selector.py
│   ├── breakout_logic.py
│   ├── stop_loss.py
│   └── indicators.py
│
├── execution/
│   ├── __init__.py
│   ├── order_manager.py           # ✅ UPDATED (phase-aware)
│   └── paper_trading.py
│
├── backtest/
│   └── backtester.py
│
├── utils/
│   ├── logger.py
│   └── helpers.py
│
├── logs/                           # Auto-generated
└── trades/                         # Auto-generated
│
├── PHASE_GUIDE.md                 # 🆕 NEW - Phase documentation
└── KITECONNECT_SETUP.md           # 🆕 NEW - This file
```

---

## 🔑 KiteConnect Token Management

### Understanding Access Tokens

**Important:** KiteConnect access tokens expire daily around 3:30 PM

### Daily Token Generation

**Method 1: Manual (Recommended)**
```bash
python generate_token.py
```

**Method 2: In Python**
```python
from kiteconnect import KiteConnect

kite = KiteConnect(api_key="your_key")
print(kite.login_url())

# Open URL, login, get request_token
data = kite.generate_session(request_token, api_secret="secret")
print(data["access_token"])
```

### Automating Token Generation (Advanced)

```python
# auto_token.py (requires selenium)
from selenium import webdriver
from selenium.webdriver.common.by import By
from kiteconnect import KiteConnect
import time

def auto_generate_token():
    """Automate token generation using Selenium"""
    # This requires your Zerodha credentials
    # Not recommended for security reasons
    # Better to use manual method daily
    pass
```

---

## 📊 Data Flow in Each Phase

### Phase 1 Flow:
```
┌─────────────┐
│  Mock Data  │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│ Strategy Logic   │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Paper Trading    │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  CSV Log Files   │
└──────────────────┘
```

### Phase 2 Flow:
```
┌──────────────────────┐
│ KiteConnect WebSocket│ ← Real-time ticks
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   Strategy Logic     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   Paper Trading      │ ← No real orders
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│    CSV Log Files     │
└──────────────────────┘
```

### Phase 3 Flow:
```
┌──────────────────────┐
│ KiteConnect WebSocket│ ← Real-time ticks
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   Strategy Logic     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   AlgoTest API       │ ← Real orders
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Order Confirmation   │
│  + CSV Log Files     │
└──────────────────────┘
```

---

## 🧪 Testing Checklist

### Phase 1 Testing:
- [ ] Bot starts without errors
- [ ] Reference levels calculated correctly
- [ ] Strikes selected properly
- [ ] Entry signals detected
- [ ] Stop loss progression works
- [ ] Trailing SL functions
- [ ] RSI exit triggers
- [ ] Trades logged to CSV
- [ ] Daily summary generated

### Phase 2 Testing:
- [ ] KiteConnect connection successful
- [ ] WebSocket connects and receives ticks
- [ ] Real-time price updates work
- [ ] Historical data fetches correctly
- [ ] Strategy executes with live data
- [ ] All Phase 1 tests still pass
- [ ] Paper trades logged correctly
- [ ] No real orders placed (verify!)

### Phase 3 Testing:
- [ ] AlgoTest credentials configured
- [ ] Test with 1 lot only first
- [ ] Order placement works
- [ ] Order confirmation received
- [ ] Position tracking accurate
- [ ] Exit orders execute properly
- [ ] P&L calculation correct
- [ ] Daily loss limit enforced

---

## 🐛 Common Issues & Solutions

### Issue: "Token expired"
```bash
Error: TokenException - Token is invalid or has expired
```
**Solution:**
```bash
python generate_token.py
# Update .env with new token
```

### Issue: "WebSocket connection failed"
```bash
Error: Unable to connect to WebSocket
```
**Solutions:**
- Check internet connection
- Verify access token is valid
- Check if KiteConnect subscription is active
- Restart the bot

### Issue: "Instrument not found"
```bash
Error: Instrument token XXX not found
```
**Solution:**
```bash
python download_instruments.py
# This updates instruments.csv with latest data
```

### Issue: "No data in reference window"
```bash
Warning: No historical data returned for token XXX
```
**Solutions:**
- Check if market is open
- Verify token is correct
- Check if it's a trading day (not weekend/holiday)

### Issue: "Rate limit exceeded"
```bash
Error: Rate limit exceeded
```
**Solutions:**
- Use WebSocket for real-time data (not REST API)
- Reduce frequency of historical data calls
- Wait a minute and retry

---

## 💡 Pro Tips

### 1. Token Management
```bash
# Create a morning startup script
cat > morning_setup.sh << 'EOF'
#!/bin/bash
echo "🌅 Morning Trading Setup"
python generate_token.py
python download_instruments.py  # Optional: run weekly
python main.py
EOF

chmod +x morning_setup.sh
./morning_setup.sh
```

### 2. Multiple Strategies
Run different phases simultaneously:
```bash
# Terminal 1: Test new logic
TRADING_PHASE=1 python main.py

# Terminal 2: Monitor live data
TRADING_PHASE=2 python main.py

# Terminal 3: Live trading (when ready)
TRADING_PHASE=3 python main.py
```

### 3. Monitoring
```bash
# Watch live logs
tail -f logs/trading.log | grep -E "ENTRY|EXIT|ERROR"

# Monitor trades
watch -n 5 'tail -20 trades/paper_trades_*.csv'

# Check WebSocket status
grep "WebSocket" logs/trading.log
```

### 4. Quick Phase Switch
```bash
# In .env, just change the number:
TRADING_PHASE=1  # Mock
TRADING_PHASE=2  # Real data, paper orders
TRADING_PHASE=3  # Real data, real orders
```

---

## 📈 Migration Path

### Current State → Phase 1
```bash
# 1. Update files
# 2. Set TRADING_PHASE=1
# 3. Run and test
```

### Phase 1 → Phase 2
```bash
# 1. Get KiteConnect API subscription
# 2. Add credentials to .env
# 3. Generate token: python generate_token.py
# 4. Download instruments: python download_instruments.py
# 5. Set TRADING_PHASE=2
# 6. Run and test with live data
```

### Phase 2 → Phase 3
```bash
# 1. Test Phase 2 for at least 2 weeks
# 2. Get AlgoTest credentials
# 3. Add to .env
# 4. Set TRADING_PHASE=3
# 5. Start with 1 lot only
# 6. Monitor actively
```

---

## 🔒 Security Best Practices

1. **Never commit .env to Git**
```bash
echo ".env" >> .gitignore
```

2. **Protect access tokens**
```bash
chmod 600 .env  # Only you can read
```

3. **Separate credentials**
```bash
# Use different API keys for testing vs production
KITE_API_KEY_TEST=xxx
KITE_API_KEY_PROD=yyy
```

4. **Monitor access**
- Check KiteConnect dashboard for API usage
- Review login history in Zerodha
- Monitor unusual activity

---

## 📞 Support Resources

### KiteConnect:
- Docs: https://kite.trade/docs/connect/v3/
- Forum: https://kite.trade/forum/
- API Status: https://kite.trade/status

### Zerodha:
- Support: https://support.zerodha.com/
- Trading: https://zerodha.com/

### Bot Issues:
- Check logs: `logs/trading.log`
- Review trades: `trades/paper_trades_*.csv`
- Validate config: `python -c "from config.settings import settings; settings.print_config()"`

---

## ✅ Final Checklist

Before going live (Phase 3):

- [ ] Tested in Phase 1 for 1 week (understand logic)
- [ ] Tested in Phase 2 for 2+ weeks (live data)
- [ ] Reviewed all trade logs
- [ ] Backtested with historical data
- [ ] KiteConnect credentials working
- [ ] AlgoTest integration tested
- [ ] Daily token generation automated
- [ ] Instruments CSV updated weekly
- [ ] Risk parameters set conservatively
- [ ] Daily loss limit configured
- [ ] Starting with 1 lot only
- [ ] Monitoring setup in place
- [ ] Understand every line of code
- [ ] Have backup plan for failures

---

## 🎯 Summary

### What You Have Now:

✅ **Phase 1:** Test strategy logic safely (mock data)  
✅ **Phase 2:** Test with real market data (paper trading)  
✅ **Phase 3:** Live trading (real money)  

✅ **KiteConnect:** Fully integrated for real-time data  
✅ **Helper Scripts:** Token generation, instrument downloads  
✅ **Phase Switching:** Simple env variable change  
✅ **Production Ready:** All safety checks in place  

### Next Steps:

1. Update your code with new files
2. Install kiteconnect: `pip install kiteconnect`
3. Start with Phase 1
4. Progress to Phase 2 when comfortable
5. Go live with Phase 3 (carefully!)

---

**Good luck with your automated trading!** 🚀📈

*Remember: Test thoroughly, start small, scale gradually!*