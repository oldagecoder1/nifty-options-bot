# Quick Start Guide

## 🚀 Get Running in 5 Minutes

### Step 1: Create Project Structure (1 min)

```bash
# Create main directory
mkdir nifty-options-bot
cd nifty-options-bot

# Create all subdirectories
mkdir -p config data strategy execution backtest utils logs trades

# Create __init__.py files
touch config/__init__.py
touch data/__init__.py
touch strategy/__init__.py
touch execution/__init__.py
touch backtest/__init__.py
touch utils/__init__.py
```

### Step 2: Copy All Files (2 min)

Copy each artifact from the chat conversation into these files:

**Root Directory:**
- `requirements.txt`
- `.env.example` → rename to `.env` after copying
- `main.py`
- `run_backtest.py`
- `README.md`

**config/ directory:**
- `config/settings.py`

**data/ directory:**
- `data/instruments.py`
- `data/broker_api.py`
- `data/instruments.csv` (use the sample provided)

**strategy/ directory:**
- `strategy/indicators.py`
- `strategy/reference_levels.py`
- `strategy/strike_selector.py`
- `strategy/breakout_logic.py`
- `strategy/stop_loss.py`

**execution/ directory:**
- `execution/order_manager.py`
- `execution/paper_trading.py`

**backtest/ directory:**
- `backtest/backtester.py`

**utils/ directory:**
- `utils/logger.py`
- `utils/helpers.py`

### Step 3: Install Dependencies (1 min)

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### Step 4: Configure Settings (1 min)

Edit `.env` file:

```bash
# Minimum required settings for paper trading
LIVE_TRADING=false
STRIKE_OFFSET=200
LOT_SIZE=75
DAILY_LOSS_LIMIT=10000
```

### Step 5: Run Paper Trading! 🎉

```bash
python main.py
```

That's it! The bot will now:
- ✅ Run in paper trading mode (no real money)
- ✅ Log all trades to `trades/paper_trades_YYYYMMDD.csv`
- ✅ Show live updates in console
- ✅ Generate daily summary at market close

---

## 📝 What Happens Next?

### During Market Hours (9:15 AM - 3:30 PM IST):

**10:00-10:15 AM:**
```
⏰ Calculating reference levels from 10:00-10:15 candle...
✅ Reference levels calculated and stored
```

**10:15 AM:**
```
🎯 Selecting strikes at 10:15...
✅ Strikes selected:
   Call: NIFTY24OCT20150CE (Token: 40007)
   Put: NIFTY24OCT20550PE (Token: 40024)
```

**10:20+ AM (When Entry Signal):**
```
🔔 Breakout detected on CALL side, waiting for confirmation...
✅ CONFIRMATION on CALL: Close=202.00 > Breakout High=199.00
📝 PAPER TRADING: Simulating order...
✅ ENTERED CALL TRADE: NIFTY24OCT20150CE @ ₹202.00
```

**During Trade:**
```
📈 SL moved to BC: 175.00 → 186.00
📈 SL moved to RC: 186.00 → 197.00
🎯 SL moved to BREAKEVEN: 197.00 → 202.00
🔼 Trailing SL updated: 202.00 → 222.00
```

**Exit:**
```
🛑 STOP LOSS HIT: Price 220.00 <= SL 222.00
📝 PAPER TRADING: Simulating exit...
🚪 EXITED CALL TRADE @ ₹222.00
   Reason: SL_HIT
   P&L: ₹1,500.00
   Daily P&L: ₹1,500.00
```

---

## 🔧 Common Tasks

### Change Strike Offset

Want strikes closer/farther from spot?

Edit `.env`:
```bash
STRIKE_OFFSET=150  # Closer strikes
# or
STRIKE_OFFSET=250  # Farther strikes
```

### View Trade Logs

```bash
# Open today's trade log
cat trades/paper_trades_20241004.csv

# Or view in Excel/Google Sheets
```

### Check Application Logs

```bash
# View detailed logs
tail -f logs/trading.log

# See errors only
grep ERROR logs/trading.log
```

### Run Backtest

First, create a historical data CSV (see README for format), then:

```bash
python run_backtest.py --data ./my_historical_data.csv
```

---

## 🐛 Quick Troubleshooting

### Bot Not Starting?

```bash
# Check if dependencies installed
pip list | grep pandas

# Check if .env exists
ls -la .env

# Check logs
cat logs/trading.log
```

### No Trades Happening?

1. Check if market is open (9:15 AM - 3:30 PM IST)
2. Check if reference levels were calculated (in logs)
3. Check if strikes were selected (in logs)
4. Verify Nifty is moving (breakout needs price movement)

### "Instruments CSV not found"?

```bash
# Check if file exists
ls -la data/instruments.csv

# Create from sample if missing
# (Copy the sample provided in artifacts)
```

---

## 📊 Understanding the Output

### Paper Trading CSV Columns:

| Column | Description |
|--------|-------------|
| trade_id | Unique ID for each trade |
| timestamp | When action occurred |
| action | ENTRY or EXIT |
| symbol | Option symbol traded |
| side | CALL or PUT |
| qty | Quantity (lot size) |
| price | Entry/Exit price |
| stop_loss | Current SL at entry |
| exit_reason | SL_HIT, RSI_EXIT, HARD_EXIT |
| pnl | Profit/Loss (only on EXIT) |

### Daily Summary:

```
📊 PAPER TRADING DAILY SUMMARY
================================================================
Total Trades: 3
Total P&L: ₹2,450.00
Winning Trades: 2
Losing Trades: 1
Win Rate: 66.67%
Average Win: ₹1,800.00
Average Loss: ₹-625.00
================================================================
```

---

## 🎯 Next Steps

1. **Run for a few days in paper mode** - Get comfortable with the output
2. **Review trade logs** - Understand entry/exit logic
3. **Backtest historical data** - Validate on past data
4. **Adjust parameters** - Fine-tune STRIKE_OFFSET, TRAILING_INCREMENT, etc.
5. **Integrate real broker** - Replace mocks in `data/broker_api.py`
6. **Go live** - Only after thorough testing! Set `LIVE_TRADING=true`

---

## ⚠️ Before Going Live

- [ ] Tested in paper trading for at least 10 trading days
- [ ] Reviewed all trade logs and understand logic
- [ ] Backtested on historical data with good results
- [ ] Integrated real broker API (not using mocks)
- [ ] Configured AlgoTest API properly
- [ ] Set conservative DAILY_LOSS_LIMIT
- [ ] Have backup internet connection
- [ ] Monitoring setup (alerts, notifications)
- [ ] Starting with 1 lot only
- [ ] Ready to monitor bot actively

---

**Need Help?** Check the main README.md for detailed documentation!

Happy Trading! 🚀