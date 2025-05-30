import streamlit as st
from config import TAG_OPTIONS, PERSONALITY_TRAITS, DEFAULT_RULES
from controllers.bot_manager_controller import BotManager


def edit_bot_page():
    if 'editing_bot' not in st.session_state:
        st.error("No bot selected for editing")
        st.session_state.page = "my_bots"
        st.rerun()

    bot = st.session_state.editing_bot
    st.title(f"✏️ Editing {bot['name']}")

    # Initialize session state for custom tags if not exists
    if 'custom_tags' not in st.session_state:
        st.session_state.custom_tags = []

    # Main form for bot editing - matches create_bot structure
    with st.form(key="edit_bot_form"):
        # Basic Info Section
        st.subheader("🧍 Character Details")
        col1, col2 = st.columns([1, 3])
        with col1:
            emoji = st.text_input(
                "Emoji",
                value=bot['emoji'],
                help="Choose an emoji to represent your bot (1-2 characters)"
            )
        with col2:
            name = st.text_input(
                "Name",
                value=bot['name'],
                help="Give your bot a unique name (max 30 characters)"
            )

        # Appearance Section
        st.subheader("👀 Physical Appearance")
        appearance_desc = st.text_area(
            "Describe your character's looks",
            value=bot.get('appearance', {}).get('description', ''),
            height=100,
            help="Include physical features, clothing, and distinctive attributes"
        )

        # Avatar selection (matching create_bot)
        st.write("**Avatar:**")
        avatar_option = st.radio(
            "Avatar Type",
            ["Emoji", "Upload Image"],
            index=0 if 'uploaded_file' not in bot.get('appearance', {}) else 1,
            horizontal=True
        )

        if avatar_option == "Upload Image":
            uploaded_file = st.file_uploader(
                "Upload Avatar Image",
                type=["png", "jpg", "jpeg"],
                key="avatar_upload"
            )
            if uploaded_file:
                st.image(uploaded_file, width=100)
        else:
            st.write(f"Preview: {emoji}")

        # Background Section
        st.subheader("📖 Character Background")
        description = st.text_area(
            "Tell us about your character",
            value=bot['desc'],
            height=150,
            help="Include their personality, quirks, mannerisms, and special characteristics"
        )

        # Personality Section
        st.subheader("🌟 Personality")
        traits = st.multiselect(
            "Key Personality Traits",
            PERSONALITY_TRAITS,
            default=[t for t in bot['personality'].get('traits', []) if t in PERSONALITY_TRAITS],
            help="Select traits that define your character's personality"
        )

        # Thought Process & Rules Section
        st.subheader("🧠 Thought Process & Rules")
        system_rules = st.text_area(
            "Behavior Rules",
            value=bot.get('system_rules', DEFAULT_RULES),
            height=200,
            help="Define how your character thinks and responds"
        )

        with st.expander("Formatting Guide"):
            st.markdown("""
            **Examples:**
            - `(Internal thoughts in parentheses)`
            - `"Spoken dialogue in quotes"`
            - `- Rules as bullet points`
            """)

        # Greeting Section
        st.subheader("👋 First Introduction")
        greeting = st.text_area(
            "How your character introduces itself",
            value=bot['personality'].get('greeting', ''),
            height=100,
            help="This will be the first message users see"
        )

        # Tags Section
        st.subheader("🏷️ Tags")
        all_tags = TAG_OPTIONS + st.session_state.custom_tags
        current_tags = [t for t in bot['tags'] if t in all_tags]
        tags = st.multiselect(
            "Select tags that describe your character",
            all_tags,
            default=current_tags
        )

        # ===== Voice Options Section =====
        with st.expander("🗣️ Voice Options"):
            # Initialize with current bot's voice settings or defaults
            current_voice = bot.get('voice', {'enabled': False, 'emotion': None})

            if hasattr(st.session_state, 'voice_service') and st.session_state.voice_service is not None:
                # Checkbox to enable/disable voice
                voice_enabled = st.checkbox(
                    "Enable Voice for this Character",
                    value=current_voice['enabled'],
                    help="Add voice synthesis to your character",
                    key="voice_enable_checkbox"
                )

                if voice_enabled:
                    try:
                        emotions = st.session_state.voice_service.get_available_emotions()
                        if emotions:
                            # Set default index based on current emotion or neutral
                            default_idx = 0
                            if current_voice.get('emotion'):
                                default_idx = emotions.index(current_voice['emotion']) if current_voice[
                                                                                              'emotion'] in emotions else 0
                            elif 'neutral' in emotions:
                                default_idx = emotions.index('neutral')

                            # Emotion selection dropdown
                            selected_emotion = st.selectbox(
                                "Select Voice Emotion",
                                options=emotions,
                                index=default_idx,
                                help="Select the emotional tone for your character's voice",
                                key="voice_emotion_select"
                            )

                            st.success(f"Voice will use: {selected_emotion.capitalize()} tone")
                            voice_emotion = selected_emotion
                        else:
                            st.warning("No voice emotions available")
                            voice_enabled = False
                    except Exception as e:
                        st.error(f"Error loading voice options: {str(e)}")
                        voice_enabled = False
                else:
                    voice_emotion = None
            else:
                st.info("Voice features are currently unavailable")
                voice_enabled = False

        # Status Section
        st.subheader("🔄 Status")
        status = st.radio(
            "Bot Status",
            ["Draft", "Published"],
            index=0 if bot.get("status", "draft") == "draft" else 1,
            horizontal=True,
            help="Draft: Only visible to you | Published: Visible to all users"
        )

        # Form submission button
        submitted = st.form_submit_button("💾 Save Changes")

    # Separate form for tag addition (matches create_bot)
    with st.container(border=True):
        st.subheader("Add Custom Tag")
        tag_cols = st.columns([4, 1])
        with tag_cols[0]:
            new_custom_tag = st.text_input(
                "Custom Tag Name",
                placeholder="Type new tag name",
                label_visibility="collapsed",
                key="new_tag_input"
            )
        with tag_cols[1]:
            if st.button(
                    "Add",
                    disabled=not new_custom_tag or new_custom_tag in all_tags,
                    key="add_tag_button"
            ):
                if new_custom_tag and new_custom_tag not in st.session_state.custom_tags:
                    st.session_state.custom_tags.append(new_custom_tag)
                    st.rerun()

    # Handle form submission
    if submitted:
        if not name:
            st.error("Please give your bot a name")
        else:
            # Update the bot data structure
            updated_bot = {
                "name": name,
                "emoji": emoji,
                "desc": description,
                "status": status.lower(),
                "appearance": {
                    "description": appearance_desc,
                    "avatar": bot.get('appearance', {}).get('avatar')
                },
                "tags": tags,
                "personality": {
                    "traits": traits,
                    "greeting": greeting,
                    "tone": bot['personality'].get('tone', 'Friendly')
                },
                "system_rules": system_rules,
                "voice": {
                    "enabled": voice_enabled,
                    "emotion": voice_emotion if voice_enabled else None
                },
                "custom": True,
                "creator": bot.get("creator", st.session_state.profile_data.get("username", "anonymous"))
            }

            # Handle uploaded file if changed
            if avatar_option == "Upload Image" and 'avatar_upload' in st.session_state and st.session_state.avatar_upload:
                updated_bot["appearance"]["uploaded_file"] = BotManager._handle_uploaded_file(
                    st.session_state.avatar_upload,
                    name
                )

            # Update the bot in user_bots
            for i, b in enumerate(st.session_state.user_bots):
                if b['name'] == bot['name']:
                    st.session_state.user_bots[i] = updated_bot
                    break

            st.success(f"Character '{name}' updated successfully!")
            st.session_state.page = "my_bots"
            st.rerun()

    # Cancel button
    if st.button("❌ Cancel"):
        st.session_state.page = "my_bots"
        st.rerun()