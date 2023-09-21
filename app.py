import uuid

import streamlit as st
import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd


def get_divider(tenure):
    if tenure == "Monthly":
        return 12
    elif tenure == "Quarterly":
        return 4
    elif tenure == "Half Yearly":
        return 2
    elif tenure == "Yearly":
        return 1
    else:
        return 0


def get_multiplier(tenure):
    if tenure == "Monthly":
        return 1
    elif tenure == "Quarterly":
        return 3
    elif tenure == "Half Yearly":
        return 6
    elif tenure == "Yearly":
        return 12
    else:
        return 0


def calculate_interest(amount, apr, tenure):
    return round(amount / 100 * apr / get_divider(tenure), 2)


def calculate_total_interest(amount, apr, start_date, end_date):
    return round(amount / 100 * apr / 12 * number_of_months(start_date, end_date), 2)


def calculate_dates(start_date, end_date, interest, amount, tenure):
    dates = []
    interest_arr = []
    amt_arr = []

    data = {"Date": dates, "Interest": interest, "Current Amount": amt_arr}
    while start_date <= end_date:
        dates.append(start_date.strftime("%m/%d/%Y"))
        interest_arr.append(interest)
        amt_arr.append(amount)
        amount = amount + interest
        start_date = start_date + relativedelta(months=+get_multiplier(tenure))
    return data


def number_of_months(start_date, end_date):
    delta = relativedelta(end_date, start_date)
    return (delta.years * 12) + delta.months


st.title("Fixed Deposit Calculator")

num1, num2 = st.columns(2)
amount = num1.number_input("Amount", value=500000)
apr = num2.number_input("Rate of Interest", value=7.65)

date_time_format = "DD/MM/YYYY"
date1, date2 = st.columns(2)
start_date = date1.date_input("Start Date", format=date_time_format, value=datetime.datetime(2023, 1, 7).date())
end_date = date2.date_input("End Date", format=date_time_format, value=datetime.datetime(2028, 7, 7).date())

tenure = st.selectbox("Interest Payable", ("Quarterly", "Monthly", "Half Yearly", "Yearly"))

st.divider()

stats1, stats2, stats3 = st.columns(3)

total_interest = calculate_total_interest(amount, apr, start_date, end_date)
interest = calculate_interest(amount, apr, tenure)

stats1.subheader("Installment Amount: " + str(interest))
stats2.subheader("Total Interest Amount: " + str(total_interest))
stats3.subheader("Total Amount after Maturity: " + str(round(amount + total_interest, 2)))

st.text("Total months: " + str(number_of_months(start_date, end_date)))

st.divider()

data = pd.DataFrame(calculate_dates(start_date, end_date, interest, amount, tenure))

st.table(data)
