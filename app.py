import logging
import traceback
import uuid
import time
import json

import pandas as pd
import streamlit as st

import io_utils
import plotting

from analytics_utils import GroupingPeriod, GroupBy, filter_transactions_by_dates

from Account import Account
from Currency import Currency
from ExpenseTracker import ExpenseTracker
from Transaction import Transaction
from Rule import Rule, RuleRelation, RuleAction, RuleCondition

BASE_LOGGER = logging.getLogger(__name__)


def remove_streamlit_footer():
    """Sets footer style to hidden to hide Streamlit footer."""
    hide_footer_style = """
    <style>
    footer {visibility: hidden;}
    """
    st.markdown(hide_footer_style, unsafe_allow_html=True)


class ExpenseTrackerApp:
    def __init__(self, config_path: str):
        self.logger = logging.getLogger(__name__)

        try:
            self.app_config = io_utils.try_load_json_to_dict(config_path)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Error while loading config: {e}") from e

        self.logger.info("Loaded app config: %s", self.app_config)

        st.set_page_config(
            page_title=self.app_config["application_name"],
            page_icon="💸",
        )

        remove_streamlit_footer()
        self.logger.info("Removed Streamlit footer")

        try:
            self.expense_tracker = ExpenseTracker.from_dict(
                st.session_state["expense_tracker"]
            )
            self.logger.info("Loaded ExpenseTracker from session state.")
        except KeyError as e:
            self.logger.info(
                "No ExpenseTracker found in session state. Creating new one."
            )
            self.expense_tracker = ExpenseTracker()

        self.expense_tracker.log_state()

    def save_expense_tracker_to_session_state(self):
        st.session_state["expense_tracker"] = self.expense_tracker.as_dict()

    def run(self):
        """Runs the app. Creates all streamlit components."""
        st.title("💸 centzz")
        st.caption("Your dead-simple personal finances app")

        (
            start_tab,
            overview_tab,
            accounts_tab,
            transactions_tab,
            analytics_tab,
            rules_tab,
        ) = st.tabs(
            ["Start", "Overview", "Accounts", "Transactions", "Analytics", "Rules"]
        )

        with start_tab:
            self.display_start_tab()

        with overview_tab:
            self.display_overview_tab()

        with accounts_tab:
            self.display_accounts_tab()

        with transactions_tab:
            self.display_transactions_tab()

        with analytics_tab:
            self.display_analytics_tab()

        with rules_tab:
            self.display_rules_tab()

    def display_start_tab(self):
        st.header("Welcome to 💸 **centzz!**")
        st.write("Read the instructions below to get started.")
        with st.expander("Read me ⚠️"):
            st.markdown(
                """
                #### 1. Add accounts
                First, you need to add your accounts.
                You can add as many accounts as you want.

                #### 2. Add transactions
                Once you have added your accounts,
                you can add transactions to them.
                You can add transactions manually,
                or import them from a CSV file.

                How to get your transactions as a CSV file depends on your bank.
                Here are pointers for some banks to get you started:

                - [UBS](#TODO)
                - [N26](#TODO)
                - [Revolut](#TODO)

                #### 3. Add rules
                Once you have added transactions,
                you can add rules to categorize them.
                💸 **centzz** provides you with a powerful rule engine
                to categorize your transactions automatically.

                #### 4. Enjoy the analytics
                Once you have added transactions and rules,
                you can enjoy the analytics.
                💸 **centzz** has an intuitive analytics engine
                to visualize your finances.

                #### 5. Save your data
                💸 **centzz** is a browser app, which means that all
                your data is stored in your browser.
                This means that if you close the tab,
                or if you don't use the app for a while,
                all your data will be lost.

                To save your data, you can download it as a JSON file.
                You can then load this file again to continue working on your data.
                """
            )
            st.warning(
                "Don't forget to come back here to **download your data** "
                "when you are done managing your accounts! Since 💸 **centzz** "
                "is a browser app, **all data will be lost** if you close the tab.",
                icon="⚠️",
            )
        with st.expander("Load data"):
            if data_file := st.file_uploader(
                label="Load your 💸 ***centzz*** data",
                type="json",
                key="load_data",
                label_visibility="collapsed",
            ):
                try:
                    data = json.loads(data_file.read().decode("utf-8"))
                    self.expense_tracker = ExpenseTracker.from_dict(data)
                    self.logger.info("Loaded ExpenseTracker from JSON file.")
                except FileNotFoundError as e:
                    raise FileNotFoundError(
                        f"Error while loading ExpenseTracker data: {e}"
                    ) from e
                self.expense_tracker.log_state()
                self.save()
                st.success(
                    "Data loaded successfully! Go to the other tabs and have fun."
                )
        with st.expander("Save data"):
            if st.download_button(
                "Download your data 📎",
                data=self.expense_tracker.as_json(),
                file_name="centzz_data.json",
                mime="application/json",
            ):
                self.logger.info("Downloading ExpenseTracker data...")
                st.success("Data saved successfully!")
        st.divider()
        st.caption(
            f"💸 **centzz** is built with ❤️ by [aristot](https://aristot.io), "
            "using [Streamlit](https://streamlit.io)."
            "\n\nYou can find the code on [GitHub](${self.app_config['github_url']}). "
            "For questions, feedback, or feature requests, "
            f"open an [issue](${self.app_config['github_url']}/issues/new) on GitHub. "
            "\n\nIf you want to support the development of this app, "
            "you can [buy me a coffee ☕️](#TODO) or support me on [Patreon](#TODO)."
        )

    def display_overview_tab(self):
        st.metric(
            "Total balance",
            f"{self.expense_tracker.balance:.2f} {self.expense_tracker.config.default_currency}",
        )

        st.header("Accounts")
        self.display_accounts()

        # Expenses this month
        st.header("Expenses this month")
        if transactions := self.expense_tracker.transactions:
            df = self.expense_tracker.get_grouped_expenses(
                group_by=GroupBy.CATEGORY, period=GroupingPeriod.MONTH
            )
            # start_date: first day of current month
            # end_date: current date
            today = pd.Timestamp.today()
            start_date = pd.Timestamp(today.year, today.month, 1)
            df = filter_transactions_by_dates(df, start_date, today)
            if not df.empty:
                st.dataframe(df)
            else:
                st.write("No expenses recorded yet...")

        else:
            st.write("No data yet...")

    def display_accounts_tab(self):
        st.header("🏦 Accounts")
        st.subheader("Overview")
        self.display_accounts()
        self.display_add_new_account()
        self.display_delete_account()

    def display_analytics_tab(self):
        # TODO: Make analytics modular to reuse also in overview tab
        # TODO: Add donut chart (with Altair) :)
        st.header("📈 Analytics")
        if not self.expense_tracker.accounts:
            st.write("No accounts found... Please add an account first.")

        if transactions := self.expense_tracker.transactions:
            selected_accounts = st.multiselect(
                "Active accounts",
                self.expense_tracker.accounts.keys(),
                default=self.expense_tracker.accounts.keys(),
            )
            col1, col2 = st.columns(2)
            aggregation_period = col1.selectbox("Group by", list(GroupingPeriod))
            aggregate_by = col2.selectbox("and", list(GroupBy))

            df = pd.DataFrame([transaction.as_dict() for transaction in transactions])
            df["date"] = pd.to_datetime(df["date"])

            min_date = df["date"].min().date()
            max_date = df["date"].max().date()

            col3, col4 = st.columns(2)
            with col3:
                start_date = st.date_input(
                    "Start date", min_date, min_value=min_date, max_value=max_date
                )
            with col4:
                end_date = st.date_input(
                    "End date", max_date, min_value=min_date, max_value=max_date
                )

            if start_date > end_date:
                st.error("End date must fall after start date.")
                return

            # Filter to keep only transactions between start and end date
            df = filter_transactions_by_dates(df, start_date, end_date)
            # Filter to keep only selected accounts
            df = df[df["account"].isin(selected_accounts)]

            # Running balance for line plot over time. amount = credit - debit
            # TODO: Need to adjust with starting balance for each account
            running_balance_df = pd.DataFrame(
                {
                    "date": df["date"],
                    "amount": df["credit"] - df["debit"],
                }
            )
            running_balance_df = running_balance_df.sort_values("date")
            running_balance_df["balance"] = running_balance_df["amount"].cumsum()

            expenses_df = self.expense_tracker.get_grouped_expenses(
                group_by=aggregate_by,
                period=aggregation_period,
                accounts=selected_accounts,
            )
            expenses_df = (
                filter_transactions_by_dates(expenses_df, start_date, end_date)
                .sort_values("date")
                .pivot_table(
                    index="date",
                    columns=aggregate_by.lower()
                    if aggregate_by != GroupBy.NONE
                    else None,
                    values="amount",
                    fill_value=0,
                )
            )
            plotting.create_line_chart(
                running_balance_df, "date", "balance", "Running Balance Over Time"
            )
            plotting.create_bar_chart(expenses_df, "Expenses Over Time")

        else:
            st.write("No transactions found... Please add transactions first.")

    def display_transactions_tab(self):
        st.header("📖 Transactions")

        if not self.expense_tracker.accounts:
            st.write("No accounts found... Please add an account first.")
            return

        # TODO: Either do this, or provide editable df UI? Also, modularize.
        with st.expander("Add single transaction"):
            col1, col2, col3 = st.columns(3)
            with col1:
                date = st.date_input("Date")
            with col2:
                account = st.selectbox("Account", self.expense_tracker.accounts.keys())
            with col3:
                currency = st.selectbox(
                    "Currency (auto selected)",
                    list(Currency),
                    index=list(Currency).index(
                        self.expense_tracker.accounts[account].currency
                    ),
                    disabled=True,
                    key="single_currency_selectbox",
                )
            payee = st.text_input("Payee")
            description = st.text_input("Description")
            debit_or_credit = st.selectbox("Debit/Credit", ["Debit", "Credit"])
            amount = st.number_input("Amount")
            category = st.text_input("Category")

            if st.button("Add transaction"):
                transaction = Transaction(
                    date=date.isoformat(),
                    payee=payee,
                    description=description,
                    debit=amount if debit_or_credit == "Debit" else 0.0,
                    credit=amount if debit_or_credit == "Credit" else 0.0,
                    account=account,
                    currency=Currency(currency),
                    category=category,
                )
                try:
                    self.expense_tracker.accounts[account].add_transaction(transaction)
                except ValueError as e:
                    st.error(f"Error adding transaction: {e}")
                    return
                st.success(f"Transaction added: {transaction}")
                self.save_and_reload()
        with st.expander("Add transactions from CSV"):
            if csv_file := st.file_uploader(
                "Choose a CSV file",
                type="csv",
                key="current_file",
            ):
                # Parse headers of CSV file to map them to transaction columns
                st.write("Choose the correct column for each transaction field:")
                try:
                    df = pd.read_csv(csv_file)
                except FileNotFoundError as e:
                    raise FileNotFoundError(f"Error while loading CSV file: {e}") from e
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
                    [
                        account.name
                        for account in self.expense_tracker.accounts.values()
                    ],
                    key="add_transactions_from_csv_account_selectbox",
                )

                overwrite = st.checkbox("Overwrite existing transactions")

                if overwrite:
                    st.warning(
                        "This will overwrite existing transactions with the same "
                        "transaction ID. Any manual modifications to these transactions will be lost.",
                        icon="⚠️",
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
                                debit=0.0
                                if pd.isna(row[headers["debit"]])
                                else row[headers["debit"]],
                                credit=0.0
                                if pd.isna(row[headers["credit"]])
                                else row[headers["credit"]],
                                account=account_selection,
                                currency=self.expense_tracker.accounts[
                                    account_selection
                                ].currency,
                            )
                            for _, row in df.iterrows()
                        ]
                        num_duplicates = self.expense_tracker.accounts[
                            account_selection
                        ].add_transactions(
                            new_transactions, overwrite_if_exists=overwrite
                        )
                        with st.spinner(
                            f"Adding {len(new_transactions)} transactions, found {num_duplicates} duplicates."
                            f"{' Overwriting...' if overwrite else ' Skipping duplicates...'}"
                        ):
                            # TODO: This is horrendous, find a better way to display the message :')
                            # The problem with toast is that I can't access the variables in the callback
                            time.sleep(2.5)
                        self.save_and_reload()
                    except Exception as e:
                        st.error(
                            f"Error reading CSV file: {e}.\nDetailed error:\n{traceback.format_exc()}"
                        )

        st.caption("All transactions")
        current_transactions = self.expense_tracker.transactions
        if not current_transactions:
            st.write("No transactions yet...")
        else:
            self.display_transactions()
            self.display_delete_all_transactions()

    def display_rules_tab(self):
        st.header("🧮 Rules")

        if not self.expense_tracker.rules:
            st.write("No rules yet...")
        else:
            df = pd.DataFrame([rule.as_dict() for rule in self.expense_tracker.rules])
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
            self.display_add_new_rule()
        with st.expander("Delete rule"):
            # TODO: Update to use ExpenseTracker
            self.display_delete_rule()

    # -----------------------------
    # DISPLAY X COMPONENT FUNCTIONS
    # -----------------------------
    # All functions below are to modularize displaying
    # different parts of the app.

    # -----------------------------
    # Account functions
    # -----------------------------

    def display_accounts(self) -> None:
        """
        Displays all accounts in ExpenseTracker.
        If no accounts are found, returns early, and prints message.
        """
        if not self.expense_tracker.accounts:
            st.write("No accounts yet...")
            return
        st.dataframe(
            [account.as_dict() for account in self.expense_tracker.accounts.values()],
            column_config={
                "name": st.column_config.TextColumn(label="Account name"),
                "currency": st.column_config.SelectboxColumn(
                    label="Currency", options=list(Currency)
                ),
                "balance": st.column_config.NumberColumn(label="Balance"),
                "starting_balance": None,  # hide starting balance
            },
            use_container_width=True,
        )

    def display_add_new_account(self):
        """Displays a form to add a new account to ExpenseTracker."""

        with st.expander("Add new account"):
            account_input = {
                "name": st.text_input("Account name"),
                "currency": st.selectbox("Currency", ["CHF", "EUR", "USD"]),
                # TODO: I'm pretty sure I'm ignoring this. I should update the code to use this.
                "starting_balance": st.number_input("Initial balance"),
            }

            account_input["currency"] = Currency(account_input["currency"])
            # Initialize balance with starting balance
            account_input["balance"] = account_input["starting_balance"]
            account = Account.from_dict(account_input)

            if not account.is_valid():
                st.error("Account name must be filled in.")

            if st.button("Create account"):
                try:
                    self.expense_tracker.add_account(account)
                except ValueError as e:
                    st.error(f"Error adding account: {e}")
                    return
                st.success(f"Account {account.name} created.")
                self.save_and_reload()

    def save(self):
        """Saves ExpenseTracker to session state, to disk. Doesn't reload."""
        self.logger.info("Saving ExpenseTrackerApp...")
        self.save_expense_tracker_to_session_state()

    def save_and_reload(self):
        """Saves ExpenseTracker to session state, to disk, and reloads the page."""
        self.save()
        st.experimental_rerun()

    def display_delete_account(self):
        """Displays a form to delete an account from ExpenseTracker."""

        with st.expander("Delete account"):
            account_to_delete = st.selectbox(
                "Account to delete", self.expense_tracker.accounts.keys()
            )
            if st.button("Delete account"):
                del self.expense_tracker.accounts[account_to_delete]
                st.success(f"Account {account_to_delete} deleted.")
                io_utils.write_expense_tracker(self.expense_tracker)
                st.experimental_rerun()

    def display_transactions(self) -> None:
        transactions = sorted(
            [
                transaction.as_dict()
                for transaction in self.expense_tracker.transactions
            ],
            key=lambda t: t["date"],
            reverse=True,  # Most recent transaction first
        )
        st.dataframe(
            transactions,
            hide_index=True,
            column_config={
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
            },
            column_order=[
                "date",
                "account",
                "payee",
                "description",
                "debit",
                "credit",
                "currency",
                "category",
            ],  # Hide transaction_id, transfer_to, transfer_from
            use_container_width=True,
        )

    def display_delete_all_transactions(self):
        col1, col2 = st.columns([2, 1])
        delete_all = col1.checkbox("Delete all transactions")
        if delete_all:
            st.warning(
                "This will delete all transactions. Action cannot be undone.", icon="⚠️"
            )
        if col2.button("Delete", disabled=not delete_all):
            for account in self.expense_tracker.accounts.values():
                account.transactions = {}
            st.success("All transactions deleted.")
            self.save_and_reload()

    def display_add_new_rule(self):
        transactions = self.expense_tracker.transactions
        if not transactions:
            st.write("No transactions yet... Please add transactions first.")
            return

        # TODO: I need to find a way to add support for RuleOperator (AND, OR, NOT)

        left, middle, right = st.columns([1, 1, 2])
        target = left.selectbox(
            "Target", list(Transaction.data_model().keys()), key="rule_target_selectbox"
        )
        relation = middle.selectbox(
            "Relation", list(RuleRelation), key="rule_relation_selectbox"
        )
        if relation == RuleRelation.EQUALS:
            rule_value = right.selectbox(
                "Value",
                options=self.expense_tracker.get_entries_for_transaction_field(target),
                key="rule_value_selectbox",
            )
            rule_value = [rule_value]
        elif relation == RuleRelation.CONTAINS:
            rule_value = right.text_input("Value", key="rule_value_text_input")
            rule_value = [rule_value]
        elif relation == RuleRelation.ONE_OF:
            rule_value = right.multiselect(
                "Values",
                options=self.expense_tracker.get_entries_for_transaction_field(target),
                key="rule_value_multiselect",
            )
        else:
            st.write("RuleRelation not implemented.")

        left, right = st.columns([1, 1])
        action = left.selectbox("Action", list(RuleAction))
        if action == RuleAction.CATEGORIZE:
            category = right.text_input("Category", key="rule_category_text_input")
        else:
            category = right.selectbox(
                "Account",
                options=self.expense_tracker.accounts.keys(),
                key="rule_category_selectbox",
            )

        st.markdown(
            f"---\n\n**Resulting Rule:**\n\n`IF` *{target}* `{relation}` *{rule_value}* `THEN` *{action}* `=` *{category}*."
        )

        if st.button("Add rule"):
            conditions = [RuleCondition(target, relation, rule_value)]
            rule = Rule(conditions, action, category)
            try:
                self.expense_tracker.add_rule(rule)
            except ValueError as e:
                st.error(f"Error adding rule: {e}")
                return
            self.expense_tracker.categorize_transactions()
            st.success(f"Rule added: {rule}")
            self.save_and_reload()

    def display_delete_rule(self):
        for rule in self.expense_tracker.rules:
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
                use_container_width=True,
                on_click=delete_rule_callback,
                args=(
                    self,
                    rule,
                ),
            ):
                pass


# I have no idea why, but having this code as a callback works.
# The same code in the display_delete_rule function, it won't work.
def delete_rule_callback(app: ExpenseTrackerApp, rule: Rule):
    app.expense_tracker.delete_rule(rule)
    app.expense_tracker.categorize_transactions()
    app.save()
    st.toast("Rule deleted.")


def main():
    logging.basicConfig(
        format="%(levelname)s %(asctime)s - %(name)s: %(message)s",
        level=logging.DEBUG,
    )
    app = ExpenseTrackerApp(config_path="config.json")
    app.run()


if __name__ == "__main__":
    main()
