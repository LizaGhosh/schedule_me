"""Agent for answering questions about calendar events using LLM."""
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


class QAAgent:
    """Answers questions about calendar events using LLM."""
    
    def __init__(self):
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            raise ValueError("GROQ_API_KEY not found")
        self.client = Groq(api_key=api_key)
    
    def answer(self, user_query: str, events: list) -> str:
        """
        Answer user question about events.
        
        Args:
            user_query: User's question
            events: List of event dictionaries
        
        Returns:
            Answer string
        """
        # Format events for prompt
        events_text = ""
        for event in events[:constants.MAX_EVENTS_FOR_QA]:
            start = event['start'].astimezone() if event['start'].tzinfo else event['start']
            events_text += f"- {event['summary']} on {start.strftime('%B %d at %I:%M %p')}\n"
        
        prompt = f"""Answer this question about calendar events:

User question: "{user_query}"

Events:
{events_text}

Provide a clear, concise answer."""

        try:
            response = self.client.chat.completions.create(
                model=constants.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful calendar assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=constants.LLM_TEMPERATURE,
                max_tokens=constants.LLM_MAX_TOKENS
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Error: {str(e)}"

