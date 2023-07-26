import pandas as pd
import streamlit as st

import io_utils


def remove_footer():
    hide_footer_style = """
    <style>
    footer {visibility: hidden;}
    """
    st.markdown(hide_footer_style, unsafe_allow_html=True)


def initialize_state():
    io_utils.load_data()
    remove_footer()


def update_account_overview(placeholder):
    if not st.session_state.accounts:
        placeholder.markdown("No accounts yet...")
        return
    # compute account balances
    for account in st.session_state.accounts.values():
        account["balance"] = sum(
            transaction["credit"] - transaction["debit"]
            for transaction in st.session_state.transactions.values()
            if transaction["account"] == account["name"]
        )
    df = pd.DataFrame(st.session_state.accounts)
    placeholder.table(df)  # Update the placeholder with the new DataFrame
