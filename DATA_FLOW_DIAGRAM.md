# Data Collection Flow - Visual Diagram

## Timeline View: How Data is Collected

```
TIME          EVENT                    NIFTY DATA              OPTION DATA
─────────────────────────────────────────────────────────────────────────────
09:15:00      Market Opens            
              Bot Starts              
              ↓                       
              Subscribe Nifty         ✅ WebSocket START      ❌ Not subscribed
              ↓                           (live ticks)
              
09:15:00      Collecting...           ✅ Tick → Candle        ❌ Not subscribed
  to                                      Aggregator
09:45:00                              
                                      
09:45:00      Reference Window        ✅ WebSocket            ❌ Not subscribed
              STARTS                      (live ticks)
              ↓                           
              Collecting...           ✅ Tick → Candle        ❌ Not subscribed
              ↓                           Aggregator
              
09:55:00      Last candle of          ✅ WebSocket            ❌ Not subscribed
              reference window            (live ticks)
              
10:00:00      Reference Window        ✅ WebSocket            ❌ Not subscribed
              ENDS                        (live ticks)
              ↓
              Calculate Ref Levels    ✅ Use aggregated       ❌ Not available
              (preliminary)               candles
              ↓
              Select Strikes          ✅ WebSocket            🔄 HISTORICAL API
              ↓                           (live ticks)            BACKFILL
              Subscribe Options                                   (09:45-10:00)
              ↓                                               
10:00:23      Recalculate Ref         ✅ Use aggregated       ✅ Historical API
              Levels (final)              candles                 (09:45-10:00)
              ↓                           (09:45-10:00)           + WebSocket
                                                                  (10:00-10:00:23)
              
10:05:00      Trading Window          ✅ WebSocket            ✅ WebSocket
              OPENS                       (live ticks)            (live ticks)
              ↓
              Monitor for Entry       ✅ WebSocket            ✅ WebSocket
              ↓                           (live ticks)            (live ticks)
              
15:15:00      Hard Exit Time          ✅ WebSocket            ✅ WebSocket
                                          (live ticks)            (live ticks)
              
15:30:00      Market Closes           ✅ WebSocket STOP       ✅ WebSocket STOP
─────────────────────────────────────────────────────────────────────────────
```

---

## Data Source Breakdown

### Nifty Spot (NIFTY 50 Index)

```
┌─────────────────────────────────────────────────────────────┐
│  NIFTY DATA COLLECTION                                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  09:15 ──────────────────────────────────────────── 15:30  │
│    │                                                   │    │
│    └──────────── WebSocket (Live Ticks) ─────────────┘    │
│                                                             │
│  All data stored in: candle_aggregator                     │
│  Reference window (09:45-10:00): ✅ Complete               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Option Strikes (Call & Put)

```
┌─────────────────────────────────────────────────────────────┐
│  OPTION DATA COLLECTION                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  09:15 ────────────── 10:00 ──────────────────────── 15:30 │
│    │                    │                              │    │
│    │                    │                              │    │
│    └─ Not Subscribed ──┤                              │    │
│                         │                              │    │
│                         ├─ Historical API (09:45-10:00)    │
│                         │  (Backfill missing data)     │    │
│                         │                              │    │
│                         └──── WebSocket (Live) ────────┘    │
│                                                             │
│  Reference window (09:45-10:00): ✅ Complete (via API)     │
│  Trading window (10:00-15:30): ✅ Complete (via WebSocket) │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Code Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                         BOT STARTUP                              │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│  1. Get Nifty Token                                              │
│     nifty_token = instrument_manager.get_nifty_token()           │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│  2. Subscribe to Nifty (IMMEDIATE)                               │
│     broker_api.start_websocket([nifty_token], on_tick)           │
│     ✅ Nifty ticks flowing into candle_aggregator                │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│  3. Trading Loop Starts                                          │
│     while running:                                               │
│         - Collect Nifty ticks (09:15 onwards)                    │
│         - Build 1-min candles in candle_aggregator               │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│  4. At 10:00 AM - Calculate Reference Levels (Preliminary)       │
│     nifty_df = candle_aggregator.get_candles(09:45-10:00)       │
│     reference_calculator.calculate(nifty_df, nifty_df, nifty_df) │
│     ⚠️  Using Nifty data for all three (temporary)               │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│  5. At 10:00 AM - Select Strikes                                 │
│     call_inst, put_inst = strike_selector.select_strikes(spot)   │
│     call_token = call_inst['token']                              │
│     put_token = put_inst['token']                                │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│  6. Subscribe to Options (for FUTURE ticks)                      │
│     broker_api.kws.subscribe([call_token, put_token])            │
│     ✅ Option ticks flowing (from 10:00:XX onwards)              │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│  7. Fetch Historical Data (BACKFILL 09:45-10:00)                 │
│     call_df = broker_api.get_historical_data(                    │
│         token=call_token,                                        │
│         from_datetime=09:45:00,                                  │
│         to_datetime=current_time  # e.g., 10:00:23               │
│     )                                                            │
│     put_df = broker_api.get_historical_data(...)                 │
│     ✅ Historical data fills the gap (09:45-10:00)               │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│  8. Recalculate Reference Levels (FINAL)                         │
│     nifty_df = candle_aggregator.get_candles(09:45-10:00)       │
│     call_ref = call_df[09:45-10:00]  # Filter historical data   │
│     put_ref = put_df[09:45-10:00]    # Filter historical data   │
│     reference_calculator.calculate(nifty_df, call_ref, put_ref)  │
│     ✅ Accurate reference levels with ALL three instruments      │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│  9. Trading Window Opens (10:00+)                                │
│     - Monitor for entry signals                                  │
│     - All three instruments streaming live via WebSocket         │
│     - Reference levels are accurate and complete                 │
└──────────────────────────────────────────────────────────────────┘
```

---

## Data Completeness Check

### Reference Window (09:45-10:00) - 15 minutes

| Instrument | Data Source | Candles Expected | Status |
|------------|-------------|------------------|--------|
| Nifty Spot | WebSocket (live) | 15 x 1-min | ✅ Complete |
| Call Option | Historical API | 15 x 1-min | ✅ Complete |
| Put Option | Historical API | 15 x 1-min | ✅ Complete |

**Result:** All three instruments have complete data for reference calculation

### Trading Window (10:00-15:30) - 5.5 hours

| Instrument | Data Source | Status |
|------------|-------------|--------|
| Nifty Spot | WebSocket (live) | ✅ Streaming |
| Call Option | WebSocket (live) | ✅ Streaming |
| Put Option | WebSocket (live) | ✅ Streaming |

**Result:** All three instruments streaming live for entry/exit signals

---

## Key Insights

### 1. **No Data Loss for Nifty**
- Subscribed from bot startup (before or at market open)
- All ticks from 09:15 onwards captured
- Reference window (09:45-10:00) has complete live data

### 2. **No Data Loss for Options**
- Historical API backfills 09:45-10:00 window
- WebSocket provides live data from 10:00 onwards
- Combined approach ensures complete coverage

### 3. **Two-Phase Reference Calculation**
- **Phase 1 (10:00:00):** Preliminary calculation with Nifty data only
- **Phase 2 (10:00:23):** Final calculation with all three instruments
- Ensures accurate reference levels before trading starts

### 4. **Trading Doesn't Start Immediately**
- Earliest entry: 10:05 AM (after first candle post-10:00)
- Realistic entry: 10:10 AM (after two-candle confirmation)
- Plenty of time for data collection and processing

---

## Potential Edge Cases

### Edge Case 1: Historical API Fails
**Scenario:** Historical API returns empty data or errors

**Current Handling:**
```python
if not call_df.empty and not put_df.empty:
    # Calculate with historical data
