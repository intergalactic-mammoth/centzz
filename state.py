import pandas as pd
import streamlit as st

import io_utils

def initialize_state():
    io_utils.load_data()


def update_account_overview(placeholder):
    if not st.session_state.accounts:
        placeholder.write("No accounts yet...")
        return
    # compute account balances
    for account in st.session_state.accounts.values():
        account['balance'] = sum(transaction['amount'] for transaction in st.session_state.transactions.values() if transaction['account'] == account['name'])
    df = pd.DataFrame(st.session_state.accounts)
    placeholder.table(df)  # Update the placeholder with the new DataFrame
