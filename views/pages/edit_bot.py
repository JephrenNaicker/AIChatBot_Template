import streamlit as st
from config import TAG_OPTIONS,PERSONALITY_TRAITS
from controllers.chat_controller import LLMChatController

def edit_bot_page():
    if 'editing_bot' not in st.session_state:
        st.error("No bot selected for editing")
        st.session_state.page = "my_bots"
        st.rerun()

    bot = st.session_state.editing_bot
    st.title(f"✏️ Editing {bot['name']}")

    # Initialize custom tags in session state if not exists
    if 'custom_tags' not in st.session_state:
        st.session_state.custom_tags = []

    # Combine standard and custom tags
    all_tag_options = TAG_OPTIONS + st.session_state.custom_tags

    # Main form for bot editing
    with st.form(key="edit_bot_form"):
        # Basic Info
        st.subheader("Basic Information")
        col1, col2 = st.columns([1, 3])
        with col1:
            emoji = st.text_input("Emoji",
                                  value=bot['emoji'],
                                  help="Choose an emoji to represent your bot")
        with col2:
            name = st.text_input("Bot Name",
                                 value=bot['name'],
                                 help="Give your bot a unique name")

        # Appearance Section
        st.subheader("Appearance")
        appearance_desc = st.text_area(
            "Physical Description",
            value=bot.get('appearance', {}).get('description', ''),
            height=100,
            help="Describe your character's physical appearance"
        )

        # Background Section
        st.subheader("Background")
        description = st.text_area(
            "Character Description",
            value=bot['desc'],
            height=150,
            help="Tell us about your character's personality and background"
        )

        # Personality Section
        st.subheader("Personality")

        # Personality traits multiselect
        traits = st.multiselect(
            "Key Personality Traits",
            PERSONALITY_TRAITS,
            default=[t for t in bot['personality'].get('traits', []) if t in PERSONALITY_TRAITS],
            help="Select traits that define your character's personality"
        )

        # Greeting Message
        st.subheader("Greeting")
        greeting = st.text_area(
            "Introduction Message",
            value=bot['personality'].get('greeting', ''),
            height=100,
            help="How your character introduces itself"
        )

        # Tags Section
        st.subheader("Tags")
        # Current tags with validation
        current_tags = [t for t in bot['tags'] if t in all_tag_options]
        tags = st.multiselect(
            "Select Tags",
            all_tag_options,
            default=current_tags
        )

        # Status selection
        st.subheader("Status")
        status = st.radio(
            "Bot Status",
            ["Draft", "Published"],
            index=0 if bot.get("status", "draft") == "draft" else 1,
            horizontal=True,
            help="Draft: Only visible to you | Published: Visible to all users"
        )

        # Form submission button
        submitted = st.form_submit_button("💾 Save Changes")

    # Separate form for tag addition
    with st.container(border=True):
        st.subheader("Add New Tag")
        tag_cols = st.columns([4, 1])
        with tag_cols[0]:
            new_custom_tag = st.text_input(
                "Custom Tag Name",
                placeholder="Type new tag name",
                label_visibility="collapsed"
            )
        with tag_cols[1]:
            if st.button(
                    "Add",
                    disabled=not new_custom_tag or new_custom_tag in all_tag_options
            ):
                if new_custom_tag and new_custom_tag not in st.session_state.custom_tags:
                    st.session_state.custom_tags.append(new_custom_tag)
                    st.rerun()

    # Handle main form submission
    if submitted:
        if not name:
            st.error("Please give your bot a name")
        else:
            # Update the bot in user_bots
            updated_bot = {
                "name": name,
                "emoji": emoji,
                "desc": description,
                "status": status.lower(),
                "appearance": {
                    "description": appearance_desc,
                    "avatar": bot.get('appearance', {}).get('avatar')
                },
                "tags": tags + ([new_custom_tag] if new_custom_tag and new_custom_tag not in tags else []),
                "personality": {
                    "traits": traits,
                    "greeting": greeting
                },
                "custom": True,
                "creator": bot.get("creator", st.session_state.profile_data.get("username", "anonymous"))
            }

            # Find and replace the bot in user_bots
            for i, b in enumerate(st.session_state.user_bots):
                if b['name'] == bot['name']:
                    st.session_state.user_bots[i] = updated_bot
                    break

            st.success(f"Bot '{name}' updated successfully!")
            st.session_state.page = "my_bots"
            st.rerun()

    # Cancel button
    if st.button("❌ Cancel"):
        st.session_state.page = "my_bots"
        st.rerun()