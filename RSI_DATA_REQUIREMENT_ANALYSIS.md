# RSI Calculation Data Requirement Analysis

## The Problem

**Your Concern:** RSI(14) requires at least 70 minutes of historical data to calculate accurately, but:
1. Option strikes are selected at 10:00 AM
2. Strikes change daily based on Nifty spot price
3. Can't use historical data because yesterday's strikes are different from today's

**Status:** ⚠️ **CRITICAL ISSUE** - Current implementation will fail!

---

## RSI Calculation Requirements

### Mathematical Requirements

**RSI(14) Formula:**
```
RSI = 100 - (100 / (1 + RS))
where RS = Average Gain / Average Loss over 14 periods
```

**Data Requirements:**
- **Minimum:** 14 periods + 1 (for first diff) = **15 candles**
- **Recommended:** 14 periods + warmup = **20-30 candles** for stable RSI
- **Ideal:** 50+ candles for accurate EMA smoothing

### Time Requirements (5-minute candles)

| Candles Needed | Time Required | Available After Strike Selection (10:00 AM) |
|----------------|---------------|---------------------------------------------|
| 15 candles | 75 minutes | ❌ Not until 11:15 AM |
| 20 candles | 100 minutes | ❌ Not until 11:40 AM |
| 30 candles | 150 minutes | ❌ Not until 12:30 PM |

**Problem:** First possible entry is 10:05-10:10 AM, but RSI won't be available until 11:15 AM at earliest!

---

## Current Code Analysis

### Where RSI is Used

**File: `main.py` (line 422-428)**
```python
# Get recent candles for RSI
recent_df = candle_aggregator.get_candles(token, '5min', count=20)
if len(recent_df) >= 15:
    rsi = get_latest_rsi(recent_df, 'close', 14)
    if rsi:
        self.rsi_peak = track_rsi_peak(rsi, self.rsi_peak)
        if check_rsi_exit_condition(rsi, self.rsi_peak, settings.RSI_EXIT_DROP):
            self._exit_trade(current_price, 'RSI_EXIT')
```

**Current Logic:**
- Requires 15 candles minimum
- Uses 5-minute candles
- Only used for **exit** (not entry)

**Problem:**
- At 10:05 AM: 1 candle available (10:00-10:05) ❌
- At 10:10 AM: 2 candles available ❌
- At 11:15 AM: 15 candles available ✅ (first time RSI can be calculated)

---

## Solution Options

### Option 1: Use 1-Minute Candles for RSI ✅ **RECOMMENDED**

**Approach:** Calculate RSI on 1-minute candles instead of 5-minute

**Advantages:**
- ✅ 15 candles = 15 minutes (available at 10:15 AM)
- ✅ 20 candles = 20 minutes (available at 10:20 AM)
- ✅ More responsive to price changes
- ✅ Can start using RSI much earlier

**Disadvantages:**
- ⚠️ More noise in RSI signal
- ⚠️ Might give false exit signals

**Implementation:**
```python
# Change from 5-minute to 1-minute candles
recent_df = candle_aggregator.get_candles(token, '1min', count=20)
if len(recent_df) >= 15:
    rsi = get_latest_rsi(recent_df, 'close', 14)
```

**Timeline:**
- 10:00 AM: Strike selected, WebSocket subscribed
- 10:15 AM: 15 x 1-min candles available → RSI ready ✅
- 10:20 AM: 20 x 1-min candles available → Stable RSI ✅

---

### Option 2: Fetch Historical Data + Live Data ⚠️ **COMPLEX**

**Approach:** Combine historical data (9:45-10:00) with live data (10:00+)

**Advantages:**
- ✅ RSI available immediately after strike selection
- ✅ Uses 5-minute candles (less noise)

**Disadvantages:**
- ❌ Historical data only has 3 candles (9:45, 9:50, 9:55)
- ❌ Still need 12 more candles = 60 minutes
- ❌ Not available until 11:00 AM
- ⚠️ Mixing historical + live data can cause inconsistencies

**Implementation:**
```python
# Fetch historical 5-min candles (9:45-10:00)
hist_df = broker_api.get_historical_data(
    token=self.call_token,
    from_datetime=datetime.combine(current_date, dt_time(9, 45)),
    to_datetime=datetime.combine(current_date, dt_time(10, 0)),
    interval='5minute'  # Only 3 candles!
)

# Get live 5-min candles (10:00+)
live_df = candle_aggregator.get_candles(token, '5min')

# Combine
combined_df = pd.concat([hist_df, live_df])

# Calculate RSI
if len(combined_df) >= 15:
    rsi = get_latest_rsi(combined_df, 'close', 14)
```

