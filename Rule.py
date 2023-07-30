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

    CATEGORIZE = "categorize as"
    TRANSFER_TO = "transfer to"
    TRANSFER_FROM = "transfer from"


@attr.s(auto_attribs=True, frozen=True)
class RuleCondition:
    """A condition of a rule.
    A condition is a comparison between a field and a value.
    The relation determines how the comparison is done.

    A rule can have multiple conditions."""

    field: str
    relation: RuleRelation
    values: list

    def __str__(self) -> str:
        """Returns a string representation of a RuleCondition."""
        return f"{self.field} {self.relation.value} [{', '.join(self.values)}]"


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

    def __str__(self) -> str:
        """Returns a string representation of a Rule."""
        # TODO: Add operator when supported
        return (
            f"Rule: IF "
            f"{', '.join(str(condition) for condition in self.conditions)} "
            f"THEN {self.action.value} {self.category}"
        )

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
