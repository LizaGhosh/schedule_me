"""Handles Google Calendar OAuth authentication for web app users."""
import os
import pickle
from flask import session, redirect, request, url_for
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import constants


class AuthManager:
    """Manages OAuth authentication for web app users."""
    
    def __init__(self):
        self.client_secrets_file = constants.CREDENTIALS_FILE
        self.scopes = constants.CALENDAR_SCOPES
        
        # OAuth redirect URI (must match Google Cloud Console settings EXACTLY)
        # Note: Both localhost and 127.0.0.1 work, but must match Google Cloud Console exactly
        self.redirect_uri = os.getenv('OAUTH_REDIRECT_URI', 'http://127.0.0.1:5000/auth/callback')
        
        # Load client config from credentials file or environment variable
        import json
        import base64
        
        # Try to load from environment variable first (for Railway deployment)
        credentials_base64 = os.getenv('GOOGLE_CREDENTIALS_BASE64')
        if credentials_base64:
            # Decode from base64
            try:
                credentials_json = base64.b64decode(credentials_base64).decode('utf-8')
                client_config = json.loads(credentials_json)
                print("✓ Loaded credentials from GOOGLE_CREDENTIALS_BASE64 environment variable")
            except Exception as e:
                print(f"Error decoding GOOGLE_CREDENTIALS_BASE64: {e}")
                print("Falling back to credentials.json file...")
                # Fall back to file
                try:
                    with open(self.client_secrets_file, 'r') as f:
                        client_config = json.load(f)
                    print(f"✓ Loaded credentials from {self.client_secrets_file}")
                except FileNotFoundError:
                    raise ValueError(f"Could not load credentials: GOOGLE_CREDENTIALS_BASE64 decode failed and {self.client_secrets_file} not found")
        else:
            # Load from file (for local development)
            try:
                with open(self.client_secrets_file, 'r') as f:
                    client_config = json.load(f)
                print(f"✓ Loaded credentials from {self.client_secrets_file}")
            except FileNotFoundError:
                raise ValueError(f"Could not load credentials: GOOGLE_CREDENTIALS_BASE64 not set and {self.client_secrets_file} not found. Please set GOOGLE_CREDENTIALS_BASE64 environment variable or provide credentials.json file.")
        
        # Extract web app credentials
        if 'web' in client_config:
            client_info = client_config['web']
        elif 'installed' in client_config:
            # Fallback for desktop app credentials
            client_info = client_config['installed']
        else:
            raise ValueError("Invalid credentials file format")
        
        # Create OAuth flow with web app configuration
        self.flow = Flow.from_client_config(
            client_config={
                'web': {
                    'client_id': client_info['client_id'],
                    'client_secret': client_info['client_secret'],
                    'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                    'token_uri': 'https://oauth2.googleapis.com/token',
                    'redirect_uris': [self.redirect_uri]
                }
            },
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )
    
    def get_authorization_url(self):
        """Get the authorization URL for OAuth flow."""
        authorization_url, state = self.flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force consent screen to get refresh token
        )
        return authorization_url, state
    
    def get_credentials_from_code(self, code):
        """Exchange authorization code for credentials."""
        self.flow.fetch_token(code=code)
        credentials = self.flow.credentials
        return credentials
    
    def build_service(self, credentials):
        """Build Google Calendar service from credentials."""
        return build('calendar', constants.CALENDAR_API_VERSION, credentials=credentials)
    
    def refresh_credentials_if_needed(self, credentials):
        """Refresh credentials if expired."""
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        return credentials


def get_user_calendar_service():
    """Get calendar service for current user session."""
    if 'credentials' not in session:
        print(f"DEBUG: No credentials in session")
        return None
    
    try:
        # Load credentials from session
        creds_dict = session['credentials']
        print(f"DEBUG: Loading credentials from session. Keys: {list(creds_dict.keys())}")
        credentials = Credentials(**creds_dict)
        
        # Refresh if needed
        auth_manager = AuthManager()
        credentials = auth_manager.refresh_credentials_if_needed(credentials)
        
        # Update session with refreshed credentials
        session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        
        # Build and return service
        service = auth_manager.build_service(credentials)
        print(f"DEBUG: Calendar service built successfully")
        return service
    except Exception as e:
        print(f"ERROR getting calendar service: {e}")
        import traceback
        traceback.print_exc()
        return None

