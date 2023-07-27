import logging
import traceback
import uuid

import pandas as pd
import streamlit as st

import io_utils
import plotting
import render
import state

from Account import Account
from Currency import Currency
from ExpenseTracker import ExpenseTracker
from Transaction import Transaction
from Rule import Rule, RuleRelation, RuleAction, RuleCondition

BASE_LOGGER = logging.getLogger(__name__)


def rule_options(header: str, transactions: list[Transaction]):
    df = pd.DataFrame([transaction.as_dict() for transaction in transactions])
    return df[header].unique()


def add_rule(expense_tracker: ExpenseTracker):
    transactions = expense_tracker.get_transactions()
    if not transactions:
        st.write("No transactions yet... Please add transactions first.")
        return

    # TODO: This only makes sense if I can add multiple conditions.
    # rule_type = st.selectbox("Rule type", [rule.value for rule in RuleType])

    if "rule_rows" not in st.session_state:
        st.session_state["rule_rows"] = 0

    left, middle, right = st.columns([1, 1, 2])
    target = left.selectbox(
        "Target", list(Transaction.data_model().keys()), key="target_"
    )
    relation = middle.selectbox("Relation", list(RuleRelation), key="relation_")
    if relation == RuleRelation.EQUALS:
        rule_value = right.selectbox(
            "Value", key="value_", options=rule_options(target, transactions)
        )
        rule_value = [rule_value]
    elif relation == RuleRelation.CONTAINS:
        rule_value = right.text_input("Value", key="value_")
        rule_value = [rule_value]
    elif relation == RuleRelation.ONE_OF:
        rule_value = right.multiselect(
            "Values", key="value_", options=rule_options(target, transactions)
        )
    else:
        st.write("RuleRelation not implemented.")

    left, right = st.columns([1, 1])
    action = left.selectbox("Action", list(RuleAction))
    if action == RuleAction.CATEGORIZE:
        category = right.text_input("Category")
    else:
        category = right.selectbox("Account", options=st.session_state.accounts.keys())

    st.markdown(
        f"**Rule:** `IF` *{target}* `{relation}` *{rule_value}* `THEN` *{action}* `=` *{category}*."
    )

    if st.button("Add rule"):
        conditions = [RuleCondition(target, relation, rule_value)]
        rule = Rule(conditions, action, category)
        try:
            expense_tracker.add_rule(rule)
        except ValueError as e:
            st.error(f"Error adding rule: {e}")
            return
        expense_tracker.categorize_transactions()
        st.success(f"Rule added: {rule}")
        io_utils.write_expense_tracker(expense_tracker)
        st.experimental_rerun()


def delete_rule(expense_tracker: ExpenseTracker):
    for rule in expense_tracker.rules:
        conditions_pretty = f", {rule.operator} ".join(
            [
                f"*{condition.field}* `{condition.relation}` *{condition.values}*"
                for condition in rule.conditions
            ]
        )
        col1, col2 = st.columns([3, 1])
        rule_pretty = f"**Rule:** `IF` {conditions_pretty} `THEN` *{rule.action}* `=` *{rule.category}*."
        col1.markdown(rule_pretty)
        if col2.button(
            "❌",
            key=str(uuid.uuid4()),
            on_click=delete_rule_callback,
            args=(
                expense_tracker,
                rule,
            ),
        ):
            pass


# I have no idea why, but this way it works. If I have this code
# in the delete_rule function, it won't work.
def delete_rule_callback(expense_tracker, rule: Rule):
    expense_tracker.delete_rule(rule)
    expense_tracker.categorize_transactions()
    io_utils.write_expense_tracker(expense_tracker)
    st.toast("Rule deleted.")


def get_expense_tracker_from_session_state():
    if "expense_tracker" not in st.session_state:
        BASE_LOGGER.info(
            "No expense tracker in session. Initializing expense tracker..."
        )
        st.session_state["expense_tracker"] = ExpenseTracker()
    return st.session_state["expense_tracker"]


def save_expense_tracker_to_session_state(expense_tracker: ExpenseTracker):
    st.session_state["expense_tracker"] = expense_tracker


def display_transactions(expense_tracker: ExpenseTracker) -> None:
    transactions = expense_tracker.get_transactions()
    if not transactions:
        st.write("No transactions yet...")
        return
    st.dataframe(transactions)


def display_accounts(expense_tracker: ExpenseTracker) -> None:
    if not expense_tracker.accounts:
        st.write("No accounts yet...")
        return
    st.dataframe([account.as_dict() for account in expense_tracker.accounts.values()])


