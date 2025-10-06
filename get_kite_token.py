"""
Simple Flask server to get Kite access token
Run this script, login via browser, get token, then stop the server
"""
from flask import Flask, request, redirect
from kiteconnect import KiteConnect
import os
from dotenv import load_dotenv
import webbrowser
import threading
import time

load_dotenv()

app = Flask(__name__)

# Kite credentials
API_KEY = os.getenv('KITE_API_KEY')
API_SECRET = os.getenv('KITE_API_SECRET')

if not API_KEY or not API_SECRET:
    print("❌ Error: KITE_API_KEY and KITE_API_SECRET must be set in .env file")
    exit(1)

kite = KiteConnect(api_key=API_KEY)

# Global variable to store token
access_token = None
server_running = True

@app.route('/')
def index():
    """Root route - redirect to login"""
    login_url = kite.login_url()
    return f'''
    <html>
        <head><title>Kite Login</title></head>
        <body style="font-family: Arial; padding: 50px; text-align: center;">
            <h1>🔐 Kite Connect - Get Access Token</h1>
            <p>Click the button below to login with your Zerodha credentials</p>
            <a href="{login_url}" style="
                display: inline-block;
                padding: 15px 30px;
                background: #387ed1;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                font-size: 18px;
            ">Login with Zerodha</a>
        </body>
    </html>
    '''

@app.route('/callback')
def callback():
    """Callback route - receives request_token from Kite"""
    global access_token, server_running
    
    request_token = request.args.get('request_token')
    
    if not request_token:
        return '''
        <html>
            <body style="font-family: Arial; padding: 50px; text-align: center;">
                <h1>❌ Error</h1>
                <p>No request token received. Please try again.</p>
            </body>
        </html>
        '''
    
    try:
        # Generate session
        data = kite.generate_session(request_token, api_secret=API_SECRET)
        access_token = data["access_token"]
        
        # Update .env file
        update_env_file(access_token)
        
        # Schedule server shutdown
        threading.Timer(2.0, shutdown_server).start()
        
        return f'''
        <html>
            <head><title>Success</title></head>
            <body style="font-family: Arial; padding: 50px; text-align: center;">
                <h1 style="color: green;">✅ Success!</h1>
                <h2>Access Token Generated</h2>
                <div style="
                    background: #f0f0f0;
                    padding: 20px;
                    margin: 20px auto;
                    max-width: 600px;
                    word-wrap: break-word;
                    font-family: monospace;
                    font-size: 14px;
                ">{access_token}</div>
                <p><strong>✅ Token saved to .env file</strong></p>
                <p>You can now close this window and run your trading bot!</p>
                <p style="color: #666; font-size: 14px;">
                    ⚠️ Note: This token expires at end of day. 
                    Run this script again tomorrow to get a new token.
                </p>
                <p style="color: #999; font-size: 12px; margin-top: 30px;">
                    Server will automatically stop in 2 seconds...
                </p>
            </body>
        </html>
        '''
        
    except Exception as e:
        return f'''
        <html>
            <body style="font-family: Arial; padding: 50px; text-align: center;">
                <h1 style="color: red;">❌ Error</h1>
                <p>{str(e)}</p>
                <p><a href="/">Try Again</a></p>
            </body>
        </html>
        '''

def update_env_file(token):
    """Update .env file with new access token"""
    try:
        # Read current .env
        with open('.env', 'r') as f:
            lines = f.readlines()
        
        # Update or add KITE_ACCESS_TOKEN
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('KITE_ACCESS_TOKEN='):
                lines[i] = f'KITE_ACCESS_TOKEN={token}\n'
                updated = True
                break
        
        if not updated:
            lines.append(f'\nKITE_ACCESS_TOKEN={token}\n')
        
        # Write back
        with open('.env', 'w') as f:
            f.writelines(lines)
        
        print(f"\n✅ Access token saved to .env file")
        print(f"Token: {token}")
        
    except Exception as e:
        print(f"⚠️  Could not update .env file: {e}")
        print(f"Please manually add this to .env:")
        print(f"KITE_ACCESS_TOKEN={token}")

def shutdown_server():
    """Shutdown Flask server"""
    global server_running
    server_running = False
    print("\n" + "="*80)
    print("✅ ACCESS TOKEN OBTAINED SUCCESSFULLY!")
    print("="*80)
    print("\n🛑 Server shutting down...")
    print("\nYou can now run your trading bot:")
    print("  python main.py")
    print("\n" + "="*80)
    
    # Shutdown Flask
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        # For production WSGI servers
        os._exit(0)
    else:
        func()

def open_browser():
    """Open browser after server starts"""
    time.sleep(1)
    webbrowser.open('http://localhost:5000')

if __name__ == '__main__':
    print("\n" + "="*80)
    print("🔐 KITE CONNECT - ACCESS TOKEN GENERATOR")
    print("="*80)
    print("\n📋 Instructions:")
    print("1. Browser will open automatically")
    print("2. Login with your Zerodha credentials")
    print("3. You'll be redirected back with the access token")
    print("4. Token will be saved to .env file automatically")
    print("5. Server will stop automatically")
    print("\n" + "="*80)
    print("\n🌐 Starting server on http://localhost:5000")
    print("⏳ Opening browser in 1 second...\n")
    
    # Open browser in background
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run Flask server
    try:
        app.run(host='localhost', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    
    print("\n✅ Done!\n")