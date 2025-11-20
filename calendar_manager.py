"""Simple calendar manager for Google Calendar API."""
import os
import pickle
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import constants


class CalendarManager:
    """Manages Google Calendar API connection."""
    
    def __init__(self, credentials_file: str = None, token_file: str = None):
        if credentials_file is None:
            credentials_file = constants.CREDENTIALS_FILE
        if token_file is None:
            token_file = constants.TOKEN_FILE
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Calendar API."""
        creds = None
        
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(f"Credentials file not found: {self.credentials_file}")
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, constants.CALENDAR_SCOPES)
                creds = flow.run_local_server(port=constants.OAUTH_PORT)
            
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('calendar', constants.CALENDAR_API_VERSION, credentials=creds)

