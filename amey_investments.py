import os
import pandas as pd
from datetime import datetime, timedelta

from google_calendar import GoogleCalendarUtil

data_path = os.path.join(os.path.dirname(__file__), "data", "amey_data.xlsx")

def load_data():
    """Load data from Excel file and filter to only include rows where Type is 'recurring'."""
    try:
        # Read the excel file
        df = pd.read_excel(data_path)
        
        # Filter to only include rows where Type is 'recurring'
        recurring_df = df[df['Type'].str.lower() == 'recurring']
        print(recurring_df)
        
        return recurring_df
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()
    
def create_events(google_calendar_util, row):
    """Create a basic recurring event for SIP payment based on the day of the month"""
    # Extract information from the row
    company = row['Company']
    folio_number = row['Folio Number']
    amount = row['Amount']
    day_of_month = row['Day of the Month']
    
    print(f"Processing: {company} (Rs.{amount}) - Day {day_of_month}")
    
    # Create event summary and description
    summary = f"{company} - {format_currency_inr(amount)}"
    description = f"Folio Number: {folio_number}"
    
    # Simple start date calculation - use the first month of the current year
    today = datetime.now()
    start_date = datetime(today.year, 1, int(day_of_month))

    # Create the recurring event (monthly)
    google_calendar_util.create_event(
        summary=summary,
        description=description,
        start_date=start_date,
        frequency=1  # Monthly
    )
    print(f"\u2713 Created event for {company} starting {start_date.strftime('%Y-%m-%d')}")


def format_currency_inr(amount):
    """Format a number in Indian currency with rupee symbol"""
    return u" \u20B9{:,}".format(amount)


if __name__ == "__main__":
    # Target calendar name - hardcoded for safety
    TARGET_CALENDAR = "SIPs"

    data = load_data()
    if not data.empty:
        print("Data loaded successfully.")
        
        # Create a calendar and events for each row
        google_calendar_util = GoogleCalendarUtil()
        google_calendar_util.create_or_use_calendar(TARGET_CALENDAR)
        google_calendar_util.clear_calendar()
        
        # Create events for each recurring payment
        for index, row in data.iterrows():
            create_events(google_calendar_util, row)
    else:
        print("No data to display.")
