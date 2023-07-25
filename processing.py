import logging

import streamlit as st
import pandas as pd

from Transaction import Transaction
from Account import Account


def create_transaction_from_row(row, account: Account, headers: dict):
    return Transaction(
        transaction_id=row[headers["transaction_id"]],
        date=pd.to_datetime(row[headers["date"]]).isoformat(),
        payee=row[headers["payee"]],
        description=", ".join(
            [
                row[header]
                for header in headers["description"]
                if row[header] and not pd.isna(row[header])
            ]
        )
        if headers["description"]
        else "",
        debit=row[headers["debit"]] if not pd.isna(row[headers["debit"]]) else 0.0,
        credit=row[headers["credit"]] if not pd.isna(row[headers["credit"]]) else 0.0,
        account=account.name,
        currency=account.currency,
    )


def handle_if_transfer(transaction: Transaction):
    for account in st.session_state.accounts.values():
        transaction_description = transaction.description.lower().strip(" ")
        if (account["iban"].lower().strip(" ") in transaction_description) or (
            account["account_number"].lower().strip(" ") in transaction_description
        ):
            logging.info(f"Found transfer to {account['name']}")
            transaction.transfer_to = account["name"]
            transaction.transfer_from = transaction.account
    return transaction


def apply_all_rules_to_all_transactions():
    for transaction_id, transaction in st.session_state.transactions.items():
        transaction = Transaction.from_dict(transaction)
        transaction.categorize(st.session_state.rules.values())
        st.session_state.transactions[transaction_id] = transaction.as_dict()


def process_transactions(df: pd.DataFrame, account: Account, headers: dict):
    duplicate_transactions = 0
    for _, row in df.iterrows():
        transaction = create_transaction_from_row(row, account, headers)
        transaction = handle_if_transfer(transaction)
        transaction.categorize(st.session_state.rules.values())
        if st.session_state.transactions.get(transaction.transaction_id):
            duplicate_transactions += 1
        st.session_state.transactions[
            transaction.transaction_id
        ] = transaction.as_dict()
    st.success(f"{len(df)} transactions added.")
    if duplicate_transactions:
        st.warning(f"{duplicate_transactions} duplicate transactions overwritten.")
