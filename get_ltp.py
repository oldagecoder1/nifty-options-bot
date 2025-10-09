#!/usr/bin/env python3
"""
Simple script to fetch LTP (Last Traded Price) for Nifty 50 and option strikes
Usage: python get_ltp.py [--strike STRIKE] [--type CE/PE]
"""

import os
import sys
import argparse
import pandas as pd
from dotenv import load_dotenv
from kiteconnect import KiteConnect

# Load environment variables
load_dotenv()

# Constants
NIFTY_TOKEN = 256265  # Nifty 50 spot token
INSTRUMENTS_CSV = './data/instruments.csv'


def get_exchange_for_token(token: int, instruments_df: pd.DataFrame) -> str:
    """
    Determine exchange (NSE/NFO) for a given token
    
    Args:
        token: Instrument token
        instruments_df: DataFrame with instruments data
        
    Returns:
        'NSE' for equity/index, 'NFO' for options
    """
    try:
        instrument = instruments_df[instruments_df['token'] == token]
        
        if not instrument.empty:
            option_type = instrument.iloc[0]['option_type']
            # EQ = Equity/Index on NSE, CE/PE = Options on NFO
            if option_type == 'EQ':
                return 'NSE'
            elif option_type in ['CE', 'PE']:
                return 'NFO'
        
        # Default to NFO if not found
        return 'NFO'
        
    except Exception as e:
        print(f"⚠️  Warning: Could not determine exchange for token {token}: {e}")
        return 'NFO'


def load_instruments():
    """Load instruments from CSV"""
    try:
        df = pd.read_csv(INSTRUMENTS_CSV)
        print(f"✅ Loaded {len(df)} instruments from {INSTRUMENTS_CSV}")
        return df
    except FileNotFoundError:
        print(f"❌ Error: Instruments CSV not found at {INSTRUMENTS_CSV}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading instruments: {e}")
        sys.exit(1)


def find_strike_token(instruments_df: pd.DataFrame, strike: float, option_type: str) -> dict:
    """
    Find token for given strike and option type
    
    Args:
        instruments_df: DataFrame with instruments data
        strike: Strike price (e.g., 25000)
        option_type: 'CE' or 'PE'
        
    Returns:
        Dictionary with token, symbol, and other details
    """
    # Get nearest weekly expiry
    instruments_df['expiry'] = pd.to_datetime(instruments_df['expiry'])
    expiries = sorted(instruments_df['expiry'].unique())
    nearest_expiry = expiries[0] if expiries else None
    
    # Filter for matching strike and option type
    mask = (
        (instruments_df['strike'] == strike) &
        (instruments_df['option_type'] == option_type) &
        (instruments_df['expiry'] == nearest_expiry)
    )
    
    result = instruments_df[mask]
    
    if result.empty:
        return None
    
    row = result.iloc[0]
    return {
        'token': int(row['token']),
        'symbol': row['symbol'],
        'strike': row['strike'],
        'option_type': row['option_type'],
        'expiry': row['expiry'],
        'lot_size': int(row['lot_size'])
    }


