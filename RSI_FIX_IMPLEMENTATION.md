# RSI Fix - Implementation Guide

## Quick Fix: Use 1-Minute Candles (5 minutes)

### The Problem
- RSI(14) needs 15 candles minimum
- With 5-minute candles: 15 × 5 = 75 minutes
- Strike selected at 10:00 AM → RSI not available until 11:15 AM ❌

### The Solution
- Use 1-minute candles instead
- With 1-minute candles: 15 × 1 = 15 minutes
- Strike selected at 10:00 AM → RSI available at 10:15 AM ✅

---

## Implementation Steps

### Step 1: Modify main.py (1 line change)

**File:** `/Users/himanshu/nifty-options-bot/main.py`  
**Line:** 422

**OLD CODE:**
```python
# Get recent candles for RSI
recent_df = candle_aggregator.get_candles(token, '5min', count=20)
if len(recent_df) >= 15:
    rsi = get_latest_rsi(recent_df, 'close', 14)
```

**NEW CODE:**
```python
# Get recent candles for RSI (using 1-min for faster availability)
recent_df = candle_aggregator.get_candles(token, '1min', count=20)
if len(recent_df) >= 15:
    rsi = get_latest_rsi(recent_df, 'close', 14)
```

**Change:** `'5min'` → `'1min'`

---

### Step 2: Adjust RSI Exit Threshold (optional but recommended)

**File:** `/Users/himanshu/nifty-options-bot/.env`

**OLD:**
```bash
RSI_EXIT_DROP=10
```

**NEW:**
```bash
# Increased threshold for 1-min candles (more noise)
RSI_EXIT_DROP=15
```

**Reason:** 1-minute candles have more noise, so RSI fluctuates more. Increasing the threshold from 10 to 15 prevents premature exits.

---

### Step 3: Add Logging for Monitoring

**File:** `/Users/himanshu/nifty-options-bot/main.py`  
**Location:** Around line 422-428

**ENHANCED CODE:**
```python
# Get recent candles for RSI (using 1-min for faster availability)
recent_df = candle_aggregator.get_candles(token, '1min', count=20)

if len(recent_df) >= 15:
    rsi = get_latest_rsi(recent_df, 'close', 14)
    if rsi:
        logger.debug(f"RSI calculated: {rsi:.2f} (using {len(recent_df)} 1-min candles)")
        self.rsi_peak = track_rsi_peak(rsi, self.rsi_peak)
        
        if check_rsi_exit_condition(rsi, self.rsi_peak, settings.RSI_EXIT_DROP):
            logger.info(f"RSI exit triggered: RSI={rsi:.2f}, Peak={self.rsi_peak:.2f}, Drop={self.rsi_peak - rsi:.2f}")
            current_price = self._get_current_option_price()
            if current_price:
                self._exit_trade(current_price, 'RSI_EXIT')
else:
    logger.debug(f"RSI not available yet: {len(recent_df)}/15 candles (1-min)")
```

---

## Complete Code Changes

### File: main.py

```python
def _manage_position_from_candle(self, candle: Dict):
    """Manage position from completed candle"""
    try:
        if not self.in_position:
            return
        
        current_price = candle['close']
        current_low = candle['low']
        
        # Check stop loss hit
        if stop_loss_manager.check_stop_loss_hit(current_low):
            sl = stop_loss_manager.get_current_sl()
            self._exit_trade(sl, 'SL_HIT')
            return
        
        # Check RSI exit
        call_inst, put_inst = strike_selector.get_instruments()
        token = self.call_token if self.current_side == 'CALL' else self.put_token
        
        # Get recent candles for RSI (using 1-min for faster availability)
        recent_df = candle_aggregator.get_candles(token, '1min', count=20)
        
        if len(recent_df) >= 15:
            rsi = get_latest_rsi(recent_df, 'close', 14)
            if rsi:
                logger.debug(f"RSI: {rsi:.2f} (Peak: {self.rsi_peak:.2f if self.rsi_peak else 'N/A'}, Candles: {len(recent_df)})")
                self.rsi_peak = track_rsi_peak(rsi, self.rsi_peak)
                
                if check_rsi_exit_condition(rsi, self.rsi_peak, settings.RSI_EXIT_DROP):
                    logger.info(f"🔔 RSI exit triggered: RSI={rsi:.2f}, Peak={self.rsi_peak:.2f}, Drop={self.rsi_peak - rsi:.2f}")
                    current_price = self._get_current_option_price()
                    if current_price:
                        self._exit_trade(current_price, 'RSI_EXIT')
        else:
            logger.debug(f"RSI not available yet: {len(recent_df)}/15 1-min candles")
    
    except Exception as e:
        logger.error(f"Error managing position: {e}", exc_info=True)
```

---

## Testing Checklist

### Before Deployment

- [ ] Code changes applied correctly
- [ ] No syntax errors (`python -m py_compile main.py`)
- [ ] RSI_EXIT_DROP updated in .env
- [ ] Logging statements added

### During Paper Trading

- [ ] Bot starts without errors
- [ ] Strikes selected at 10:00 AM
- [ ] Log shows "RSI not available yet" before 10:15 AM
- [ ] Log shows "RSI calculated" after 10:15 AM
- [ ] RSI values are in 0-100 range
- [ ] RSI exit triggers when conditions met
- [ ] No crashes or exceptions

### Monitoring

