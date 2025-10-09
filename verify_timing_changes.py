#!/usr/bin/env python3
"""
Verification script for timing changes
Run this to verify all timing configurations are correct
"""

import os
from datetime import time, datetime
from dotenv import load_dotenv

load_dotenv()

def check_env_variables():
    """Check .env configuration"""
    print("\n" + "="*60)
    print("📋 CHECKING .ENV CONFIGURATION")
    print("="*60)
    
    checks = {
        'TRADING_PHASE': ('2', 'Phase 2 (Real data + Paper trading)'),
        'REFERENCE_WINDOW_START': ('09:45', 'Reference window starts at 09:45'),
        'REFERENCE_WINDOW_END': ('10:00', 'Reference window ends at 10:00'),
        'STRIKE_SELECTION_TIME': ('10:00', 'Strikes selected at 10:00'),
    }
    
    all_passed = True
    for key, (expected, description) in checks.items():
        actual = os.getenv(key, '')
        status = '✅' if actual == expected else '❌'
        print(f"{status} {key}: {actual} (expected: {expected})")
        if actual != expected:
            print(f"   ⚠️  {description}")
            all_passed = False
    
    return all_passed

def check_code_files():
    """Check code files for correct timing"""
    print("\n" + "="*60)
    print("🔍 CHECKING CODE FILES")
    print("="*60)
    
    checks = []
    
    # Check breakout_logic.py
    try:
        with open('strategy/breakout_logic.py', 'r') as f:
            content = f.read()
            if 'time(10, 0)' in content:
                checks.append(('✅', 'breakout_logic.py', 'Trading start time set to 10:00'))
            else:
                checks.append(('❌', 'breakout_logic.py', 'Trading start time NOT set to 10:00'))
    except Exception as e:
        checks.append(('❌', 'breakout_logic.py', f'Error reading file: {e}'))
    
    # Check main.py
    try:
        with open('main.py', 'r') as f:
            content = f.read()
            if 'dt_time(9, 45)' in content and 'dt_time(10, 0)' in content:
                checks.append(('✅', 'main.py', 'Reference window timing correct (09:45-10:00)'))
            else:
                checks.append(('❌', 'main.py', 'Reference window timing incorrect'))
    except Exception as e:
        checks.append(('❌', 'main.py', f'Error reading file: {e}'))
    
    # Check candle_aggregator.py
    try:
        with open('utils/candle_aggregator.py', 'r') as f:
            content = f.read()
            if 'candle_time >= end_time' in content:
                checks.append(('✅', 'candle_aggregator.py', 'Candle filtering logic fixed (>= end_time)'))
            else:
                checks.append(('❌', 'candle_aggregator.py', 'Candle filtering logic NOT fixed'))
    except Exception as e:
        checks.append(('❌', 'candle_aggregator.py', f'Error reading file: {e}'))
    
    # Check reference_levels.py
    try:
        with open('strategy/reference_levels.py', 'r') as f:
            content = f.read()
            if '09:45-10:00' in content:
                checks.append(('✅', 'reference_levels.py', 'Documentation updated to 09:45-10:00'))
            else:
                checks.append(('❌', 'reference_levels.py', 'Documentation NOT updated'))
    except Exception as e:
        checks.append(('❌', 'reference_levels.py', f'Error reading file: {e}'))
    
    all_passed = True
    for status, filename, message in checks:
        print(f"{status} {filename}: {message}")
        if status == '❌':
            all_passed = False
    
    return all_passed

def print_timeline():
    """Print expected timeline"""
    print("\n" + "="*60)
    print("⏰ EXPECTED TIMELINE")
    print("="*60)
    
    timeline = [
        ('09:15', 'Market opens, bot starts collecting data'),
        ('09:45', 'Reference window starts'),
        ('10:00', 'Reference levels calculated, strikes selected'),
        ('10:00', 'Trading window opens'),
        ('10:05+', 'First possible entry (more likely 10:10)'),
        ('15:15', 'Hard exit if in position'),
        ('15:30', 'Market closes'),
    ]
    
    for time_str, description in timeline:
        print(f"  {time_str} - {description}")

def print_candle_logic():
    """Print candle timestamp logic"""
    print("\n" + "="*60)
    print("📊 CANDLE TIMESTAMP LOGIC")
    print("="*60)
    
    print("\n5-Minute Candle Structure:")
    print("  Timestamp | Data Period        | Completes At")
    print("  ----------|--------------------|--------------")
    print("  09:45     | 09:45:00-09:49:59 | 09:50:00")
    print("  09:50     | 09:50:00-09:54:59 | 09:55:00")
    print("  09:55     | 09:55:00-09:59:59 | 10:00:00")
    print("  10:00     | 10:00:00-10:04:59 | 10:05:00")
    print("  10:05     | 10:05:00-10:09:59 | 10:10:00")
    print("  10:10     | 10:10:00-10:14:59 | 10:15:00")
    
    print("\nReference Window (09:45-10:00):")
    print("  ✓ Includes: 09:45, 09:50, 09:55 candles")
    print("  ✗ Excludes: 10:00 candle (contains data from 10:00:00 onwards)")
    print("  Total: 15 minutes of data (09:45:00 to 09:59:59)")
    
    print("\nEntry Signal Example (at 10:10 AM):")
    print("  Previous candle: 10:00 (data 10:00:00-10:04:59)")
    print("  Current candle:  10:05 (data 10:05:00-10:09:59)")
    print("  For CALL entry:")
    print("    1. 10:00 close > RN ✓")
    print("    2. 10:05 close > RN ✓")
    print("    3. 10:05 close > 10:00 close ✓")

def main():
    """Run all verification checks"""
    print("\n" + "="*60)
    print("🔧 TIMING CHANGES VERIFICATION SCRIPT")
    print("="*60)
    
    env_ok = check_env_variables()
    code_ok = check_code_files()
    
    print_timeline()
    print_candle_logic()
    
    print("\n" + "="*60)
    print("📊 VERIFICATION SUMMARY")
    print("="*60)
    
    if env_ok and code_ok:
        print("✅ ALL CHECKS PASSED!")
        print("\nYour bot is ready for live market testing with new timing:")
        print("  • Reference window: 09:45-10:00")
        print("  • Strike selection: 10:00")
        print("  • Trading starts: 10:00")
        print("\nNext steps:")
        print("  1. Run: python download_instruments.py")
        print("  2. Verify KiteConnect token is valid")
        print("  3. Start bot: python main.py")
        return 0
    else:
        print("❌ SOME CHECKS FAILED!")
        print("\nPlease review the errors above and fix them before running the bot.")
        return 1

if __name__ == '__main__':
    exit(main())