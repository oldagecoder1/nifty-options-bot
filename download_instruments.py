"""
Download Nifty option instruments from KiteConnect
Run this weekly to get latest strikes and expiries
"""
from kiteconnect import KiteConnect
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def main():
    # Load credentials
    api_key = os.getenv('KITE_API_KEY')
    access_token = os.getenv('KITE_ACCESS_TOKEN')
    
    if not api_key or not access_token:
        print("❌ Error: KITE_API_KEY and KITE_ACCESS_TOKEN must be set in .env")
        print("Run 'python get_kite_token.py' first to get access token")
        return
    
    print("\n" + "="*70)
    print("📥 DOWNLOADING NIFTY INSTRUMENTS FROM KITECONNECT")
    print("="*70)
    
    try:
        # Connect to KiteConnect
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        
        # Test connection
        profile = kite.profile()
        print(f"\n✅ Connected as: {profile['user_name']} ({profile['email']})")
        
        print("\n🔄 Downloading instruments...")
        
        # Get NFO instruments (Nifty options)
        nfo_instruments = kite.instruments("NFO")
        
        # Filter for NIFTY options only
        nifty_options = [
            inst for inst in nfo_instruments 
            if inst['name'] == 'NIFTY' and inst['instrument_type'] in ['CE', 'PE']
        ]
        
        print(f"   Found {len(nifty_options)} NIFTY option contracts")
        
        # Get Nifty 50 Index
        nse_instruments = kite.instruments("NSE")
        nifty_index = [
            inst for inst in nse_instruments
            if inst['tradingsymbol'] == 'NIFTY 50'
        ]
        
        if nifty_index:
            print(f"   Found NIFTY 50 index")
        
        # Combine all instruments
        all_instruments = nifty_index + nifty_options
        
        # Convert to our CSV format
        df_mapped = pd.DataFrame({
            'symbol': [inst['tradingsymbol'] for inst in all_instruments],
            'token': [inst['instrument_token'] for inst in all_instruments],
            'strike': [inst.get('strike', 0) for inst in all_instruments],
            'expiry': [inst.get('expiry', '') for inst in all_instruments],  # Keep as string initially
            'option_type': [inst.get('instrument_type', 'INDEX') for inst in all_instruments],
            'lot_size': [inst['lot_size'] for inst in all_instruments]
        })
        
        # Convert expiry to string format (YYYY-MM-DD)
        def format_expiry(expiry):
            if expiry == '' or pd.isna(expiry):
                return datetime.now().strftime('%Y-%m-%d')
            if isinstance(expiry, str):
                try:
                    return pd.to_datetime(expiry).strftime('%Y-%m-%d')
                except:
                    return expiry
            try:
                return expiry.strftime('%Y-%m-%d')
            except:
                return str(expiry)
        
        df_mapped['expiry'] = df_mapped['expiry'].apply(format_expiry)
        
        # Sort by expiry and strike
        df_mapped = df_mapped.sort_values(['expiry', 'strike', 'option_type'])
        
        # Save to CSV
        output_path = 'data/instruments_06_10.csv'
        os.makedirs('data', exist_ok=True)
        df_mapped.to_csv(output_path, index=False)
        
        print(f"\n✅ Saved {len(df_mapped)} instruments to {output_path}")
        
        # Show summary
        print("\n📊 SUMMARY:")
        print("="*70)
        
        # Group by expiry
        expiries = df_mapped[df_mapped['option_type'] != 'INDEX']['expiry'].value_counts().sort_index()
        print(f"\nAvailable Expiries:")
        for expiry, count in expiries.head(5).items():  # Show first 5 expiries
            print(f"   {expiry}: {count} contracts")
        
        # Show sample data
        print(f"\n📋 Sample Data (first 10 rows):")
        print("-"*70)
        print(df_mapped.head(10).to_string(index=False))
        print("-"*70)
        
        # Show nearby strikes for current Nifty level
        try:
            nifty_ltp = kite.ltp(["NSE:NIFTY 50"])["NSE:NIFTY 50"]["last_price"]
            print(f"\n📍 Current Nifty: {nifty_ltp:.2f}")
            
            # Find nearest weekly expiry
            nearest_expiry = df_mapped[df_mapped['option_type'] != 'INDEX']['expiry'].min()
            print(f"📅 Nearest Expiry: {nearest_expiry}")
            
            # Show strikes near current level
            nearby = df_mapped[
                (df_mapped['expiry'] == nearest_expiry) &
                (df_mapped['strike'] >= nifty_ltp - 500) &
                (df_mapped['strike'] <= nifty_ltp + 500)
            ].sort_values('strike')
            
            if not nearby.empty:
                print(f"\n🎯 Nearby Strikes for {nearest_expiry}:")
                print(nearby[['symbol', 'strike', 'option_type', 'token']].to_string(index=False))
        except Exception as e:
            print(f"\n⚠️  Could not fetch current Nifty price: {e}")
        
        print("\n" + "="*70)
        print("✅ DOWNLOAD COMPLETE!")
        print("="*70)
        print("\n💡 TIP: Run this script weekly to get latest expiries")
        print("   New weekly options are added every Thursday\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nPossible issues:")
        print("  • Access token might be expired (run get_kite_token.py)")
        print("  • Check your internet connection")
        print("  • Verify KiteConnect API subscription is active\n")

if __name__ == '__main__':
    main()