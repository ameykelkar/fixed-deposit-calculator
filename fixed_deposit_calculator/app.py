import io
import os

import streamlit as st
import pandas as pd
import datetime
import hashlib

from cryptography.fernet import Fernet
from dateutil.relativedelta import relativedelta

from fixed_deposit_calculator.formatter import my_column_config, format_currency_to_inr

# Set page config
st.set_page_config(page_title="Fixed Deposit Interest Calculator", layout="wide")


@st.cache_data(show_spinner=False)
def load_key() -> bytes:
    """
    Load the Fernet key from Streamlit secrets.
    """
    key_str = st.secrets["cryptography"]["fernet_key"]
    return key_str.encode()


@st.cache_data(show_spinner=False)
def get_password_hash() -> str:
    """
    Get the hashed password from Streamlit secrets.
    """
    # Default to 'password' if not set in secrets
    try:
        return st.secrets["authentication"]["password_hash"]
    except KeyError:
        # This is just a fallback in case secrets aren't configured
        # Using a hardcoded hash of 'password' as default
        return "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"  # SHA-256 of 'password'


def verify_password(password: str) -> bool:
    """
    Verify if the provided password matches the stored hash.
    """
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    return password_hash == get_password_hash()


def decrypt_bytes(encrypted_data: bytes, key: bytes) -> bytes:
    """
    Decrypt a chunk of bytes and return the plaintext bytes.
    """
    f = Fernet(key)
    return f.decrypt(encrypted_data)


enc_path = os.path.join(os.path.dirname(__file__), "data.xlsx.enc")


# Function to calculate next interest date based on frequency and start date
def calculate_next_interest_date(start_date, frequency, today, maturity_date):
    if frequency not in ["H", "Y", "Q", "M", "C"]:
        return None

    if frequency == "C":  # Cumulative - interest paid at maturity
        return maturity_date  # Interest paid at maturity for cumulative deposits

    # Convert start_date to datetime if it's not already
    if isinstance(start_date, str):
        start_date = pd.to_datetime(start_date)

    # Initialize the next interest date to the start date
    next_date = start_date

    # Define the delta based on frequency
    if frequency == "M":  # Monthly
        delta = relativedelta(months=1)
    elif frequency == "Q":  # Quarterly
        delta = relativedelta(months=3)
    elif frequency == "H":  # Half-yearly
        delta = relativedelta(months=6)
    elif frequency == "Y":  # Yearly
        delta = relativedelta(years=1)

    # Convert today to pandas Timestamp for comparison
    today_ts = pd.Timestamp(today)
    maturity_ts = (
        pd.Timestamp(maturity_date)
        if not isinstance(maturity_date, pd.Timestamp)
        else maturity_date
    )

    # Find the next interest date after today
    while next_date <= today_ts:
        next_date += delta
        # If next interest date exceeds maturity date, interest will be paid at maturity
        if next_date > maturity_ts:
            return maturity_date

    return next_date


# Function to calculate all interest dates for a financial year
def calculate_financial_year_interest_dates(
    start_date, frequency, fy_start, fy_end, maturity_date
):
    if frequency not in ["H", "Y", "Q", "M", "C"]:
        return []

    # Convert all dates to pandas Timestamp for consistent comparison
    start_date_ts = pd.Timestamp(start_date)
    fy_start_ts = pd.Timestamp(fy_start)
    fy_end_ts = pd.Timestamp(fy_end)
    maturity_date_ts = pd.Timestamp(maturity_date)

    if frequency == "C":  # Cumulative - only if maturity is within the financial year
        if fy_start_ts <= maturity_date_ts <= fy_end_ts:
            return [maturity_date_ts]
        return []

    # Define the delta based on frequency
    if frequency == "M":  # Monthly
        delta = relativedelta(months=1)
    elif frequency == "Q":  # Quarterly
        delta = relativedelta(months=3)
    elif frequency == "H":  # Half-yearly
        delta = relativedelta(months=6)
    elif frequency == "Y":  # Yearly
        delta = relativedelta(years=1)

    # Initialize dates list and the current date
    interest_dates = []
    current_date = start_date_ts

    # Find all interest dates that fall within the financial year
    while current_date <= fy_end_ts:
        if current_date >= fy_start_ts and current_date <= fy_end_ts:
            if (
                current_date <= maturity_date_ts
            ):  # Only include if before or equal to maturity
                interest_dates.append(current_date)

        current_date += delta
        if current_date > maturity_date_ts:
            # If maturity is within financial year, add it as the final payment
            if (
                maturity_date_ts >= fy_start_ts
                and maturity_date_ts <= fy_end_ts
                and maturity_date_ts not in interest_dates
            ):
                interest_dates.append(maturity_date_ts)
            break

    return interest_dates


