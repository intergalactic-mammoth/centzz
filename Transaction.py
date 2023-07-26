import attr

from Account import Account, Currency
from Rule import RuleRelation


@attr.s(auto_attribs=True)
class Transaction:
    transaction_id: str
    date: str
    payee: str
    description: str
    debit: float
    credit: float
    account: str
    currency: Currency
    category: str = "Other"
    transfer_to: str = ""
    transfer_from: str = ""

    @staticmethod
    def data_model():
        return {
            "transaction_id": str,
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

    def as_dict(self) -> dict:
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

    @classmethod
    def from_dict(cls, transaction_dict: dict) -> "Transaction":
        return cls(
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
