import attr

from Currency import Currency
from Rule import RuleRelation, Rule, RuleCondition


@attr.s(auto_attribs=True)
class Transaction:
    """
    Debit and credit are always positive.
    """

    transaction_id: str
    date: str
    payee: str
    description: str
    debit: float = attr.ib(converter=abs)
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

    def _condition_applies(self, condition: RuleCondition) -> bool:
        field = condition.field
        relation = condition.relation
        values = condition.values

        if relation == RuleRelation.CONTAINS.value:
            return any(value in getattr(self, field) for value in values)
        if relation == RuleRelation.EQUALS.value:
            assert len(values) == 1
            return getattr(self, field) == values[0]
        if relation == RuleRelation.ONE_OF.value:
            return getattr(self, field) in values
        raise ValueError(f"Unknown relation {relation}")

    def _rule_applies(self, rule: Rule) -> bool:
        return all(self._condition_applies(condition) for condition in rule.conditions)

    # TODO: I need to figure out a deterministic way of applying
    # rule precedence, and how to handle rule collisions.
    def categorize(self, rules: list[Rule]) -> None:
        matched = False
        for rule in rules:
            if self._rule_applies(rule):
                self.category = rule.category
                if rule.action == "transfer to":
                    self.transfer_to = rule.category
                    self.category = "Transfer"
                elif rule.action == "transfer from":
                    self.transfer_from = rule.category
                    self.category = "Transfer"

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
