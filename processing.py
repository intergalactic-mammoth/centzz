import streamlit as st
import pandas as pd


def create_transaction_from_row(row, account_name):
    return {
        "id": row["Transaction no."],
        "date": row["Trade date"],
        "beneficiary": row["Description1"],
        "description": f'{row["Description2"]} :: {row["Description3"]}',
        "amount": row["Debit"] if row["Debit"] else row["Credit"],
        "currency": st.session_state.accounts[account_name]["currency"],
        "account": account_name,
        "category": "",
        "tags": [],
        "notes": "",
    }


def apply_all_rules_to_all_transactions():
    for transaction_id, transaction in st.session_state.transactions.items():
        st.session_state.transactions[transaction_id] = apply_rules_to_transaction(
            transaction
        )


def apply_rules_to_transaction(transaction):
    for rule in st.session_state.rules.values():
        keywords = [
            contains.strip() for contains in rule["contains"].lower().split(",")
        ]
        if rule["field"] == "beneficiary" and any(
            keyword in transaction["beneficiary"].lower() for keyword in keywords
        ):
            transaction["category"] = rule["category"]
        elif rule["field"] == "description" and any(
            keyword in transaction["description"].lower() for keyword in keywords
        ):
            transaction["category"] = rule["category"]
        else:
            transaction["category"] = "Other"
    return transaction


def process_transactions(df, account_name):
    duplicate_transactions = 0
    for _, row in df.iterrows():
        transaction_id = row["Transaction no."]
        transaction = create_transaction_from_row(row, account_name)
        transaction = apply_rules_to_transaction(transaction)
        if st.session_state.transactions.get(transaction_id):
            duplicate_transactions += 1
        st.session_state.transactions[transaction_id] = transaction
    st.success(f"{len(df)} transactions added.")
    if duplicate_transactions:
        st.warning(f"{duplicate_transactions} duplicate transactions overwritten.")
