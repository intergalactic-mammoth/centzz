import attr
import enum
import logging


class RuleOperator(enum.StrEnum):
    """The operator to use when evaluating the conditions of a rule."""

    ANY = "any"
    ALL = "all"


class RuleRelation(enum.StrEnum):
    """The relation to use when evaluating a condition of a rule."""

    CONTAINS = "contains"
    EQUALS = "is"
    ONE_OF = "one of"


class RuleAction(enum.StrEnum):
    """The action to take when a rule applies."""

    TRANSFER_TO = "transfer to"
    TRANSFER_FROM = "transfer from"
    CATEGORIZE = "categorize"


@attr.s(auto_attribs=True, frozen=True)
class RuleCondition:
    """A condition of a rule.
    A condition is a comparison between a field and a value.
    The relation determines how the comparison is done.

    A rule can have multiple conditions."""

    field: str
    relation: RuleRelation
    values: list


@attr.s(auto_attribs=True, frozen=True)
class Rule:
    """A rule that can be applied to transactions.
    A rule consists of multiple conditions that are combined with an operator.
    If the rule applies, the action is taken."""

    conditions: list[RuleCondition]
    action: RuleAction
    category: str
    operator: RuleOperator = RuleOperator.ALL
    logger: logging.Logger = logging.getLogger(__name__)

    def as_dict(self) -> dict:
        """Returns a dictionary representation of a Rule."""
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
        """Returns a Rule from a dictionary representation."""
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
