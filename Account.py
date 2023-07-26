import attr
import enum


class Currency(enum.StrEnum):
    CHF = "CHF"
    EUR = "EUR"
    USD = "USD"


@attr.s(auto_attribs=True)
class Account:
    name: str
    iban: str
    currency: Currency
    starting_balance: float = 0.0
    balance: float = 0.0
    bank: str = ""
    account_number: str = ""

    def already_exists(self, accounts: dict["Account"]) -> bool:
        return any(
            (self.name == existing_account.name or self.iban == existing_account.iban)
            for existing_account in accounts.values()
        )

    def is_valid(self) -> bool:
        return self.name and self.iban

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "bank": self.bank,
            "account_number": self.account_number,
            "iban": self.iban,
            "currency": self.currency,
            "starting_balance": self.starting_balance,
            "balance": self.balance,
        }

    @classmethod
    def from_dict(cls, account_dict: dict) -> "Account":
        return cls(
            name=account_dict["name"],
            iban=account_dict["iban"],
            currency=Currency[account_dict["currency"]],
            starting_balance=account_dict["starting_balance"],
            balance=account_dict["balance"],
            bank=account_dict["bank"],
            account_number=account_dict["account_number"],
        )
