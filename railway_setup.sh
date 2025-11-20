#!/bin/bash
# Quick setup script for Railway deployment
# Run this to prepare your environment variables

echo "🚂 Railway Deployment Setup"
echo "============================"
echo ""

# Generate Flask secret key
FLASK_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(16))")
echo "Generated FLASK_SECRET_KEY: $FLASK_SECRET"
echo ""

echo "📋 Environment Variables to Add in Railway:"
echo "--------------------------------------------"
echo ""
echo "GROQ_API_KEY=your_groq_api_key_here"
echo "ELEVENLABS_API_KEY=your_elevenlabs_api_key_here"
echo "FLASK_SECRET_KEY=$FLASK_SECRET"
echo "OAUTH_REDIRECT_URI=https://your-app-name.up.railway.app/auth/callback"
echo ""
echo "⚠️  Remember to:"
echo "   1. Replace 'your-app-name' with your actual Railway domain"
echo "   2. Update Google Cloud Console with the redirect URI"
echo "   3. Add test users in Google Cloud Console"
echo ""