def main():
    logging.basicConfig(
        format="%(levelname)s %(asctime)s - %(name)s: %(message)s",
        level=logging.DEBUG,
    )
    app_config = io_utils.load_app_config()
    BASE_LOGGER.info("Loaded app config: %s", app_config)
    st.set_page_config(
        page_title=app_config["application_name"],
        page_icon="💸",
    )
    state.initialize_state()

    st.title("💸 centzz")
    st.caption("Your dead-simple personal finances app")

    expense_tracker = io_utils.load_expense_tracker()
    save_expense_tracker_to_session_state(expense_tracker)

    overview_tab, accounts_tab, graphs_tab, transactions_tab, rules_tab = st.tabs(
        ["Overview", "Accounts", "Graphs", "Transactions", "Rules"]
    )

    with overview_tab:
        st.metric(
            "Total balance",
            f"{expense_tracker.balance:.2f} {expense_tracker.config.default_currency}",
        )

        st.header("Accounts")
        display_accounts(expense_tracker)

        # Display current transactions
        st.header("Transactions")
        transactions = expense_tracker.get_transactions()
        if not transactions:
            st.write("No transactions yet...")
        else:
            render.transactions_table(transactions)

        # Plots
        st.header("Plots")
        # Plot running balance over time
        if transactions:
            balance_df = pd.DataFrame(
                {
                    "date": transaction.date,
                    "amount": transaction.credit - transaction.debit,
                }
                for transaction in transactions
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
                        "date": transaction.date,
                        "category": transaction.category,
                        "amount": transaction.debit,
                        "account": transaction.account,
                    }
                    for transaction in transactions
                    if transaction.debit > 0 and transaction.category != "Transfer"
                ]
            )
            transactions_df["date"] = pd.to_datetime(transactions_df["date"])

            period_grouping = st.selectbox(
                "Group expenses by", ["Day", "Month", "Year"]
            )
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

    with accounts_tab:
        st.header("🏦 Accounts")

        st.subheader("Overview")

        display_accounts(expense_tracker)

        with st.expander("Add new account"):
            account_input = {
                "name": st.text_input("Account name"),
                "currency": st.selectbox("Currency", ["CHF", "EUR", "USD"]),
                # TODO: I'm pretty sure I'm ignoring this. I should update the code to use this.
                "starting_balance": st.number_input("Initial balance"),
            }
            st.caption(
                "Bank and account number are optional. They are used for automatically detecting transfers between accounts."
            )

            account_input["currency"] = Currency(account_input["currency"])
            # Initialize balance with starting balance
            account_input["balance"] = account_input["starting_balance"]
            account = Account.from_dict(account_input)

            if not account.is_valid():
                st.error("Account name and must be filled in.")

            if account.already_exists(expense_tracker.accounts):
                st.error(f'Account with name "{account.name}" already exists.')
                return

            if st.button("Create account"):
                expense_tracker.add_account(account)
                st.success(f"Account {account.name} created.")
                save_expense_tracker_to_session_state(expense_tracker)
                # TODO: Handle writing with new ExpenseTracker
                io_utils.write_expense_tracker(expense_tracker)
                st.experimental_rerun()

        with st.expander("Delete account"):
            account_to_delete = st.selectbox(
                "Account to delete", expense_tracker.accounts.keys()
            )
            if st.button("Delete account"):
                del expense_tracker.accounts[account_to_delete]
                st.success(f"Account {account_to_delete} deleted.")
                io_utils.write_expense_tracker(expense_tracker)
                st.experimental_rerun()

    with transactions_tab:
        st.header("📖 Transactions")

        if not expense_tracker.accounts:
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
                    [account.name for account in expense_tracker.accounts.values()],
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
                        new_transactions = [
                            Transaction(
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
                                debit=row[headers["debit"]]
                                if not pd.isna(row[headers["debit"]])
                                else 0.0,
                                credit=row[headers["credit"]]
                                if not pd.isna(row[headers["credit"]])
                                else 0.0,
                                account=account_selection,
                                currency=expense_tracker.accounts[
                                    account_selection
                                ].currency,
                            )
                            for _, row in df.iterrows()
                        ]
                        expense_tracker.accounts[account_selection].add_transactions(
                            new_transactions, overwrite_if_exists=True
                        )
                        st.success(f"{len(new_transactions)} transactions added.")
                        save_expense_tracker_to_session_state(expense_tracker)
                        io_utils.write_expense_tracker(expense_tracker)
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(
                            f"Error reading CSV file: {e}.\nDetailed error:\n{traceback.format_exc()}"
                        )

        current_transactions = expense_tracker.get_transactions()
        if not current_transactions:
            st.write("No transactions yet...")
            return

        st.caption("All transactions")
        render.transactions_table(current_transactions)

    with rules_tab:
        st.header("📝 Rules")

        if not expense_tracker.rules:
            st.write("No rules yet...")
        else:
            df = pd.DataFrame([rule.as_dict() for rule in expense_tracker.rules])
            df["conditions"] = df["conditions"].apply(
                lambda conditions: ", ".join(
                    [
                        f"{condition['field']} {condition['relation']} {condition['values']}"
                        for condition in conditions
                    ]
                )
            )
            st.dataframe(
                df,
                hide_index=True,
                column_config={
                    "conditions": st.column_config.TextColumn(label="Conditions"),
                    "action": st.column_config.TextColumn(label="Action"),
                    "category": st.column_config.TextColumn(label="Category"),
                },
            )

        with st.expander("Add new rule"):
            # TODO: Update to use ExpenseTracker
            add_rule(expense_tracker)
        with st.expander("Delete rule"):
            # TODO: Update to use ExpenseTracker
            delete_rule(expense_tracker)


if __name__ == "__main__":
    main()
