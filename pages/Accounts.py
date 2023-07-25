import streamlit as st
import schwifty

import io_utils
import state
import render

from Account import Account, Currency


def main():
    app_config = io_utils.load_app_config()
    st.set_page_config(
        page_title=f"Accounts ⋅ {app_config['application_name']}",
        page_icon="💸",
    )
    state.initialize_state()

    st.header("🏦 Accounts")

    st.subheader("Overview")
    account_overview_placeholder = st.empty()

    if not st.session_state.accounts:
        st.write("No accounts yet...")
        return

    st.dataframe(
        st.session_state.accounts.values(),
        hide_index=True,
        column_config=render.get_accounts_column_config(),
    )

    with st.expander("Add new account"):
        account_input = {
            "name": st.text_input("Account name"),
            "bank": st.text_input("Bank (optional)"),
            "account_number": st.text_input("Account number (optional)"),
            "iban": st.text_input("IBAN"),
            "currency": st.selectbox("Currency", ["CHF", "EUR", "USD"]),
            # TODO: I'm pretty sure I'm ignoring this. I should update the code to use this.
            "starting_balance": st.number_input("Initial balance"),
        }
        st.caption(
            "Bank and account number are optional. They are used for automatically detecting transfers between accounts."
        )

        if not schwifty.IBAN(account_input["iban"], allow_invalid=True).is_valid:
            st.error(
                'IBAN is not valid. Please enter a valid IBAN (e.g. "CH93 0076 2011 6238 5295 7")."'
            )

        account_input["currency"] = Currency(account_input["currency"])
        # Initialize balance with starting balance
        account_input["balance"] = account_input["starting_balance"]
        account = Account.from_dict(account_input)

        if not account.is_valid():
            st.error("Both account name and IBAN must be filled in.")

        if account.already_exists(st.session_state.accounts):
            st.error(
                f'Account with name "{account.name}" or IBAN "{account.iban}" already exists.'
            )

        if st.button("Create account"):
            st.session_state.accounts[account.name] = account.as_dict()
            state.update_account_overview(account_overview_placeholder)
            st.success(f"Account {account.name} created.")
            io_utils.write_data()

    with st.expander("Delete account"):
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
