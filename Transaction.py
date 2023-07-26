from typing import Union

from Account import Account, Currency
from Rule import RuleRelation


class Transaction:
    def __init__(
        self,
        transaction_id: Union[int, str],
        date: str,
        payee: str,
        description: str,
        debit: float,
        credit: float,
        account: str,
        currency: Currency,
        category: str = "Other",
        transfer_to: str = "",
        transfer_from: str = "",
    ):
        """
        Will always take the absolute value for debit and credit.
        """
        self.transaction_id = transaction_id
        self.date = date
        self.payee = payee
        self.description = description
        self.debit = abs(debit) if debit else 0.0
        self.credit = abs(credit) if credit else 0.0
        self.account = account

        self.currency = currency.value
        self.category = category
        self.transfer_to = transfer_to
        self.transfer_from = transfer_from

    @staticmethod
    def data_model():
        return {
            "transaction_id": Union[int, str],
            "date": str,
            "payee": str,
            "description": str,
            "debit": float,
            "credit": float,
            "account": str,
            "currency": str,
            "category": str,
            "transfer_to": str,
            "transfer_from": str,
        }

    def _check_condition(self, condition: dict) -> bool:
        field = condition["field"]
        relation = condition["relation"]
        values = condition["values"]

        if relation == RuleRelation.CONTAINS.value:
            return any(value in getattr(self, field) for value in values)
        elif relation == RuleRelation.EQUALS.value:
            assert len(values) == 1
            return getattr(self, field) == values[0]
        elif relation == RuleRelation.ONE_OF.value:
            return getattr(self, field) in values
        else:
            raise ValueError(f"Unknown relation {relation}")

    def _apply_rule(self, rule: dict) -> bool:
        return all(
            self._check_condition(condition) for condition in rule["conditions"]
        )

    def categorize(self, rules: list[dict]) -> None:
        matched = False
        for rule in rules:
            if self._apply_rule(rule):
                self.category = rule["category"]
                matched = True
                break

        if not matched:
            self.category = "Other"

    def as_dict(self):
        return {
            "transaction_id": self.transaction_id,
            "date": self.date,
            "payee": self.payee,
            "description": self.description,
            "debit": self.debit,
            "credit": self.credit,
            "account": self.account,
            "currency": self.currency,
            "category": self.category,
            "transfer_to": self.transfer_to,
            "transfer_from": self.transfer_from,
        }

    @staticmethod
    def from_dict(transaction_dict: dict):
        return Transaction(
            transaction_id=transaction_dict["transaction_id"],
            date=transaction_dict["date"],
            payee=transaction_dict["payee"],
            description=transaction_dict["description"],
            debit=transaction_dict["debit"],
            credit=transaction_dict["credit"],
            account=transaction_dict["account"],
            currency=Currency(transaction_dict["currency"]),
            category=transaction_dict["category"],
            transfer_to=transaction_dict["transfer_to"],
            transfer_from=transaction_dict["transfer_from"],
        )
