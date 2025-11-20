"""Agent for identifying user intent."""
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


class IntentAgent:
    """Identifies user intent from natural language."""
    
    def __init__(self):
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            raise ValueError("GROQ_API_KEY not found")
        self.client = Groq(api_key=api_key)
    
    def identify_intent(self, user_query: str) -> str:
        """
        Identify user intent from query.
        
        Args:
            user_query: User's natural language query
        
        Returns:
            Intent string: 'query', 'create', 'modify', 'cancel', or 'quit'
        """
        prompt = f"""Classify the user's intent into one of these categories:
- 'query': User wants information about events (e.g., "show events", "what's on my calendar", "events tomorrow")
- 'create': User wants to create a new event (e.g., "schedule a meeting", "create event", "add appointment")
- 'modify': User wants to modify an existing event (e.g., "change time", "update event", "reschedule")
- 'cancel': User wants to cancel/delete an event (e.g., "cancel meeting", "delete event", "remove appointment")
- 'quit': User wants to stop/exit/quit the application (e.g., "quit", "exit", "stop", "bye", "goodbye", "I'm done")

User query: "{user_query}"

Return ONLY one word: query, create, modify, cancel, or quit"""

        try:
            response = self.client.chat.completions.create(
                model=constants.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are an intent classifier. Return only the intent word."},
                    {"role": "user", "content": prompt}
                ],
                temperature=constants.INTENT_AGENT_TEMPERATURE,
                max_tokens=constants.INTENT_AGENT_MAX_TOKENS
            )
            
            intent = response.choices[0].message.content.strip().lower()
            
            # Validate intent
            valid_intents = ['query', 'create', 'modify', 'cancel', 'quit']
            if intent not in valid_intents:
                # Default to query if unclear
                return 'query'
            
            return intent
            
        except Exception as e:
            # Default to query on error
            return 'query'

