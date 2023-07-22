import traceback

import streamlit as st
import pandas as pd

import io_utils
import state
import processing


def main():
    app_config = io_utils.load_app_config()

    st.set_page_config(
        page_title=f"Transactions ⋅ {app_config['application_name']}",
        page_icon="💸",
    )
    state.initialize_state()

    st.header("Transactions 📝")
    # Handle transaction input.
    st.header("Upload transactions")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    account_name = st.selectbox(
        "Account", [account["name"] for account in st.session_state.accounts.values()]
    )
    add_transactions = st.button("Add transactions")
    # CSV data look like this:
    # Trade date,Trade time,Booking date,Value date,Currency,Debit,Credit,Individual amount,Balance,Transaction no.,Description1,Description2,Description3,Footnotes
    # 2023-06-26,,2023-06-26,2023-06-26,CHF,-2500,,,25185.49,9915677LK3435687,Interactive Brokers LLC,"IBKR FUND FOR STOCKS + E, Standing order","Reason for payment: U10468788 / Aristotelis Economides, Account no. IBAN: CH20 8909 5000 0105 6967 4, Costs: E-Banking domestic, Transaction no. 9915677LK3435687",
    #
    # Transactions should be saved like this:
    # id, date, beneficiary, description, amount, currency, account, category, tags, notes
    # 9915677LK3435687, 2023-06-26, Interactive Brokers LLC, IBKR FUND FOR STOCKS + E, Standing order, -2500, CHF, IBAN: CH20 8909 5000 0105 6967 4, Investing, ["Interactive Brokers", "Investing"], "Reason for payment: U10468788 / Aristotelis Economides, Costs: E-Banking domestic"
    if uploaded_file is not None and add_transactions:
        try:
            df = pd.read_csv(uploaded_file)
            df.fillna(
                {
                    "Debit": 0,
                    "Credit": 0,
                    "Description1": "",
                    "Description2": "",
                    "Description3": "",
                },
                inplace=True,
            )
            processing.process_transactions(df, account_name)
            state.update_account_overview(st.session_state.account_overview_placeholder)
            io_utils.write_data()
        except Exception as e:
            st.error(
                f"Error reading CSV file: {e}.\nDetailed error:\n{traceback.format_exc()}"
            )


if __name__ == "__main__":
    main()
