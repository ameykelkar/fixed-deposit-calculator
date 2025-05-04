from __future__ import print_function

import os

import pandas as pd
import babel.numbers

from dateutil.relativedelta import relativedelta

from google_calendar import GoogleCalendarUtil


def get_divider(tenure):
    if tenure == "M":
        return 12
    elif tenure == "Q":
        return 4
    elif tenure == "H":
        return 2
    elif tenure == "Y":
        return 1
    else:
        return 0


def fmt_curr(amt):
    return babel.numbers.format_currency(amt.item(), "INR", locale="en_IN")


def calculate_interest(amount, apr, tenure):
    return amount * apr / get_divider(tenure)


def number_of_months(start_date, end_date):
    delta = relativedelta(end_date, start_date)
    return (delta.years * 12) + delta.months


def calculate_total_interest(amount, apr, start_date, end_date):
    return amount * apr / 12 * number_of_months(start_date, end_date)


def create_maturity_events(google_calendar_util, row):
    summary = (
        "FD maturing: "
        + row["NAME OF THE DEPOSITEE"]
        + ": "
        + fmt_curr(row["DEPOSIT AMT"])
        + " - "
        + str(row["DEP NO"])
    )

    description = (
        "Deposit Amount: "
        + fmt_curr(row["DEPOSIT AMT"])
        + "\nDeposit Number: "
        + str(row["DEP NO"])
        + "\nCustomer Number: "
        + str(row["CUST ID"])
    )

    google_calendar_util.create_maturity_event(
        summary, description, row["MATURITY DATE"]
    )


def create_events(google_calendar_util, row):
    apr = row["RATE OF INT."]
    amt = row["DEPOSIT AMT"]
    tenure = row["INTEREST PAYABLE"]
    start_date = row["DATE"]
    end_date = row["MATURITY DATE"]
    frequency = int(12 / get_divider(tenure))
    total_interest = calculate_total_interest(amt, apr, start_date, end_date)

    summary = (
        row["NAME OF THE DEPOSITEE"]
        + ": "
        + fmt_curr(calculate_interest(amt, apr, tenure))
        + " - "
        + str(row["DEP NO"])
    )

    description = (
        "Deposit Amount: "
        + fmt_curr(row["DEPOSIT AMT"])
        + "\nDeposit Number: "
        + str(row["DEP NO"])
        + "\nCustomer Number: "
        + str(row["CUST ID"])
        + "\nTotal Interest: "
        + fmt_curr(total_interest)
        + "\nAmount after Maturity: "
        + fmt_curr(amt + total_interest)
    )

    google_calendar_util.create_event(
        summary=summary,
        description=description,
        start_date=start_date,
        end_date=end_date - pd.Timedelta(1, unit="d"),
        frequency=frequency,
    )


def main():
    # Get the directory where the project is located
    project_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct path to the data file
    data_file_path = os.path.join(project_dir, 'data', 'data.xlsx')

    df = pd.read_excel(data_file_path, sheet_name="vivek fd 2025")

    google_calendar_util = GoogleCalendarUtil()

    google_calendar_util.create_or_use_calendar()

    google_calendar_util.clear_calendar()

    for i in range(len(df)):
        row = df.iloc[i]

        if row["INTEREST PAYABLE"] != "C":
            create_events(google_calendar_util, row)

        create_maturity_events(google_calendar_util, row)


if __name__ == "__main__":
    main()
