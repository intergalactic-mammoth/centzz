import json
import logging
import traceback

import pandas as pd
import streamlit as st

import plotting
import processing
import io_utils
import state

def main():
    logging.basicConfig(level=logging.DEBUG)
    app_config = io_utils.load_app_config()

    st.set_page_config(
        page_title=app_config['application_name'],
        page_icon="💸",
    )
    state.initialize_state()

    st.title("centzz 💸")

    st.header("Accounts")
    # Create a placeholder for the account overview
    st.session_state.account_overview_placeholder = st.empty()

    # Initial update of account overview
    state.update_account_overview(st.session_state.account_overview_placeholder)

    # Display current transactions
    st.header("Transactions")
    if st.session_state.transactions:
        processing.apply_all_rules_to_all_transactions()
        df = pd.DataFrame(st.session_state.transactions.values())
        edited_df = st.data_editor(df)
        if edited_df is not None:
            st.session_state.transactions = {transaction['id']: transaction for transaction in edited_df.to_dict('records')}
            io_utils.write_data()
    else:
        st.write("No transactions yet...")

    # Plots
    st.header("Plots")
    # Plot running balance over time
    if st.session_state.transactions:
        balance_df = pd.DataFrame({
            'date': [transaction['date'] for transaction in st.session_state.transactions.values()],
            'balance': [transaction['amount'] for transaction in st.session_state.transactions.values()]
        })
        balance_df['date'] = pd.to_datetime(balance_df['date'])
        balance_df.sort_values('date', inplace=True)
        balance_df['running_balance'] = balance_df['balance'].cumsum()
        plotting.create_line_chart(balance_df, 'date', 'running_balance', 'Running Balance Over Time')

        # Plot expenses by category and account
        transactions_df = pd.DataFrame(st.session_state.transactions.values())
        transactions_df['date'] = pd.to_datetime(transactions_df['date'])
        period_grouping = st.selectbox('Group expenses by', ['Day', 'Month', 'Year'])
        if period_grouping == 'Day':
            transactions_df['date'] = transactions_df['date'].dt.to_period('D').dt.to_timestamp()
        elif period_grouping == 'Month':
            transactions_df['date'] = transactions_df['date'].dt.to_period('M').dt.to_timestamp()
        else:  # Default to grouping by year
            transactions_df['date'] = transactions_df['date'].dt.to_period('Y').dt.to_timestamp()
        # Filter out income
        transactions_df = transactions_df[transactions_df['amount'] < 0]
        # Reverse sign of amounts
        transactions_df['amount'] = transactions_df['amount'].abs()
        # Filter out transfers
        transactions_df = transactions_df[transactions_df['category'] != 'Transfer']
        # Group by date and category
        transactions_df = transactions_df.groupby(['date', 'category'])['amount'].sum().unstack(fill_value=0)
        plotting.create_bar_chart(transactions_df, 'Expenses Over Time')
    else:
        st.write("No data to plot yet...")

if __name__ == "__main__":
    main()
