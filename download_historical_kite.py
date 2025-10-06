"""
Download historical 1-minute candles from KiteConnect
"""
from kiteconnect import KiteConnect
import pandas as pd
from datetime import datetime, timedelta
import os
import argparse
from dotenv import load_dotenv

load_dotenv()

def download_instrument_data(kite, instrument_token, from_date, to_date, interval='minute'):
    """Download data for one instrument"""
    all_data = []
    current_date = from_date
    print(current_date, to_date)
    while current_date <= to_date:
        chunk_end = min(current_date + timedelta(days=59), to_date)
        
        print(f"  Fetching {current_date.date()} to {chunk_end.date()}...")
        
        try:
            data = kite.historical_data(
                instrument_token=instrument_token,
                from_date=current_date,
                to_date=chunk_end,
                interval=interval
            )
            all_data.extend(data)
        except Exception as e:
            print(f"  Error: {e}")
        
        current_date = chunk_end + timedelta(days=1)
    
    return pd.DataFrame(all_data)

def main():
    """Download historical data for Nifty and options"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Download historical data from KiteConnect')
    parser.add_argument('--start', type=str, required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--nifty-token', type=int, required=True, help='Nifty instrument token')
    parser.add_argument('--call-token', type=int, required=True, help='Call option token')
    parser.add_argument('--put-token', type=int, required=True, help='Put option token')
    parser.add_argument('--output', type=str, default=None, help='Output CSV filename (optional)')
    
    args = parser.parse_args()
    
    # Parse dates
    try:
        from_date = datetime.strptime(args.start, '%Y-%m-%d')
        to_date = datetime.strptime(args.end, '%Y-%m-%d')
    except ValueError:
        print("❌ Error: Invalid date format. Use YYYY-MM-DD")
        return
    
    # Generate default output filename if not provided
    if args.output:
        output_file = args.output
    else:
        output_file = f"historical_data_{args.start}_to_{args.end}.csv"
    
    # Connect to KiteConnect
    kite = KiteConnect(api_key=os.getenv('KITE_API_KEY'))
    kite.set_access_token(os.getenv('KITE_ACCESS_TOKEN'))
    
    print("="*80)
    print("DOWNLOADING HISTORICAL DATA FROM KITECONNECT")
    print("="*80)
    print(f"Date Range: {args.start} to {args.end}")
    print(f"Nifty Token: {args.nifty_token}")
    print(f"Call Token: {args.call_token}")
    print(f"Put Token: {args.put_token}")
    print(f"Output File: {output_file}")
    print("="*80)
    
    # Download Nifty
    print("\n📊 Downloading Nifty 50 data...")
    nifty_df = download_instrument_data(kite, args.nifty_token, from_date, to_date)
    print(f"✅ Got {len(nifty_df)} Nifty candles")
    
    # Download Call
    print("\n📊 Downloading Call option data...")
    call_df = download_instrument_data(kite, args.call_token, from_date, to_date)
    print(f"✅ Got {len(call_df)} Call candles")
    
    # Download Put
    print("\n📊 Downloading Put option data...")
    put_df = download_instrument_data(kite, args.put_token, from_date, to_date)
    print(f"✅ Got {len(put_df)} Put candles")
    
    # Check if we have data
    if nifty_df.empty or call_df.empty or put_df.empty:
        print("\n❌ Error: One or more instruments returned no data")
        print(f"   Nifty: {len(nifty_df)} candles")
        print(f"   Call: {len(call_df)} candles")
        print(f"   Put: {len(put_df)} candles")
        return
    
    # Merge data
    print("\n🔄 Merging data...")
    
    # Rename columns
    nifty_df = nifty_df.rename(columns={
        'date': 'datetime',
        'open': 'nifty_open',
        'high': 'nifty_high',
        'low': 'nifty_low',
        'close': 'nifty_close'
    })
    
    call_df = call_df.rename(columns={
        'date': 'datetime',
        'open': 'call_open',
        'high': 'call_high',
        'low': 'call_low',
        'close': 'call_close'
    })
    
    put_df = put_df.rename(columns={
        'date': 'datetime',
        'open': 'put_open',
        'high': 'put_high',
        'low': 'put_low',
        'close': 'put_close'
    })
    
    # Merge on datetime
    merged = nifty_df[['datetime', 'nifty_open', 'nifty_high', 'nifty_low', 'nifty_close']]
    merged = merged.merge(
        call_df[['datetime', 'call_open', 'call_high', 'call_low', 'call_close']],
        on='datetime',
        how='inner'
    )
    merged = merged.merge(
        put_df[['datetime', 'put_open', 'put_high', 'put_low', 'put_close']],
        on='datetime',
        how='inner'
    )
    
    # Save
    merged.to_csv(output_file, index=False)
    
    print(f"\n✅ Saved {len(merged)} rows to {output_file}")
    print("\n📋 Sample data:")
    print(merged.head(10))
    print("\n" + "="*80)
    print("DOWNLOAD COMPLETE!")
    print("="*80)
    print(f"\n💡 Use this file for testing:")
    print(f"   python test_with_historical_candles.py --data {output_file}")

if __name__ == '__main__':
    main()