else:
    logger.warning("Could not fetch complete historical option data")
    # Falls back to preliminary calculation (Nifty-only)
```

**Impact:** 
- Reference levels might be less accurate (using Nifty instead of options)
- Trading can still proceed, but with caution
- Should add alert/notification for this scenario

**Recommendation:** Add retry logic for historical API

### Edge Case 2: WebSocket Disconnects
**Scenario:** WebSocket connection drops during market hours

**Current Handling:**
- KiteConnect has auto-reconnect
- Candle aggregator continues with available data
- Might miss some ticks during reconnection

**Impact:**
- Candles might have gaps
- Entry/exit signals might be delayed
- Should monitor connection status

**Recommendation:** Add connection health monitoring

### Edge Case 3: Strike Selection Delayed
**Scenario:** Strike selection takes longer than expected (e.g., 10:01 instead of 10:00)

**Current Handling:**
```python
# fetch_end_time = current_time (not fixed 10:00)
call_df = broker_api.get_historical_data(
    from_datetime=start_time,      # 09:45
    to_datetime=fetch_end_time,    # Current time (e.g., 10:01:15)
    interval='1minute'
)
```

**Impact:**
- Historical API fetches extra data (09:45-10:01)
- Filtered to exact 09:45-10:00 window anyway
- No data loss, just slightly more API usage

**Recommendation:** Current handling is robust

---

## Verification Checklist

When bot runs in live market, verify:

- [ ] Nifty subscription happens before 09:45
- [ ] Nifty candles accumulate from 09:15 onwards
- [ ] Strike selection completes around 10:00
- [ ] Historical API call succeeds for both Call and Put
- [ ] Historical data contains 15 candles (09:45-09:59)
- [ ] Reference levels recalculated with option data
- [ ] WebSocket continues streaming after 10:00
- [ ] Trading signals start appearing after 10:05

**Log Messages to Look For:**
```
✅ "Subscribing to Nifty spot for real-time data..."
✅ "WebSocket started - receiving Nifty ticks"
✅ "Selecting strikes at 10:00..."
✅ "Fetching historical option data from 09:45 to 10:00:XX..."
✅ "Reference levels recalculated with historical option data"
✅ "Call: 15 candles, Put: 15 candles"
```

---

## Conclusion

**Your concern about data loss is completely valid and shows good system thinking!**

However, the codebase already implements a robust solution:

1. ✅ **Nifty data:** Collected from 09:15 via WebSocket
2. ✅ **Option data:** Backfilled from 09:45 via Historical API
3. ✅ **Reference levels:** Calculated with complete data
4. ✅ **Trading:** Begins with accurate reference levels

**No code changes needed** - the architecture handles this correctly!

The only potential improvement would be adding:
- Retry logic for historical API failures
- Connection health monitoring
- Alerts for data quality issues

But the core data collection flow is solid. 🎯