**Timeline:**
- 10:00 AM: 3 historical candles (9:45-10:00)
- 11:00 AM: 3 historical + 12 live = 15 candles → RSI ready ✅

---

### Option 3: Disable RSI Exit Until Sufficient Data ⚠️ **PARTIAL SOLUTION**

**Approach:** Only use RSI exit after 11:15 AM, rely on other exits before that

**Advantages:**
- ✅ Simple to implement
- ✅ No code changes to RSI calculation
- ✅ Other exits (SL, target, hard exit) still work

**Disadvantages:**
- ❌ No RSI exit for first 1+ hour of trading
- ❌ Might miss good exit opportunities
- ⚠️ Inconsistent exit strategy

**Implementation:**
```python
# Check if enough candles available
recent_df = candle_aggregator.get_candles(token, '5min', count=20)
if len(recent_df) >= 15:
    # RSI exit available
    rsi = get_latest_rsi(recent_df, 'close', 14)
    # ... rest of logic
else:
    # RSI not available yet, skip RSI exit
    logger.debug(f"RSI not available yet ({len(recent_df)}/15 candles)")
```

**Timeline:**
- 10:05-11:15 AM: Only SL and target exits
- 11:15+ AM: RSI exit also available

---

### Option 4: Use Nifty RSI as Proxy ⚠️ **NOT RECOMMENDED**

**Approach:** Calculate RSI on Nifty spot (which has data from 9:15) and use as proxy for option RSI

**Advantages:**
- ✅ Nifty data available from 9:15 AM
- ✅ RSI available immediately

**Disadvantages:**
- ❌ Nifty RSI ≠ Option RSI (different price movements)
- ❌ Options have leverage and decay
- ❌ Misleading signals
- ❌ Not accurate for option exits

**Not recommended** - Option price behavior is too different from Nifty

---

### Option 5: Reduce RSI Period ⚠️ **CHANGES STRATEGY**

**Approach:** Use RSI(7) instead of RSI(14)

**Advantages:**
- ✅ Only needs 8 candles = 40 minutes (5-min) or 8 minutes (1-min)
- ✅ Available much earlier

**Disadvantages:**
- ❌ Changes the trading strategy
- ❌ More sensitive to noise
- ❌ Might give premature exits
- ⚠️ Would need to re-backtest entire strategy

---

## Recommended Solution: Hybrid Approach

### Phase 1: Use 1-Minute Candles (10:00-10:30 AM)

```python
# For first 30 minutes after strike selection
if current_time < datetime.combine(current_date, dt_time(10, 30)):
    # Use 1-minute candles for faster RSI availability
    recent_df = candle_aggregator.get_candles(token, '1min', count=20)
    if len(recent_df) >= 15:
        rsi = get_latest_rsi(recent_df, 'close', 14)
```

**Available:** 10:15 AM (15 minutes after strike selection)

### Phase 2: Use 5-Minute Candles (10:30+ AM)

```python
# After 30 minutes, switch to 5-minute candles
else:
    # Use 5-minute candles for more stable RSI
    recent_df = candle_aggregator.get_candles(token, '5min', count=20)
    if len(recent_df) >= 15:
        rsi = get_latest_rsi(recent_df, 'close', 14)
```

**Available:** 11:15 AM (15 x 5-min candles)

### Fallback: Disable RSI if Insufficient Data

```python
if len(recent_df) < 15:
    logger.debug(f"RSI not available yet ({len(recent_df)}/15 candles)")
    # Skip RSI exit, rely on SL and target
    return
```

---

## Implementation Plan

### Step 1: Modify `_manage_position_from_candle()` in `main.py`

