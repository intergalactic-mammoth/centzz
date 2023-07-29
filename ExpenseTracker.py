import attr
import logging
import json

import pandas as pd

from analytics_utils import GroupingPeriod, GroupBy, GROUPING_PERIOD_TO_PANDAS
from Account import Account
from Currency import Currency, CurrencyConverter
from Rule import Rule
from Transaction import Transaction


@attr.s(auto_attribs=True)
class ExpenseTrackerConfig:
    default_currency: Currency


@attr.s(auto_attribs=True)
class ExpenseTracker:
    """Represents an expense tracker.
    An expense tracker consists of multiple accounts and rules.

    The tracker does not hold any transactions itself, but rather delegates them to the accounts.
    """

    accounts: dict[str, Account] = attr.Factory(dict)
    rules: list[Rule] = attr.Factory(list)
    logger: logging.Logger = logging.getLogger(__name__)
    config: ExpenseTrackerConfig = ExpenseTrackerConfig(Currency.CHF)

    @property
    def balance(self) -> float:
        """Returns the balance of all accounts in the default currency.
        The balance is calculated by adding the balance of accounts."""
        return sum(
            CurrencyConverter.convert(
                account.balance,
                account.currency,
                self.config.default_currency,
            )
            for account in self.accounts.values()
        )

    @property
    def transactions(self) -> list[Transaction]:
        """Returns a list of all transactions in all accounts."""
        return [
            transaction
            for account in self.accounts.values()
            for transaction in account.transactions.values()
        ]

    def log_state(self) -> None:
        """Logs a summary of the ExpenseTracker."""
        self.logger.info(f"Balance: {self.balance} {self.config.default_currency}")
        self.logger.info(
            f"Holding {len(self.accounts)} accounts, {len(self.rules)} rules, "
            f"{len(self.transactions)} transactions."
        )

    def add_account(self, account: Account) -> None:
        """Adds an account to the ExpenseTracker.
        Raises ValueError if the account already exists or is not valid."""
        if account.already_exists(self.accounts):
            raise ValueError("Account already exists")
        if not account.is_valid():
            raise ValueError("Account is not valid")
        self.accounts[account.name] = account
        self.logger.debug(f"Added account {account.name}")

    def delete_account(self, account_name: str) -> None:
        """Deletes an account from the ExpenseTracker.
        Raises ValueError if the account does not exist."""
        try:
            del self.accounts[account_name]
        except KeyError as e:
            raise ValueError(f"Account {account_name} does not exist: {e}") from e
        self.logger.debug(f"Deleted account {account_name}")

    def add_rule(self, rule: Rule) -> None:
        """Adds a rule to the ExpenseTracker.
        Raises ValueError if the rule already exists."""
        if rule in self.rules:
            raise ValueError("Rule already exists")
        self.rules.append(rule)
        self.logger.debug(f"Added rule {rule}")

    def delete_rule(self, rule: Rule) -> None:
        """Deletes a rule from the ExpenseTracker.
        Raises ValueError if the rule does not exist."""
        self.rules.remove(rule)
        self.logger.debug(f"Deleted rule {rule}")

    def get_transactions_in_accounts(
        self, account_names: list[str]
    ) -> list[Transaction]:
        """Returns a list of all transactions in the given accounts.
        Raises ValueError if any of the accounts do not exist."""
        for account_name in account_names:
            if not self.accounts.get(account_name):
                raise ValueError(f"Account {account_name} does not exist")
        return [
            transaction
            for account_name in account_names
            for transaction in self.accounts[account_name].transactions.values()
        ]

    def get_grouped_expenses(
        self,
        group_by: GroupBy = GroupBy.NONE,
        period: GroupingPeriod = GroupingPeriod.NONE,
        accounts: list[str] = None,
    ) -> pd.DataFrame:
        """Returns a DataFrame with the expenses grouped by the given categorization method and period.

        DataFrame columns contain only a subset of the Transaction fields:
        - date
        - amount
        - category
        - account

        IMPORTANT ⚠️
        - Amount in expenses is normalized to the default currency.
        - Excludes expenses categorized as "Transfer".
        """
        time_offset = GROUPING_PERIOD_TO_PANDAS[period]
        transactions = (
            self.get_transactions_in_accounts(accounts)
            if accounts
            else self.transactions
        )
        group_cols = [pd.Grouper(key="date", freq=time_offset)]
        if group_by != GroupBy.NONE:
            group_cols.append(group_by.value.lower())
        return (
            pd.DataFrame(
                [
                    {
                        "date": pd.to_datetime(transaction.date),
                        "amount": CurrencyConverter.convert(
                            transaction.debit,
                            transaction.currency,
                            self.config.default_currency,
                        ),
                        "category": transaction.category,
                        "account": transaction.account,
                    }
                    for transaction in transactions
                    if transaction.debit > 0 and transaction.category != "Transfer"
                ]
            )
            .groupby(group_cols)
            .sum(numeric_only=True)
            .reset_index()
        )

    def get_entries_for_transaction_field(self, field: str) -> list:
        """For the given transaction field, return all distinct values in the ExpenseTracker's transactions.

        For example, if field is "payee", return all distinct payees in the ExpenseTracker's transactions.
        """
        if field == "account":
            return list(self.accounts.keys())
        if field == "currency":
            return list(Currency)

        if field not in Transaction.data_model():
            raise ValueError(f"Field {field} does not exist")
        return list({getattr(transaction, field) for transaction in self.transactions})

    def categorize_transactions(self) -> None:
        """Categorizes all transactions in the ExpenseTracker by applying existing rules."""
        for transaction in self.transactions:
            transaction.categorize(self.rules)

    def extend(self, other: "ExpenseTracker") -> None:
        """Extends the ExpenseTracker with the given ExpenseTracker.
        Raises ValueError if any of the accounts, rules, or transactions already exist.
        """
        try:
            for account in other.accounts.values():
                self.add_account(account)
        except ValueError as e:
            raise ValueError(f"Account {account.name} already exists: {e}") from e
        try:
            for rule in other.rules:
                self.add_rule(rule)
        except ValueError as e:
            raise ValueError(f"Rule {rule} already exists: {e}") from e
        try:
            for transaction in other.transactions:
                self.accounts[transaction.account].add_transaction(transaction)
        except KeyError as e:
            raise ValueError(
                f"Account {transaction.account} does not exist: {e}"
            ) from e

    def as_dict(self) -> dict:
        """Returns a dictionary representation of the ExpenseTracker."""
        return {
            "accounts": [account.as_dict() for account in self.accounts.values()],
            "rules": [rule.as_dict() for rule in self.rules],
            "transactions": [
                transaction.as_dict()
                for account in self.accounts.values()
                for transaction in account.transactions.values()
            ],
            "config": attr.asdict(self.config),
        }

    def as_json(self) -> str:
        """Returns a JSON representation of the ExpenseTracker."""
        return json.dumps(self.as_dict(), indent=4)

    @classmethod
    def from_dict(cls, expense_tracker_dict: dict) -> "ExpenseTracker":
        """Returns an ExpenseTracker from a dictionary representation."""
        expense_tracker = cls()
        if config := expense_tracker_dict.get("config"):
            expense_tracker.config = ExpenseTrackerConfig(**config)
        if accounts := expense_tracker_dict.get("accounts"):
            for account_dict in accounts:
                account = Account.from_dict(account_dict)
                expense_tracker.add_account(account)
        if rules := expense_tracker_dict.get("rules"):
            for rule_dict in rules:
                rule = Rule.from_dict(rule_dict)
                expense_tracker.add_rule(rule)
        if transactions := expense_tracker_dict.get("transactions"):
            for transaction_dict in transactions:
                transaction = Transaction.from_dict(transaction_dict)
                expense_tracker.accounts[transaction.account].add_transaction(
                    transaction
                )
        return expense_tracker
