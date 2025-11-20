"""Calendar agent for retrieving and storing calendar events."""
from typing import Dict, Any, List
from datetime import datetime, timezone
from googleapiclient.errors import HttpError
import sqlite3
import json
import sys
import os

# Add parent directory to path to import constants and database
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import constants
from database import CalendarDatabase


class CalendarAgent:
    """Agent for retrieving and storing calendar events."""
    
    def __init__(self, calendar_service, db_path: str = None, timezone_manager=None):
        """
        Initialize the calendar agent.
        
        Args:
            calendar_service: Google Calendar API service instance
            db_path: Path to SQLite database file (defaults to constants.DB_PATH)
            timezone_manager: TimezoneManager instance for timezone handling
        """
        if db_path is None:
            db_path = constants.DB_PATH
        self.service = calendar_service
        self.db_path = db_path
        self.timezone_manager = timezone_manager
        # Initialize database (creates schema if needed)
        CalendarDatabase(db_path)
    
    def get_all_events(self, store_in_db: bool = True) -> Dict[str, Any]:
        """
        Retrieve all calendar events (up to NUM_RECENT_EVENTS most recent).
        Optionally stores them in the database.
        
        Args:
            store_in_db: Whether to store events in database (default: True)
        
        Returns:
            Dictionary with events and metadata:
            - success: bool
            - events: List of event dictionaries
            - count: Number of events retrieved
            - message: Status message
        """
        try:
            # Get current time
            now = datetime.now(timezone.utc)
            time_min = now.isoformat().replace('+00:00', 'Z')
            
            # Query calendar for upcoming events
            events_result = self.service.events().list(
                calendarId=constants.CALENDAR_ID,
                timeMin=time_min,
                maxResults=constants.NUM_RECENT_EVENTS,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            
            events = events_result.get('items', [])

            
            # Process events into structured format
            processed_events = []
            for event in events:
                event_start = event['start'].get('dateTime', event['start'].get('date'))
                event_end = event['end'].get('dateTime', event['end'].get('date'))
                
                # Parse event times
                if 'T' in event_start:
                    event_start_dt = datetime.fromisoformat(event_start.replace('Z', '+00:00'))
                    event_end_dt = datetime.fromisoformat(event_end.replace('Z', '+00:00'))
                else:
                    # All-day event
                    event_start_dt = datetime.fromisoformat(event_start).replace(tzinfo=timezone.utc)
                    event_end_dt = datetime.fromisoformat(event_end).replace(tzinfo=timezone.utc)
                
                # Convert to user timezone if timezone_manager is available
                if self.timezone_manager:
                    event_start_dt = self.timezone_manager.convert_to_user_tz(event_start_dt)
                    event_end_dt = self.timezone_manager.convert_to_user_tz(event_end_dt)
                
                processed_event = {
                    'id': event.get('id'),
                    'summary': event.get('summary', 'No title'),
                    'description': event.get('description', ''),
                    'start': event_start_dt,
                    'end': event_end_dt,
                    'location': event.get('location', ''),
                    'attendees': [att.get('email', '') for att in event.get('attendees', [])],
                    'status': event.get('status', 'confirmed'),
                    'htmlLink': event.get('htmlLink', '')
                }
                
                processed_events.append(processed_event)

            # Store events in database if requested
            if store_in_db and processed_events:
                stored_count = self._store_events(processed_events)
                message = f'Retrieved {len(processed_events)} events and stored {stored_count} in database'
            else:
                message = f'Retrieved {len(processed_events)} events'
            
            return {
                'success': True,
                'events': processed_events,
                'count': len(processed_events),
                'message': message
            }
            
        except HttpError as error:
            return {
                'success': False,
                'events': [],
                'count': 0,
                'message': f'An error occurred: {error}',
                'error': str(error)
            }
        except Exception as e:
            return {
                'success': False,
                'events': [],
                'count': 0,
                'message': f'Could not retrieve events: {str(e)}',
                'error': str(e)
            }
    
    def _store_events(self, events: List[Dict[str, Any]]) -> int:
        """Store events in the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            count = 0
            if self.timezone_manager:
                now = self.timezone_manager.format_for_sqlite(self.timezone_manager.now_in_user_tz())
            else:
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            for event in events:
                # Convert to SQLite-friendly 24-hour format (YYYY-MM-DD HH:MM:SS) in UTC
                if isinstance(event['start'], datetime):
                    if self.timezone_manager:
                        start_time = self.timezone_manager.format_for_sqlite(event['start'])
                    else:
                        start_time = event['start'].strftime('%Y-%m-%d %H:%M:%S')
                else:
                    start_time = event['start']
                
                if isinstance(event['end'], datetime):
                    if self.timezone_manager:
                        end_time = self.timezone_manager.format_for_sqlite(event['end'])
                    else:
                        end_time = event['end'].strftime('%Y-%m-%d %H:%M:%S')
                else:
                    end_time = event['end']
                
                attendees_json = json.dumps(event.get('attendees', []))
                
                cursor.execute('''
                    INSERT OR REPLACE INTO events 
                    (id, summary, description, start_time, end_time, location, 
                     attendees, status, html_link, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 
                            COALESCE((SELECT created_at FROM events WHERE id = ?), ?), ?)
                ''', (
                    event.get('id'),
                    event.get('summary', ''),
                    event.get('description', ''),
                    start_time,
                    end_time,
                    event.get('location', ''),
                    attendees_json,
                    event.get('status', 'confirmed'),
                    event.get('htmlLink', ''),
                    event.get('id'),
                    now,
                    now
                ))
                count += 1
            
            conn.commit()
            conn.close()
            return count
            
        except Exception as e:
            print(f"Error storing events: {e}")
            return 0

