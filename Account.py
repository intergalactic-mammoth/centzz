import attr
import logging

from Currency import Currency
from Transaction import Transaction


@attr.s(auto_attribs=True)
class Account:
    name: str
    currency: Currency
    starting_balance: float = 0.0
    transactions: dict[str, "Transaction"] = attr.Factory(dict)
    logger: logging.Logger = logging.getLogger(__name__)

    @property
    def balance(self) -> float:
        return self.starting_balance + sum(
            transaction.credit - transaction.debit
            for transaction in self.transactions.values()
        )

    def already_exists(self, accounts: dict["Account"]) -> bool:
        return any(
            (self.name == existing_account.name)
            for existing_account in accounts.values()
        )

    def is_valid(self) -> bool:
        return self.name

    def add_transaction(
        self, transaction: Transaction, overwrite_if_exists: bool = False
    ) -> None:
        if transaction.transaction_id in self.transactions and not overwrite_if_exists:
            raise ValueError("Transaction already exists")
        self.transactions[transaction.transaction_id] = transaction
        # self.logger.debug(f"Added transaction {transaction.transaction_id}")

    def delete_transaction(self, transaction_id: str) -> None:
        del self.transactions[transaction_id]
        # self.logger.debug(f"Deleted transaction {transaction_id}")

    def add_transactions(
        self, transactions: list[Transaction], overwrite_if_exists: bool = False
    ) -> None:
        for transaction in transactions:
            self.add_transaction(transaction, overwrite_if_exists)
        self.logger.debug(f"Added {len(transactions)} transactions")

    def delete_transactions(self, transaction_ids: list[str]) -> None:
        for transaction_id in transaction_ids:
            self.delete_transaction(transaction_id)
        self.logger.debug(f"Deleted {len(transaction_ids)} transactions")

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "currency": self.currency,
            "starting_balance": self.starting_balance,
            "balance": self.balance,
        }

    @classmethod
    def from_dict(cls, account_dict: dict) -> "Account":
        return cls(
            name=account_dict["name"],
            currency=Currency[account_dict["currency"]],
            starting_balance=account_dict["starting_balance"],
        )
