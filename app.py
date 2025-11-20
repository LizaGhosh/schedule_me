"""Flask web application for calendar scheduling."""
from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from flask_cors import CORS
from auth_manager import AuthManager, get_user_calendar_service
import threading
import queue
import json
import os
import tempfile
import secrets
import constants

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(16))
# Configure session to persist
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours
CORS(app, supports_credentials=True)

# Auth manager for OAuth flow (lazy initialization)
auth_manager = None

def get_auth_manager():
    """Get or create auth manager instance."""
    global auth_manager
    if auth_manager is None:
        auth_manager = AuthManager()
    return auth_manager

# Per-user orchestrators (stored in session)
orchestrators = {}

def init_orchestrator():
    """Initialize orchestrator for current user session (lazy initialization)."""
    try:
        print(f"DEBUG: init_orchestrator() called")
        # Get user's calendar service
        calendar_service = get_user_calendar_service()
        if not calendar_service:
            print(f"ERROR: Cannot initialize orchestrator - calendar service is None")
            print(f"Session has credentials: {'credentials' in session}")
            if 'credentials' in session:
                print(f"Credentials keys: {list(session['credentials'].keys())}")
            return None
        
        print(f"DEBUG: Calendar service obtained, proceeding with orchestrator initialization...")
        
        # Use session ID as key for per-user orchestrators
        session_id = session.get('session_id')
        if not session_id:
            session_id = secrets.token_hex(16)
            session['session_id'] = session_id
        
        # Check if orchestrator already exists for this user
        if session_id in orchestrators:
            print(f"DEBUG: Using existing orchestrator for session {session_id}")
            return orchestrators[session_id]
        
        # Create new orchestrator for this user
        # For web app, use a default timezone or get from calendar
        # We'll initialize without timezone prompt for web
        from timezone_manager import TimezoneManager
        import pytz
        
        # Get calendar timezone
        try:
            print(f"DEBUG: Getting calendar timezone...")
            calendar_info = calendar_service.calendars().get(calendarId=constants.CALENDAR_ID).execute()
            calendar_tz = calendar_info.get('timeZone', 'UTC')
            print(f"DEBUG: Calendar timezone: {calendar_tz}")
            tz_manager = TimezoneManager(calendar_tz)
        except Exception as e:
            print(f"WARNING: Failed to get calendar timezone: {e}, using UTC")
            import traceback
            traceback.print_exc()
            tz_manager = TimezoneManager('UTC')
        
        # Create orchestrator components manually to avoid interactive prompts
        # Note: TranscriptionAgent was removed - not needed for web app
        from agents.intent_agent import IntentAgent
        from agents.action_parser_agent import ActionParserAgent
        from agents.validation_agent import ValidationAgent
        from agents.calendar_agent import CalendarAgent
        from agents.calendar_management_agent import CalendarManagementAgent
        from agents.qa_agent import QAAgent
        from agents.sql_agent import SQLAgent
        from agents.database_agent import DatabaseAgent
        from agents.response_agent import ResponseAgent
        from agents.tts_agent import TTSAgent
        
        qa_agent = QAAgent()
        try:
            tts_agent = TTSAgent() if os.getenv('ELEVENLABS_API_KEY') else None
        except Exception as e:
            print(f"Warning: TTS agent initialization failed: {e}")
            tts_agent = None
        # Per-user database path
        user_db_path = f"{constants.DB_PATH}.{session_id}"
        
        orchestrator = type('Orchestrator', (), {
            'timezone_manager': tz_manager,
            'intent_agent': IntentAgent(),
            'action_parser_agent': ActionParserAgent(),
            'validation_agent': ValidationAgent(),
            'calendar_agent': CalendarAgent(calendar_service, user_db_path, tz_manager),
            'calendar_management_agent': CalendarManagementAgent(calendar_service, tz_manager),
            'qa_agent': qa_agent,
            'sql_agent': SQLAgent(user_db_path, qa_agent, tz_manager),
            'database_agent': DatabaseAgent(user_db_path, tz_manager),
            'response_agent': ResponseAgent(),
            'tts_agent': tts_agent,
        })()
        
        # Initialize database
        print(f"DEBUG: Initializing database at {user_db_path}...")
        from database import CalendarDatabase
        db = CalendarDatabase(user_db_path)
        db.clear_all_events()
        print(f"DEBUG: Fetching events and storing in DB...")
        orchestrator.calendar_agent.get_all_events(store_in_db=True)
        print(f"DEBUG: Events fetched and stored")
        
        # Store orchestrator for this user
        orchestrators[session_id] = orchestrator
        print(f"DEBUG: Orchestrator stored for session {session_id}")
    
        result = orchestrators.get(session_id)
        print(f"DEBUG: Returning orchestrator: {'Found' if result else 'None'}")
        return result
    except Exception as e:
        print(f"ERROR in init_orchestrator(): {e}")
        import traceback
        traceback.print_exc()
        return None

