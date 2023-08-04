import logging
import traceback
import uuid
import time
import json

import pandas as pd
import streamlit as st

import plotting

from analytics_utils import (
    ChartType,
    GroupingPeriod,
    GroupBy,
    FinancialMetric,
    TransactionType,
    GROUPING_PERIOD_TO_ALTAIR_TIMEUNIT,
    FINANCIAL_METRIC_TO_TRANSACTION_FIELD,
    filter_df_transactions_by_dates,
)

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
    """
    Represents the main app.

    It is responsible for creating the UI and handling user input.
    """

    def __init__(self, config_path: str):
        self.logger = logging.getLogger(__name__)
        self.logger.info("============ Initializing ExpenseTrackerApp ============")
        try:
            with open(config_path, "r") as f:
                self.app_config = json.load(f)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Error while loading config: {e}") from e

        self.logger.info("Loaded app config: %s", self.app_config)

        # Set page config. This must be done before calling any other Streamlit code.
        st.set_page_config(
            page_title="centzz",
            page_icon="./static/centzz-icon-no-bg.png",
            menu_items={
                "Report a bug": f"{self.app_config['github_url']}/issues/new",
                "About": """

                This app is built with ❤️ by [aristot](https://aristot.io).

                Did the world really need yet another expenses tracking app? Maybe, maybe not.
                I just couldn't find one that was did what I needed.

                You can find the code on [GitHub](${self.app_config['github_url']}).
                """,
            },
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
                f"No ExpenseTracker found in session state: {e}. Creating new one."
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
            rules_tab,
            analytics_tab,
        ) = st.tabs(
            ["Start", "Overview", "Accounts", "Transactions", "Rules", "Analytics"]
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
        with st.expander("Quickstart"):
            st.markdown(
                """
                #### 1. Add an account 🏦
                Go to the Accounts tab, and add an account.
                You can add as many accounts as you want.

                #### 2. Add transactions 📖
                Once you have added an account,
                you can add transactions to it from the Transactions tab.
                You can add transactions manually (don't),
                or import them from a CSV file.

                How to get your transactions as a CSV file depends on your bank.
                A quick Google search should help you find out how to do it.
                Here are pointers for some banks to get you started:

                - [UBS](https://help.revolut.com/en-US/help/profile-and-plan/managing-my-account/viewing-my-account-statements/)
                - [Twint](https://www.twint.ch/en/faq/how-do-i-download-an-overview-of-my-revenues-and-charges/)
                - [N26](https://support.n26.com/en-eu/payments-transfers-and-withdrawals/balance-and-limits/how-to-get-bank-statement-n26)
                - [Revolut](#TODO)

                #### 3. Add rules 🧮
                Once you have added transactions,
                you can add rules to categorize them.
                That's where things start to get interesting.
                💸 **centzz** provides you with a powerful rule engine
                to categorize your transactions automatically.

                #### 4. Enjoy the analytics 📈
                Once you have added transactions and rules,
                you can enjoy the analytics.
                💸 **centzz** has an intuitive analytics engine
                to visualize your finances.

                #### 5. Save your data 💾
                💸 **centzz** is a browser app, which means that all
                your data is stored in your browser.
                While this is great for privacy and security,
                it means that if you close the tab, reload the page,
                or if you don't use the app for some time,
                all your data will be lost.

                So, every time you're done using the app, make sure to
                save your data by clicking on the "Save data" section.

                To save your data, you can download it as a JSON file.
                You can then load this file again to continue working on your data.
                """
            )
            st.warning(
                "Don't forget to come back to this page to **download your data** "
                "when you are done managing your accounts! Since 💸 **centzz** "
                "is a browser app, **all data will be lost** if you close or reload the tab.",
                icon="⚠️",
            )
        with st.expander("Load data "):
            data_file = st.file_uploader(
                label="If you have previously exported your data, you can load it here:",
                type="json",
                key="load_data",
            )
            if (
                st.button("Load data 🚀", disabled=(data_file is None), type="primary")
                and data_file
            ):
                self._load_app_data_from_json(data_file)
        with st.expander("Save data"):
            st.caption(
                "Export your data as a JSON file, to load it again next time you use the app.",
                help="The app runs on your browser, so all data will be lost if you close the tab. Exporing them allows you to restore your data next time you use the app.",
            )
            if st.download_button(
                "Download data 📎",
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

    def _load_app_data_from_json(self, data_file) -> None:
        """Loads app data from uploaded file to ExpenseTracker."""
        try:
            result = json.loads(data_file.read().decode("utf-8"))
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Error while loading JSON data: {e}") from e
        try:
            self.expense_tracker.extend(ExpenseTracker.from_dict(result))
        except KeyError as e:
            raise KeyError(f"Error while updating ExpenseTracker data: {e}") from e
        self.logger.info("Loaded ExpenseTracker from JSON file.")
        self.expense_tracker.log_state()
        self.save()
        st.success("Data loaded successfully! Go to the other tabs and have fun.")

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
            df = self.expense_tracker.get_grouped_transactions(
                transaction_type=TransactionType.EXPENSE,
                group_by=GroupBy.CATEGORY,
                period=GroupingPeriod.MONTH,
            )
            # start_date: first day of current month
            # end_date: current date
            today = pd.Timestamp.today()
            start_date = pd.Timestamp(today.year, today.month, 1)
            df = filter_df_transactions_by_dates(df, start_date, today)
            if not df.empty:
                st.dataframe(df)
            else:
                st.write("No expenses yet...")

        else:
            st.write("No data yet...")

    def display_accounts_tab(self):
        st.header("🏦 Accounts")
        st.subheader("Overview")
        self.display_accounts()
        self.display_add_new_account()
        self.display_delete_account()

    def display_analytics_tab(self):
        st.header("📈 Analytics")
        if not self.expense_tracker.accounts:
            st.write("No accounts found... Please add an account first.")

        transactions = self.expense_tracker.transactions

        if not transactions:
            st.write("No transactions found... Please add transactions first.")
            return

        active_account_col, plot_type_col = st.columns(2)
        all_accounts = list(self.expense_tracker.accounts.keys())
        with active_account_col:
            selected_accounts = st.multiselect(
                "Active accounts",
                all_accounts,
                default=all_accounts,
            )
        with plot_type_col:
            plot_type = st.selectbox(
                "Plot type",
                list(ChartType),
            )
        col0, col1, col2 = st.columns(3)
        with col0:
            transaction_field = st.selectbox("Show", list(FinancialMetric))
        with col1:
            grouping_period = st.selectbox("grouped by", list(GroupingPeriod))
        with col2:
            group_by = st.selectbox("and", list(GroupBy))

        df = pd.DataFrame(transaction.as_dict() for transaction in transactions)
        # Make date column a datetime object
        df["date"] = pd.to_datetime(df["date"])
        # Fill all numerical nans with 0
        df["credit"] = pd.to_numeric(df["credit"], errors="coerce").fillna(0)
        df["debit"] = pd.to_numeric(df["debit"], errors="coerce").fillna(0)

        # Get the min and max dates possible for the date range selector
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
        # Rename column "debit" to "expense" and credit to "income"
        # df = df.rename(columns={"debit": "expense", "credit": "income"})
        df["balance"] = df["credit"] - df["debit"]
        # Filter to keep only transactions between start and end date
        df = filter_df_transactions_by_dates(df, start_date, end_date)
        # Filter to keep only transactions from selected accounts
        df = df[df["account"].isin(selected_accounts)]

        transaction_field = FINANCIAL_METRIC_TO_TRANSACTION_FIELD[transaction_field]
        cumulative = False
        if "cumulative" in transaction_field:
            cumulative = True
            transaction_field = transaction_field.replace("cumulative_", "")

        chart = plotting.get_chart_data(
            df,
            transaction_field=transaction_field,
            group_by=group_by.lower(),
            timeunit=GROUPING_PERIOD_TO_ALTAIR_TIMEUNIT[grouping_period],
            cumulative=cumulative,
            chart_type=plot_type.value.lower(),
        )
        st.altair_chart(chart, use_container_width=True)

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

            if st.button("Add transaction", type="primary"):
                transaction = Transaction(
                    transaction_id=str(uuid.uuid4()),
                    date=date.isoformat(),
                    payee=payee,
                    description=description,
                    debit=amount if debit_or_credit == "Debit" else 0.0,
                    credit=amount if debit_or_credit == "Credit" else 0.0,
                    account=account,
                    currency=Currency(currency),
                )
                try:
                    transaction.categorize(self.expense_tracker.rules)
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

                add_transactions = st.button("Add transactions", type="primary")
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
            # Assert there is only one condition. TODO: Remove this when multiple conditions are supported.
            assert all(len(rule.conditions) == 1 for rule in self.expense_tracker.rules)

            # Add rules to DF but decompose condition (there is only 1 in each list)
            df = pd.DataFrame(
                [
                    {
                        "field": rule.conditions[0].field,
                        "relation": rule.conditions[0].relation,
                        "values": rule.conditions[0].values,
                        "action": rule.action,
                        "category": rule.category,
                    }
                    for rule in self.expense_tracker.rules
                ]
            )

            st.dataframe(
                df,
                hide_index=True,
                column_config={
                    "field": st.column_config.SelectboxColumn(
                        label="Field", options=Transaction.data_model().keys()
                    ),
                    "relation": st.column_config.SelectboxColumn(
                        label="Relation", options=list(RuleRelation)
                    ),
                    "values": st.column_config.ListColumn(label="Values"),
                    "action": st.column_config.SelectboxColumn(
                        label="Action", options=list(RuleAction)
                    ),
                    "category": st.column_config.TextColumn(label="Category"),
                    "operator": None,  # hide operator since it's not functional yet. TODO
                },
            )

        with st.expander("Add/Edit rule"):
            self.display_add_or_edit_rule()

        with st.expander("Delete rule"):
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
            account_name = st.text_input(
                "Account name", help="Unique name to identify the account."
            )
            account_currency = st.selectbox("Currency", ["CHF", "EUR", "USD"])
            account_initial_balance = st.number_input(
                "Initial balance",
                help="""
                    Initial balance of the account.
                    e.g. If you are uploading transactions from the
                    last 3 months, set to the amount of money you had in the account
                    before the first transaction that appears in the CSV file.

                    If you are adding transactions manually, set to the amount of money
                    you have in the account right now.

                    If you are uploading a CSV with the full history of transactions,
                    leave at 0.
                    """,
            )

            account = Account.from_dict(
                {
                    "name": account_name,
                    "currency": Currency(account_currency),
                    "starting_balance": account_initial_balance,
                }
            )

            if not account.is_valid():
                st.error("Account name must be filled in.")

            if st.button("Create account", type="primary"):
                try:
                    self.expense_tracker.add_account(account)
                    st.success(f"Account {account.name} created.")
                    self.save_and_reload()
                except ValueError as e:
                    st.error(f"Error adding account: {e}")
                    return

    def save(self):
        """Saves ExpenseTracker to session state. Doesn't reload."""
        self.logger.info("Saving ExpenseTrackerApp...")
        self.save_expense_tracker_to_session_state()

    def save_and_reload(self):
        """Saves ExpenseTracker to session state, and reloads the page."""
        self.save()
        st.experimental_rerun()

    def display_delete_account(self):
        """Displays a form to delete an account from ExpenseTracker."""

        with st.expander("Delete account"):
            account_to_delete = st.selectbox(
                "Account to delete", self.expense_tracker.accounts.keys()
            )
            if st.button(
                "Delete account",
                disabled=(account_to_delete is None),
                type="primary",
            ):
                del self.expense_tracker.accounts[account_to_delete]
                st.success(f"Account {account_to_delete} deleted.")
                self.save_and_reload()

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

    def display_add_or_edit_rule(self):
        def get_index(l: list, item: object) -> int:
            """Returns index of item in list, or 0 if not found."""
            try:
                return l.index(item)
            except ValueError:
                return 0

        transactions = self.expense_tracker.transactions
        if not transactions:
            st.write("No transactions yet... Please add transactions first.")
            return

        rules = self.expense_tracker.rules
        edit_rule = st.checkbox("Edit existing rule?") if rules else False
        if edit_rule:
            rule_to_edit = st.selectbox(
                "Rule to edit",
                rules,
                format_func=lambda rule: rule.__str__(),
                help="Editing a rule will delete the old rule and create a new one!",
            )

        # TODO: I need to find a way to add support for RuleOperator (AND, OR, NOT)

        left, middle, right = st.columns([1, 1, 2])
        transaction_headers = list(Transaction.data_model().keys())
        target = left.selectbox(
            "Target",
            transaction_headers,
            key="rule_target_selectbox",
            index=get_index(
                transaction_headers,
                rule_to_edit.conditions[0].field if edit_rule else None,
            ),
            help="The transaction field to match against. `payee` or `description` are the most common to use here.",
        )
        rule_relations = list(RuleRelation)
        relation = middle.selectbox(
            "Relation",
            rule_relations,
            key="rule_relation_selectbox",
            index=get_index(
                rule_relations,
                rule_to_edit.conditions[0].relation if edit_rule else None,
            ),
            help="""
            `contains` will match if the target contains any of the specified values.
            For example, if the target is `payee`, and the value is `foo`,
            the rule will match if the payee is `foo`, `foobar`, or `barfoo`.

            `equals` will match if the target is exactly equal to the specified value.

            `one of` will match if the target is equal to any of the specified values.""",
        )
        if relation == RuleRelation.EQUALS:
            entries_for_target = self.expense_tracker.get_entries_for_transaction_field(
                target
            )
            rule_value = right.selectbox(
                "Value",
                options=entries_for_target,
                key="rule_value_selectbox",
                help="The rule will match if `target` is exactly equal to the specified value.",
                index=get_index(
                    entries_for_target,
                    rule_to_edit.conditions[0].values[0] if edit_rule else None,
                ),
            )
            rule_value = [rule_value]
        elif relation == RuleRelation.CONTAINS:
            rule_value = right.text_input(
                "Value",
                key="rule_value_text_input",
                placeholder="Comma-separated list (e.g. 'foo, bar, bob')",
                help="""
                    The rule will match if `target` contains any of the specified values.
                    Separate values with a comma.

                    The values are case-insensitive ('foo', 'Foo', and 'FOO' are all the same).""",
                value=", ".join(rule_to_edit.conditions[0].values) if edit_rule else "",
            )
            rule_value = [value.strip().lower() for value in rule_value.split(",")]
        elif relation == RuleRelation.ONE_OF:
            entries_for_target = self.expense_tracker.get_entries_for_transaction_field(
                target
            )
            rule_value = right.multiselect(
                "Values",
                options=entries_for_target,
                key="rule_value_multiselect",
                placeholder="Choose one or more values",
                help="The rule will match if `target` is equal to any of the specified values.",
            )
        else:
            st.write("RuleRelation not implemented.")

        left, right = st.columns([1, 1])
        rule_actions = list(RuleAction)
        action = left.selectbox(
            "Action",
            rule_actions,
            help="What to do with the transaction if the rule matches.",
            index=get_index(rule_actions, rule_to_edit.action if edit_rule else None),
        )
        if action == RuleAction.CATEGORIZE:
            category = right.text_input(
                "Category",
                key="rule_category_text_input",
                value=rule_to_edit.category if edit_rule else "",
                placeholder="(e.g. 'Food', 'Rent', 'Salary')",
            )
        else:
            accounts = list(self.expense_tracker.accounts.keys())
            category = right.selectbox(
                "Account",
                options=accounts,
                key="rule_category_selectbox",
                index=get_index(accounts, rule_to_edit.category if edit_rule else None),
            )

        st.markdown("**Resulting rule:**")
        st.markdown(f"`IF` *{target}* `{relation}`")
        for value in rule_value:
            st.write(f":blue[{value}]")
        st.markdown(f"`THEN` *{action}* :blue[{category}]")

        button_label = "Edit rule" if edit_rule else "Add rule"
        if st.button(button_label, type="primary"):
            conditions = [RuleCondition(target, relation, rule_value)]
            rule = Rule(conditions, action, category)
            try:
                if edit_rule:
                    self.expense_tracker.delete_rule(rule_to_edit)
                self.expense_tracker.add_rule(rule)
            except ValueError as e:
                st.error(f"Error adding rule: {e}")
                return
            self.expense_tracker.categorize_transactions()
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
        format="%(levelname)s :: %(asctime)s :: %(filename)s l.%(lineno)d :: %(message)s",
        level=logging.DEBUG,
    )
    app = ExpenseTrackerApp(config_path="config.json")
    app.run()


if __name__ == "__main__":
    main()
