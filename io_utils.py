import json
import os

import streamlit as st


def load_app_config():
    return try_load_json_to_dict("config.json")


def try_load_json_to_dict(filename: str) -> dict:
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def try_load_json_to_list(filename: str) -> list:
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def write_json_to_file(filename: str, data: dict):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as f:
        json.dump(data, f)


def load_data():
    st.session_state.accounts = try_load_json_to_dict("_data/accounts.json")
    st.session_state.transactions = try_load_json_to_dict("_data/transactions.json")
    st.session_state.rules = try_load_json_to_dict("_data/rules.json")


def write_data():
    write_json_to_file("_data/accounts.json", st.session_state.accounts)
    write_json_to_file("_data/transactions.json", st.session_state.transactions)
    write_json_to_file("_data/rules.json", st.session_state.rules)


def write_rules():
    write_json_to_file("_data/rules.json", st.session_state.rules)


def write_accounts():
    write_json_to_file("_data/accounts.json", st.session_state.accounts)


def write_transactions():
    write_json_to_file("_data/transactions.json", st.session_state.transactions)
