# Kite Access Token Setup Guide

## 🎯 Quick Setup (5 Minutes)

### Step 1: Setup Kite Connect App (One Time)

1. **Go to Kite Connect Developer Console:**
   - Visit: https://developers.kite.trade/apps
   - Login with your Zerodha credentials

2. **Create New App:**
   - Click "Create new app"
   - Fill details:
     - **App name:** My Trading Bot
     - **Redirect URL:** `http://localhost:5000/callback`
     - **Description:** Automated trading bot
   - Click "Create"

3. **Get API Credentials:**
   - Copy **API Key** 
   - Copy **API Secret**
   - Add to `.env` file:
   ```bash
   KITE_API_KEY=your_api_key_here
   KITE_API_SECRET=your_api_secret_here
   ```

---

## 🔑 Get Access Token (Daily - Before Market)

### Method 1: Using Flask Server (Recommended) ✅

**Run the token server:**

```bash
# Install Flask (one time)
pip install flask

# Run token server
python get_kite_token.py
```

**What happens:**
1. ✅ Server starts on http://localhost:5000
2. ✅ Browser opens automatically
3. ✅ Click "Login with Zerodha"
4. ✅ Enter Zerodha credentials (User ID, Password, TOTP/PIN)
5. ✅ Redirected back with success message
6. ✅ Token automatically saved to `.env`
7. ✅ Server stops automatically

**Output:**
```
================================================================================
✅ ACCESS TOKEN OBTAINED SUCCESSFULLY!
================================================================================

🛑 Server shutting down...

You can now run your trading bot:
  python main.py

================================================================================
```

---

### Method 2: Manual (Fallback)

If Flask doesn't work, use manual method:

```bash
python generate_token.py
```

Then follow on-screen instructions.

---

## 📋 Complete Workflow

### Every Trading Day:

**Morning (Before 9:15 AM):**

```bash
# 1. Get fresh access token
python get_kite_token.py

# Wait for browser to open → Login → Token saved automatically

# 2. Run your bot
python main.py
```

**That's it!** ✅

---

## 🔧 Troubleshooting

### Issue: "Redirect URI mismatch"

**Solution:**
- Go to Kite Developer Console: https://developers.kite.trade/apps
- Edit your app
- Ensure Redirect URL is exactly: `http://localhost:5000/callback`
- Save changes

### Issue: "Port 5000 already in use"

**Solution:**
```bash
# Kill process on port 5000
# On Mac/Linux:
lsof -ti:5000 | xargs kill -9

# On Windows:
netstat -ano | findstr :5000
taskkill /PID <PID_NUMBER> /F

# Then run again:
python get_kite_token.py
```

### Issue: Browser doesn't open

**Solution:**
```bash
# Manually open in browser:
http://localhost:5000
```

### Issue: Flask not installed

**Solution:**
```bash
pip install flask
```

---

## 🔐 Security Notes

1. **Access Token Expires Daily**
   - Generate new token every morning
   - Token expires around 3:30 PM

2. **Never Share Tokens**
   - Don't commit `.env` to Git
   - Keep tokens private

3. **API Secret Protection**
   - Store in `.env` only
   - Never hardcode in scripts

---

## 📊 Kite Connect App Settings

**In Developer Console (https://developers.kite.trade/apps):**

| Setting | Value |
|---------|-------|
| **App Name** | My Trading Bot |
| **Redirect URL** | `http://localhost:5000/callback` |
| **Status** | Active |
| **Permissions** | Orders, Holdings, Profile |

---

## 🚀 Quick Reference

```bash
# Daily morning routine:

# 1. Get token (opens browser automatically)
python get_kite_token.py

# 2. Run bot (Phase 2 - Real data, paper trading)
TRADING_PHASE=2 python main.py

# 3. Or run live trading (Phase 3)
TRADING_PHASE=3 python main.py
```

---

## 📁 Files

| File | Purpose |
|------|---------|
| `get_kite_token.py` | Flask server to get access token |
| `generate_token.py` | Manual method (fallback) |
| `.env` | Stores tokens (auto-updated) |

---

## ✅ Checklist

Before first run:

- [ ] Created Kite Connect app at https://developers.kite.trade/apps
- [ ] Set Redirect URL to `http://localhost:5000/callback`
- [ ] Added `KITE_API_KEY` to `.env`
- [ ] Added `KITE_API_SECRET` to `.env`
- [ ] Installed Flask: `pip install flask`
- [ ] Tested token generation: `python get_kite_token.py`
- [ ] Token saved to `.env` automatically
- [ ] Ready to run bot!

---

## 🎯 Summary

**One-time setup:**
1. Create Kite app
2. Set redirect URL: `http://localhost:5000/callback`
3. Add API key/secret to `.env`

**Daily (before trading):**
1. Run `python get_kite_token.py`
2. Login in browser
3. Token saved automatically
4. Run your bot!

**Simple, fast, automated!** 🚀