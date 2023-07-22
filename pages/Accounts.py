import streamlit as st

import io_utils
import state


def account_exists(account: dict) -> bool:
    # Name and IBAN must both be unique
    for existing_account in st.session_state.accounts.values():
        if (
            account["name"] == existing_account["name"]
            or account["iban"] == existing_account["iban"]
        ):
            return True
    return False


def account_is_valid(account: dict) -> bool:
    if not account["name"] or not account["iban"]:
        st.warning("Both account name and IBAN must be filled in.")
        return False
    if account_exists(account):
        st.error(
            f'Account with name "{account["name"]}" or IBAN "{account["iban"]}" already exists.'
        )
        return False
    return True


def main():
    app_config = io_utils.load_app_config()
    st.set_page_config(
        page_title=f"Accounts ⋅ {app_config['application_name']}",
        page_icon="💸",
    )
    state.initialize_state()

    st.header("Accounts 🏦")

    st.subheader("Overview")
    account_overview_placeholder = st.empty()

    # Initial update of account overview
    state.update_account_overview(account_overview_placeholder)

    st.subheader("Add new account")
    account = {
        "name": st.text_input("Account name"),
        "iban": st.text_input("IBAN"),
        "currency": st.selectbox("Currency", ["CHF", "EUR", "USD"]),
        # TODO: I'm pretty sure I'm ignoring this. I should update the code to use this.
        "balance": st.number_input("Initial balance"),
    }
    if st.button("Create account") and account_is_valid(account):
        st.session_state.accounts[account["name"]] = account
        state.update_account_overview(account_overview_placeholder)
        st.success(f'Account {account["name"]} created.')
        io_utils.write_data()

    st.subheader("Delete account")
    account_to_delete = st.selectbox(
        "Account to delete", st.session_state.accounts.keys()
    )
    if st.button("Delete account"):
        del st.session_state.accounts[account_to_delete]
        state.update_account_overview(account_overview_placeholder)
        st.success(f"Account {account_to_delete} deleted.")
        io_utils.write_data()


if __name__ == "__main__":
    main()
