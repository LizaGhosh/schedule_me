"""Agent for validating calendar modifications."""
import os
import sys
from groq import Groq
from dotenv import load_dotenv

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import constants

load_dotenv()


class ValidationAgent:
    """Validates that calendar modifications match user intent."""
    
    def __init__(self):
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            raise ValueError("GROQ_API_KEY not found")
        self.client = Groq(api_key=api_key)
    
    def validate(self, user_query: str, action_type: str, event_data: dict) -> dict:
        """
        Validate that the modification matches user intent.
        
        Args:
            user_query: Original user query
            action_type: 'create', 'modify', or 'cancel'
            event_data: Event data from database after modification
        
        Returns:
            Dictionary with 'valid' (bool) and 'message' (str)
        """
        # Format event data for comparison
        event_info = ""
        if event_data:
            start = event_data.get('start', '')
            end = event_data.get('end', '')
            if start:
                start_str = start.strftime('%Y-%m-%d %I:%M %p') if hasattr(start, 'strftime') else str(start)
            else:
                start_str = 'N/A'
            if end:
                end_str = end.strftime('%Y-%m-%d %I:%M %p') if hasattr(end, 'strftime') else str(end)
            else:
                end_str = 'N/A'
            
            event_info = f"Summary: {event_data.get('summary', 'N/A')}, Start: {start_str}, End: {end_str}"
        else:
            event_info = "Event not found or was deleted"
        
        prompt = f"""User requested: "{user_query}"
Action performed: {action_type}
Result in database: {event_info}

Check if the action result matches what the user requested. Return JSON:
{{"valid": true/false, "message": "explanation"}}

If the result doesn't match the user's request, set valid to false."""

        try:
            response = self.client.chat.completions.create(
                model=constants.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a validation agent. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=constants.VALIDATION_AGENT_TEMPERATURE,
                max_tokens=constants.VALIDATION_AGENT_MAX_TOKENS
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith('```'):
                parts = content.split('```')
                if len(parts) > 1:
                    content = parts[1]
                    if content.startswith('json'):
                        content = content[4:]
                content = content.strip()
            
            import json
            result = json.loads(content)
            return result
            
        except Exception as e:
            # On error, assume valid (don't block on validation errors)
            return {'valid': True, 'message': f'Validation error: {str(e)}'}

