import enum


class RuleType(enum.Enum):
    ANY = "any"
    ALL = "all"


class RuleRelation(enum.Enum):
    CONTAINS = "contains"
    EQUALS = "is"
    ONE_OF = "one of"


class RuleAction(enum.Enum):
    TRANSFER_TO = "transfer to"
    TRANSFER_FROM = "transfer from"
    CATEGORIZE = "categorize"


class RuleCondition:
    def __init__(self, field: str, relation: RuleRelation, values: list):
        self.field = field
        self.relation = relation
        self.values = values

    def __repr__(self):
        return f"RuleCondition: {self.field} - {self.relation} - {self.values}"

    def __str__(self):
        return f"RuleCondition: {self.field} - {self.relation} - {self.values}"

    def __hash__(self):
        return hash((self.field, self.relation, tuple(self.values)))

    def __eq__(self, other):
        if not isinstance(other, RuleCondition):
            return NotImplemented
        return (self.field, self.relation, self.values) == (
            other.field,
            other.relation,
            other.values,
        )


class Rule:
    def __init__(
        self,
        conditions: list[RuleCondition],
        action: RuleAction,
        category: str,
        type: RuleType = RuleType.ALL,
    ):
        self.conditions = conditions
        self.action = action
        self.category = category
        self.type = type

    def __repr__(self):
        return f"Rule: {self.conditions} --> {self.action} = {self.category}"

    def __str__(self):
        return f"Rule: {self.conditions} --> {self.action} = {self.category}"

    def __hash__(self):
        return hash((tuple(self.conditions), self.action, self.category))

    def __eq__(self, other):
        if not isinstance(other, Rule):
            return NotImplemented
        return (self.conditions, self.action, self.category) == (
            other.conditions,
            other.action,
            other.category,
        )

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

    @staticmethod
    def from_dict(rule_dict: dict) -> "Rule":
        return Rule(
            conditions=[
                RuleCondition(
                    field=condition["field"],
                    relation=condition["relation"],
                    values=condition["values"],
                )
                for condition in rule_dict["conditions"]
            ],
            action=rule_dict["action"],
            category=rule_dict["category"],
            type=RuleType(rule_dict["type"]),
        )
