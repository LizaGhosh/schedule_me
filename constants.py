"""Constants for the scheduling system."""

# Database configuration
DB_PATH = 'calendar_events.db'

# Google Calendar API configuration
CALENDAR_SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_API_VERSION = 'v3'
CALENDAR_ID = 'primary'
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.pickle'
OAUTH_PORT = 0

# Number of most recent events to retrieve
NUM_RECENT_EVENTS = 6

# Event display limits
MAX_EVENTS_FOR_QA = 20
MAX_EVENTS_FOR_RESPONSE = 20
MAX_EVENTS_FOR_PARSER = 10

# LLM parameters
LLM_TEMPERATURE = 0.3
LLM_MAX_TOKENS = 200
LLM_MODEL = "llama-3.1-8b-instant"

# LLM parameters for specific agents
INTENT_AGENT_TEMPERATURE = 0.1
INTENT_AGENT_MAX_TOKENS = 10
VALIDATION_AGENT_TEMPERATURE = 0.1
VALIDATION_AGENT_MAX_TOKENS = 100

# Voice transcription parameters
TRANSCRIPTION_TIMEOUT = 10
TRANSCRIPTION_PHRASE_TIME_LIMIT = 15
AMBIENT_NOISE_DURATION = 1

# ElevenLabs TTS configuration
ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice (default). Get voice IDs from https://elevenlabs.io/app/voices
ELEVENLABS_MODEL = "eleven_multilingual_v2"  # Free tier compatible model

