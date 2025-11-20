"""Timezone management for the calendar system."""
import pytz
from datetime import datetime
from typing import Optional


class TimezoneManager:
    """Manages timezone for calendar events and queries."""
    
    def __init__(self, timezone_str: Optional[str] = None):
        """
        Initialize timezone manager.
        
        Args:
            timezone_str: Timezone string (e.g., 'America/New_York', 'UTC', 'Asia/Kolkata')
                         If None, defaults to UTC
        """
        if timezone_str:
            try:
                self.user_timezone = pytz.timezone(timezone_str)
            except pytz.exceptions.UnknownTimeZoneError:
                print(f"Warning: Unknown timezone '{timezone_str}'. Using UTC.")
                self.user_timezone = pytz.UTC
        else:
            self.user_timezone = pytz.UTC
    
    def set_timezone(self, timezone_str: str) -> bool:
        """
        Set the user's timezone.
        
        Args:
            timezone_str: Timezone string (e.g., 'America/New_York', 'UTC')
        
        Returns:
            True if successful, False if invalid timezone
        """
        try:
            self.user_timezone = pytz.timezone(timezone_str)
            return True
        except pytz.exceptions.UnknownTimeZoneError:
            print(f"Error: Unknown timezone '{timezone_str}'")
            return False
    
    def get_timezone(self) -> pytz.BaseTzInfo:
        """Get the current user timezone."""
        return self.user_timezone
    
    def get_timezone_name(self) -> str:
        """Get the timezone name as string."""
        return str(self.user_timezone)
    
    def convert_to_user_tz(self, dt: datetime) -> datetime:
        """
        Convert datetime to user's timezone.
        
        Args:
            dt: Datetime object (can be timezone-aware or naive)
        
        Returns:
            Datetime in user's timezone
        """
        if dt.tzinfo is None:
            # Assume UTC if naive
            dt = pytz.UTC.localize(dt)
        
        return dt.astimezone(self.user_timezone)
    
    def convert_to_utc(self, dt: datetime) -> datetime:
        """
        Convert datetime to UTC.
        
        Args:
            dt: Datetime object in user's timezone
        
        Returns:
            Datetime in UTC
        """
        if dt.tzinfo is None:
            # Assume user timezone if naive
            dt = self.user_timezone.localize(dt)
        
        return dt.astimezone(pytz.UTC)
    
    def now_in_user_tz(self) -> datetime:
        """Get current time in user's timezone."""
        return datetime.now(self.user_timezone)
    
    def format_for_sqlite(self, dt: datetime) -> str:
        """
        Format datetime for SQLite storage (24-hour format, UTC).
        
        Args:
            dt: Datetime object
        
        Returns:
            String in format 'YYYY-MM-DD HH:MM:SS' (UTC)
        """
        # Convert to UTC first
        if dt.tzinfo is None:
            dt = self.user_timezone.localize(dt)
        utc_dt = dt.astimezone(pytz.UTC)
        
        # Format for SQLite
        return utc_dt.strftime('%Y-%m-%d %H:%M:%S')
    
    def parse_from_sqlite(self, sqlite_str: str) -> datetime:
        """
        Parse datetime from SQLite format (assumes UTC).
        
        Args:
            sqlite_str: String in format 'YYYY-MM-DD HH:MM:SS'
        
        Returns:
            Datetime object in user's timezone
        """
        # Parse as UTC
        utc_dt = datetime.strptime(sqlite_str, '%Y-%m-%d %H:%M:%S')
        utc_dt = pytz.UTC.localize(utc_dt)
        
        # Convert to user timezone
        return utc_dt.astimezone(self.user_timezone)
    
    def get_utc_offset_hours(self) -> float:
        """
        Get UTC offset in hours for the user's timezone.
        
        Returns:
            Offset in hours (e.g., -5.0 for EST, 5.5 for IST)
        """
        now = datetime.now(self.user_timezone)
        offset = now.utcoffset()
        return offset.total_seconds() / 3600.0
    
    def get_sqlite_timezone_modifier(self) -> str:
        """
        Get SQLite timezone modifier string for user's timezone.
        SQLite uses hour offsets in format: '-5 hours' or '+5 hours'
        
        Returns:
            SQLite timezone modifier string (e.g., '-5 hours' for EST)
        """
        offset_hours = self.get_utc_offset_hours()
        sign = '-' if offset_hours < 0 else '+'
        hours = abs(int(offset_hours))
        minutes = abs(int((offset_hours % 1) * 60))
        
        # SQLite doesn't support fractional hours directly, so we use hours and minutes
        if minutes == 0:
            return f"{sign}{hours} hours"
        else:
            # Use both hours and minutes
            return f"{sign}{hours} hours, {sign}{minutes} minutes"

