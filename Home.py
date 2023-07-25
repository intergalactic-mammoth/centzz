import json
import logging
import traceback

import pandas as pd
import streamlit as st

import io_utils
import plotting
import processing
import render
import state


def display_transactions():
    processing.apply_all_rules_to_all_transactions()
    df = pd.DataFrame(st.session_state.transactions.values())
    edited_df = st.data_editor(df)
    if edited_df is not None:
        st.session_state.transactions = {
            transaction["id"]: transaction
            for transaction in edited_df.to_dict("records")
        }
        io_utils.write_data()


def main():
    logging.basicConfig(level=logging.DEBUG)
    app_config = io_utils.load_app_config()

    st.set_page_config(
        page_title=app_config["application_name"],
        page_icon="💸",
    )
    state.initialize_state()

    st.title("💸 centzz")
    st.caption("Your dead-simple personal finances app")

    st.header("Accounts")

    if not st.session_state.accounts:
        st.write("No accounts yet...")
    else:
        st.dataframe(
            st.session_state.accounts.values(),
            hide_index=True,
            column_config=render.get_accounts_column_config(),
        )

    # Display current transactions
    st.header("Transactions")
    if not st.session_state.transactions:
        st.write("No transactions yet...")
    else:
        render.transactions_table(st.session_state.transactions.values())

    # Plots
    st.header("Plots")
    # Plot running balance over time
    if st.session_state.transactions:
        transactions_list = list(st.session_state.transactions.values())
        balance_df = pd.DataFrame(
            {
                "date": [transaction["date"] for transaction in transactions_list],
                "amount": [
                    transaction["credit"] - transaction["debit"]
                    for transaction in transactions_list
                ],
            }
        )
        balance_df["date"] = pd.to_datetime(balance_df["date"])
        balance_df.sort_values("date", inplace=True)
        balance_df["balance"] = balance_df["amount"].cumsum()

        plotting.create_line_chart(
            balance_df, "date", "balance", "Running Balance Over Time"
        )

        # Plot expenses by category and account
        transactions_df = pd.DataFrame(
            [
                {
                    "date": transaction["date"],
                    "category": transaction["category"],
                    "amount": transaction["debit"],
                    "account": transaction["account"],
                }
                for transaction in transactions_list
                if transaction["debit"] > 0 and transaction["category"] != "Transfer"
            ]
        )
        transactions_df["date"] = pd.to_datetime(transactions_df["date"])

        period_grouping = st.selectbox("Group expenses by", ["Day", "Month", "Year"])
        if period_grouping == "Year":
            transactions_df["date"] = (
                transactions_df["date"].dt.to_period("Y").dt.to_timestamp()
            )
        elif period_grouping == "Month":
            transactions_df["date"] = (
                transactions_df["date"].dt.to_period("M").dt.to_timestamp()
            )
        else:  # Default to grouping by day
            transactions_df["date"] = (
                transactions_df["date"].dt.to_period("D").dt.to_timestamp()
            )
        # Group by date and category
        transactions_df = (
            transactions_df.groupby(["date", "category"])["amount"]
            .sum()
            .unstack(fill_value=0)
        )
        plotting.create_bar_chart(transactions_df, "Expenses Over Time")
    else:
        st.write("No data to plot yet...")


if __name__ == "__main__":
    main()
