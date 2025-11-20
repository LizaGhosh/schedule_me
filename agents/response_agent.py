"""Agent for generating conversational responses from query results."""
import os
import sys
import json
from typing import List, Dict, Any
from groq import Groq
from dotenv import load_dotenv

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import constants

load_dotenv()


class ResponseAgent:
    """Generates conversational responses from SQL query results using LLM."""
    
    def __init__(self):
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            raise ValueError("GROQ_API_KEY not found")
        self.client = Groq(api_key=api_key)
    
    def generate_response(self, user_query: str, events: List[Dict[str, Any]]) -> str:
        """
        Generate conversational response from query results.
        
        Args:
            user_query: Original user query
            events: List of event dictionaries from SQL query
        
        Returns:
            Conversational response string
        """
        # Format events for prompt
        events_text = ""
        for event in events[:constants.MAX_EVENTS_FOR_RESPONSE]:
            start = event['start']
            end = event['end']
            events_text += f"- {event['summary']} on {start.strftime('%B %d')} from {start.strftime('%I:%M %p')} to {end.strftime('%I:%M %p')}"
            if event.get('location'):
                events_text += f" at {event['location']}"
            events_text += "\n"
        
        prompt = f"""User asked: "{user_query}"

Query results:
{events_text if events else "No events found."}

Generate a natural, conversational response to the user's question based on these results. Be concise and friendly."""

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
            # Fallback to simple response
            if events:
                return f"Found {len(events)} event(s) matching your query."
            else:
                return "I don't see any events matching your request."

