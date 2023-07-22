import streamlit as st
import pandas as pd

import processing
import io_utils
import state

# TODO: WHen rule is deleted, Delete rule UI doesn't auto update.
# TODO: WHen rule is deleted, Transactions UI doesn't auto update.


def add_rule():
    name = st.text_input("Rule name")
    rule = {
        "contains": st.text_input("Contains (separate with comma)"),
        "field": st.selectbox("In field", ["beneficiary", "description"]),
        "category": st.text_input("Category"),
    }
    if st.button("Add rule"):
        st.session_state.rules[name] = rule
        st.success(
            f'Rule added: ({rule["field"]} contains {rule["contains"]}) -> {rule["category"]}'
        )
        processing.apply_all_rules_to_all_transactions()
        io_utils.write_data()


def delete_rule():
    rule_to_delete = st.selectbox("Rule to delete", st.session_state.rules.keys())
    if st.button("Delete rule"):
        del st.session_state.rules[rule_to_delete]
        st.success(f"Rule deleted: {rule_to_delete}")
        processing.apply_all_rules_to_all_transactions()
        io_utils.write_data()


def main():
    app_config = io_utils.load_app_config()

    st.set_page_config(
        page_title=f"Rules ⋅ {app_config['application_name']}",
        page_icon="💸",
    )
    state.initialize_state()

    # Add rules for transaction categorization
    st.header("Category Rules 📝")
    if not st.session_state.rules:
        st.write("No rules yet...")
    else:
        st.write(pd.DataFrame(st.session_state.rules))
    st.subheader("Add new rule")
    add_rule()
    st.subheader("Delete rule")
    delete_rule()


if __name__ == "__main__":
    main()
