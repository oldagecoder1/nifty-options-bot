"""
Test script to verify historical candle data preservation
"""
from datetime import datetime
import pandas as pd
from utils.candle_aggregator import candle_aggregator

# Test data - simulating what broker API returns
test_token = 256265
test_data = [
    {
        'timestamp': datetime(2025, 10, 7, 9, 15),
        'open': 25085.3,
        'high': 25139.7,
        'low': 25085.3,
        'close': 25122.45
    },
    {
        'timestamp': datetime(2025, 10, 7, 9, 16),
        'open': 25122.5,
        'high': 25145.0,
        'low': 25120.0,
        'close': 25130.2
    },
    {
        'timestamp': datetime(2025, 10, 7, 9, 17),
        'open': 25130.0,
        'high': 25130.0,
        'low': 25090.0,
        'close': 25097.75
    }
]

print("=" * 80)
print("Testing Historical Candle Data Preservation")
print("=" * 80)

# Add historical candles using the new method
print("\n📥 Adding historical candles...")
for candle_data in test_data:
    timestamp = candle_data['timestamp']
    print(f"\nAdding candle for {timestamp.strftime('%Y-%m-%d %H:%M:%S')}:")
    print(f"  Open:  {candle_data['open']}")
    print(f"  High:  {candle_data['high']}")
    print(f"  Low:   {candle_data['low']}")
    print(f"  Close: {candle_data['close']}")
    
    candle_aggregator.add_historical_candle(
        test_token,
        {
            'open': candle_data['open'],
            'high': candle_data['high'],
            'low': candle_data['low'],
            'close': candle_data['close']
        },
        timestamp
    )

# Retrieve and verify the candles
print("\n" + "=" * 80)
print("📊 Retrieving stored candles...")
print("=" * 80)

candles_df = candle_aggregator.get_candles(test_token, interval='1min')

if not candles_df.empty:
    print(f"\n✅ Successfully retrieved {len(candles_df)} candles:\n")
    print(candles_df.to_string())
    
    # Verify OHLC values are preserved
    print("\n" + "=" * 80)
    print("🔍 Verification:")
    print("=" * 80)
    
    all_correct = True
    for i, (idx, row) in enumerate(candles_df.iterrows()):
        expected = test_data[i]
        
        print(f"\nCandle {i+1} ({idx.strftime('%H:%M:%S')}):")
        
        checks = [
            ('Open', row['open'], expected['open']),
            ('High', row['high'], expected['high']),
            ('Low', row['low'], expected['low']),
            ('Close', row['close'], expected['close'])
        ]
        
        for name, actual, expected_val in checks:
            match = "✅" if actual == expected_val else "❌"
            print(f"  {match} {name}: {actual} (expected: {expected_val})")
            if actual != expected_val:
                all_correct = False
    
    print("\n" + "=" * 80)
    if all_correct:
        print("✅ ALL CHECKS PASSED - OHLC data is correctly preserved!")
    else:
        print("❌ SOME CHECKS FAILED - OHLC data is NOT correctly preserved!")
    print("=" * 80)
else:
    print("❌ No candles retrieved!")

print("\n✅ Test completed!")