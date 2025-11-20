# OAUTH_REDIRECT_URI Setup Guide

## What is OAUTH_REDIRECT_URI?

This is the URL where Google redirects users after they authenticate. It must match **exactly** what's configured in Google Cloud Console.

## Step-by-Step Setup

### Step 1: Deploy to Railway First

1. Deploy your app to Railway (even without this variable set)
2. Railway will give you a URL like:
   - `https://your-app-name.up.railway.app`
   - Or `https://schedule-me-production.up.railway.app`
   - Or a custom domain if you set one up

### Step 2: Get Your Railway URL

After deployment, find your URL:

1. Go to Railway dashboard
2. Click on your service
3. Click **"Settings"** tab
4. Look for **"Domains"** or **"Generate Domain"**
5. Your URL will be shown there (e.g., `https://schedule-me-production.up.railway.app`)

### Step 3: Set OAUTH_REDIRECT_URI in Railway

1. Go to Railway → Your Service → **"Variables"** tab
2. Click **"+ New Variable"**
3. Add:
   - **Name:** `OAUTH_REDIRECT_URI`
   - **Value:** `https://YOUR-RAILWAY-URL/auth/callback`
   - Replace `YOUR-RAILWAY-URL` with your actual Railway domain
   
   **Example:**
   ```
   https://schedule-me-production.up.railway.app/auth/callback
   ```

4. Click **"Add"** or **"Save"**

### Step 4: Update Google Cloud Console

**CRITICAL:** You must also add this URL to Google Cloud Console:

1. Go to [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials)
2. Click on your **OAuth 2.0 Client ID**
3. Under **"Authorized redirect URIs"**, add:
   - `https://YOUR-RAILWAY-URL/auth/callback`
   - (Same URL as above)
4. Click **"Save"**

### Step 5: Wait and Test

1. Wait 5-10 minutes for changes to propagate
2. Try logging in to your Railway app
3. OAuth should work!

## Important Notes

⚠️ **The URL must match EXACTLY:**
- ✅ `https://your-app.up.railway.app/auth/callback` (correct)
- ❌ `https://your-app.up.railway.app/auth/callback/` (trailing slash - wrong!)
- ❌ `http://your-app.up.railway.app/auth/callback` (http instead of https - wrong!)

⚠️ **Both places must match:**
- Railway environment variable: `OAUTH_REDIRECT_URI`
- Google Cloud Console: Authorized redirect URIs

## Temporary Setup (Before You Have Railway URL)

If you need to set it before deployment:

1. **Option 1:** Leave it empty/unset initially
   - The app will use default: `http://127.0.0.1:5000/auth/callback`
   - Update it after you get Railway URL

2. **Option 2:** Use a placeholder
   - Set: `https://placeholder.up.railway.app/auth/callback`
   - Update it immediately after deployment

3. **Option 3:** Set it after first deployment
   - Deploy without it
   - Get your Railway URL
   - Add the variable
   - Update Google Cloud Console
   - Redeploy

## Quick Checklist

- [ ] Deployed app to Railway
- [ ] Got Railway URL (e.g., `https://your-app.up.railway.app`)
- [ ] Added `OAUTH_REDIRECT_URI` to Railway variables with full URL
- [ ] Added same URL to Google Cloud Console → Credentials → Authorized redirect URIs
- [ ] No trailing slashes
- [ ] Using `https://` not `http://`
- [ ] Waited 5-10 minutes for propagation
- [ ] Tested login

## Example

If your Railway URL is: `https://schedule-me-production.up.railway.app`

Then set:
- **Railway Variable:** `OAUTH_REDIRECT_URI` = `https://schedule-me-production.up.railway.app/auth/callback`
- **Google Cloud Console:** Add `https://schedule-me-production.up.railway.app/auth/callback` to Authorized redirect URIs

## Troubleshooting

### "Redirect URI mismatch" error:
- Check both URLs match exactly (Railway + Google Cloud Console)
- No trailing slashes
- Using `https://` not `http://`
- Wait 5-10 minutes after updating

### Can't find Railway URL:
- Check Railway dashboard → Settings → Domains
- Look in deployment logs
- Check service overview page

### OAuth not working:
- Verify URL is added in both places
- Check Railway logs for errors
- Ensure app is in "Testing" mode in Google Cloud Console
- Test users are added

