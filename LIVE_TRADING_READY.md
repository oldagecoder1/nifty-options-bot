# 🚀 LIVE TRADING READY - PAPER TRADING MODE

## ✅ CHANGES COMPLETED

### 1. Entry Logic Implementation ✅
The new entry rules have been **correctly implemented** in `strategy/breakout_logic.py`:

**Entry Rules:**
- After 10:00, once all reference levels (RN, GN, BN) are set
- Monitor Nifty 5-minute chart for entry signals
- **CALL Entry:** 
  - Candle K closes above RN
  - Next candle (K+1) also closes above RN AND above previous candle's close
- **PUT Entry:**
  - Candle K closes below GN
  - Next candle (K+1) also closes below GN AND below previous candle's close
- After exit/stop-loss, wait for same breakout and confirmation setup before re-entry

### 2. Re-entry Logic ✅
After position exit, the system:
- Requires price to close back below RN (for CALL) or above GN (for PUT) on two consecutive candles
- Then waits for fresh two-candle confirmation before allowing new entry
- This prevents immediate re-entry in choppy conditions

### 3. Configuration Updates ✅
- **Trading Phase:** Set to Phase 2 (Real data + Paper trading)
- **Reference Window:** Set to 09:45-10:00
- **Strike Selection:** Set to 10:00
- **Trading Start:** Set to 10:00 (after reference levels are calculated)

### 4. Main.py Entry Logic Fixed ✅
- Entry now triggers directly from Nifty 5-minute candle confirmation
- No longer waits for option candle breakout (old logic removed)
- Fetches current option price at moment of entry signal
- Calls `notify_position_closed()` after exit to re-arm detector

---

## 📋 PRE-TRADING CHECKLIST

### Before Market Opens (9:00 AM):

#### 1. Download Latest Instruments ⚠️
```bash
python download_instruments.py
```
This downloads the latest Nifty option contracts from KiteConnect.
**Run this weekly** (especially on Thursdays when new weekly options are added).

#### 2. Verify Access Token 🔑
Your current access token in `.env`:
```
KITE_ACCESS_TOKEN=pXCv2nrCgBPuthNAT18jhUN0BEJMSO4m
```

**Check if token is valid:**
```bash
python get_kite_token.py --check
```

If expired, generate new token:
```bash
python get_kite_token.py
```

#### 3. Verify Configuration ✅
Current settings in `.env`:
- **TRADING_PHASE=2** (Real data + Paper trading) ✅
- **REFERENCE_WINDOW:** 09:45-10:00 ✅
- **STRIKE_SELECTION_TIME:** 10:00 ✅
- **STRIKE_OFFSET:** 200 points
- **LOT_SIZE:** 75
- **DAILY_LOSS_LIMIT:** ₹10,000

---

## 🎯 HOW TO RUN TODAY

### Start the Bot (9:00-9:15 AM):
```bash
python main.py
```

### What Will Happen:

**9:15 AM - Market Opens:**
- Bot connects to KiteConnect
- Subscribes to Nifty 50 spot (token: 256265)
- Starts receiving real-time tick data
- Aggregates ticks into 1-minute and 5-minute candles

**09:45-10:00 AM - Reference Window:**
- Bot collects Nifty data from 09:45 to 10:00
- At 10:00, calculates reference levels (RN, GN, BN)

**10:00 AM - Strike Selection:**
- Selects Call and Put strikes (ATM ± 200 points)
- Subscribes to selected option instruments
- Fetches historical option data from 09:45-10:00
- Recalculates reference levels with option data

**After 10:00 - Trading Window:**
- Monitors Nifty 5-minute candles for entry signals
- When two-candle confirmation occurs:
  - Logs entry in paper trading mode (no real order)
  - Starts monitoring for exit conditions
- Exit triggers:
  - Stop-loss hit (progressive/trailing)
  - RSI exit condition
  - Hard exit at 3:15 PM

**3:15 PM - Hard Exit:**
- Any open position is closed
- Daily summary is printed

---

## 📊 MONITORING

### Log Files:
```bash
# Watch live logs
tail -f logs/trading.log

# View paper trades
cat trades/paper_trades_YYYYMMDD.csv
```

### What to Watch For:
1. **Connection Status:** "✅ WebSocket started - receiving Nifty ticks"
2. **Reference Levels:** "✅ Reference levels calculated"
3. **Strike Selection:** "✅ Strikes selected"
4. **Entry Signals:** "✅ Entry signal confirmed on Nifty 5-min chart: CALL/PUT"
5. **Paper Trades:** "📝 PHASE 2: Simulating order..."

---

## 🔴 IMPORTANT NOTES

### Paper Trading Mode (Phase 2):
- ✅ Uses **REAL live market data** from KiteConnect
- ✅ Monitors **REAL Nifty and option prices**
- ✅ Logs all trades to CSV file
- ❌ **NO REAL ORDERS** are placed
- ❌ **NO MONEY** at risk

### To Switch to Live Trading (Phase 3):
**DO NOT DO THIS without thorough testing!**
1. Set `TRADING_PHASE=3` in `.env`
2. Configure AlgoTest API credentials
3. Verify order placement logic
4. Start with small position size

---

## 🐛 TROUBLESHOOTING

### "Access token expired"
```bash
python get_kite_token.py
```
Update the new token in `.env`

### "Nifty token not found"
```bash
python download_instruments.py
```

### "No candles available"
- Check if market is open (9:15 AM - 3:30 PM)
- Verify WebSocket connection in logs
- Check internet connectivity

### "Could not fetch option price"
- Ensure strikes are selected at 10:00
- Check if options are subscribed in logs
- Verify instrument tokens are valid

---

## 📈 EXPECTED BEHAVIOR TODAY

1. **9:15 AM:** Bot starts, connects to KiteConnect
2. **09:45-10:00 AM:** Collects reference data
3. **10:00 AM:** Calculates levels, selects strikes
4. **10:05+ AM:** First possible entry (after two 5-min candles post-10:00)
5. **Throughout day:** Monitors for entry/exit signals
6. **3:15 PM:** Hard exit if in position
7. **3:30 PM:** Market closes, bot can be stopped

---

## 🎓 STRATEGY SUMMARY

**Reference Levels (09:45-10:00):**
- RN (Red Nifty) = Highest high of Nifty in window
- GN (Green Nifty) = Lowest low of Nifty in window
- BN (Blue Nifty) = Middle of RN and GN

**Entry (After 10:00):**
- CALL: Two consecutive 5-min Nifty candles close above RN (with second > first)
- PUT: Two consecutive 5-min Nifty candles close below GN (with second < first)

**Exit:**
- Progressive stop-loss (moves up as price increases)
- Trailing stop-loss (after breakeven)
- RSI exit (when RSI drops 10 points from peak)
- Hard exit at 3:15 PM

**Re-entry:**
- After exit, price must close back to opposite side of level
- Then wait for fresh two-candle confirmation

---

## ✅ READY TO RUN

Your bot is configured and ready for live data paper trading!

**Start command:**
```bash
python main.py
```

**Monitor logs:**
```bash
tail -f logs/trading.log
```

**Good luck! 🚀📈**