def get_ltp(kite: KiteConnect, tokens: list, instruments_df: pd.DataFrame) -> dict:
    """
    Fetch LTP for given tokens
    
    Args:
        kite: KiteConnect instance
        tokens: List of instrument tokens
        instruments_df: DataFrame with instruments data
        
    Returns:
        Dictionary with token -> LTP mapping
    """
    try:
        # Build instrument keys with correct exchange prefix and trading symbol
        instrument_keys = []
        token_to_key = {}
        
        for token in tokens:
            # Find the instrument in the dataframe
            instrument = instruments_df[instruments_df['token'] == token]
            
            if not instrument.empty:
                row = instrument.iloc[0]
                symbol = row['symbol']
                option_type = row['option_type']
                
                # Determine exchange based on option type
                if option_type == 'EQ' or option_type == 'INDEX':
                    exchange = 'NSE'
                elif option_type in ['CE', 'PE']:
                    exchange = 'NFO'
                else:
                    exchange = 'NFO'
                
                # Create trading symbol key (e.g., 'NSE:NIFTY 50' or 'NFO:NIFTY25O0725000CE')
                key = f"{exchange}:{symbol}"
                instrument_keys.append(key)
                token_to_key[token] = key
        
        # Fetch LTP
        ltp_data = kite.ltp(instrument_keys)
        
        # Extract LTP values
        result = {}
        for token, key in token_to_key.items():
            if key in ltp_data:
                result[token] = ltp_data[key]['last_price']
        
        return result
        
    except Exception as e:
        print(f"❌ Error fetching LTP: {e}")
        return {}


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Fetch LTP for Nifty 50 and option strikes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get Nifty 50 LTP only
  python get_ltp.py
  
  # Get Nifty 50 + Call option at 25000 strike
  python get_ltp.py --strike 25000 --type CE
  
  # Get Nifty 50 + Put option at 24800 strike
  python get_ltp.py --strike 24800 --type PE
        """
    )
    
    parser.add_argument('--strike', type=float, help='Strike price (e.g., 25000)')
    parser.add_argument('--type', choices=['CE', 'PE'], help='Option type: CE (Call) or PE (Put)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if (args.strike and not args.type) or (args.type and not args.strike):
        print("❌ Error: Both --strike and --type must be provided together")
        sys.exit(1)
    
    # Check for KiteConnect credentials
    api_key = os.getenv('KITE_API_KEY')
    access_token = os.getenv('KITE_ACCESS_TOKEN')
    
    if not api_key or not access_token:
        print("❌ Error: KITE_API_KEY and KITE_ACCESS_TOKEN must be set in .env file")
        sys.exit(1)
    
    # Load instruments
    print("\n" + "="*60)
    print("📊 NIFTY LTP FETCHER")
    print("="*60)
    
    instruments_df = load_instruments()
    
    # Connect to KiteConnect
    try:
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        
        # Test connection
        profile = kite.profile()
        print(f"✅ Connected to KiteConnect - User: {profile.get('user_name', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Failed to connect to KiteConnect: {e}")
        sys.exit(1)
    
    # Prepare tokens to fetch
    tokens_to_fetch = [NIFTY_TOKEN]
    token_info = {
        NIFTY_TOKEN: {
            'symbol': 'NIFTY 50',
            'type': 'Index'
        }
    }
    
    # Add strike if provided
    if args.strike and args.type:
        strike_data = find_strike_token(instruments_df, args.strike, args.type)
        
        if strike_data:
            tokens_to_fetch.append(strike_data['token'])
            token_info[strike_data['token']] = {
                'symbol': strike_data['symbol'],
                'type': f"{args.type} Option",
                'strike': strike_data['strike'],
                'expiry': strike_data['expiry'].strftime('%Y-%m-%d'),
                'lot_size': strike_data['lot_size']
            }
            print(f"✅ Found strike: {strike_data['symbol']} (Token: {strike_data['token']})")
        else:
            print(f"⚠️  Warning: Strike {args.strike} {args.type} not found in instruments")
    
    # Fetch LTP
    print("\n" + "-"*60)
    print("📈 Fetching LTP...")
    print("-"*60)
    
    ltp_data = get_ltp(kite, tokens_to_fetch, instruments_df)
    
    # Display results
    if ltp_data:
        print("\n" + "="*60)
        print("💰 LAST TRADED PRICES (LTP)")
        print("="*60)
        
        for token, ltp in ltp_data.items():
            info = token_info.get(token, {})
            symbol = info.get('symbol', f'Token {token}')
            instrument_type = info.get('type', 'Unknown')
            
            print(f"\n📊 {symbol}")
            print(f"   Type: {instrument_type}")
            print(f"   Token: {token}")
            
            if 'strike' in info:
                print(f"   Strike: ₹{info['strike']:,.2f}")
                print(f"   Expiry: {info['expiry']}")
                print(f"   Lot Size: {info['lot_size']}")
            
            print(f"   💰 LTP: ₹{ltp:,.2f}")
        
        print("\n" + "="*60)
    else:
        print("❌ No LTP data received")
    
    print("\n✅ Done!\n")


if __name__ == '__main__':
    main()