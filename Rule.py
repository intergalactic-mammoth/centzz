import attr
import enum
import logging


class RuleOperator(enum.StrEnum):
    ANY = "any"
    ALL = "all"


class RuleRelation(enum.StrEnum):
    CONTAINS = "contains"
    EQUALS = "is"
    ONE_OF = "one of"


class RuleAction(enum.StrEnum):
    TRANSFER_TO = "transfer to"
    TRANSFER_FROM = "transfer from"
    CATEGORIZE = "categorize"


@attr.s(auto_attribs=True, frozen=True)
class RuleCondition:
    field: str
    relation: RuleRelation
    values: list


@attr.s(auto_attribs=True, frozen=True)
class Rule:
    conditions: list[RuleCondition]
    action: RuleAction
    category: str
    operator: RuleOperator = RuleOperator.ALL
    logger: logging.Logger = logging.getLogger(__name__)

    def as_dict(self) -> dict:
        return {
            "conditions": [
                {
                    "field": condition.field,
                    "relation": condition.relation,
                    "values": condition.values,
                }
                for condition in self.conditions
            ],
            "action": self.action,
            "category": self.category,
            "operator": self.operator.value,
        }

    @classmethod
    def from_dict(cls, rule_dict: dict) -> "Rule":
        return cls(
            conditions=[
                RuleCondition(
                    field=condition["field"],
                    relation=RuleRelation(condition["relation"]),
                    values=condition["values"],
                )
                for condition in rule_dict["conditions"]
            ],
            action=RuleAction(rule_dict["action"]),
            category=rule_dict["category"],
            operator=RuleOperator(rule_dict["operator"]),
        )
