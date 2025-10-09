# Kite LTP Format Changes

## Summary
Updated the codebase to use Kite's correct LTP format with trading symbols instead of tokens.

## Changes Made

### 1. **data/instruments.py**
- Added `get_trading_symbol(token)` method to convert tokens to trading symbols
- Returns format: `"NSE:NIFTY 50"` for spot index, `"NFO:NIFTY25O0725000CE"` for options
- Automatically determines exchange (NSE/NFO) based on option_type

### 2. **data/broker_api.py**
- Updated `get_ltp(token)` method to use trading symbols instead of tokens
- Updated `get_quote(token)` method to use trading symbols instead of tokens
- Now calls `instrument_manager.get_trading_symbol(token)` to get the correct format
- Maintains backward compatibility with WebSocket tick data

### 3. **get_ltp.py**
- Updated `get_ltp()` function to build trading symbols from instruments.csv
- Now correctly formats as `"EXCHANGE:SYMBOL"` instead of `"EXCHANGE:TOKEN"`

## How It Works

### Before (Incorrect):
```python
# Using token directly
instrument_key = f"NSE:{token}"  # e.g., "NSE:256265"
ltp_data = kite.ltp([instrument_key])
```

### After (Correct):
```python
# Using trading symbol
trading_symbol = instrument_manager.get_trading_symbol(token)  # e.g., "NSE:NIFTY 50"
ltp_data = kite.ltp([trading_symbol])
```

## Examples

### Spot Nifty:
- **Token**: 256265
- **Trading Symbol**: `"NSE:NIFTY 50"`

### Call Option:
- **Token**: 9827074
- **Trading Symbol**: `"NFO:NIFTY25O0725000CE"`

### Put Option:
- **Token**: 9827586
- **Trading Symbol**: `"NFO:NIFTY25O0725000PE"`

## Nearest Weekly Expiry

The system already handles nearest weekly expiry selection:
- `instrument_manager.get_nearest_weekly_expiry()` finds the closest expiry date
- `strike_selector.select_strikes()` uses this expiry when selecting strikes
- Options are automatically selected from the nearest weekly expiry

## Late Start Handling (After 10 AM)

The system already handles late starts properly:

### In `main.py`:
```python
# Step 1: Calculate reference levels
if not self.reference_levels_set:
    if current_time.time() >= dt_time(10, 0):
        # Started after 10 AM - fetch historical data
        self._calculate_reference_levels_from_historical()
    elif is_between_times('10:00', '10:01'):
        # Normal flow - use aggregated candles
        self._calculate_reference_levels_from_candles()

# Step 2: Select strikes at 10:00
if self.reference_levels_set and not self.strikes_selected:
    if current_time.time() >= dt_time(10, 0):
        self._select_strikes()
```

### What Happens:
1. **Before 9:15 AM**: Bot waits for market to open
2. **9:15-10:00 AM**: Collects real-time ticks and builds candles
3. **At 10:00 AM**: Calculates reference levels and selects strikes
4. **After 10:00 AM (Late Start)**: 
   - Immediately fetches historical data from 9:45-10:00
   - Calculates reference levels from historical data
   - Selects strikes immediately
   - Starts monitoring for entry signals

## Testing

To test the changes:

```bash
# Test LTP fetching
python get_ltp.py

# Test with specific strike
python get_ltp.py --strike 25000 --type CE

# Run the main bot (will handle late starts automatically)
python main.py
```

## Notes

- All changes maintain backward compatibility
- WebSocket tick data is still prioritized (faster)
- REST API calls now use correct trading symbol format
- No changes needed to instruments.csv format
- The system automatically handles all timing scenarios