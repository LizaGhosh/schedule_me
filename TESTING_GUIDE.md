# Testing Guide - How to Share This App

This guide explains how to share the Calendar Assistant app with testers.

## Option 1: Local Network Testing (Easiest for Quick Testing)

### For You (Host):

1. **Find your local IP address:**
   ```bash
   # On macOS/Linux:
   ifconfig | grep "inet " | grep -v 127.0.0.1
   
   # On Windows:
   ipconfig
   ```
   You'll see something like `192.168.1.100` or `10.0.0.5`

2. **Update Google Cloud Console:**
   - Go to [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials)
   - Click on your OAuth 2.0 Client ID
   - Under "Authorized redirect URIs", add:
     - `http://YOUR_IP:5000/auth/callback` (e.g., `http://192.168.1.100:5000/auth/callback`)
   - Save changes

3. **Update your `.env` file:**
   ```
   OAUTH_REDIRECT_URI=http://YOUR_IP:5000/auth/callback
   ```

4. **Run the app on your local network:**
   ```bash
   # Update app.py to allow external connections
   # Change: app.run(debug=True, port=5000)
   # To: app.run(debug=True, host='0.0.0.0', port=5000)
   python app.py
   ```

5. **Share with testers:**
   - Give them the URL: `http://YOUR_IP:5000`
   - Make sure they're on the same WiFi/network
   - Add their emails as test users in Google Cloud Console

### For Testers:

1. **Open the URL** you provided (e.g., `http://192.168.1.100:5000`)
2. **Click "Login"** and authenticate with Google
3. **Start using the app!**

**Limitations:**
- Only works on the same network
- Your computer must be running
- Not accessible from outside your network

---

## Option 2: Cloud Hosting (Best for Remote Testing)

### Recommended Platforms:

#### A. **Heroku** (Free tier available)
```bash
# Install Heroku CLI
# Create Procfile:
echo "web: gunicorn app:app" > Procfile

# Create runtime.txt:
echo "python-3.11" > runtime.txt

# Deploy:
heroku create your-app-name
heroku config:set GROQ_API_KEY=your_key
heroku config:set ELEVENLABS_API_KEY=your_key
heroku config:set FLASK_SECRET_KEY=your_secret
heroku config:set OAUTH_REDIRECT_URI=https://your-app-name.herokuapp.com/auth/callback
git push heroku main
```

#### B. **Railway** (Easy deployment)
1. Connect your GitHub repo
2. Add environment variables
3. Deploy automatically

#### C. **Render** (Free tier)
1. Connect GitHub repo
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `gunicorn app:app`
4. Add environment variables

### Steps for Cloud Deployment:

1. **Update Google Cloud Console:**
   - Add your production URL to "Authorized redirect URIs":
     - `https://your-app-name.herokuapp.com/auth/callback`
   - Or whatever your deployment URL is

2. **Update environment variables:**
   - Set `OAUTH_REDIRECT_URI` to your production URL
   - Add all API keys

3. **Update app.py:**
   ```python
   if __name__ == '__main__':
       port = int(os.environ.get('PORT', 5000))
       app.run(host='0.0.0.0', port=port, debug=False)
   ```

4. **Add gunicorn to requirements.txt:**
   ```
   gunicorn>=21.2.0
   ```

5. **Share the production URL** with testers

---

## Option 3: Share Code Repository (For Technical Testers)

### What to Share:

1. **Repository access** (GitHub, GitLab, etc.)
2. **Setup instructions** (from README.md)
3. **Environment variables template** (without actual keys)

### What Testers Need:

1. **API Keys:**
   - Groq API key (they can get their own from https://console.groq.com/)
   - ElevenLabs API key (optional, from https://elevenlabs.io/)

2. **Google OAuth Setup:**
   - They need to create their own Google Cloud project
   - Or you add them as test users to your project

3. **Credentials file:**
   - Either share `credentials.json` (if safe)
   - Or they create their own OAuth credentials

---

## Important: Google OAuth Setup for Testers

### If Using Your Google Cloud Project:

1. **Go to [OAuth Consent Screen](https://console.cloud.google.com/apis/credentials/consent)**
2. **Make sure app is in "Testing" mode** (not "Published")
3. **Add test users:**
   - Scroll to "Test users" section
   - Click "+ ADD USERS"
   - Add each tester's email address
   - Save

4. **Add redirect URIs:**
   - Go to [Credentials](https://console.cloud.google.com/apis/credentials)
   - Click your OAuth 2.0 Client ID
   - Add all redirect URIs:
     - `http://localhost:5000/auth/callback` (for local testing)
     - `http://YOUR_IP:5000/auth/callback` (for local network)
     - `https://your-production-url.com/auth/callback` (for cloud)

### If Testers Use Their Own Google Cloud Project:

They need to:
1. Create a Google Cloud project
2. Enable Calendar API
3. Create OAuth 2.0 credentials
4. Configure OAuth consent screen
5. Download `credentials.json`

---

## Quick Start for Testers

### Minimal Setup (Using Your Credentials):

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd schedule_me
   ```

2. **Set up virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` file:**
   ```
   GROQ_API_KEY=their_groq_key
   ELEVENLABS_API_KEY=their_elevenlabs_key  # Optional
   FLASK_SECRET_KEY=generate_with_python_secrets
   OAUTH_REDIRECT_URI=http://localhost:5000/auth/callback
   ```

5. **Get `credentials.json`:**
   - Either from you (if you share it)
   - Or create their own in Google Cloud Console

6. **Run the app:**
   ```bash
   python app.py
   ```

7. **Open browser:**
   - Go to `http://localhost:5000`
   - Click "Login"
   - Authenticate with Google

---

## Testing Checklist

### Before Sharing:

- [ ] App is in "Testing" mode (not "Published")
- [ ] All test user emails are added to Google Cloud Console
- [ ] Redirect URIs are configured correctly
- [ ] Environment variables are set
- [ ] App runs without errors
- [ ] OAuth login works for you

### For Each Tester:

- [ ] They can access the app URL
- [ ] They can log in with Google
- [ ] They can see their calendar events
- [ ] They can query events
- [ ] They can create/modify/cancel events
- [ ] Voice input works (if using)

---

## Troubleshooting

### "Access Denied" Error:
- Check if app is in "Testing" mode
- Verify tester's email is in "Test users" list
- Wait 5-10 minutes after adding test users

### "Redirect URI Mismatch":
- Verify redirect URI matches exactly in Google Cloud Console
- Check `OAUTH_REDIRECT_URI` in `.env` file
- No trailing slashes!

### "Not authenticated" (401 errors):
- Clear browser cookies
- Try logging in again
- Check server logs for errors

### Can't Access on Local Network:
- Check firewall settings
- Verify both devices are on same network
- Try using `0.0.0.0` as host instead of localhost

---

## Security Notes

⚠️ **Important:**
- Don't commit `credentials.json` to Git
- Don't share API keys publicly
- Use environment variables for sensitive data
- For production, use HTTPS (not HTTP)
- Consider rate limiting for public deployments

---

## Recommended Approach

**For Quick Testing (1-5 users):**
- Use Option 1 (Local Network) or Option 3 (Share Code)

**For Wider Testing (5-100 users):**
- Use Option 2 (Cloud Hosting) with app in "Testing" mode

**For Production:**
- Complete Google app verification
- Use proper cloud hosting with HTTPS
- Set up proper domain and SSL

