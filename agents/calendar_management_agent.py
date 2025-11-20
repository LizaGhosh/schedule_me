"""Agent for creating, modifying, and canceling calendar events."""
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from googleapiclient.errors import HttpError
import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import constants


class CalendarManagementAgent:
    """Agent for managing calendar events (create, modify, cancel)."""
    
    def __init__(self, calendar_service, timezone_manager=None):
        """
        Initialize calendar management agent.
        
        Args:
            calendar_service: Google Calendar API service instance
            timezone_manager: TimezoneManager instance for timezone handling
        """
        self.service = calendar_service
        self.timezone_manager = timezone_manager
    
    def create_event(self, summary: str, start_time: datetime, end_time: datetime,
                    description: str = "", location: str = "", attendees: list = None) -> Dict[str, Any]:
        """
        Create a new calendar event.
        
        Args:
            summary: Event title
            start_time: Start datetime (in user timezone)
            end_time: End datetime (in user timezone)
            description: Event description
            location: Event location
            attendees: List of attendee email addresses
        
        Returns:
            Dictionary with success status and event details
        """
        try:
            # Convert to UTC for Google Calendar API
            if self.timezone_manager:
                start_utc = self.timezone_manager.convert_to_utc(start_time)
                end_utc = self.timezone_manager.convert_to_utc(end_time)
            else:
                start_utc = start_time.astimezone(timezone.utc) if start_time.tzinfo else start_time
                end_utc = end_time.astimezone(timezone.utc) if end_time.tzinfo else end_time
            
            # Format for Google Calendar API (RFC3339)
            start_rfc = start_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
            end_rfc = end_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            print(f"Creating event: {summary}")
            print(f"UTC times: start={start_rfc}, end={end_rfc}")
            
            event_body = {
                'summary': summary,
                'description': description,
                'location': location,
                'start': {'dateTime': start_rfc, 'timeZone': 'UTC'},
                'end': {'dateTime': end_rfc, 'timeZone': 'UTC'},
            }
            
            if attendees:
                event_body['attendees'] = [{'email': email} for email in attendees]
            
            print(f"Event body: {event_body}")
            event = self.service.events().insert(calendarId=constants.CALENDAR_ID, body=event_body).execute()
            print(f"Event created: {event.get('id')}, start: {event.get('start')}, end: {event.get('end')}")
            
            # Verify event was created
            if event and event.get('id'):
                return {
                    'success': True,
                    'event_id': event.get('id'),
                    'summary': event.get('summary'),
                    'message': f"Event '{summary}' created successfully"
                }
            else:
                return {
                    'success': False,
                    'error': 'Event creation returned no event ID',
                    'message': 'Failed to create event: No event ID returned'
                }
            
        except HttpError as error:
            return {
                'success': False,
                'error': str(error),
                'message': f"Failed to create event: {error}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f"Error creating event: {str(e)}"
            }
    
    def modify_event(self, event_id: str, summary: Optional[str] = None,
                    start_time: Optional[datetime] = None, end_time: Optional[datetime] = None,
                    description: Optional[str] = None, location: Optional[str] = None,
                    attendees: Optional[list] = None) -> Dict[str, Any]:
        """
        Modify an existing calendar event.
        
        Args:
            event_id: ID of event to modify
            summary: New event title (optional)
            start_time: New start datetime (optional)
            end_time: New end datetime (optional)
            description: New description (optional)
            location: New location (optional)
            attendees: New list of attendee emails (optional)
        
        Returns:
            Dictionary with success status and event details
        """
        try:
            # Get existing event
            event = self.service.events().get(calendarId=constants.CALENDAR_ID, eventId=event_id).execute()
            
            # Calculate original duration if start_time is provided but end_time is not
            if start_time and not end_time:
                # Parse original start and end times
                original_start_str = event['start'].get('dateTime', event['start'].get('date'))
                original_end_str = event['end'].get('dateTime', event['end'].get('date'))
                
                # Parse to datetime
                if 'T' in original_start_str:
                    original_start = datetime.fromisoformat(original_start_str.replace('Z', '+00:00'))
                    original_end = datetime.fromisoformat(original_end_str.replace('Z', '+00:00'))
                else:
                    original_start = datetime.fromisoformat(original_start_str).replace(tzinfo=timezone.utc)
                    original_end = datetime.fromisoformat(original_end_str).replace(tzinfo=timezone.utc)
                
                # Calculate duration
                duration = original_end - original_start
                
                # Set new end time = new start time + original duration
                end_time = start_time + duration
            
            # Update fields if provided
            if summary:
                event['summary'] = summary
            if description is not None:
                event['description'] = description
            if location is not None:
                event['location'] = location
            if attendees is not None:
                event['attendees'] = [{'email': email} for email in attendees]
            
            # Update times if provided
            if start_time or end_time:
                if start_time:
                    if self.timezone_manager:
                        start_utc = self.timezone_manager.convert_to_utc(start_time)
                    else:
                        start_utc = start_time.astimezone(timezone.utc) if start_time.tzinfo else start_time
                    start_rfc = start_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
                    event['start'] = {'dateTime': start_rfc, 'timeZone': 'UTC'}
                
                if end_time:
                    if self.timezone_manager:
                        end_utc = self.timezone_manager.convert_to_utc(end_time)
                    else:
                        end_utc = end_time.astimezone(timezone.utc) if end_time.tzinfo else end_time
                    end_rfc = end_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
                    event['end'] = {'dateTime': end_rfc, 'timeZone': 'UTC'}
            
            # Update event
            updated_event = self.service.events().update(
                calendarId=constants.CALENDAR_ID,
                eventId=event_id,
                body=event
            ).execute()
            
            return {
                'success': True,
                'event_id': updated_event.get('id'),
                'summary': updated_event.get('summary'),
                'message': f"Event '{updated_event.get('summary')}' updated successfully"
            }
            
        except HttpError as error:
            return {
                'success': False,
                'error': str(error),
                'message': f"Failed to modify event: {error}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f"Error modifying event: {str(e)}"
            }
    
    def check_conflicts(self, start_time: datetime, end_time: datetime, exclude_event_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Check for conflicting events in the calendar.
        
        Args:
            start_time: Proposed start datetime (in user timezone)
            end_time: Proposed end datetime (in user timezone)
            exclude_event_id: Event ID to exclude from conflict check (for modifications)
        
        Returns:
            List of conflicting events
        """
        try:
            # Convert to UTC for API query
            if self.timezone_manager:
                start_utc = self.timezone_manager.convert_to_utc(start_time)
                end_utc = self.timezone_manager.convert_to_utc(end_time)
            else:
                start_utc = start_time.astimezone(timezone.utc) if start_time.tzinfo else start_time
                end_utc = end_time.astimezone(timezone.utc) if end_time.tzinfo else end_time
            
            # Query calendar for events in this time range
            start_rfc = start_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
            end_rfc = end_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            events_result = self.service.events().list(
                calendarId=constants.CALENDAR_ID,
                timeMin=start_rfc,
                timeMax=end_rfc,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            conflicts = []
            for event in events_result.get('items', []):
                event_id = event.get('id')
                # Skip the event being modified
                if exclude_event_id and event_id == exclude_event_id:
                    continue
                
                # Check if events actually overlap
                event_start_str = event['start'].get('dateTime', event['start'].get('date'))
                event_end_str = event['end'].get('dateTime', event['end'].get('date'))
                
                if 'T' in event_start_str:
                    event_start = datetime.fromisoformat(event_start_str.replace('Z', '+00:00'))
                    event_end = datetime.fromisoformat(event_end_str.replace('Z', '+00:00'))
                else:
                    event_start = datetime.fromisoformat(event_start_str).replace(tzinfo=timezone.utc)
                    event_end = datetime.fromisoformat(event_end_str).replace(tzinfo=timezone.utc)
                
                # Check overlap: new event starts before existing ends AND new event ends after existing starts
                if start_utc < event_end and end_utc > event_start:
                    conflicts.append({
                        'id': event_id,
                        'summary': event.get('summary', 'Untitled Event'),
                        'start': event_start,
                        'end': event_end,
                        'location': event.get('location', '')
                    })
            
            return conflicts
            
        except Exception as e:
            # On error, return empty list (don't block on conflict check errors)
            return []
    
    def cancel_event(self, event_id: str) -> Dict[str, Any]:
        """
        Cancel/delete a calendar event.
        
        Args:
            event_id: ID of event to cancel
        
        Returns:
            Dictionary with success status
        """
        try:
            print(f"Cancelling event ID: {event_id}")
            
            # Get event summary before deleting
            event = self.service.events().get(calendarId=constants.CALENDAR_ID, eventId=event_id).execute()
            summary = event.get('summary', 'Event')
            print(f"Found event: {summary}")
            
            # Delete event
            self.service.events().delete(calendarId=constants.CALENDAR_ID, eventId=event_id).execute()
            print(f"Event deleted from Google Calendar")
            
            return {
                'success': True,
                'event_id': event_id,
                'message': f"Event '{summary}' cancelled successfully"
            }
            
        except HttpError as error:
            print(f"HTTP Error cancelling event: {error}")
            return {
                'success': False,
                'error': str(error),
                'message': f"Failed to cancel event: {error}"
            }
        except Exception as e:
            print(f"Exception cancelling event: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Error cancelling event: {str(e)}"
            }

