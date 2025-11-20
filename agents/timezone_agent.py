"""Agent for setting and managing timezone."""
import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from timezone_manager import TimezoneManager
import pytz


class TimezoneAgent:
    """Agent for handling timezone setup and queries."""
    
    def __init__(self):
        self.timezone_manager = None
    
    def ask_user_timezone(self) -> TimezoneManager:
        """
        Ask user for their timezone.
        
        Returns:
            TimezoneManager instance
        """
        print("\nPlease enter your timezone.")
        print("Examples: 'America/New_York', 'America/Los_Angeles', 'Europe/London', 'Asia/Kolkata', 'UTC'")
        print("Or type 'list' to see common timezones.")
        
        while True:
            user_input = input("Timezone: ").strip()
            
            if user_input.lower() == 'list':
                self._print_common_timezones()
                continue
            
            if not user_input:
                print("Using UTC as default.")
                self.timezone_manager = TimezoneManager('UTC')
                break
            
            if self.timezone_manager is None:
                self.timezone_manager = TimezoneManager()
            
            if self.timezone_manager.set_timezone(user_input):
                print(f"Timezone set to: {self.timezone_manager.get_timezone_name()}")
                break
            else:
                print("Invalid timezone. Please try again or type 'list' for options.")
        
        return self.timezone_manager
    
    def _print_common_timezones(self):
        """Print common timezone options."""
        common = [
            ('UTC', 'UTC'),
            ('America/New_York', 'Eastern Time (US)'),
            ('America/Chicago', 'Central Time (US)'),
            ('America/Denver', 'Mountain Time (US)'),
            ('America/Los_Angeles', 'Pacific Time (US)'),
            ('Europe/London', 'London'),
            ('Europe/Paris', 'Paris'),
            ('Asia/Kolkata', 'India'),
            ('Asia/Tokyo', 'Tokyo'),
            ('Australia/Sydney', 'Sydney'),
        ]
        print("\nCommon timezones:")
        for tz, desc in common:
            print(f"  {tz:25} - {desc}")

