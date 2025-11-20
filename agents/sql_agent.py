"""Agent for converting natural language to SQL queries."""
import os
import sqlite3
import sys
from groq import Groq
from dotenv import load_dotenv
from typing import Optional

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import constants

load_dotenv()


class SQLAgent:
    """Converts natural language to SQL queries for calendar events."""
    
    def __init__(self, db_path: str = None, qa_agent=None, timezone_manager=None):
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            raise ValueError("GROQ_API_KEY not found")
        self.client = Groq(api_key=api_key)
        if db_path is None:
            db_path = constants.DB_PATH
        self.db_path = db_path
        self.qa_agent = qa_agent
        self.timezone_manager = timezone_manager
    
    def _get_schema(self) -> str:
        """Dynamically read database schema."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get table info
            cursor.execute("PRAGMA table_info(events)")
            columns = cursor.fetchall()
            
            schema = "Table: events\nColumns:\n"
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                not_null = " NOT NULL" if col[3] else ""
                default = f" DEFAULT {col[4]}" if col[4] else ""
                pk = " PRIMARY KEY" if col[5] else ""
                
                schema += f"- {col_name} ({col_type}{not_null}{default}{pk})\n"
            
            conn.close()
            return schema
            
        except Exception as e:
            print(f"Error reading schema: {e}")
            # Fallback to basic schema
            return """
            Table: events
            Columns:
            - id (TEXT PRIMARY KEY)
            - summary (TEXT)
            - start_time (TEXT)
            - end_time (TEXT)
            """
    
    def text_to_sql(self, user_query: str, events: Optional[list] = None) -> Optional[str]:
        """
        Convert natural language query to SQL.
        
        Args:
            user_query: User's question in natural language
            events: Optional list of events for fallback QA agent
        
        Returns:
            SQL query string, or None if failed and QA agent was used
        """
        schema = self._get_schema()
        
        # Get timezone info for SQL generation
        tz_modifier = None
        user_today = None
        if self.timezone_manager:
            tz_modifier = self.timezone_manager.get_sqlite_timezone_modifier()
            user_now = self.timezone_manager.now_in_user_tz()
            user_today = user_now.strftime('%Y-%m-%d')
        
        # Build timezone-aware examples
        if tz_modifier:
            today_example = f"SELECT * FROM events WHERE date(datetime(start_time, '{tz_modifier}')) = date(datetime('now', '{tz_modifier}'))"
            tomorrow_example = f"SELECT * FROM events WHERE date(datetime(start_time, '{tz_modifier}')) = date(datetime('now', '{tz_modifier}', '+1 day'))"
            week_example = f"SELECT * FROM events WHERE date(datetime(start_time, '{tz_modifier}')) >= date(datetime('now', '{tz_modifier}')) AND date(datetime(start_time, '{tz_modifier}')) <= date(datetime('now', '{tz_modifier}', '+7 days'))"
        else:
            today_example = "SELECT * FROM events WHERE date(start_time) = date('now')"
            tomorrow_example = "SELECT * FROM events WHERE date(start_time) = date('now', '+1 day')"
            week_example = "SELECT * FROM events WHERE date(start_time) >= date('now') AND date(start_time) <= date('now', '+7 days')"
        
        prompt = f"""Convert this natural language query to SQL for the events table.

Schema:
{schema}

User query: "{user_query}"

Return ONLY a valid SQL SELECT query. Use SQLite syntax.
IMPORTANT: 
- Use '+1 day' (with plus sign) for tomorrow, NOT '1 day'
- Timestamps are stored in UTC format (YYYY-MM-DD HH:MM:SS) in the database
- Use datetime() with timezone modifier '{tz_modifier}' to convert UTC to user timezone
- Then use date() to extract date part for comparisons
- Current date in user timezone: {user_today if user_today else 'unknown'}
- Timezone modifier to use: '{tz_modifier}' (apply to both 'now' and start_time)

Examples:
- "show all events" -> SELECT * FROM events ORDER BY start_time
- "events today" -> {today_example}
- "events tomorrow" -> {tomorrow_example}
- "events tomorrow after 5pm" -> SELECT * FROM events WHERE date(datetime(start_time, '{tz_modifier}')) = date(datetime('now', '{tz_modifier}', '+1 day')) AND time(datetime(start_time, '{tz_modifier}')) > '17:00:00'
- "meetings with john" -> SELECT * FROM events WHERE attendees LIKE '%john%'
- "events this week" -> {week_example}

SQL query:"""
        
        try:
            response = self.client.chat.completions.create(
                model=constants.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a SQL query generator. Return ONLY valid SQL, no explanations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=constants.LLM_TEMPERATURE,
                max_tokens=constants.LLM_MAX_TOKENS
            )
            
            sql = response.choices[0].message.content.strip()
            # Remove markdown code blocks if present
            if sql.startswith('```'):
                sql = sql.split('```')[1]
                if sql.startswith('sql'):
                    sql = sql[3:]
                sql = sql.strip()
            
            return sql
            
        except Exception as e:
            print(f"Error generating SQL: {e}")
            # Fallback to QA agent if available
            if self.qa_agent and events:
                print("Using fallback QA agent...")
                answer = self.qa_agent.answer(user_query, events)
                print(f"\n{answer}")
                return None
            # Fallback: return all events
            return "SELECT * FROM events ORDER BY start_time"

