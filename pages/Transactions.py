import traceback

import streamlit as st
import pandas as pd

import io_utils
import state
import processing
import render

from Account import Account


def main():
    app_config = io_utils.load_app_config()

    st.set_page_config(
        page_title=f"Transactions ⋅ {app_config['application_name']}",
        page_icon="💸",
    )
    state.initialize_state()

    st.header("📖 Transactions")

    if not st.session_state.accounts:
        st.write("No accounts found... Please add an account first.")
        return

    with st.expander("Add transactions from CSV"):
        if csv_file := st.file_uploader(
            "Choose a CSV file", type="csv", key="current_file"
        ):
            # Parse headers of CSV file to map them to transaction columns
            st.write("Choose the correct column for each transaction field:")
            df = pd.read_csv(csv_file)
            transaction_id_header = st.selectbox("Transaction ID", df.columns)
            date_header = st.selectbox("Date", df.columns)
            payee_header = st.selectbox("Payee", df.columns)
            description_header = st.multiselect("Description(s)", df.columns)
            credit_header = st.selectbox("Credit", df.columns)
            debit_header = st.selectbox("Debit", df.columns)

            headers = {
                "transaction_id": transaction_id_header,
                "date": date_header,
                "payee": payee_header,
                "description": tuple(description_header)
                if description_header
                else None,
                "credit": credit_header,
                "debit": debit_header,
            }

            account_selection = st.selectbox(
                "Account",
                [account["name"] for account in st.session_state.accounts.values()],
            )

            # Make sure that all headers are different, and that all headers are selected
            if len(set(headers.values())) != len(headers.values()):
                st.error("All headers must be different.")
                return
            if None in headers.values():
                st.error("All headers must be set.")
                return

            add_transactions = st.button("Add transactions")
            if add_transactions and account_selection:
                try:
                    account = Account.from_dict(
                        st.session_state.accounts[account_selection]
                    )
                    processing.process_transactions(
                        df,
                        account,
                        headers,
                    )
                    account.balance = sum(
                        transaction["credit"] - transaction["debit"]
                        for transaction in st.session_state.transactions.values()
                        if transaction["account"] == account.name
                    )
                    st.session_state.accounts[account.name] = account.as_dict()
                    io_utils.write_data()
                except Exception as e:
                    st.error(
                        f"Error reading CSV file: {e}.\nDetailed error:\n{traceback.format_exc()}"
                    )

    if not st.session_state.transactions:
        st.write("No transactions yet...")
        return

    st.caption("All transactions")
    render.transactions_table(st.session_state.transactions.values())


if __name__ == "__main__":
    main()
