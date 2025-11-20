"""Simple orchestrator for calling agents."""
from agents.calendar_agent import CalendarAgent
from agents.sql_agent import SQLAgent
from agents.database_agent import DatabaseAgent
from agents.qa_agent import QAAgent
from agents.timezone_agent import TimezoneAgent
from agents.response_agent import ResponseAgent
from agents.intent_agent import IntentAgent
from agents.calendar_management_agent import CalendarManagementAgent
from agents.action_parser_agent import ActionParserAgent
from agents.validation_agent import ValidationAgent
from datetime import datetime
import constants


class Orchestrator:
    """Orchestrator that coordinates agents."""
    
    def __init__(self, calendar_service, db_path: str = None):
        """
        Initialize orchestrator with agents.
        
        Args:
            calendar_service: Google Calendar API service instance
            db_path: Path to SQLite database file (defaults to constants.DB_PATH)
        """
        if db_path is None:
            db_path = constants.DB_PATH
        
        # Get and print Google Calendar timezone
        try:
            calendar_info = calendar_service.calendars().get(calendarId=constants.CALENDAR_ID).execute()
            calendar_tz = calendar_info.get('timeZone', 'Unknown')
            print(f"\nYour Google Calendar timezone: {calendar_tz}")
        except Exception as e:
            print(f"\nCould not retrieve Google Calendar timezone: {e}")
            print("Defaulting to UTC")
        
        # Ask for timezone
        self.timezone_agent = TimezoneAgent()
        self.timezone_manager = self.timezone_agent.ask_user_timezone()
        
        self.intent_agent = IntentAgent()
        self.action_parser_agent = ActionParserAgent()
        self.validation_agent = ValidationAgent()
        self.calendar_agent = CalendarAgent(calendar_service, db_path, self.timezone_manager)
        self.calendar_management_agent = CalendarManagementAgent(calendar_service, self.timezone_manager)
        self.qa_agent = QAAgent()
        self.sql_agent = SQLAgent(db_path, qa_agent=self.qa_agent, timezone_manager=self.timezone_manager)
        self.database_agent = DatabaseAgent(db_path, self.timezone_manager)
        self.response_agent = ResponseAgent()
    
    def run(self):
        """Main run loop."""
        print("\nCalendar Assistant - Speak your request or type 'quit' to exit\n")
        
        # Clear database and repopulate with fresh events
        print("Syncing calendar events to database...")
        from database import CalendarDatabase
        db = CalendarDatabase(self.calendar_agent.db_path)
        db.clear_all_events()
        self.calendar_agent.get_all_events(store_in_db=True)
        print("Ready!\n")
        
        # Print structured database before user input
        print("=" * 60)
        print("DATABASE CONTENTS:")
        print("=" * 60)
        all_events = self.database_agent.execute_query("SELECT * FROM events ORDER BY start_time", print_raw=False)
        if all_events:
            for event in all_events:
                # Events are already in user timezone from database_agent
                start = event['start']
                end = event['end']
                print(f"ID: {event['id']}")
                print(f"  Summary: {event['summary']}")
                print(f"  Start: {start.strftime('%Y-%m-%d %I:%M %p')}")
                print(f"  End: {end.strftime('%Y-%m-%d %I:%M %p')}")
                print(f"  Location: {event.get('location', 'N/A')}")
                print(f"  Attendees: {', '.join(event.get('attendees', [])) if event.get('attendees') else 'None'}")
                print()
        else:
            print("No events in database.")
        print("=" * 60)
        print()
        
        while True:
            try:
                # Get voice input (for CLI - web app uses text input)
                try:
                    from agents.transcription_agent import TranscriptionAgent
                    if not hasattr(self, 'transcription_agent'):
                        self.transcription_agent = TranscriptionAgent()
                    user_input = self.transcription_agent.transcribe()
                except (ImportError, ModuleNotFoundError):
                    # Fallback to text input if transcription not available
                    user_input = input("\nEnter your query (or 'quit' to exit): ").strip()
                
                if not user_input:
                    continue
                
                # Identify user intent
                intent = self.intent_agent.identify_intent(user_input)
                
                if intent == 'quit':
                    print("Goodbye!")
                    break
                
                if intent == 'query':
                    # User wants information about events
                    result = self.calendar_agent.get_all_events(store_in_db=False)
                    events_data = result.get('events', []) if result and result.get('success') else []
                    
                    # Try SQL query
                    sql_query = self.sql_agent.text_to_sql(user_input, events=events_data)
                    
                    if sql_query:
                        # SQL succeeded, execute query
                        print(f"SQL Query: {sql_query}")
                        events = self.database_agent.execute_query(sql_query, print_raw=False)
                        
                        # Generate conversational response using LLM
                        response = self.response_agent.generate_response(user_input, events)
                        print(response)
                    # If sql_query is None, QA agent already handled it
                
                elif intent == 'create':
                    # Get current date for context
                    if self.timezone_manager:
                        current_date = self.timezone_manager.now_in_user_tz().strftime('%Y-%m-%d')
                    else:
                        current_date = datetime.now().strftime('%Y-%m-%d')
                    
                    # Parse create parameters
                    params = self.action_parser_agent.parse_create(user_input, current_date=current_date)
                    
                    if 'error' in params:
                        print(f"Error parsing request: {params['error']}")
                    elif 'start_time' not in params or 'end_time' not in params:
                        print(f"Error: Missing required parameters. Got: {list(params.keys())}")
                    else:
                        # Parse datetime strings
                        try:
                            print(f"Parsed params: {params}")
                            start_dt = datetime.strptime(params['start_time'], '%Y-%m-%d %H:%M')
                            end_dt = datetime.strptime(params['end_time'], '%Y-%m-%d %H:%M')
                            
                            print(f"Parsed start: {start_dt}, end: {end_dt}")
                            
                            # Localize to user timezone
                            if self.timezone_manager:
                                start_dt = self.timezone_manager.user_timezone.localize(start_dt)
                                end_dt = self.timezone_manager.user_timezone.localize(end_dt)
                            
                            print(f"After timezone: start={start_dt}, end={end_dt}")
                            
                            # Check for conflicts
                            conflicts = self.calendar_management_agent.check_conflicts(start_dt, end_dt)
                            if conflicts:
                                # Generate conflict message
                                proposed_event = {
                                    'summary': params.get('summary', 'Event'),
                                    'start_time': start_dt.strftime('%Y-%m-%d %I:%M %p') if hasattr(start_dt, 'strftime') else str(start_dt),
                                    'end_time': end_dt.strftime('%Y-%m-%d %I:%M %p') if hasattr(end_dt, 'strftime') else str(end_dt)
                                }
                                conflict_message = self.action_parser_agent.generate_conflict_message(
                                    user_input, proposed_event, conflicts
                                )
                                print(conflict_message)
                                continue
                            
                            # Create event
                            result = self.calendar_management_agent.create_event(
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
                                db = CalendarDatabase(self.calendar_agent.db_path)
                                db.clear_all_events()
                                self.calendar_agent.get_all_events(store_in_db=True)
                                
                                # Validate the creation
                                event_id = result.get('event_id')
                                if event_id:
                                    # Get the created event from database
                                    validation_events = self.database_agent.execute_query(
                                        f"SELECT * FROM events WHERE id = '{event_id}'", 
                                        print_raw=False
                                    )
                                    if validation_events:
                                        validation_result = self.validation_agent.validate(
                                            user_input, 'create', validation_events[0]
                                        )
                                        if not validation_result.get('valid', True):
                                            print(f"Validation failed: {validation_result.get('message', 'Action did not match user request')}")
                                            continue
                                
                                print(result.get('message', 'Event created.'))
                                print(f"Event ID: {result.get('event_id', 'N/A')}")
                            else:
                                print(result.get('message', 'Failed to create event.'))
                                if 'error' in result:
                                    print(f"Error details: {result['error']}")
                            
                        except Exception as e:
                            print(f"Error creating event: {e}")
                
                elif intent == 'modify':
                    # Get events for context
                    result = self.calendar_agent.get_all_events(store_in_db=False)
                    events_data = result.get('events', []) if result and result.get('success') else []
                    
                    # Parse modify parameters
                    params = self.action_parser_agent.parse_modify(user_input, events_data)
                    
                    if 'error' in params:
                        print(f"Error parsing request: {params['error']}")
                    elif 'event_id' not in params:
                        print("Could not identify which event to modify.")
                    else:
                        # Parse optional datetime strings
                        start_dt = None
                        end_dt = None
                        
                        if params.get('start_time'):
                            start_dt = datetime.strptime(params['start_time'], '%Y-%m-%d %H:%M')
                            if self.timezone_manager:
                                start_dt = self.timezone_manager.user_timezone.localize(start_dt)
                        
                        if params.get('end_time'):
                            end_dt = datetime.strptime(params['end_time'], '%Y-%m-%d %H:%M')
                            if self.timezone_manager:
                                end_dt = self.timezone_manager.user_timezone.localize(end_dt)
                        
                        # Check for conflicts (excluding the event being modified)
                        if start_dt:
                            # If end_dt not provided, get original event duration
                            if not end_dt:
                                try:
                                    from googleapiclient.discovery import build
                                    event = self.calendar_management_agent.service.events().get(
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
                                    # If can't get original event, skip conflict check
                                    pass
                            
                            if end_dt:
                                conflicts = self.calendar_management_agent.check_conflicts(
                                    start_dt, end_dt, exclude_event_id=params['event_id']
                                )
                                if conflicts:
                                    # Generate conflict message
                                    proposed_event = {
                                        'summary': params.get('summary', 'Event'),
                                        'start_time': start_dt.strftime('%Y-%m-%d %I:%M %p') if hasattr(start_dt, 'strftime') else str(start_dt),
                                        'end_time': end_dt.strftime('%Y-%m-%d %I:%M %p') if hasattr(end_dt, 'strftime') else str(end_dt)
                                    }
                                    conflict_message = self.action_parser_agent.generate_conflict_message(
                                        user_input, proposed_event, conflicts
                                    )
                                    print(conflict_message)
                                    continue
                        
                        # Modify event
                        result = self.calendar_management_agent.modify_event(
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
                            db = CalendarDatabase(self.calendar_agent.db_path)
                            db.clear_all_events()
                            self.calendar_agent.get_all_events(store_in_db=True)
                            
                            # Validate the modification
                            event_id = params['event_id']
                            validation_events = self.database_agent.execute_query(
                                f"SELECT * FROM events WHERE id = '{event_id}'", 
                                print_raw=False
                            )
                            if validation_events:
                                validation_result = self.validation_agent.validate(
                                    user_input, 'modify', validation_events[0]
                                )
                                if not validation_result.get('valid', True):
                                    print(f"Validation failed: {validation_result.get('message', 'Action did not match user request')}")
                                    continue
                            
                            print(result.get('message', 'Event modified.'))
                        else:
                            print(result.get('message', 'Failed to modify event.'))
                
                elif intent == 'cancel':
                    # Get events for context
                    result = self.calendar_agent.get_all_events(store_in_db=False)
                    events_data = result.get('events', []) if result and result.get('success') else []
                    
                    # Parse cancel parameters
                    params = self.action_parser_agent.parse_cancel(user_input, events_data)
                    
                    print(f"Cancel params: {params}")
                    
                    if 'error' in params:
                        print(f"Error parsing request: {params['error']}")
                    elif 'event_id' not in params:
                        print("Could not identify which event to cancel.")
                    else:
                        print(f"Attempting to cancel event: {params['event_id']}")
                        # Cancel event
                        result = self.calendar_management_agent.cancel_event(params['event_id'])
                        
                        if result.get('success'):
                            # Refresh database
                            from database import CalendarDatabase
                            db = CalendarDatabase(self.calendar_agent.db_path)
                            db.clear_all_events()
                            self.calendar_agent.get_all_events(store_in_db=True)
                            
                            # Validate the cancellation (event should not exist)
                            event_id = params['event_id']
                            validation_events = self.database_agent.execute_query(
                                f"SELECT * FROM events WHERE id = '{event_id}'", 
                                print_raw=False
                            )
                            validation_result = self.validation_agent.validate(
                                user_input, 'cancel', validation_events[0] if validation_events else None
                            )
                            if not validation_result.get('valid', True):
                                print(f"Validation failed: {validation_result.get('message', 'Action did not match user request')}")
                                continue
                            
                            print(result.get('message', 'Event cancelled.'))
                        else:
                            print(result.get('message', 'Failed to cancel event.'))
                            if 'error' in result:
                                print(f"Error details: {result['error']}")
                
                else:
                    # Unknown intent, default to query
                    result = self.calendar_agent.get_all_events(store_in_db=False)
                    events_data = result.get('events', []) if result and result.get('success') else []
                    sql_query = self.sql_agent.text_to_sql(user_input, events=events_data)
                    if sql_query:
                        events = self.database_agent.execute_query(sql_query, print_raw=False)
                        response = self.response_agent.generate_response(user_input, events)
                        print(response)
                
                print()  # Blank line
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}\n")

