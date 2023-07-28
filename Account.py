import attr
import logging

from Currency import Currency
from Transaction import Transaction


@attr.s(auto_attribs=True)
class Account:
    """Represents an account."""

    name: str
    currency: Currency
    starting_balance: float = 0.0
    transactions: dict[str, "Transaction"] = attr.Factory(dict)
    logger: logging.Logger = logging.getLogger(__name__)

    @property
    def balance(self) -> float:
        """Returns the balance of the account.
        The balance is calculated by adding the starting balance and the sum of all transactions.
        """
        return self.starting_balance + sum(
            transaction.credit - transaction.debit
            for transaction in self.transactions.values()
        )

    def already_exists(self, accounts: dict["Account"]) -> bool:
        """Returns True if the account already exists, False otherwise."""
        return any(
            (self.name == existing_account.name)
            for existing_account in accounts.values()
        )

    def is_valid(self) -> bool:
        """Returns True if the account is valid, False otherwise."""
        return self.name

    def add_transaction(
        self, transaction: Transaction, overwrite_if_exists: bool = False
    ) -> bool:
        """
        Adds a new transaction. Returns True if the transaction already existed.
        """
        transaction_exists = transaction.transaction_id in self.transactions
        if not overwrite_if_exists and transaction_exists:
            return transaction_exists
        self.transactions[transaction.transaction_id] = transaction
        return transaction_exists

    def delete_transaction(self, transaction_id: str) -> None:
        del self.transactions[transaction_id]

    def add_transactions(
        self, transactions: list[Transaction], overwrite_if_exists: bool = False
    ) -> int:
        """
        Adds transactions to account. Returns the number of duplicate transactions.
        """
        num_duplicate_transactions = sum(
            bool(self.add_transaction(transaction, overwrite_if_exists))
            for transaction in transactions
        )
        self.logger.info(
            "Added %s transactions. %s duplicates were %s overwritten.",
            len(transactions),
            num_duplicate_transactions,
            "" if overwrite_if_exists else "not",
        )
        return num_duplicate_transactions

    def delete_transactions(self, transaction_ids: list[str]) -> None:
        """Deletes transactions from account."""
        for transaction_id in transaction_ids:
            self.delete_transaction(transaction_id)
        self.logger.info(f"Deleted {len(transaction_ids)} transactions")

    def as_dict(self) -> dict:
        """Returns a dictionary representation of an Account."""
        return {
            "name": self.name,
            "currency": self.currency,
            "starting_balance": self.starting_balance,
            "balance": self.balance,
        }

    @classmethod
    def from_dict(cls, account_dict: dict) -> "Account":
        """Returns an Account from a dictionary representation."""
        return cls(
            name=account_dict["name"],
            currency=Currency[account_dict["currency"]],
            starting_balance=account_dict["starting_balance"],
        )