Watch for these log messages:
```
✅ "RSI calculated: 65.23 (using 18 1-min candles)"
✅ "RSI exit triggered: RSI=55.12, Peak=68.45, Drop=13.33"
⚠️  "RSI not available yet: 12/15 1-min candles"
```

---

## Expected Timeline

### Trading Day Timeline with 1-Min RSI

```
09:15 AM ─── Market opens, bot starts
             Nifty WebSocket subscribed
             
09:45 AM ─── Reference window starts
             
10:00 AM ─── Reference levels calculated
             Strikes selected
             Options WebSocket subscribed
             
10:01 AM ─── 1 x 1-min candle (RSI: ❌ not available)
10:05 AM ─── 5 x 1-min candles (RSI: ❌ not available)
10:10 AM ─── 10 x 1-min candles (RSI: ❌ not available)

10:15 AM ─── 15 x 1-min candles (RSI: ✅ AVAILABLE!)
             First possible RSI exit
             
10:20 AM ─── 20 x 1-min candles (RSI: ✅ stable)
             
10:30 AM ─── 30 x 1-min candles (RSI: ✅ very stable)
             
...rest of trading day with RSI available
```

---

## Rollback Plan

If 1-minute RSI causes issues (too many false exits):

### Option A: Revert to 5-minute candles
```python
# main.py line 422
recent_df = candle_aggregator.get_candles(token, '5min', count=20)
```

### Option B: Disable RSI exit temporarily
```python
# main.py - comment out RSI exit logic
# if check_rsi_exit_condition(rsi, self.rsi_peak, settings.RSI_EXIT_DROP):
#     self._exit_trade(current_price, 'RSI_EXIT')
```

### Option C: Increase threshold further
```bash
# .env
RSI_EXIT_DROP=20  # Even more conservative
```

---

## Performance Comparison

### Before Fix (5-min candles)

| Metric | Value |
|--------|-------|
| RSI Available At | 11:15 AM |
| Time Without RSI | 75 minutes |
| Exits Available | SL, Target only |
| Risk | Higher (no RSI exit) |

### After Fix (1-min candles)

| Metric | Value |
|--------|-------|
| RSI Available At | 10:15 AM |
| Time Without RSI | 15 minutes |
| Exits Available | SL, Target, RSI |
| Risk | Lower (all exits active) |

**Improvement:** RSI available **60 minutes earlier** ✅

---

## Advanced: Hybrid Implementation (Optional)

If you want the best of both worlds (1-min early, 5-min later):

### Code for Hybrid Approach

```python
def _manage_position_from_candle(self, candle: Dict):
    """Manage position from completed candle"""
    try:
        if not self.in_position:
            return
        
        current_price = candle['close']
        current_low = candle['low']
        
        # Check stop loss hit
        if stop_loss_manager.check_stop_loss_hit(current_low):
            sl = stop_loss_manager.get_current_sl()
            self._exit_trade(sl, 'SL_HIT')
            return
        
        # Check RSI exit with hybrid approach
        token = self.call_token if self.current_side == 'CALL' else self.put_token
        current_time = get_current_time()
        
        # Determine time since strike selection
        strike_time = datetime.combine(current_time.date(), dt_time(10, 0))
        minutes_since_strike = (current_time - strike_time).total_seconds() / 60
        
        # Use 1-min candles for first 30 minutes, then switch to 5-min
        if minutes_since_strike < 30:
            interval = '1min'
            min_candles = 15
        else:
            interval = '5min'
            min_candles = 15
        
        # Get recent candles
        recent_df = candle_aggregator.get_candles(token, interval, count=20)
        
        if len(recent_df) >= min_candles:
            rsi = get_latest_rsi(recent_df, 'close', 14)
            if rsi:
                logger.debug(f"RSI: {rsi:.2f} ({interval}, {len(recent_df)} candles)")
                self.rsi_peak = track_rsi_peak(rsi, self.rsi_peak)
                
                if check_rsi_exit_condition(rsi, self.rsi_peak, settings.RSI_EXIT_DROP):
                    logger.info(f"🔔 RSI exit: RSI={rsi:.2f}, Peak={self.rsi_peak:.2f}")
                    current_price = self._get_current_option_price()
                    if current_price:
                        self._exit_trade(current_price, 'RSI_EXIT')
        else:
            logger.debug(f"RSI not ready: {len(recent_df)}/{min_candles} {interval} candles")
    
    except Exception as e:
        logger.error(f"Error managing position: {e}", exc_info=True)
```

---

## Summary

### What Changed
1. ✅ RSI now uses 1-minute candles instead of 5-minute
2. ✅ RSI available at 10:15 AM instead of 11:15 AM
3. ✅ RSI_EXIT_DROP increased from 10 to 15 (optional)
4. ✅ Added logging for monitoring

### What to Watch
- ⚠️ Monitor for false RSI exits (too frequent)
- ⚠️ Check RSI values are reasonable (0-100)
- ⚠️ Verify RSI exit improves performance

### Next Steps
1. Apply the code changes
2. Test in paper trading
3. Monitor for 2-3 trading days
4. Adjust RSI_EXIT_DROP if needed
5. Consider hybrid approach for production

---

**Status:** ✅ **READY TO IMPLEMENT**  
**Time Required:** 5-10 minutes  
**Risk Level:** 🟡 Low (easily reversible)  
**Expected Benefit:** RSI exit available 60 minutes earlier