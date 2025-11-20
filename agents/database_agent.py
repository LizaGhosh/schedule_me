"""Agent for querying the events database."""
import sqlite3
import json
from typing import List, Dict, Any
from datetime import datetime
import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import constants


class DatabaseAgent:
    """Queries the events database using SQL."""
    
    def __init__(self, db_path: str = None, timezone_manager=None):
        """
        Initialize database agent.
        
        Args:
            db_path: Path to SQLite database file (defaults to constants.DB_PATH)
            timezone_manager: TimezoneManager instance for timezone conversion
        """
        if db_path is None:
            db_path = constants.DB_PATH
        self.db_path = db_path
        self.timezone_manager = timezone_manager
    
    def execute_query(self, sql_query: str, print_raw: bool = True) -> List[Dict[str, Any]]:
        """
        Execute SQL query and return results.
        
        Args:
            sql_query: SQL SELECT query string
            print_raw: Whether to print raw SQL output
        
        Returns:
            List of event dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(sql_query)
            rows = cursor.fetchall()
            
            # Don't print raw SQL output here - orchestrator will handle conversational output
            
            events = []
            for row in rows:
                # Parse timestamp from SQLite format (YYYY-MM-DD HH:MM:SS) - stored in UTC
                start_str = row['start_time']
                end_str = row['end_time']
                
                # Convert to datetime - handle both ISO and SQLite formats
                if 'T' in start_str:
                    start_dt = datetime.fromisoformat(start_str)
                else:
                    start_dt = datetime.strptime(start_str, '%Y-%m-%d %H:%M:%S')
                
                if 'T' in end_str:
                    end_dt = datetime.fromisoformat(end_str)
                else:
                    end_dt = datetime.strptime(end_str, '%Y-%m-%d %H:%M:%S')
                
                # Convert from UTC to user timezone if timezone_manager is available
                if self.timezone_manager:
                    start_dt = self.timezone_manager.parse_from_sqlite(start_str)
                    end_dt = self.timezone_manager.parse_from_sqlite(end_str)
                
                event = {
                    'id': row['id'],
                    'summary': row['summary'],
                    'description': row['description'],
                    'start': start_dt,
                    'end': end_dt,
                    'location': row['location'],
                    'attendees': json.loads(row['attendees']) if row['attendees'] else [],
                    'status': row['status'],
                    'htmlLink': row['html_link']
                }
                events.append(event)
            
            conn.close()
            return events
            
        except Exception as e:
            print(f"Error executing query: {e}")
            return []

