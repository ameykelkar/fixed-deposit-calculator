import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


class GoogleCalendarUtil:
    service = None
    calendar_id = None
    # Get the directory where the project is located
    project_dir = os.path.dirname(os.path.abspath(__file__))

    def __init__(self):
        creds = None
        scope = ["https://www.googleapis.com/auth/calendar"]
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", scope)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", scope
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(creds.to_json())

        self.service = build("calendar", "v3", credentials=creds)

    @staticmethod
    def parse_date(date):
        return date.strftime("%Y-%m-%d")

    @staticmethod
    def parse_date_without_hyphens(date):
        return date.strftime("%Y%m%d")

    def create_or_use_calendar(self, calendar_summary):
        calendar_list = self.service.calendarList().list(maxResults=2500).execute()
        for calendar in calendar_list["items"]:
            if calendar["summary"] == calendar_summary:
                self.calendar_id = calendar["id"]
                print("Calendar already exists: " + self.calendar_id)
                return

        calendar = {"summary": calendar_summary, "timeZone": "Asia/Kolkata"}

        created_calendar = self.service.calendars().insert(body=calendar).execute()

        self.calendar_id = created_calendar["id"]
        print("Calendar created: " + self.calendar_id)

    def clear_calendar(self):
        events = self.get_all_events()

        for event in events["items"]:
            self.service.events().delete(
                calendarId=self.calendar_id, eventId=event["id"]
            ).execute()

        print("Cleared all calendar events.")

    def create_event(self, summary, description, start_date, frequency, end_date=None):
        event = {"summary": summary, "description": description,
                 "start": {"date": str(GoogleCalendarUtil.parse_date(start_date))}, "end": {
                "date": str(self.parse_date(start_date)),
            }, "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 900},
                    {"method": "email", "minutes": 900},
                ],
            }, "recurrence": [self._create_monthly_recurrence_rule(end_date, frequency)]}
        
        # Set recurrence rule

        event = (
            self.service.events()
            .insert(calendarId=self.calendar_id, body=event)
            .execute()
        )
        print("Event created: %s" % (event.get("htmlLink")))
        
    def _create_monthly_recurrence_rule(self, end_date, frequency):
        """Create a monthly recurrence rule.
        
        Args:
            end_date: End date for the recurrence. If None, recurrence continues indefinitely.
            frequency: The interval for recurrence (e.g., 1 for every month).
            
        Returns:
            A string with the formatted recurrence rule.
        """
        if end_date is not None:
            return (
                "RRULE:FREQ=MONTHLY;UNTIL=" 
                + str(self.parse_date_without_hyphens(end_date))
                + ";INTERVAL=" 
                + str(frequency)
            )
        else:
            # For indefinite recurrence, omit the UNTIL part
            return "RRULE:FREQ=MONTHLY;INTERVAL=" + str(frequency)

    def create_maturity_event(self, summary, description, end_date):
        event = {
            "summary": summary,
            "description": description,
            "start": {"date": str(GoogleCalendarUtil.parse_date(end_date))},
            "end": {"date": str(GoogleCalendarUtil.parse_date(end_date))},
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 10980},
                    {"method": "email", "minutes": 10980},
                ],
            },
        }

        event = (
            self.service.events()
            .insert(calendarId=self.calendar_id, body=event)
            .execute()
        )
        print("Maturity event created: %s" % (event.get("htmlLink")))

    def get_all_events(self):
        return (
            self.service.events()
            .list(calendarId=self.calendar_id, maxResults=2500)
            .execute()
        )
