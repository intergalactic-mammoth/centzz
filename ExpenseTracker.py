import attr
import logging

from Account import Account
from Currency import Currency, CurrencyConverter
from Rule import Rule
from Transaction import Transaction


@attr.s(auto_attribs=True)
class ExpenseTrackerConfig:
    default_currency: Currency


@attr.s(auto_attribs=True)
class ExpenseTracker:
    accounts: dict[str, Account] = attr.Factory(dict)
    rules: list[Rule] = attr.Factory(list)
    logger: logging.Logger = logging.getLogger(__name__)
    config: ExpenseTrackerConfig = ExpenseTrackerConfig(Currency.CHF)

    @property
    def balance(self) -> float:
        return sum(
            CurrencyConverter.convert(
                account.balance,
                account.currency,
                self.config.default_currency,
            )
            for account in self.accounts.values()
        )

    def add_account(self, account: Account) -> None:
        if account.already_exists(self.accounts):
            raise ValueError("Account already exists")
        if not account.is_valid():
            raise ValueError("Account is not valid")
        self.accounts[account.name] = account
        self.logger.debug(f"Added account {account.name}")

    def delete_account(self, account_name: str) -> None:
        del self.accounts[account_name]
        self.logger.debug(f"Deleted account {account_name}")

    def add_rule(self, rule: Rule) -> None:
        if rule in self.rules:
            raise ValueError("Rule already exists")
        self.rules.append(rule)
        self.logger.debug(f"Added rule {rule}")

    def delete_rule(self, rule: Rule) -> None:
        self.rules.remove(rule)
        self.logger.debug(f"Deleted rule {rule}")

    def get_transactions(self, account_name: str = None) -> list[Transaction]:
        if account_name and not self.accounts.get(account_name):
            raise ValueError(f"Account {account_name} does not exist")
        if not account_name:
            return [
                transaction
                for account in self.accounts.values()
                for transaction in account.transactions.values()
            ]
        return list(self.accounts[account_name].transactions.values())

    def categorize_transactions(self) -> None:
        for transaction in self.get_transactions():
            transaction.categorize(self.rules)

    def as_dict(self) -> dict:
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

    @classmethod
    def from_dict(cls, expense_tracker_dict: dict) -> "ExpenseTracker":
        expense_tracker = cls()
        config = expense_tracker_dict.get("config")
        if config:
            expense_tracker.config = ExpenseTrackerConfig(**config)

        for account_dict in expense_tracker_dict["accounts"]:
            account = Account.from_dict(account_dict)
            expense_tracker.add_account(account)
        for rule_dict in expense_tracker_dict["rules"]:
            rule = Rule.from_dict(rule_dict)
            expense_tracker.add_rule(rule)
        for transaction_dict in expense_tracker_dict["transactions"]:
            transaction = Transaction.from_dict(transaction_dict)
            expense_tracker.accounts[transaction.account].add_transaction(transaction)
        return expense_tracker
