# Timing Changes Summary

## Overview
Updated the trading bot timing configuration to align with the new strategy requirements.

## Changes Made

### 1. Reference Window Timing
**OLD:** 10:00 AM - 10:15 AM  
**NEW:** 09:45 AM - 10:00 AM

The bot now calculates reference levels (RN, GN, BN) from the 15-minute window between 09:45 and 10:00.

### 2. Strike Selection Time
**OLD:** 10:15 AM  
**NEW:** 10:00 AM

Strike selection now happens immediately after reference levels are calculated at 10:00 AM.

### 3. Trading Start Time
**OLD:** 10:15 AM  
**NEW:** 10:00 AM

The bot can now start looking for entry signals from 10:00 AM onwards (after strike selection is complete).

## Files Modified

### Configuration Files
1. **`.env`**
   - `REFERENCE_WINDOW_START`: Changed from `10:00` to `09:45`
   - `REFERENCE_WINDOW_END`: Changed from `10:15` to `10:00`
   - `STRIKE_SELECTION_TIME`: Changed from `10:15` to `10:00`

### Strategy Files
2. **`strategy/reference_levels.py`**
   - Updated docstrings to reflect 09:45-10:00 window
   - Updated function documentation

3. **`strategy/breakout_logic.py`**
   - Changed `_trade_start_time` from `time(10, 15)` to `time(10, 0)`
   - Updated all comments and docstrings mentioning 10:15 to 10:00
   - Trading window now opens at 10:00 instead of 10:15

### Main Application
4. **`main.py`**
   - Updated reference level calculation trigger from `10:15-10:16` to `10:00-10:01`
   - Changed strike selection time check from `10:15` to `10:00`
   - Updated `_calculate_reference_levels_from_candles()` to use 09:45-10:00 window
   - Updated `_select_strikes()` docstring
   - Updated `_recalculate_with_option_data()` to fetch historical data from 09:45

## Timeline of Events (New)

### 09:15 AM - Market Opens
- Bot starts collecting tick data
- WebSocket connection established
- Candle aggregation begins

### 09:45 AM - Reference Window Starts
- Bot begins collecting data for reference level calculation
- Aggregates 1-minute candles for Nifty

### 10:00 AM - Reference Calculation & Strike Selection
- Reference levels calculated from 09:45-10:00 data
  - RN = High of 09:45-10:00 period
  - GN = Low of 09:45-10:00 period
  - BN = (RN + GN) / 2
- Strikes selected immediately:
  - CALL strike = Nifty spot + STRIKE_OFFSET
  - PUT strike = Nifty spot - STRIKE_OFFSET
- Historical option data fetched from 09:45-10:00
- Reference levels recalculated with actual option data
- Trading window opens

### 10:00+ AM - Trading Window
- Bot monitors Nifty 5-minute candles for entry signals
- Two-candle confirmation required:
  - **CALL:** Both candles close > RN, second > first
  - **PUT:** Both candles close < GN, second < first

### First Possible Entry
- **Earliest:** 10:05 AM (after first 5-min candle completes at 10:00)
- **More likely:** 10:10 AM (after two consecutive 5-min candles)

## Understanding Candle Timestamps

### How 5-Minute Candles Work

The candle aggregator uses the **start time** of each candle period as the timestamp:

- **10:00 candle** = Data from 10:00:00 to 10:04:59 (timestamp: 10:00)
- **10:05 candle** = Data from 10:05:00 to 10:09:59 (timestamp: 10:05)
- **10:10 candle** = Data from 10:10:00 to 10:14:59 (timestamp: 10:10)
- **10:15 candle** = Data from 10:15:00 to 10:19:59 (timestamp: 10:15)

### When Candles Complete

A candle is marked as "completed" when the first tick of the **next** period arrives:

- At 10:05:00, the 10:00 candle completes
- At 10:10:00, the 10:05 candle completes
- At 10:15:00, the 10:10 candle completes

### Entry Signal Example

**Scenario:** Checking for CALL entry at 10:15:00

When the bot receives the 10:10 candle (completed at 10:15:00):
- **Previous candle:** 10:05 (data from 10:05:00 to 10:09:59)
- **Current candle:** 10:10 (data from 10:10:00 to 10:14:59)

For CALL entry:
1. 10:05 candle close > RN ✓
2. 10:10 candle close > RN ✓
3. 10:10 close > 10:05 close ✓

If all conditions met → Enter CALL position

## Important Notes

### 1. Candle Timing is Correct
The existing candle aggregator already handles timestamps correctly. No changes were needed to the candle aggregation logic.

### 2. Reference Window
The 09:45-10:00 window gives us 15 minutes of data (three 5-minute candles) to establish reference levels before trading begins.

### 3. Strike Selection
Strikes are now selected at 10:00 AM sharp, giving the bot the full trading day to find entry opportunities.

### 4. First Entry Timing
- The earliest possible entry is at 10:05 AM (if the 10:00 candle meets criteria)
- More realistically, first entry will be at 10:10 AM or later (after two-candle confirmation)

### 5. Re-entry After Exit
After any exit (SL/target/manual), the bot requires price to move back to the opposite side of the breakout level on two consecutive candles before allowing re-entry.

## Testing Recommendations

1. **Verify Reference Calculation:**
   - Check logs at 10:00 AM to confirm reference levels are calculated
   - Verify RN, GN, BN values are based on 09:45-10:00 data

2. **Verify Strike Selection:**
   - Check logs at 10:00 AM to confirm strikes are selected
   - Verify option tokens are subscribed to WebSocket

3. **Verify Trading Window:**
   - Check logs show "Trading window opened (>= 10:00)"
   - Verify entry signals can be generated from 10:00 onwards

4. **Monitor First Entry:**
   - Watch for first entry signal (likely between 10:05-10:15)
   - Verify two-candle confirmation logic is working

## Rollback Instructions

If you need to revert to the old timing (10:00-10:15 reference window):

1. Edit `.env`:
   ```
   REFERENCE_WINDOW_START=10:00
   REFERENCE_WINDOW_END=10:15
   STRIKE_SELECTION_TIME=10:15
   ```

2. Restart the bot

The code will automatically use the new timing from environment variables.