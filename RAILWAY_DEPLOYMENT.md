# Railway Deployment Guide

Step-by-step guide to deploy the Calendar Assistant app to Railway.

## Prerequisites

1. **GitHub Account** (or GitLab/Bitbucket)
2. **Railway Account** - Sign up at [railway.app](https://railway.app)
3. **Google Cloud Console** access (for OAuth setup)
4. **API Keys:**
   - Groq API key
   - ElevenLabs API key (optional)

## Step 1: Prepare Your Code

### 1.1 Ensure all files are ready:

✅ **Files already created:**
- `Procfile` - Tells Railway how to run your app
- `railway.json` - Railway configuration
- `requirements.txt` - Already includes gunicorn

### 1.2 Commit your code to Git:

```bash
cd schedule_me

# Make sure all changes are committed
git add .
git commit -m "Prepare for Railway deployment"

# Push to GitHub (if not already pushed)
git push origin main
```

## Step 2: Set Up Railway Project

### 2.1 Create Railway Account

1. Go to [railway.app](https://railway.app)
2. Click "Start a New Project"
3. Sign up with GitHub (recommended) or email

### 2.2 Create New Project

1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Authorize Railway to access your GitHub
4. Select your repository
5. Railway will auto-detect it's a Python app

### 2.3 Configure Build Settings

Railway should auto-detect:
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`

If not, you can set it manually in the settings.

## Step 3: Configure Environment Variables

### 3.1 Add Environment Variables in Railway

1. In your Railway project, click on your service
2. Go to **"Variables"** tab
3. Click **"New Variable"**
4. Add each of these:

```
GROQ_API_KEY=your_groq_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
FLASK_SECRET_KEY=your_secret_key_here
OAUTH_REDIRECT_URI=https://your-app-name.up.railway.app/auth/callback
```

**To generate FLASK_SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_hex(16))"
```

### 3.2 Get Your Railway URL

1. After deployment, Railway will give you a URL like:
   - `https://your-app-name.up.railway.app`
2. **Update `OAUTH_REDIRECT_URI`** with your actual Railway URL:
   ```
   OAUTH_REDIRECT_URI=https://your-app-name.up.railway.app/auth/callback
   ```

## Step 4: Configure Google OAuth

### 4.1 Update Google Cloud Console

1. Go to [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials)
2. Click on your **OAuth 2.0 Client ID**
3. Under **"Authorized redirect URIs"**, add:
   - `https://your-app-name.up.railway.app/auth/callback`
   - (Replace with your actual Railway URL)
4. Click **"Save"**

### 4.2 Add Test Users

1. Go to [OAuth Consent Screen](https://console.cloud.google.com/apis/credentials/consent)
2. Make sure app is in **"Testing"** mode
3. Scroll to **"Test users"** section
4. Click **"+ ADD USERS"**
5. Add all tester email addresses
6. Click **"Save"**

## Step 5: Add Credentials File

### Option A: Use Railway's File System (Recommended for Testing)

1. In Railway, go to your service
2. Click **"Settings"** → **"Source"**
3. Upload `credentials.json` as a file
4. Or use Railway's file system to create it

**Better Option: Use Environment Variable**

### Option B: Use Base64 Encoded Credentials (More Secure)

1. **Encode credentials.json:**
   ```bash
   # On macOS/Linux:
   base64 -i credentials.json > credentials_base64.txt
   
   # Or:
   cat credentials.json | base64 > credentials_base64.txt
   ```

2. **Add to Railway Variables:**
   - Variable name: `GOOGLE_CREDENTIALS_BASE64`
   - Value: (paste the base64 string)

3. **Update app to decode it:**
   - We'll need to modify the code to read from this variable

### Option C: Use Railway's Volume (For Production)

1. In Railway, add a **"Volume"**
2. Mount it to `/app/credentials.json`
3. Upload your `credentials.json` file

**For now, let's use Option A (simplest):**

1. In Railway dashboard, go to your service
2. Click **"Settings"**
3. You can add files through the Railway CLI or web interface

**Actually, the easiest way:**
- Keep `credentials.json` in your repo (but add it to `.gitignore` for local)
- Or use Railway's file upload feature
- Or we can modify the code to read from an environment variable

## Step 6: Deploy

### 6.1 Automatic Deployment

Railway will automatically deploy when you:
- Push to your main branch (if connected to GitHub)
- Or manually trigger a deployment

### 6.2 Manual Deployment

1. In Railway dashboard, click **"Deploy"**
2. Railway will:
   - Install dependencies
   - Build your app
   - Start the server

### 6.3 Check Deployment Logs

1. Click on your service
2. Go to **"Deployments"** tab
3. Click on the latest deployment
4. Check the logs for any errors

## Step 7: Test Your Deployment

### 7.1 Get Your Railway URL

1. In Railway dashboard, click on your service
2. Click **"Settings"** → **"Generate Domain"**
3. Copy your URL (e.g., `https://your-app.up.railway.app`)

### 7.2 Test the App

1. Open your Railway URL in a browser
2. Click **"Login"**
3. Authenticate with Google
4. Test the app functionality

## Step 8: Add Custom Domain (Optional)

1. In Railway, go to **"Settings"**
2. Click **"Custom Domain"**
3. Add your domain
4. Update DNS records as instructed
5. Update `OAUTH_REDIRECT_URI` with your custom domain

## Troubleshooting

### Deployment Fails

**Check logs:**
1. Go to **"Deployments"** tab
2. Click on failed deployment
3. Check error messages

**Common issues:**
- Missing environment variables
- `credentials.json` not found
- Port binding issues (should use `$PORT`)

### "Module not found" Errors

- Check `requirements.txt` has all dependencies
- Railway installs from `requirements.txt` automatically

### OAuth Errors

- Verify redirect URI matches exactly
- Check test users are added
- Ensure app is in "Testing" mode

### App Crashes

1. Check Railway logs
2. Verify all environment variables are set
3. Check `credentials.json` is accessible
4. Verify port is set to `$PORT` (Railway provides this)

## Railway CLI (Optional)

Install Railway CLI for easier management:

```bash
# Install
npm i -g @railway/cli

# Login
railway login

# Link to project
railway link

# View logs
railway logs

# Set variables
railway variables set GROQ_API_KEY=your_key
```

## Cost

Railway offers:
- **Free tier:** $5 credit/month
- **Hobby plan:** $5/month (if you exceed free tier)
- Check [railway.app/pricing](https://railway.app/pricing) for current pricing

## Next Steps

1. ✅ Deploy to Railway
2. ✅ Test with your own account
3. ✅ Add test users in Google Cloud Console
4. ✅ Share Railway URL with testers
5. ✅ Monitor usage and logs

## Security Notes

⚠️ **Important:**
- Don't commit `credentials.json` to public repos
- Use Railway's environment variables for secrets
- Consider using Railway's volume for credentials file
- For production, complete Google app verification
- Use HTTPS (Railway provides this automatically)

---

## Quick Checklist

- [ ] Code pushed to GitHub
- [ ] Railway project created
- [ ] Environment variables set in Railway
- [ ] Google OAuth redirect URI updated
- [ ] Test users added to Google Cloud Console
- [ ] `credentials.json` accessible in Railway
- [ ] App deployed successfully
- [ ] Tested login and basic functionality
- [ ] Shared URL with testers

---

**Need help?** Check Railway's [documentation](https://docs.railway.app) or their Discord community.

