# Railway Environment Variables Setup

## How Railway Accesses Your API Keys

Railway uses **Environment Variables** to securely store and access your API keys. These are set in the Railway dashboard and are automatically available to your app at runtime.

## Step-by-Step: Adding Environment Variables in Railway

### 1. Go to Your Railway Project

1. Log in to [railway.app](https://railway.app)
2. Click on your project
3. Click on your service (the app you're deploying)

### 2. Navigate to Variables Tab

1. In your service, click on the **"Variables"** tab (or **"Settings"** → **"Variables"**)
2. You'll see a list of environment variables (initially empty)

### 3. Add Each Environment Variable

Click **"+ New Variable"** for each of these:

#### Required Variables:

**1. GROQ_API_KEY**
- **Name:** `GROQ_API_KEY`
- **Value:** Your Groq API key (get from https://console.groq.com/)
- Click **"Add"**

**2. ELEVENLABS_API_KEY**
- **Name:** `ELEVENLABS_API_KEY`
- **Value:** Your ElevenLabs API key (get from https://elevenlabs.io/)
- Click **"Add"**

**3. FLASK_SECRET_KEY**
- **Name:** `FLASK_SECRET_KEY`
- **Value:** Generate with: `python -c "import secrets; print(secrets.token_hex(16))"`
- Click **"Add"**

**4. OAUTH_REDIRECT_URI**
- **Name:** `OAUTH_REDIRECT_URI`
- **Value:** `https://your-app-name.up.railway.app/auth/callback`
- ⚠️ **Important:** Replace `your-app-name` with your actual Railway domain (you'll get this after first deployment)
- Click **"Add"**

### 4. How Your App Accesses These

Your app automatically reads these using `os.getenv()`:

```python
# In your code (already set up):
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
OAUTH_REDIRECT_URI = os.getenv('OAUTH_REDIRECT_URI')
```

Railway automatically injects these into your app's environment when it runs.

## Visual Guide

```
Railway Dashboard
├── Your Project
    └── Your Service
        ├── Variables Tab  ← Click here
        │   ├── + New Variable
        │   │   ├── Name: GROQ_API_KEY
        │   │   └── Value: sk-...
        │   ├── + New Variable
        │   │   ├── Name: ELEVENLABS_API_KEY
        │   │   └── Value: ...
        │   └── + New Variable
        │       ├── Name: FLASK_SECRET_KEY
        │       └── Value: ...
        └── Deployments
```

## Security Notes

✅ **Safe:**
- Environment variables in Railway are encrypted
- They're only accessible to your app at runtime
- They're not visible in logs or code

❌ **Never:**
- Commit API keys to Git
- Share API keys in screenshots
- Hardcode keys in your code

## Updating Variables

1. Go to Variables tab
2. Click on the variable you want to update
3. Edit the value
4. Click **"Save"**
5. Railway will automatically redeploy your app

## Getting Your API Keys

### Groq API Key:
1. Go to https://console.groq.com/
2. Sign up/login
3. Go to API Keys section
4. Create a new API key
5. Copy it (you'll only see it once!)

### ElevenLabs API Key:
1. Go to https://elevenlabs.io/
2. Sign up/login
3. Go to Profile → API Keys
4. Create a new API key
5. Copy it

### Flask Secret Key:
Run this command locally:
```bash
python -c "import secrets; print(secrets.token_hex(16))"
```
Copy the output and use it as `FLASK_SECRET_KEY`

## Troubleshooting

### "API key not found" errors:
- Check variable names match exactly (case-sensitive!)
- Verify variables are added in Railway
- Check spelling: `GROQ_API_KEY` not `GROQ_API` or `GROQ_KEY`

### Variables not updating:
- Save the variable in Railway
- Wait for automatic redeploy (or trigger manual deploy)
- Check Railway logs for errors

### Can't see variables:
- Make sure you're in the correct service
- Check you have access to the project
- Try refreshing the page

## Quick Checklist

- [ ] `GROQ_API_KEY` added
- [ ] `ELEVENLABS_API_KEY` added
- [ ] `FLASK_SECRET_KEY` added (generated securely)
- [ ] `OAUTH_REDIRECT_URI` added (with actual Railway URL)
- [ ] All variable names match exactly (case-sensitive)
- [ ] No extra spaces in variable names or values
- [ ] Variables saved successfully

---

**Pro Tip:** You can also set variables using Railway CLI:
```bash
railway variables set GROQ_API_KEY=your_key_here
```

