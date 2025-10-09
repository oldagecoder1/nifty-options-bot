"""
Test script to verify late start handling logic
"""
from datetime import datetime, time as dt_time
import pytz

# Simulate different start times
IST = pytz.timezone('Asia/Kolkata')

def test_start_time_logic(start_time_str):
    """Test the logic for different start times"""
    
    # Parse start time
    hour, minute = map(int, start_time_str.split(':'))
    start_time = dt_time(hour, minute)
    
    print(f"\n{'='*60}")
    print(f"Testing Start Time: {start_time_str}")
    print(f"{'='*60}")
    
    # Check conditions
    should_fetch_historical = start_time >= dt_time(9, 45)
    should_process_immediately = start_time >= dt_time(10, 0)
    
    print(f"Should fetch historical data (>= 9:45): {should_fetch_historical}")
    print(f"Should process immediately (>= 10:00): {should_process_immediately}")
    
    # Determine flow
    if not should_fetch_historical:
        print("\n✅ Flow: Normal start")
        print("   1. Subscribe to Nifty spot")
        print("   2. Collect live ticks")
        print("   3. Wait for 10:00 AM")
        print("   4. Calculate reference levels from aggregated candles")
        print("   5. Select strikes")
    elif should_fetch_historical and not should_process_immediately:
        print("\n✅ Flow: Late start (before 10:00 AM)")
        print("   1. Subscribe to Nifty spot")
        print("   2. Fetch historical data from 9:15 to now")
        print("   3. Feed to candle aggregator")
        print("   4. Wait for 10:00 AM in trading loop")
        print("   5. Calculate reference levels")
        print("   6. Select strikes")
    else:  # should_process_immediately
        print("\n✅ Flow: Late start (after 10:00 AM)")
        print("   1. Subscribe to Nifty spot")
        print("   2. Fetch historical data from 9:15 to now")
        print("   3. Feed to candle aggregator")
        print("   4. Extract 9:45-10:00 window")
        print("   5. Calculate reference levels immediately")
        print("   6. Select strikes immediately")
        print("   7. Subscribe to option tokens")
        print("   8. Ready for trading!")

# Test different scenarios
test_cases = [
    "09:00",  # Before 9:45
    "09:30",  # Before 9:45
    "09:45",  # Exactly 9:45
    "09:50",  # Between 9:45 and 10:00
    "09:59",  # Just before 10:00
    "10:00",  # Exactly 10:00
    "10:15",  # After 10:00
    "10:30",  # After 10:00
    "11:00",  # Much later
    "14:00",  # Afternoon
]

print("\n" + "="*60)
print("LATE START HANDLING - TEST SCENARIOS")
print("="*60)

for test_time in test_cases:
    test_start_time_logic(test_time)

print("\n" + "="*60)
print("All test scenarios completed!")
print("="*60)