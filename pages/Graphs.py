import streamlit as st

import io_utils
import state


def main():
    app_config = io_utils.load_app_config()

    st.set_page_config(
        page_title=f"Graphs ⋅ {app_config['application_name']}",
        page_icon="💸",
    )

    state.initialize_state()
    st.header("📈 Graphs")


if __name__ == "__main__":
    main()
