import streamlit as st
import pandas as pd

from Currency import Currency
from Transaction import Transaction


def get_accounts_column_config():
    return {
        "name": st.column_config.TextColumn(label="Account name"),
        "bank": st.column_config.TextColumn(label="Bank"),
        "account_number": st.column_config.TextColumn(label="Account number"),
        "iban": st.column_config.TextColumn(label="IBAN"),
        "currency": st.column_config.SelectboxColumn(
            label="Currency", options=[item.value for item in Currency]
        ),
        "balance": st.column_config.NumberColumn(label="Balance"),
        "starting_balance": None,  # hide starting balance
    }


def get_transactions_column_config():
    return {
        "date": st.column_config.DateColumn(
            label="Date",
            format="DD/MM/YYYY",
        ),
        "payee": st.column_config.TextColumn(
            label="Payee",
        ),
        "description": st.column_config.TextColumn(
            label="Description",
        ),
        "debit": st.column_config.NumberColumn(
            label="Debit",
        ),
        "credit": st.column_config.NumberColumn(
            label="Credit",
        ),
        "account": st.column_config.TextColumn(
            label="Account",
        ),
        "currency": st.column_config.SelectboxColumn(
            label="Currency", options=[item.value for item in Currency]
        ),
        "category": st.column_config.TextColumn(
            label="Category",
        ),
    }


def transactions_table(transactions: list[Transaction]):
    if not transactions:
        return
    df = pd.DataFrame([transaction.as_dict() for transaction in transactions])
    # Convert string date to datetime
    df["date"] = pd.to_datetime(df["date"])
    # Sort by date
    df = df.sort_values(by="date", ascending=False)
    # Remove uid and transaction_id columns
    df = df.drop(columns=["transaction_id", "transfer_to", "transfer_from"])
    # TODO: Ask user if they want to save changes before applying them
    st.dataframe(
        df,
        hide_index=True,
        column_config=get_transactions_column_config(),
    )
