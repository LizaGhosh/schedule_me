"""Main entry point."""
from orchestrator import Orchestrator
from calendar_manager import CalendarManager


def main():
    """Run the calendar assistant."""
    try:
        print("Initializing calendar assistant...")
        calendar = CalendarManager()
        orchestrator = Orchestrator(calendar.service)
        orchestrator.run()
    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    main()

