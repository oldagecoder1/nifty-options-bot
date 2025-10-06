"""
Generate KiteConnect access token (run this daily)
"""
from kiteconnect import KiteConnect
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    api_key = os.getenv('KITE_API_KEY')
    api_secret = os.getenv('KITE_API_SECRET')
    
    if not api_key or not api_secret:
        print("❌ Error: KITE_API_KEY and KITE_API_SECRET must be set in .env file")
        return
    
    kite = KiteConnect(api_key=api_key)
    
    print("\n" + "="*70)
    print("🔑 KITECONNECT ACCESS TOKEN GENERATOR")
    print("="*70)
    print("\n📋 INSTRUCTIONS:")
    print("\n1. Open this URL in your browser:")
    print(f"\n   {kite.login_url()}\n")
    print("2. Login with your Zerodha credentials")
    print("3. After login, you'll be redirected to a URL like:")
    print("   http://127.0.0.1/?request_token=XXXXX&action=login&status=success")
    print("\n4. Copy the 'request_token' value (the XXXXX part)")
    print("="*70)
    
    request_token = input("\n✏️  Paste request_token here: ").strip()
    
    if not request_token:
        print("❌ No token provided. Exiting.")
        return
    
    try:
        print("\n🔄 Generating session...")
        data = kite.generate_session(request_token, api_secret=api_secret)
        access_token = data["access_token"]
        
        print("\n" + "="*70)
        print("✅ ACCESS TOKEN GENERATED SUCCESSFULLY!")
        print("="*70)
        print(f"\n🔑 Access Token:\n{access_token}")
        print("\n📝 Add this to your .env file:")
        print(f"KITE_ACCESS_TOKEN={access_token}")
        print("\n⚠️  IMPORTANT:")
        print("   • This token expires at the end of the day (around 3:30 PM)")
        print("   • You need to regenerate it every trading day")
        print("   • Keep it secure - don't share it")
        print("="*70 + "\n")
        
        # Optionally update .env file
        update = input("📌 Auto-update .env file? (y/n): ").strip().lower()
        if update == 'y':
            update_env_file(access_token)
        
    except Exception as e:
        print(f"\n❌ Error generating token: {e}")
        print("\nCommon issues:")
        print("  • Request token might be expired (valid for few minutes only)")
        print("  • API secret might be incorrect")
        print("  • Check your internet connection")
        print("\nTry again with a fresh request_token\n")

def update_env_file(access_token):
    """Update .env file with new access token"""
    try:
        # Read current .env
        with open('.env', 'r') as f:
            lines = f.readlines()
        
        # Update or add KITE_ACCESS_TOKEN
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('KITE_ACCESS_TOKEN='):
                lines[i] = f'KITE_ACCESS_TOKEN={access_token}\n'
                updated = True
                break
        
        if not updated:
            lines.append(f'\nKITE_ACCESS_TOKEN={access_token}\n')
        
        # Write back
        with open('.env', 'w') as f:
            f.writelines(lines)
        
        print("✅ .env file updated successfully!\n")
        
    except Exception as e:
        print(f"⚠️  Could not auto-update .env: {e}")
        print("Please update manually.\n")

if __name__ == '__main__':
    main()