# Queue for voice input/output
voice_queue = queue.Queue()
response_queue = queue.Queue()


@app.before_request
def log_request_info():
    """Log all incoming requests for debugging."""
    if request.path.startswith('/auth/callback') or request.path.startswith('/login'):
        print(f"\n{'='*60}")
        print(f"REQUEST: {request.method} {request.path}")
        print(f"URL: {request.url}")
        print(f"Args: {dict(request.args)}")
        print(f"{'='*60}\n")

@app.route('/')
def index():
    """Main page."""
    # Check if user is authenticated
    if 'credentials' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')


@app.route('/login')
def login():
    """Initiate OAuth login flow."""
    try:
        auth_mgr = get_auth_manager()
        authorization_url, state = auth_mgr.get_authorization_url()
        session['oauth_state'] = state
        print(f"Redirecting to: {authorization_url}")
        return redirect(authorization_url)
    except Exception as e:
        print(f"Error in login: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Login failed: {str(e)}'}), 500


@app.route('/auth/callback')
def oauth_callback():
    """Handle OAuth callback."""
    try:
        print(f"\n=== OAuth Callback Received ===")
        print(f"Request URL: {request.url}")
        print(f"Request args: {dict(request.args)}")
        print(f"Request method: {request.method}")
        print(f"===============================\n")
        
        # Check for error from Google
        error = request.args.get('error')
        if error:
            error_description = request.args.get('error_description', 'Unknown error')
            error_uri = request.args.get('error_uri', '')
            
            # Log all error details for debugging
            print(f"=== OAuth Error Details ===")
            print(f"Error: {error}")
            print(f"Description: {error_description}")
            print(f"Error URI: {error_uri}")
            print(f"All request args: {dict(request.args)}")
            print(f"===========================")
            
            # Decode URL-encoded error description
            from urllib.parse import unquote
            error_description_decoded = unquote(error_description.replace('+', ' '))
            
            # Provide specific guidance based on error type
            guidance = ""
            if 'access_denied' in error or 'consent' in error_description.lower():
                guidance = f"""
                <h3>Access Denied Error</h3>
                <p><strong>Important:</strong> Even if you added the user as a test user, the app must be in "Testing" mode (not "Published") for test users to work.</p>
                
                <h4>Step-by-Step Fix:</h4>
                <ol>
                    <li><strong>Go to OAuth Consent Screen:</strong> <a href="https://console.cloud.google.com/apis/credentials/consent" target="_blank">Click here</a></li>
                    <li><strong>Check Publishing Status:</strong> Look at the top of the page - does it say "In production" or "Testing"?</li>
                    <li><strong>If it says "In production":</strong>
                        <ul>
                            <li>Click the "<strong>BACK TO TESTING</strong>" button (usually at the top right)</li>
                            <li>Confirm the change</li>
                        </ul>
                    </li>
                    <li><strong>Add Test Users:</strong>
                        <ul>
                            <li>Scroll to "Test users" section</li>
                            <li>Click "+ ADD USERS"</li>
                            <li>Add the email address of the user trying to log in</li>
                            <li>Click "ADD"</li>
                        </ul>
                    </li>
                    <li><strong>Save all changes</strong></li>
                    <li><strong>Wait 5-10 minutes</strong> for changes to propagate</li>
                    <li><strong>Clear browser cache/cookies</strong> or use incognito mode</li>
                    <li><strong>Try logging in again</strong></li>
                </ol>
                
                <h4>Common Issues:</h4>
                <ul>
                    <li>❌ App is "Published" instead of "Testing" - test users only work in Testing mode</li>
                    <li>❌ Email not added exactly as it appears in Google account</li>
                    <li>❌ Changes not saved or not propagated yet (wait a few minutes)</li>
                    <li>❌ Browser cache showing old OAuth state</li>
                </ul>
                
                <h4>If Still Not Working:</h4>
                <p>Check the server logs above for the exact error message. The error description will tell you exactly what Google is rejecting.</p>
                """
            elif 'redirect_uri_mismatch' in error_description.lower():
                guidance = """
                <h3>Redirect URI Mismatch:</h3>
                <p>The redirect URI in your app doesn't match Google Cloud Console settings.</p>
                <p><strong>Fix:</strong></p>
                <ol>
                    <li>Go to <a href="https://console.cloud.google.com/apis/credentials" target="_blank">Credentials</a></li>
                    <li>Click on your OAuth 2.0 Client ID</li>
                    <li>Under "Authorized redirect URIs", ensure <code>http://localhost:5000/auth/callback</code> is listed</li>
                    <li>Save changes</li>
                </ol>
                """
            
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Authentication Error</title>
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 50px auto; padding: 20px; line-height: 1.6; }}
                    h2 {{ color: #d32f2f; }}
                    h3 {{ color: #1976d2; margin-top: 30px; }}
                    h4 {{ color: #555; margin-top: 20px; }}
                    code {{ background: #f5f5f5; padding: 2px 6px; border-radius: 3px; font-family: monospace; }}
                    a {{ color: #1976d2; text-decoration: none; }}
                    a:hover {{ text-decoration: underline; }}
                    ol, ul {{ margin: 10px 0; padding-left: 30px; }}
                    li {{ margin: 8px 0; }}
                    .error-box {{ background: #ffebee; border-left: 4px solid #d32f2f; padding: 15px; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <h2>🔒 Authentication Error</h2>
                <div class="error-box">
                    <p><strong>Error Code:</strong> <code>{error}</code></p>
                    <p><strong>Description:</strong> {error_description_decoded}</p>
                    {f'<p><strong>Error URI:</strong> <a href="{error_uri}" target="_blank">{error_uri}</a></p>' if error_uri else ''}
                </div>
                {guidance if guidance else '<p>Please check the server logs for more details.</p>'}
                <p style="margin-top: 30px;"><a href="/login">← Try again</a></p>
            </body>
            </html>
            """, 403
        
        # Verify state
        state = session.get('oauth_state')
        received_state = request.args.get('state')
        print(f"State verification - Session: {state}, Received: {received_state}")
        if not state or received_state != state:
            print(f"ERROR: Invalid state parameter")
            return jsonify({'error': 'Invalid state parameter'}), 400
        
        # Get authorization code
        code = request.args.get('code')
        print(f"Authorization code received: {code[:20] + '...' if code else 'None'}")
        if not code:
            print(f"ERROR: No authorization code provided")
            return jsonify({'error': 'No authorization code provided'}), 400
        
        print(f"Attempting to exchange code for credentials...")
        
        # Exchange code for credentials
        print(f"Exchanging authorization code for credentials...")
        try:
            auth_mgr = get_auth_manager()
            credentials = auth_mgr.get_credentials_from_code(code)
            print(f"✓ Credentials obtained successfully")
        except Exception as e:
            print(f"✗ ERROR exchanging code for credentials: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'Failed to get credentials: {str(e)}'}), 500
        
        # Store credentials in session
        print(f"Storing credentials in session...")
        session.permanent = True  # Make session persistent
        session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        print(f"✓ Credentials stored. Session ID: {session.get('session_id', 'NOT SET')}")
        print(f"Credentials keys: {list(session['credentials'].keys())}")
        print(f"Session permanent: {session.permanent}")
        
        # Clear OAuth state
        session.pop('oauth_state', None)
        
        return redirect(url_for('index'))
    except Exception as e:
        print(f"OAuth callback error: {e}")
        import traceback
        traceback.print_exc()
        return f"""
        <html>
            <body>
                <h2>Authentication Failed</h2>
                <p><strong>Error:</strong> {str(e)}</p>
                <p><a href="/login">Try again</a></p>
            </body>
        </html>
        """, 500


@app.route('/logout')
def logout():
    """Logout user and clear session."""
    session_id = session.get('session_id')
    if session_id and session_id in orchestrators:
        del orchestrators[session_id]
    session.clear()
    return redirect(url_for('login'))


@app.route('/api/auth/status')
def auth_status():
    """Check authentication status."""
    return jsonify({
        'authenticated': 'credentials' in session,
        'has_calendar_access': get_user_calendar_service() is not None
    })


@app.route('/api/events', methods=['GET'])
def get_events():
    """Get all calendar events."""
    try:
        orch = init_orchestrator()
        if not orch:
            return jsonify({'success': False, 'error': 'Not authenticated. Please log in.'}), 401
        
        result = orch.calendar_agent.get_all_events(store_in_db=False)
        events = result.get('events', []) if result and result.get('success') else []
        
        # Format events for frontend
        formatted_events = []
        for event in events:
            formatted_events.append({
                'id': event.get('id'),
                'summary': event.get('summary', 'No title'),
                'start': event.get('start').isoformat() if event.get('start') else None,
                'end': event.get('end').isoformat() if event.get('end') else None,
                'location': event.get('location', ''),
                'description': event.get('description', '')
            })
        
        return jsonify({'success': True, 'events': formatted_events})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/query', methods=['POST'])
def handle_query():
    """Handle user query (voice or text)."""
    try:
        data = request.json
        user_input = data.get('query', '').strip()
        
        if not user_input:
            return jsonify({'success': False, 'error': 'Empty query'}), 400
        
        # Initialize orchestrator if needed
        print(f"DEBUG: /api/query - Initializing orchestrator...")
        orch = init_orchestrator()
        if not orch:
            print(f"ERROR: /api/query - Orchestrator is None, returning 401")
            return jsonify({'success': False, 'error': 'Not authenticated. Please log in.'}), 401
        print(f"DEBUG: /api/query - Orchestrator initialized successfully")
        
        # Process query through orchestrator
        # This is a simplified version - in production, you'd want async handling
        intent = orch.intent_agent.identify_intent(user_input)
        
        response_text = ""
        events = []
        
        if intent == 'query':
            result = orch.calendar_agent.get_all_events(store_in_db=False)
            events_data = result.get('events', []) if result and result.get('success') else []
            
            sql_query = orch.sql_agent.text_to_sql(user_input, events=events_data)
            
            if sql_query:
                events = orch.database_agent.execute_query(sql_query, print_raw=False)
                response_text = orch.response_agent.generate_response(user_input, events)
            else:
                response_text = orch.qa_agent.answer(user_input, events_data)
        
        elif intent == 'create':
            # Get current date for context
            if orch.timezone_manager:
                current_date = orch.timezone_manager.now_in_user_tz().strftime('%Y-%m-%d')
            else:
                from datetime import datetime
                current_date = datetime.now().strftime('%Y-%m-%d')
            
            params = orch.action_parser_agent.parse_create(user_input, current_date=current_date)
            
            if 'error' not in params and 'start_time' in params and 'end_time' in params:
                from datetime import datetime
                start_dt = datetime.strptime(params['start_time'], '%Y-%m-%d %H:%M')
                end_dt = datetime.strptime(params['end_time'], '%Y-%m-%d %H:%M')
                
                if orch.timezone_manager:
                    start_dt = orch.timezone_manager.user_timezone.localize(start_dt)
                    end_dt = orch.timezone_manager.user_timezone.localize(end_dt)
                
                # Check conflicts
                conflicts = orch.calendar_management_agent.check_conflicts(start_dt, end_dt)
                if conflicts:
                    proposed_event = {
                        'summary': params.get('summary', 'Event'),
                        'start_time': start_dt.strftime('%Y-%m-%d %I:%M %p'),
                        'end_time': end_dt.strftime('%Y-%m-%d %I:%M %p')
                    }
                    response_text = orch.action_parser_agent.generate_conflict_message(
                        user_input, proposed_event, conflicts
                    )
                else:
                    result = orch.calendar_management_agent.create_event(
                        summary=params.get('summary', 'Event'),
                        start_time=start_dt,
                        end_time=end_dt,
                        description=params.get('description', ''),
                        location=params.get('location', ''),
                        attendees=params.get('attendees', [])
                    )
                    
                    if result.get('success'):
                        # Refresh database
                        from database import CalendarDatabase
                        db = CalendarDatabase(orch.calendar_agent.db_path)
                        db.clear_all_events()
                        orch.calendar_agent.get_all_events(store_in_db=True)
                        response_text = result.get('message', 'Event created.')
                    else:
                        response_text = result.get('message', 'Failed to create event.')
            else:
                response_text = f"Error: {params.get('error', 'Could not parse request')}"
        
        elif intent == 'modify':
            # Get events for context
            result = orch.calendar_agent.get_all_events(store_in_db=False)
            events_data = result.get('events', []) if result and result.get('success') else []
            
            # Parse modify parameters
            params = orch.action_parser_agent.parse_modify(user_input, events_data)
            
            if 'error' in params:
                response_text = f"Error parsing request: {params['error']}"
            elif 'event_id' not in params:
                response_text = "Could not identify which event to modify."
            else:
                # Parse optional datetime strings
                from datetime import datetime
                start_dt = None
                end_dt = None
                
                if params.get('start_time'):
                    start_dt = datetime.strptime(params['start_time'], '%Y-%m-%d %H:%M')
                    if orch.timezone_manager:
                        start_dt = orch.timezone_manager.user_timezone.localize(start_dt)
                
                if params.get('end_time'):
                    end_dt = datetime.strptime(params['end_time'], '%Y-%m-%d %H:%M')
                    if orch.timezone_manager:
                        end_dt = orch.timezone_manager.user_timezone.localize(end_dt)
                
                # Check for conflicts (excluding the event being modified)
                if start_dt:
                    # If end_dt not provided, get original event duration
                    if not end_dt:
                        try:
                            import constants
                            event = orch.calendar_management_agent.service.events().get(
                                calendarId=constants.CALENDAR_ID, eventId=params['event_id']
                            ).execute()
                            original_start_str = event['start'].get('dateTime', event['start'].get('date'))
                            original_end_str = event['end'].get('dateTime', event['end'].get('date'))
                            
                            if 'T' in original_start_str:
                                original_start = datetime.fromisoformat(original_start_str.replace('Z', '+00:00'))
                                original_end = datetime.fromisoformat(original_end_str.replace('Z', '+00:00'))
                            else:
                                from datetime import timezone
                                original_start = datetime.fromisoformat(original_start_str).replace(tzinfo=timezone.utc)
                                original_end = datetime.fromisoformat(original_end_str).replace(tzinfo=timezone.utc)
                            
                            duration = original_end - original_start
                            end_dt = start_dt + duration
                        except:
                            pass
                    
                    if end_dt:
                        conflicts = orch.calendar_management_agent.check_conflicts(
                            start_dt, end_dt, exclude_event_id=params['event_id']
                        )
                        if conflicts:
                            proposed_event = {
                                'summary': params.get('summary', 'Event'),
                                'start_time': start_dt.strftime('%Y-%m-%d %I:%M %p'),
                                'end_time': end_dt.strftime('%Y-%m-%d %I:%M %p')
                            }
                            response_text = orch.action_parser_agent.generate_conflict_message(
                                user_input, proposed_event, conflicts
                            )
                        else:
                            # Modify event
                            result = orch.calendar_management_agent.modify_event(
                                event_id=params['event_id'],
                                summary=params.get('summary'),
                                start_time=start_dt,
                                end_time=end_dt,
                                description=params.get('description'),
                                location=params.get('location'),
                                attendees=params.get('attendees')
                            )
                            
                            if result.get('success'):
                                # Refresh database
                                from database import CalendarDatabase
                                db = CalendarDatabase(orch.calendar_agent.db_path)
                                db.clear_all_events()
                                orch.calendar_agent.get_all_events(store_in_db=True)
                                response_text = result.get('message', 'Event modified.')
                            else:
                                response_text = result.get('message', 'Failed to modify event.')
                    else:
                        response_text = "Error: Could not determine end time for modification."
                else:
                    # Modify event without time change
                    result = orch.calendar_management_agent.modify_event(
                        event_id=params['event_id'],
                        summary=params.get('summary'),
                        start_time=start_dt,
                        end_time=end_dt,
                        description=params.get('description'),
                        location=params.get('location'),
                        attendees=params.get('attendees')
                    )
                    
                    if result.get('success'):
                        # Refresh database
                        from database import CalendarDatabase
                        db = CalendarDatabase(orch.calendar_agent.db_path)
                        db.clear_all_events()
                        orch.calendar_agent.get_all_events(store_in_db=True)
                        response_text = result.get('message', 'Event modified.')
                    else:
                        response_text = result.get('message', 'Failed to modify event.')
        
        elif intent == 'cancel':
            # Get events for context
            result = orch.calendar_agent.get_all_events(store_in_db=False)
            events_data = result.get('events', []) if result and result.get('success') else []
            
            # Parse cancel parameters
            params = orch.action_parser_agent.parse_cancel(user_input, events_data)
            
            if 'error' in params:
                response_text = f"Error parsing request: {params['error']}"
            elif 'event_id' not in params:
                response_text = "Could not identify which event to cancel."
            else:
                # Cancel event
                result = orch.calendar_management_agent.cancel_event(params['event_id'])
                
                if result.get('success'):
                    # Refresh database
                    from database import CalendarDatabase
                    db = CalendarDatabase(orch.calendar_agent.db_path)
                    db.clear_all_events()
                    orch.calendar_agent.get_all_events(store_in_db=True)
                    response_text = result.get('message', 'Event cancelled.')
                else:
                    response_text = result.get('message', 'Failed to cancel event.')
        
        elif intent == 'quit':
            response_text = "Goodbye!"
        
        # Format events for response
        formatted_events = []
        for event in events:
            formatted_events.append({
                'id': event.get('id'),
                'summary': event.get('summary', 'No title'),
                'start': event.get('start').isoformat() if event.get('start') else None,
                'end': event.get('end').isoformat() if event.get('end') else None,
                'location': event.get('location', ''),
            })
        
        # Reload events if modification was made
        if intent in ['create', 'modify', 'cancel']:
            try:
                result = orch.calendar_agent.get_all_events(store_in_db=False)
                all_events = result.get('events', []) if result and result.get('success') else []
                formatted_events = []
                for event in all_events:
                    formatted_events.append({
                        'id': event.get('id'),
                        'summary': event.get('summary', 'No title'),
                        'start': event.get('start').isoformat() if event.get('start') else None,
                        'end': event.get('end').isoformat() if event.get('end') else None,
                        'location': event.get('location', ''),
                    })
            except:
                pass
        
        return jsonify({
            'success': True,
            'response': response_text,
            'intent': intent,
            'events': formatted_events
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    """Generate audio from text using ElevenLabs."""
    try:
        data = request.json
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({'success': False, 'error': 'No text provided'}), 400
        
        orch = init_orchestrator()
        
        if not orch.tts_agent:
            print("TTS agent not available")
            return jsonify({'success': False, 'error': 'TTS not configured. Please set ELEVENLABS_API_KEY in .env file.'}), 503
        
        print(f"Generating audio for text: {text[:50]}...")
        
        # Generate audio
        try:
            audio_bytes = orch.tts_agent.generate_audio(text)
        except Exception as e:
            print(f"Exception in generate_audio: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': f'Failed to generate audio: {str(e)}'}), 500
        
        if not audio_bytes:
            print("Failed to generate audio bytes - returned None or empty")
            return jsonify({'success': False, 'error': 'Failed to generate audio (returned None)'}), 500
        
        if len(audio_bytes) == 0:
            print("Generated audio is empty (0 bytes)")
            return jsonify({'success': False, 'error': 'Generated audio is empty'}), 500
        
        print(f"Generated audio: {len(audio_bytes)} bytes")
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_file.write(audio_bytes)
        temp_file.close()
        
        # Return audio file
        return send_file(
            temp_file.name,
            mimetype='audio/mpeg',
            as_attachment=False,
            download_name='response.mp3'
        )
        
    except Exception as e:
        print(f"TTS error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    # Allow external connections for testing on local network
    # Set host='0.0.0.0' to allow connections from other devices on your network
    # For production, use a proper WSGI server like gunicorn
    host = os.getenv('FLASK_HOST', '127.0.0.1')  # Default to localhost only
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host=host, port=port, debug=debug)

