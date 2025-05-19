import streamlit as st
from config import TAG_OPTIONS
from controllers.bot_manager_controller import BotManager


def create_bot_page():
    st.title("🤖 Create Your Own Chat Bot")

    # Initialize session state variables
    BotManager._init_bot_creation_session()

    # Show preset options
    BotManager._display_preset_options()

    # Main creation form
    with st.form(key="main_bot_form"):
        form_data = BotManager._display_creation_form()
        submitted = st.form_submit_button("✨ Create Character")

        if submitted:
            BotManager._handle_form_submission(form_data)

    # Tag addition form (outside main form)
    with st.form(key="tag_addition_form"):
        st.subheader("Add Custom Tag")
        new_tag_col, add_col = st.columns([4, 1])
        with new_tag_col:
            new_custom_tag = st.text_input(
                "Custom Tag Name",
                placeholder="Type new tag name",
                label_visibility="collapsed",
                key="new_tag_input"
            )
        with add_col:
            if st.form_submit_button(
                    "Add",
                    disabled=not new_custom_tag or new_custom_tag in (TAG_OPTIONS + st.session_state.custom_tags)
            ):
                if new_custom_tag and new_custom_tag not in st.session_state.custom_tags:
                    st.session_state.custom_tags.append(new_custom_tag)
                    st.rerun()

    # Cancel button (outside both forms)
    if st.button("❌ Cancel"):
        if 'preset_data' in st.session_state:
            del st.session_state.preset_data
        st.session_state.page = "my_bots"
        st.rerun()