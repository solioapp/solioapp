# OAuth Setup Guide

This document describes how to obtain OAuth credentials for Google and Twitter/X login.

---

## Google OAuth 2.0

### 1. Create a Project in Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Name the project (e.g., "Solio") and create it

### 2. Configure OAuth Consent Screen

1. In the menu, select **APIs & Services** → **OAuth consent screen**
2. Select type "External" (for public use)
3. Fill in:
   - **App name**: Solio
   - **User support email**: your email
   - **Developer contact email**: your email
4. In "Scopes" add:
   - `email`
   - `profile`
   - `openid`
5. Save and continue

### 3. Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Select **Web application**
4. Fill in:
   - **Name**: Solio Web Client
   - **Authorized JavaScript origins**:
     - `http://localhost:5000` (for development)
     - `https://your-domain.com` (for production)
   - **Authorized redirect URIs**:
     - `http://localhost:5000/auth/google/callback` (for development)
     - `https://your-domain.com/auth/google/callback` (for production)
5. Click **Create**

### 4. Copy Credentials

After creation, you will see:
- **Client ID**: `xxxxx.apps.googleusercontent.com`
- **Client Secret**: `GOCSPX-xxxxx`

Add to your `.env` file:
```env
GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxx
```

---

## Twitter/X OAuth 2.0

### 1. Create a Developer Account

1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Sign in with your Twitter account
3. Apply for a Developer account (free for basic access)
4. Fill out the form describing your use case (crowdfunding platform, user authentication)

### 2. Create Project and App

1. After approval, go to **Developer Portal Dashboard**
2. Click **+ Create Project**
3. Fill in:
   - **Project name**: Solio
   - **Use case**: Select relevant option (e.g., "Building tools for Twitter users")
4. Create an app within the project

### 3. Configure OAuth 2.0

1. In app settings, go to **User authentication settings**
2. Click **Set up**
3. Select:
   - **App permissions**: Read (sufficient for login)
   - **Type of App**: Web App
   - **App info**:
     - **Callback URI / Redirect URL**:
       - `http://localhost:5000/auth/twitter/callback` (development)
       - `https://your-domain.com/auth/twitter/callback` (production)
     - **Website URL**: `https://your-domain.com` or `http://localhost:5000`
4. Save

### 4. Get Credentials

1. In the **Keys and tokens** section, find:
   - **OAuth 2.0 Client ID**
   - **OAuth 2.0 Client Secret**

Add to your `.env` file:
```env
TWITTER_CLIENT_ID=xxxxx
TWITTER_CLIENT_SECRET=xxxxx
```

### Note on Twitter API Tiers

Twitter has different access levels:
- **Free**: Limited requests, but sufficient for authentication
- **Basic** ($100/month): Higher limits
- **Pro**: Full access

For basic OAuth login, the Free tier is sufficient.

---

## Testing OAuth

### Local Development

For local testing you need:

1. Run the application: `python run.py`
2. Application runs at `http://localhost:5000`
3. OAuth callbacks must point to `localhost:5000`

### Production Deployment

For production deployment:

1. Set up a domain pointing to your server
2. Install SSL certificate (Let's Encrypt)
3. Update OAuth callbacks to your domain:
   - `https://your-domain.com/auth/google/callback`
   - `https://your-domain.com/auth/twitter/callback`
4. Update `.env` on the server

---

## Troubleshooting

### Google: "redirect_uri_mismatch"
- Check that the callback URL in Google Console exactly matches the URL in your application
- Make sure you're using the correct protocol (http vs https)

### Twitter: "Something went wrong"
- Check that the callback URL is exactly the same
- Make sure the app has OAuth 2.0 configured (not OAuth 1.0a)

### General Issues
- Wait a few minutes after changing settings (propagation may take time)
- Clear browser cookies and cache
- Check browser console for detailed error messages

---

## Security Recommendations

1. **Never commit the `.env` file to git**
2. **Use different credentials for development and production**
3. **Rotate secrets regularly**
4. **Limit permissions to the minimum required** (read-only for login)
5. **Monitor usage** in developer consoles
