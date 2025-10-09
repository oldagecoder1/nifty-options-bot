"""
Test script to verify data storage functionality
"""
from datetime import datetime
from utils.data_storage import data_storage
from utils.candle_aggregator import candle_aggregator
import time

def test_tick_storage():
    """Test saving ticks to CSV"""
    print("=" * 80)
    print("Testing Tick Storage")
    print("=" * 80)
    
    # Simulate some ticks for Nifty
    nifty_token = 256265
    
    print(f"\nSaving 10 test ticks for token {nifty_token}...")
    for i in range(10):
        ltp = 21500.0 + i * 10
        timestamp = datetime.now()
        data_storage.save_tick(nifty_token, ltp, timestamp, "NIFTY50")
        print(f"  Tick {i+1}: LTP={ltp}, Time={timestamp.strftime('%H:%M:%S.%f')}")
        time.sleep(0.1)
    
    print("\n✅ Ticks saved successfully!")
    print(f"Check file: {data_storage.ticks_dir}/ticks_NIFTY50_{nifty_token}_{data_storage._get_date_string()}.csv")

def test_candle_storage():
    """Test saving candles to CSV"""
    print("\n" + "=" * 80)
    print("Testing Candle Storage")
    print("=" * 80)
    
    nifty_token = 256265
    
    # Create test candles
    print(f"\nSaving test 1-min candles for token {nifty_token}...")
    for i in range(5):
        candle = {
            'timestamp': datetime.now().replace(second=0, microsecond=0),
            'token': nifty_token,
            'open': 21500.0 + i * 10,
            'high': 21510.0 + i * 10,
            'low': 21490.0 + i * 10,
            'close': 21505.0 + i * 10
        }
        data_storage.save_1min_candle(nifty_token, candle, "NIFTY50")
        print(f"  Candle {i+1}: O={candle['open']}, H={candle['high']}, L={candle['low']}, C={candle['close']}")
        time.sleep(0.1)
    
    print("\n✅ Candles saved successfully!")
    print(f"Check file: {data_storage.candles_1min_dir}/candles_1min_NIFTY50_{nifty_token}_{data_storage._get_date_string()}.csv")

def test_candle_aggregator_integration():
    """Test candle aggregator with data storage"""
    print("\n" + "=" * 80)
    print("Testing Candle Aggregator Integration")
    print("=" * 80)
    
    nifty_token = 256265
    
    print(f"\nAdding ticks to candle aggregator (will auto-save to CSV)...")
    
    # Add ticks that span multiple 1-minute candles
    base_time = datetime.now().replace(second=0, microsecond=0)
    
    # First candle (minute 0)
    for i in range(5):
        ltp = 21500.0 + i * 2
        timestamp = base_time.replace(second=i * 10)
        candle_aggregator.add_tick(nifty_token, ltp, timestamp)
        print(f"  Added tick: LTP={ltp}, Time={timestamp.strftime('%H:%M:%S')}")
    
    # Second candle (minute 1) - this will complete the first candle
    print("\n  Moving to next minute (will complete previous candle)...")
    next_minute = base_time.replace(minute=base_time.minute + 1)
    candle_aggregator.add_tick(nifty_token, 21510.0, next_minute)
    print(f"  Added tick: LTP=21510.0, Time={next_minute.strftime('%H:%M:%S')}")
    
    print("\n✅ Candle aggregator integration test complete!")
    print(f"Check file: {data_storage.candles_1min_dir}/candles_1min_{nifty_token}_{data_storage._get_date_string()}.csv")

def main():
    """Run all tests"""
    try:
        test_tick_storage()
        test_candle_storage()
        test_candle_aggregator_integration()
        
        print("\n" + "=" * 80)
        print("All Tests Completed Successfully!")
        print("=" * 80)
        print(f"\nData files location: {data_storage.base_dir}")
        print(f"  - Ticks: {data_storage.ticks_dir}")
        print(f"  - 1-min Candles: {data_storage.candles_1min_dir}")
        print(f"  - 5-min Candles: {data_storage.candles_5min_dir}")
        
    finally:
        # Cleanup
        data_storage.close_all_files()
        print("\n✅ All files closed")

if __name__ == "__main__":
    main()