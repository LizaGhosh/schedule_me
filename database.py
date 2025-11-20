"""Simple database initialization for storing calendar events."""
import sqlite3
import constants


class CalendarDatabase:
    """Simple SQLite database for storing calendar events."""
    
    def __init__(self, db_path: str = None):
        """
        Initialize the database and create schema.
        
        Args:
            db_path: Path to SQLite database file (defaults to constants.DB_PATH)
        """
        if db_path is None:
            db_path = constants.DB_PATH
        self.db_path = db_path
        self._create_database()
    
    def _create_database(self):
        """Create database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                summary TEXT NOT NULL,
                description TEXT,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                location TEXT,
                attendees TEXT,
                status TEXT,
                html_link TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        # Create index for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_start_time ON events(start_time)
        ''')
        
        conn.commit()
        conn.close()
    
    def clear_all_events(self):
        """Clear all events from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM events')
        conn.commit()
        conn.close()
