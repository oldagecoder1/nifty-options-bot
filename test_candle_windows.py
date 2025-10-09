"""
Test script to verify 5-minute candle window calculations
"""
from datetime import datetime, time as dt_time
import pandas as pd

def test_candle_windows():
    """Test that candle windows are calculated correctly"""
    
    print("=" * 80)
    print("Testing 5-Minute Candle Window Calculations")
    print("=" * 80)
    
    # Test cases for different times
    test_times = [
        "10:00:00",
        "10:05:00", 
        "10:10:00",
        "10:15:00",
        "10:20:00",
        "10:25:00",
    ]
    
    for time_str in test_times:
        # Parse time
        hour, minute, second = map(int, time_str.split(':'))
        candle_start = datetime(2024, 1, 15, hour, minute, second)
        
        # Calculate candle end (start + 4 min 59 sec)
        candle_end = candle_start + pd.Timedelta(minutes=4, seconds=59)
        
        print(f"\nCandle Start: {candle_start.strftime('%H:%M:%S')}")
        print(f"Candle End:   {candle_end.strftime('%H:%M:%S')}")
        print(f"Window:       {candle_start.strftime('%H:%M:%S')} - {candle_end.strftime('%H:%M:%S')}")
        print(f"Duration:     5 minutes (covers all ticks in this period)")
    
    print("\n" + "=" * 80)
    print("Candle Aggregator Logic:")
    print("=" * 80)
    print("- A tick at 10:15:00 starts the 10:15 candle")
    print("- All ticks from 10:15:00 to 10:19:59 update the 10:15 candle")
    print("- When first tick at 10:20:00 arrives, the 10:15 candle is marked complete")
    print("- The callback fires with the completed 10:15 candle data")
    print("=" * 80)
    
    # Test the rounding logic used in candle_aggregator
    print("\n" + "=" * 80)
    print("Testing Candle Rounding Logic (from candle_aggregator.py):")
    print("=" * 80)
    
    test_ticks = [
        "10:15:00",
        "10:15:30",
        "10:17:45",
        "10:19:59",
        "10:20:00",  # This starts new candle
    ]
    
    interval_minutes = 5
    
    for tick_time_str in test_ticks:
        hour, minute, second = map(int, tick_time_str.split(':'))
        tick_timestamp = datetime(2024, 1, 15, hour, minute, second)
        
        # This is the rounding logic from candle_aggregator.py line 63-67
        candle_time = tick_timestamp.replace(
            minute=(tick_timestamp.minute // interval_minutes) * interval_minutes,
            second=0,
            microsecond=0
        )
        
        print(f"Tick at {tick_time_str} -> Belongs to candle: {candle_time.strftime('%H:%M:%S')}")
    
    print("=" * 80)

if __name__ == "__main__":
    test_candle_windows()