```python
def _manage_position_from_candle(self, candle: Dict):
    """Manage position from completed candle"""
    try:
        if not self.in_position:
            return
        
        # ... existing stop loss logic ...
        
        # Check RSI exit with hybrid approach
        token = self.call_token if self.current_side == 'CALL' else self.put_token
        current_time = get_current_time()
        strike_selection_time = datetime.combine(current_time.date(), dt_time(10, 0))
        
        # Determine which candle interval to use
        time_since_selection = (current_time - strike_selection_time).total_seconds() / 60
        
        if time_since_selection < 30:
            # Use 1-minute candles for first 30 minutes
            recent_df = candle_aggregator.get_candles(token, '1min', count=20)
            min_candles = 15
            logger.debug("Using 1-min candles for RSI (early trading)")
        else:
            # Use 5-minute candles after 30 minutes
            recent_df = candle_aggregator.get_candles(token, '5min', count=20)
            min_candles = 15
            logger.debug("Using 5-min candles for RSI (stable trading)")
        
        # Calculate RSI if enough data
        if len(recent_df) >= min_candles:
            rsi = get_latest_rsi(recent_df, 'close', 14)
            if rsi:
                self.rsi_peak = track_rsi_peak(rsi, self.rsi_peak)
                if check_rsi_exit_condition(rsi, self.rsi_peak, settings.RSI_EXIT_DROP):
                    current_price = self._get_current_option_price()
                    if current_price:
                        self._exit_trade(current_price, 'RSI_EXIT')
        else:
            logger.debug(f"RSI not available yet ({len(recent_df)}/{min_candles} candles)")
    
    except Exception as e:
        logger.error(f"Error managing position: {e}", exc_info=True)
```

### Step 2: Add Configuration

Add to `.env`:
```bash
# RSI Configuration
RSI_PERIOD=14
RSI_EARLY_INTERVAL=1min  # Use 1-min candles for first 30 minutes
RSI_STABLE_INTERVAL=5min  # Use 5-min candles after 30 minutes
RSI_SWITCH_TIME_MINUTES=30  # Switch from 1-min to 5-min after this many minutes
```

### Step 3: Update Documentation

Update `LIVE_TRADING_READY.md` to explain RSI availability timeline

---

## Timeline Comparison

### Current Implementation (5-min candles only)

| Time | Candles Available | RSI Status |
|------|-------------------|------------|
| 10:00 | 0 | ❌ Not available |
| 10:05 | 1 | ❌ Not available |
| 10:30 | 6 | ❌ Not available |
| 11:00 | 12 | ❌ Not available |
| 11:15 | 15 | ✅ **First available** |

**Problem:** No RSI exit for first 75 minutes!

### Recommended Hybrid Approach

| Time | Interval | Candles Available | RSI Status |
|------|----------|-------------------|------------|
| 10:00 | - | 0 | ❌ Not available |
| 10:05 | 1-min | 5 | ❌ Not available |
| 10:15 | 1-min | 15 | ✅ **Available (1-min)** |
| 10:30 | Switch | 30 (1-min) | ✅ Available (1-min) |
| 11:15 | 5-min | 15 (5-min) | ✅ **Available (5-min)** |

**Benefit:** RSI exit available from 10:15 AM (60 minutes earlier!)

---

## Testing Recommendations

### Test 1: RSI Availability
- Start bot at 9:15 AM
- Check logs at 10:15 AM for "RSI available" message
- Verify RSI values are reasonable (0-100 range)

### Test 2: Interval Switching
- Verify 1-min candles used before 10:30 AM
- Verify 5-min candles used after 10:30 AM
- Check for smooth transition

### Test 3: Insufficient Data Handling
- Verify no crashes when RSI data insufficient
- Verify other exits (SL, target) still work

### Test 4: RSI Exit Trigger
- Simulate RSI drop scenario
- Verify exit triggered correctly
- Check exit price and reason logged

---

## Alternative: Simplest Solution (If Time-Constrained)

**Just use 1-minute candles for all RSI calculations:**

```python
# Simple change in main.py line 422
recent_df = candle_aggregator.get_candles(token, '1min', count=20)  # Changed from '5min'
```

**Pros:**
- ✅ One-line change
- ✅ RSI available at 10:15 AM
- ✅ Works throughout the day

**Cons:**
- ⚠️ More noise in RSI
- ⚠️ Might need to adjust RSI_EXIT_DROP threshold

---

## Conclusion

**Critical Issue Identified:** Current implementation cannot calculate RSI until 11:15 AM, making RSI exit unavailable for first 75 minutes of trading.

**Recommended Solution:** 
1. **Short-term:** Use 1-minute candles for RSI (one-line change)
2. **Long-term:** Implement hybrid approach (1-min early, 5-min later)

**Action Required:** Choose solution and implement before live trading!

**Risk if Not Fixed:** 
- RSI exit will never trigger in first hour
- Might hold losing positions longer than intended
- Strategy performance will differ from backtest

---

**Status:** ⚠️ **REQUIRES IMMEDIATE ATTENTION**  
**Priority:** 🔴 **HIGH** - Affects core exit strategy  
**Estimated Fix Time:** 30 minutes (simple) to 2 hours (hybrid)