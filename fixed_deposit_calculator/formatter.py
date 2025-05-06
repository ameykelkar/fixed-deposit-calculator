import streamlit as st
from babel.numbers import format_currency

date_format = "MMM DD, Y"

# Column configuration for the DataFrame
my_column_config = {
    "DEPOSIT AMT": st.column_config.NumberColumn(format="accounting"),
    "RATE OF INT": st.column_config.NumberColumn(format="percent"),
    "INTEREST AMOUNT": st.column_config.NumberColumn(format="accounting"),
    "FY_INTEREST_AMOUNT": st.column_config.NumberColumn(format="accounting"),
    "DATE": st.column_config.DateColumn(format=date_format),
    "MATURITY DATE": st.column_config.DateColumn(format=date_format),
    "NEXT INTEREST DATE": st.column_config.DateColumn(format=date_format),
}

def format_currency_to_inr(value):
    return format_currency(value, 'INR', locale='en_IN')