# Function to calculate interest amount for a single payment
def calculate_interest_amount(deposit_amt, rate, frequency):
    # Convert annual rate to the rate for the specific frequency
    if frequency == "M":
        return deposit_amt * rate / 12
    elif frequency == "Q":
        return deposit_amt * rate / 4
    elif frequency == "H":
        return deposit_amt * rate / 2
    elif frequency == "Y":
        return deposit_amt * rate
    elif frequency == "C":  # For cumulative, show simple interest for now
        return deposit_amt * rate
    else:
        return 0


def check_authentication():
    """Check if the user is authenticated and handle the login process.
    Returns True if authenticated, False otherwise."""
    # Initialize session state for authentication
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("Fixed Deposit Interest Calculator")
        st.subheader("Login Required")
        
        # Create login form
        with st.form("login_form"):
            password = st.text_input("Enter Password", type="password")
            submit_button = st.form_submit_button("Login")
            
            if submit_button:
                if verify_password(password):
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Incorrect password. Please try again.")
        
        # User is not authenticated
        return False
    
    # User is authenticated
    return True


# Main function
def main():
    # Check authentication before proceeding
    if not check_authentication():
        return
    
    # Only execute the rest of the code if authenticated
    st.title("Fixed Deposit Interest Calculator")

    # Display current date
    today = datetime.date.today()
    st.write(f"Current Date: {today.strftime('%B %d, %Y')}")

    # Define financial year
    if today.month >= 4:  # April onwards is the new financial year
        fy_start = pd.Timestamp(datetime.date(today.year, 4, 1))
        fy_end = pd.Timestamp(datetime.date(today.year + 1, 3, 31))
    else:  # Jan-Mar is part of the previous financial year
        fy_start = pd.Timestamp(datetime.date(today.year - 1, 4, 1))
        fy_end = pd.Timestamp(datetime.date(today.year, 3, 31))

    # Read the Excel file
    try:
        # Load the key
        key = load_key()

        # Get decrypted data
        if not os.path.exists(enc_path):
            st.error(f"Encrypted file `{enc_path}` not found.")

        # 1. Read encrypted bytes
        encrypted_bytes = open(enc_path, "rb").read()

        # 2. Decrypt in memory
        decrypted_bytes = decrypt_bytes(encrypted_bytes, key)

        # 3. Load into pandas via BytesIO
        df = pd.read_excel(io.BytesIO(decrypted_bytes))

        # Convert date columns to datetime
        df["DATE"] = pd.to_datetime(df["DATE"])
        df["MATURITY DATE"] = pd.to_datetime(df["MATURITY DATE"])

        # Calculate the next interest date for each deposit
        df["NEXT INTEREST DATE"] = df.apply(
            lambda row: calculate_next_interest_date(
                row["DATE"], row["INTEREST PAYABLE"], today, row["MATURITY DATE"]
            ),
            axis=1,
        )

        # Calculate interest amount
        df["INTEREST AMOUNT"] = df.apply(
            lambda row: calculate_interest_amount(
                row["DEPOSIT AMT"], row["RATE OF INT"], row["INTEREST PAYABLE"]
            ),
            axis=1,
        )

        # Calculate and add all financial year interest dates and amounts
        df["FY_INTEREST_DATES"] = df.apply(
            lambda row: calculate_financial_year_interest_dates(
                row["DATE"],
                row["INTEREST PAYABLE"],
                fy_start,
                fy_end,
                row["MATURITY DATE"],
            ),
            axis=1,
        )

        # Calculate financial year interest amount for each deposit
        df["FY_INTEREST_AMOUNT"] = df.apply(
            lambda row: (
                len(row["FY_INTEREST_DATES"])
                * calculate_interest_amount(
                    row["DEPOSIT AMT"], row["RATE OF INT"], row["INTEREST PAYABLE"]
                )
                if row["INTEREST PAYABLE"] != "C"
                else (
                    calculate_interest_amount(
                        row["DEPOSIT AMT"], row["RATE OF INT"], row["INTEREST PAYABLE"]
                    )
                    if any(date <= fy_end for date in row["FY_INTEREST_DATES"])
                    else 0
                )
            ),
            axis=1,
        )

        # Create a column to flag deposits with interest due this month
        df["DUE THIS MONTH"] = df["NEXT INTEREST DATE"].apply(
            lambda x: pd.notnull(x)
            and pd.Timestamp(x).month == today.month
            and pd.Timestamp(x).year == today.year
        )

        # Format currency columns for display
        display_df = df.copy()

        # Convert frequency codes to full text
        frequency_map = {
            "M": "Monthly",
            "Q": "Quarterly",
            "H": "Half-yearly",
            "Y": "Yearly",
            "C": "Cumulative",
        }
        display_df["INTEREST PAYABLE"] = display_df["INTEREST PAYABLE"].map(
            frequency_map
        )

        # Display all deposits
        st.header("All Fixed Deposits")
        st.dataframe(
            display_df[
                [
                    "DEP NO",
                    "NAME OF THE DEPOSITEE",
                    "DATE",
                    "MATURITY DATE",
                    "DEPOSIT AMT",
                    "RATE OF INT",
                    "INTEREST PAYABLE",
                    "NEXT INTEREST DATE",
                    "INTEREST AMOUNT",
                ]
            ].astype(str),
            hide_index=True,
            use_container_width=True,
            column_config=my_column_config
        )

        # Filter deposits with interest due this month
        this_month_df = df[df["DUE THIS MONTH"] == True]
        display_this_month_df = display_df[df["DUE THIS MONTH"] == True]

        # Summary section
        st.markdown("---")
        st.header(f"Interest Summary for {today.strftime('%B %Y')}")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Deposits", len(df))
            st.metric("Deposits with Interest Due This Month", len(this_month_df))

        with col2:
            total_deposit = df["DEPOSIT AMT"].sum()
            st.metric("Total Deposit Amount", format_currency_to_inr(total_deposit))
            total_interest = this_month_df["INTEREST AMOUNT"].sum()
            st.metric("Total Interest Due This Month", format_currency_to_inr(total_interest))

        # Create tabs for all months with interest due
        st.markdown("---")
        
        # Get all unique months where deposits have interest due (current and future)
        # First, filter out nulls and get all unique next interest dates
        valid_interest_dates = df[df["NEXT INTEREST DATE"].notnull()]["NEXT INTEREST DATE"].unique()
        
        # Create a list of (year, month) tuples for sorting
        month_year_tuples = [(pd.Timestamp(date).year, pd.Timestamp(date).month) for date in valid_interest_dates]
        month_year_tuples = sorted(list(set(month_year_tuples)))
        
        # Filter to include only current and future months
        current_tuple = (today.year, today.month)
        future_months = [(y, m) for y, m in month_year_tuples if (y > today.year) or (y == today.year and m >= today.month)]
        
        # Create month names for tabs
        months = [datetime.date(y, m, 1).strftime('%B %Y') for y, m in future_months]
        
        # Create tabs
        if months:
            # Add a heading before the tabs
            st.header("Deposits with Interest Due")
            
            tabs = st.tabs(months)
            
            # For each month tab
            for i, (tab, (year, month)) in enumerate(zip(tabs, future_months)):
                with tab:
                    month_date = datetime.date(year, month, 1)
                    
                    # Add the month as a subheader inside the tab
                    st.subheader(f"{month_date.strftime('%B %Y')}")
                    
                    # Filter deposits with interest due in this month
                    month_df = df[df["NEXT INTEREST DATE"].apply(
                        lambda x: pd.notnull(x) 
                        and pd.Timestamp(x).month == month 
                        and pd.Timestamp(x).year == year
                    )]
                    
                    display_month_df = display_df[df["NEXT INTEREST DATE"].apply(
                        lambda x: pd.notnull(x) 
                        and pd.Timestamp(x).month == month 
                        and pd.Timestamp(x).year == year
                    )]
                    
                    if not month_df.empty:
                        st.dataframe(
                            display_month_df[
                                [
                                    "DEP NO",
                                    "NAME OF THE DEPOSITEE",
                                    "DATE",
                                    "DEPOSIT AMT",
                                    "RATE OF INT",
                                    "INTEREST PAYABLE",
                                    "NEXT INTEREST DATE",
                                    "INTEREST AMOUNT",
                                ]
                            ].astype(str),
                            hide_index=True,
                            use_container_width=True,
                            column_config=my_column_config,
                        )
                        
                        # Calculate total interest for this month
                        month_total_interest = month_df["INTEREST AMOUNT"].sum()
                        
                        # Calculate interest for the previous month
                        prev_month_date = month_date - pd.DateOffset(months=1)
                        prev_month_df = df[df["NEXT INTEREST DATE"].apply(
                            lambda x: pd.notnull(x) 
                            and pd.Timestamp(x).month == prev_month_date.month 
                            and pd.Timestamp(x).year == prev_month_date.year
                        )]
                        
                        prev_month_total_interest = prev_month_df["INTEREST AMOUNT"].sum() if not prev_month_df.empty else 0
                        
                        # Calculate difference and determine arrow direction
                        interest_diff = month_total_interest - prev_month_total_interest
                        diff_percentage = (interest_diff / prev_month_total_interest * 100) if prev_month_total_interest > 0 else 0
                        
                        # Format the difference message with arrows
                        if interest_diff > 0:
                            diff_message = f"↑ {format_currency_to_inr(interest_diff)} (+{diff_percentage:.2f}%) compared to {prev_month_date.strftime('%B %Y')}"
                            diff_color = "green"
                        elif interest_diff < 0:
                            diff_message = f"↓ {format_currency_to_inr(abs(interest_diff))} (-{abs(diff_percentage):.2f}%) compared to {prev_month_date.strftime('%B %Y')}"
                            diff_color = "red"
                        else:
                            diff_message = f"No change compared to {prev_month_date.strftime('%B %Y')}"
                            diff_color = "gray"
                        
                        # Display interest metrics
                        st.success(
                            f"Total interest to be received in {month_date.strftime('%B %Y')}: {format_currency_to_inr(month_total_interest)}"
                        )
                        
                        # Display the comparison with previous month
                        if prev_month_total_interest > 0 or interest_diff != 0:
                            st.markdown(f"<span style='color:{diff_color};'>{diff_message}</span>", unsafe_allow_html=True)
                        else:
                            st.info(f"No interest data available for {prev_month_date.strftime('%B %Y')} for comparison")
                    else:
                        st.info(f"No deposits will pay interest in {month_date.strftime('%B %Y')}")
        else:
            st.info("No deposits with future interest payments found")

        # Display financial year interest summary
        st.markdown("---")
        st.header(
            f"Financial Year Interest Summary ({fy_start.strftime('%b %d, %Y')} to {fy_end.strftime('%b %d, %Y')})"
        )

        # Create a dataframe with just FY interest info
        fy_df = df[df["FY_INTEREST_AMOUNT"] > 0].copy()

        if not fy_df.empty:
            # Format for display
            fy_display_df = fy_df.copy()

            fy_display_df["INTEREST PAYABLE"] = fy_display_df["INTEREST PAYABLE"].map(
                frequency_map
            )
            fy_display_df["INTEREST FREQUENCY"] = fy_display_df[
                "FY_INTEREST_DATES"
            ].apply(lambda x: f"{len(x)} payment(s)")

            # Show the table
            st.dataframe(
                fy_display_df[
                    [
                        "DEP NO",
                        "NAME OF THE DEPOSITEE",
                        "DEPOSIT AMT",
                        "RATE OF INT",
                        "INTEREST PAYABLE",
                        "INTEREST FREQUENCY",
                        "FY_INTEREST_AMOUNT",
                    ]
                ].astype(str),
                hide_index=True,
                use_container_width=True,
                column_config=my_column_config,
            )

            # Show total FY interest
            total_fy_interest = fy_df["FY_INTEREST_AMOUNT"].sum()
            st.success(
                f"Total interest earned in financial year {fy_start.year}-{fy_end.year}: {format_currency_to_inr(total_fy_interest)}"
            )
        else:
            st.info(
                f"No interest earned in financial year {fy_start.year}-{fy_end.year}"
            )

    except Exception as e:
        st.error(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
