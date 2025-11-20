"""Agent for parsing action parameters from natural language."""
import os
import sys
import json
from groq import Groq
from dotenv import load_dotenv

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import constants

load_dotenv()


class ActionParserAgent:
    """Parses action parameters from natural language."""
    
    def __init__(self):
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            raise ValueError("GROQ_API_KEY not found")
        self.client = Groq(api_key=api_key)
    
    def parse_create(self, user_query: str, current_date: str = None) -> dict:
        """
        Parse parameters for creating an event.
        
        Args:
            user_query: User's natural language query
            current_date: Current date in format "YYYY-MM-DD" (optional)
        
        Returns:
            Dictionary with: summary, start_time, end_time, description, location, attendees
        """
        date_context = f"Current date: {current_date}" if current_date else ""
        
        prompt = f"""Extract event details from this query to create a calendar event.

{date_context}

User query: "{user_query}"

Return a JSON object with:
- summary: Event title/name
- start_time: Start time in format "YYYY-MM-DD HH:MM" (24-hour format). Use the CURRENT DATE or calculate relative dates (today, tomorrow) based on the current date provided.
- end_time: End time in format "YYYY-MM-DD HH:MM" (24-hour format, default to 1 hour after start_time if not specified)
- description: Event description (optional, empty string if not provided)
- location: Event location (optional, empty string if not provided)
- attendees: List of email addresses (optional, empty list if not provided)

IMPORTANT: 
- Always use the current date provided to calculate relative dates like "tomorrow"
- Always provide both start_time and end_time. If end_time is not specified, default to 1 hour after start_time.
- Return ONLY valid JSON."""

        try:
            response = self.client.chat.completions.create(
                model=constants.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a calendar event parser. Return ONLY valid JSON, no explanations, no markdown, just the JSON object."},
                    {"role": "user", "content": prompt}
                ],
                temperature=constants.LLM_TEMPERATURE,
                max_tokens=constants.LLM_MAX_TOKENS
            )
            
            content = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith('```'):
                parts = content.split('```')
                if len(parts) > 1:
                    content = parts[1]
                    if content.startswith('json'):
                        content = content[4:]
                content = content.strip()
            
            if not content:
                return {'error': 'Empty response from LLM'}
            
            result = json.loads(content)
            return result
            
        except json.JSONDecodeError as e:
            raw_content = response.choices[0].message.content if 'response' in locals() else 'No response'
            print(f"JSON parse error: {e}")
            print(f"Raw response: {raw_content}")
            return {'error': f'Invalid JSON response: {str(e)}'}
        except Exception as e:
            return {'error': str(e)}
    
    def parse_modify(self, user_query: str, events: list) -> dict:
        """
        Parse parameters for modifying an event.
        
        Args:
            user_query: User's natural language query
            events: List of available events to help identify which event to modify
        
        Returns:
            Dictionary with: event_id, and optional fields to update
        """
        # Format events for context
        events_text = ""
        for event in events[:constants.MAX_EVENTS_FOR_PARSER]:
            events_text += f"- {event['id']}: {event['summary']} on {event['start'].strftime('%Y-%m-%d %I:%M %p')}\n"
        
        prompt = f"""Extract modification details from this query.

Available events:
{events_text if events_text else "No events found."}

User query: "{user_query}"

Return a JSON object with:
- event_id: ID of event to modify (from available events or user description)
- summary: New title (optional, null if not changing)
- start_time: New start time in format "YYYY-MM-DD HH:MM" (optional, null if not changing)
- end_time: New end time in format "YYYY-MM-DD HH:MM" (optional, null if not changing)
- description: New description (optional, null if not changing)
- location: New location (optional, null if not changing)
- attendees: New list of emails (optional, null if not changing)

Return ONLY valid JSON."""

        try:
            response = self.client.chat.completions.create(
                model=constants.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a calendar event parser. Return ONLY valid JSON, no explanations, no markdown, just the JSON object."},
                    {"role": "user", "content": prompt}
                ],
                temperature=constants.LLM_TEMPERATURE,
                max_tokens=constants.LLM_MAX_TOKENS
            )
            
            content = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith('```'):
                parts = content.split('```')
                if len(parts) > 1:
                    content = parts[1]
                    if content.startswith('json'):
                        content = content[4:]
                content = content.strip()
            
            if not content:
                return {'error': 'Empty response from LLM'}
            
            result = json.loads(content)
            return result
            
        except json.JSONDecodeError as e:
            raw_content = response.choices[0].message.content if 'response' in locals() else 'No response'
            print(f"JSON parse error: {e}")
            print(f"Raw response: {raw_content}")
            return {'error': f'Invalid JSON response: {str(e)}'}
        except Exception as e:
            return {'error': str(e)}
    
    def parse_cancel(self, user_query: str, events: list) -> dict:
        """
        Parse parameters for canceling an event.
        
        Args:
            user_query: User's natural language query
            events: List of available events to help identify which event to cancel
        
        Returns:
            Dictionary with: event_id
        """
        # Format events for context
        events_text = ""
        for event in events[:constants.MAX_EVENTS_FOR_PARSER]:
            events_text += f"- {event['id']}: {event['summary']} on {event['start'].strftime('%Y-%m-%d %I:%M %p')}\n"
        
        prompt = f"""Extract event to cancel from this query.

Available events:
{events_text if events_text else "No events found."}

User query: "{user_query}"

Return a JSON object with:
- event_id: ID of event to cancel (from available events or user description)

Return ONLY valid JSON."""

        try:
            response = self.client.chat.completions.create(
                model=constants.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a calendar event parser. Return ONLY valid JSON, no explanations, no markdown, just the JSON object."},
                    {"role": "user", "content": prompt}
                ],
                temperature=constants.LLM_TEMPERATURE,
                max_tokens=constants.LLM_MAX_TOKENS
            )
            
            content = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith('```'):
                parts = content.split('```')
                if len(parts) > 1:
                    content = parts[1]
                    if content.startswith('json'):
                        content = content[4:]
                content = content.strip()
            
            if not content:
                return {'error': 'Empty response from LLM'}
            
            result = json.loads(content)
            return result
            
        except json.JSONDecodeError as e:
            raw_content = response.choices[0].message.content if 'response' in locals() else 'No response'
            print(f"JSON parse error: {e}")
            print(f"Raw response: {raw_content}")
            return {'error': f'Invalid JSON response: {str(e)}'}
        except Exception as e:
            return {'error': str(e)}
    
    def generate_conflict_message(self, user_query: str, proposed_event: dict, conflicts: list) -> str:
        """
        Generate a conversational message about scheduling conflicts.
        
        Args:
            user_query: Original user query
            proposed_event: Proposed event details (summary, start_time, end_time)
            conflicts: List of conflicting events
        
        Returns:
            Conversational message about the conflict
        """
        # Format proposed event
        start_str = proposed_event.get('start_time', '')
        end_str = proposed_event.get('end_time', '')
        summary = proposed_event.get('summary', 'Event')
        
        # Format conflicts
        conflicts_text = ""
        for conflict in conflicts:
            conflict_start = conflict.get('start', '')
            conflict_end = conflict.get('end', '')
            if hasattr(conflict_start, 'strftime'):
                conflict_start_str = conflict_start.strftime('%Y-%m-%d %I:%M %p')
            else:
                conflict_start_str = str(conflict_start)
            if hasattr(conflict_end, 'strftime'):
                conflict_end_str = conflict_end.strftime('%I:%M %p')
            else:
                conflict_end_str = str(conflict_end)
            
            conflicts_text += f"- {conflict.get('summary', 'Event')} from {conflict_start_str} to {conflict_end_str}\n"
        
        prompt = f"""User requested: "{user_query}"

Proposed event: {summary} from {start_str} to {end_str}

Conflicting events:
{conflicts_text}

Generate a friendly, conversational message informing the user about the scheduling conflict. Be concise and helpful."""

        try:
            response = self.client.chat.completions.create(
                model=constants.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful calendar assistant. Provide natural, conversational responses."},
                    {"role": "user", "content": prompt}
                ],
                temperature=constants.LLM_TEMPERATURE,
                max_tokens=constants.LLM_MAX_TOKENS
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"I found a scheduling conflict. You already have an event at that time."

