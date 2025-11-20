# Calendar Assistant

An intelligent, voice-enabled calendar scheduling assistant with a clean web interface.

## Features

- 🎤 Voice and text input
- 📅 Google Calendar integration
- 🤖 AI-powered natural language processing
- ⚡ Real-time event management
- 🎨 Clean, minimal interface

## Setup

### 1. Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Google Calendar API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Calendar API
4. Create OAuth 2.0 credentials (Web application, not Desktop app)
5. Add authorized redirect URI: `http://localhost:5000/auth/callback` (or your production URL)
6. Download credentials and save as `credentials.json` in the project root
7. Configure OAuth Consent Screen:
   - Add the Calendar API scope: `https://www.googleapis.com/auth/calendar`
   - **For Published Apps**: Google may require app verification for sensitive scopes
   - **Verification Process**: 
     - Go to OAuth Consent Screen → Publish status
     - If verification is required, you'll need to:
       - Provide app information (privacy policy, terms of service)
       - Complete security assessment (for sensitive scopes)
       - Wait for Google's review (can take days/weeks)
   - **Alternative**: Keep app in "Testing" mode and add users as test users (up to 100 users)

### 3. Environment Variables

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_groq_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
FLASK_SECRET_KEY=your_secret_key_here  # For session management (generate with: python -c "import secrets; print(secrets.token_hex(16))")
OAUTH_REDIRECT_URI=http://127.0.0.1:5000/auth/callback  # Must match Google Cloud Console settings EXACTLY
```

Get your API keys from:
- [Groq](https://console.groq.com/) - for LLM functionality
- [ElevenLabs](https://elevenlabs.io/) - for text-to-speech (optional)

## Running the Application

### Web Interface (Recommended)

**For local use only:**
```bash
python app.py
```
Then open your browser to `http://localhost:5000`

**For testing on local network (allow other devices to connect):**
```bash
# Set environment variable to allow external connections
export FLASK_HOST=0.0.0.0
python app.py
```
Then share `http://YOUR_IP:5000` with testers on the same network.

**Note:** See `TESTING_GUIDE.md` for detailed instructions on sharing the app with testers.

### Command Line Interface

```bash
python scheduler.py
```

## Usage

### Web Interface

1. Open the web interface in your browser
2. Type or speak your query:
   - "What events do I have today?"
   - "Schedule a meeting tomorrow at 3pm"
   - "Show me events for this week"
   - "Cancel my meeting with John"

### Voice Input

Click the microphone button to use voice input (requires browser support for Web Speech API).

## Project Structure

```
schedule_me/
├── app.py                 # Flask web application
├── scheduler.py           # CLI entry point
├── orchestrator.py        # Main orchestrator
├── calendar_manager.py    # Google Calendar API
├── constants.py           # Configuration constants
├── database.py            # Database schema
├── timezone_manager.py    # Timezone handling
├── agents/                # AI agents
│   ├── calendar_agent.py
│   ├── sql_agent.py
│   ├── intent_agent.py
│   └── ...
├── templates/             # HTML templates
│   └── index.html
├── static/                # Static files
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
└── requirements.txt
```

## Architecture

The application uses an agentic architecture:

- **Orchestrator**: Coordinates all agents
- **Intent Agent**: Identifies user intent (query/create/modify/cancel)
- **Action Parser**: Extracts parameters from natural language
- **Calendar Agent**: Retrieves events from Google Calendar
- **SQL Agent**: Generates SQL queries for event queries
- **Calendar Management Agent**: Creates/modifies/cancels events
- **Validation Agent**: Validates actions match user intent
- **Response Agent**: Generates conversational responses

## License

MIT
