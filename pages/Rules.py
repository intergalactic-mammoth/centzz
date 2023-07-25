import streamlit as st
import pandas as pd

import processing
import io_utils
import state

from Rule import Rule, RuleType, RuleRelation, RuleAction, RuleCondition
from Transaction import Transaction

# TODO: WHen rule is deleted, Delete rule UI doesn't auto update.
# TODO: WHen rule is deleted, Transactions UI doesn't auto update.


def rule_options(header: str):
    df = pd.DataFrame(st.session_state.transactions.values())
    return df[header].unique()


def add_rule():
    # TODO: This only makes sense if I can add multiple conditions.
    # rule_type = st.selectbox("Rule type", [rule.value for rule in RuleType])

    if "rule_rows" not in st.session_state:
        st.session_state["rule_rows"] = 0

    left, middle, right = st.columns([1, 1, 2])
    target = left.selectbox(
        "Target",
        [column for column in Transaction.data_model().keys()],
        key=f"target_",
    )
    relation = middle.selectbox(
        "Relation",
        [relation.value for relation in RuleRelation],
        key=f"relation_",
    )
    if relation == RuleRelation.EQUALS.value:
        rule_value = right.selectbox(
            "Value", key=f"value_", options=rule_options(target)
        )
        rule_value = [rule_value]
    elif relation == RuleRelation.CONTAINS.value:
        rule_value = right.text_input("Value", key=f"value_")
        rule_value = [rule_value]
    elif relation == RuleRelation.ONE_OF.value:
        rule_value = right.multiselect(
            "Values", key=f"value_", options=rule_options(target)
        )
    else:
        st.write("RuleRelation not implemented.")

    left, right = st.columns([1, 1])
    action = left.selectbox("Action", [action.value for action in RuleAction])
    if action == RuleAction.CATEGORIZE.value:
        category = right.text_input("Category")
    else:
        category = right.selectbox("Account", options=st.session_state.accounts.keys())

    st.markdown(
        f"**Rule:** `IF` :blue[*{target}*] `{relation}` :blue[*{rule_value}*] `THEN` :blue[*{action}*] `=` :blue[*{category}*]."
    )

    if st.button("Add rule"):
        conditions = []
        conditions.append(RuleCondition(target, relation, rule_value))
        rule = Rule(conditions, action, category)
        if st.session_state.rules.get(str(hash(rule))):
            st.error(f"Rule already exists: {rule}")
            return
        else:
            st.session_state.rules[hash(rule)] = rule.as_dict()
            st.success(f"Rule added: {rule}")
            io_utils.write_rules()
            processing.apply_all_rules_to_all_transactions()
            io_utils.write_transactions()


def delete_rule():
    rules_pretty = {}
    for rule_hash, rule_dict in st.session_state.rules.items():
        conditions_pretty = f", {rule_dict['type']} ".join(
            [
                f"{condition['field']} {condition['relation']} {condition['values']}"
                for condition in rule_dict["conditions"]
            ]
        )
        rules_pretty[
            f"IF {conditions_pretty} THEN {rule_dict['action']} = {rule_dict['category']}"
        ] = rule_hash
    rule_to_delete = st.selectbox("Rule to delete", rules_pretty.keys())
    if st.button("Delete rule"):
        del st.session_state.rules[rules_pretty[rule_to_delete]]
        st.success(f"Rule deleted: {rule_to_delete}")
        io_utils.write_rules()
        processing.apply_all_rules_to_all_transactions()
        io_utils.write_transactions()
        # To update the UI
        st.experimental_rerun()


def main():
    app_config = io_utils.load_app_config()

    st.set_page_config(
        page_title=f"Rules ⋅ {app_config['application_name']}",
        page_icon="💸",
    )
    state.initialize_state()

    st.header("📝 Rules")

    if not st.session_state.rules:
        st.write("No rules yet...")
    else:
        df = pd.DataFrame(st.session_state.rules.values())
        df["conditions"] = df["conditions"].apply(
            lambda conditions: ", ".join(
                [
                    f"{condition['field']} {condition['relation']} {condition['values']}"
                    for condition in conditions
                ]
            )
        )
        st.dataframe(
            df,
            hide_index=True,
            column_config={
                "conditions": st.column_config.TextColumn(label="Conditions"),
                "action": st.column_config.TextColumn(label="Action"),
                "category": st.column_config.TextColumn(label="Category"),
            },
        )

    with st.expander("Add new rule"):
        add_rule()

    with st.expander("Delete rule"):
        delete_rule()


if __name__ == "__main__":
    main()
