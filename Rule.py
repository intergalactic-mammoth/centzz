import enum
import attr


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


@attr.s(auto_attribs=True)
class RuleCondition:
    field: str
    relation: RuleRelation
    values: list


@attr.s(auto_attribs=True)
class Rule:
    conditions: list[RuleCondition]
    action: RuleAction
    category: str
    type: RuleOperator = RuleOperator.ALL

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
            "type": self.type.value,
        }

    @classmethod
    def from_dict(cls, rule_dict: dict) -> "Rule":
        return cls(
            conditions=[
                RuleCondition(
                    field=rule_dict["conditions"][i]["field"],
                    relation=RuleRelation[rule_dict["conditions"][i]["relation"]],
                    values=rule_dict["conditions"][i]["values"],
                )
                for i in range(len(rule_dict["conditions"]))
            ],
            action=RuleAction[rule_dict["action"]],
            category=rule_dict["category"],
            type=RuleOperator[rule_dict["type"]],
        )
