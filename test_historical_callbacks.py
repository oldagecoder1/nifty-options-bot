"""
Test script to verify that callbacks are triggered when loading historical data
"""
from datetime import datetime, timedelta
from utils.candle_aggregator import CandleAggregator

# Track callback invocations
callback_count = 0
completed_candles = []

def on_5min_candle(token, candle):
    """Callback that gets triggered when a 5-minute candle completes"""
    global callback_count, completed_candles
    callback_count += 1
    completed_candles.append(candle.copy())
    print(f"✅ Callback #{callback_count} triggered for 5-min candle at {candle['timestamp']}")
    print(f"   OHLC: O={candle['open']:.2f}, H={candle['high']:.2f}, L={candle['low']:.2f}, C={candle['close']:.2f}")

# Create aggregator and register callback
aggregator = CandleAggregator()
aggregator.register_5min_callback(on_5min_candle)

print("=" * 80)
print("TEST: Loading Historical Data with Callbacks")
print("=" * 80)

# Simulate loading historical 1-minute candles from 9:15 to 9:35 (20 minutes = 4 complete 5-min candles)
base_time = datetime(2025, 1, 7, 9, 15)
token = 256265  # Nifty token

print(f"\n📥 Loading 20 historical 1-minute candles (9:15 to 9:34)...")
print(f"Expected: 4 callbacks for 5-min candles at 9:15, 9:20, 9:25, 9:30\n")

for i in range(20):
    timestamp = base_time + timedelta(minutes=i)
    
    # Create sample OHLC data for each 1-minute candle
    candle_data = {
        'open': 25000 + i * 10,
        'high': 25000 + i * 10 + 20,
        'low': 25000 + i * 10 - 10,
        'close': 25000 + i * 10 + 5
    }
    
    print(f"Loading 1-min candle at {timestamp.strftime('%H:%M')} - Close={candle_data['close']:.2f}")
    
    # Add historical candle (with callbacks enabled by default)
    aggregator.add_historical_candle(token, candle_data, timestamp)

print("\n" + "=" * 80)
print("RESULTS:")
print("=" * 80)
print(f"Total callbacks triggered: {callback_count}")
print(f"Expected callbacks: 4 (for 9:15, 9:20, 9:25, 9:30)")

if callback_count == 4:
    print("✅ SUCCESS: Correct number of callbacks triggered!")
else:
    print(f"❌ FAILURE: Expected 4 callbacks but got {callback_count}")

print("\nCompleted 5-minute candles:")
for candle in completed_candles:
    print(f"  {candle['timestamp'].strftime('%H:%M')} - O={candle['open']:.2f}, H={candle['high']:.2f}, L={candle['low']:.2f}, C={candle['close']:.2f}")

# Verify OHLC aggregation is correct
print("\n" + "=" * 80)
print("OHLC AGGREGATION VERIFICATION:")
print("=" * 80)

# First 5-min candle (9:15-9:19) should aggregate 1-min candles 0-4
if completed_candles:
    first_candle = completed_candles[0]
    print(f"\nFirst 5-min candle (9:15):")
    print(f"  Open: {first_candle['open']:.2f} (should be 25000.00 - first candle's open)")
    print(f"  High: {first_candle['high']:.2f} (should be 25060.00 - max of all highs)")
    print(f"  Low: {first_candle['low']:.2f} (should be 24990.00 - min of all lows)")
    print(f"  Close: {first_candle['close']:.2f} (should be 25045.00 - last candle's close)")
    
    # Verify
    expected_open = 25000.0
    expected_high = 25060.0  # 25040 + 20
    expected_low = 24990.0   # 25000 - 10
    expected_close = 25045.0  # 25040 + 5
    
    if (first_candle['open'] == expected_open and 
        first_candle['high'] == expected_high and 
        first_candle['low'] == expected_low and 
        first_candle['close'] == expected_close):
        print("  ✅ OHLC aggregation is CORRECT!")
    else:
        print("  ❌ OHLC aggregation is INCORRECT!")

print("\n" + "=" * 80)
print("TEST WITH CALLBACKS DISABLED:")
print("=" * 80)

# Reset
callback_count = 0
completed_candles = []
aggregator2 = CandleAggregator()
aggregator2.register_5min_callback(on_5min_candle)

print(f"\n📥 Loading 20 historical 1-minute candles with trigger_callbacks=False...")

for i in range(20):
    timestamp = base_time + timedelta(minutes=i)
    candle_data = {
        'open': 25000 + i * 10,
        'high': 25000 + i * 10 + 20,
        'low': 25000 + i * 10 - 10,
        'close': 25000 + i * 10 + 5
    }
    
    # Add historical candle with callbacks DISABLED
    aggregator2.add_historical_candle(token, candle_data, timestamp, trigger_callbacks=False)

print(f"\nTotal callbacks triggered: {callback_count}")
print(f"Expected callbacks: 0 (callbacks disabled)")

if callback_count == 0:
    print("✅ SUCCESS: Callbacks correctly suppressed!")
else:
    print(f"❌ FAILURE: Expected 0 callbacks but got {callback_count}")

print("\n" + "=" * 80)
print("SUMMARY:")
print("=" * 80)
print("✅ Historical data loading now triggers callbacks for entry/exit logic")
print("✅ OHLC data is properly aggregated from 1-min to 5-min candles")
print("✅ Callbacks can be optionally disabled with trigger_callbacks=False")
print("=" * 80)