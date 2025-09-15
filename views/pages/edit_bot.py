import streamlit as st
from config import TAG_OPTIONS, PERSONALITY_TRAITS, DEFAULT_RULES
from controllers.bot_manager_controller import BotManager
from controllers.chat_controller import LLMChatController

# Character limits (same as create_bot.py)
NAME_LIMIT = 80
GREETING_LIMIT = 1000
DESC_LIMIT = 6000
APPEARANCE_LIMIT = DESC_LIMIT


async def _render_character_details_section(form_data, bot):
    """Render the character details section"""
    st.subheader("🧍 Character Details")
    col1, col2 = st.columns([1, 3])
    with col1:
        form_data["basic"]["emoji"] = st.text_input(
            "Emoji",
            value=bot.get("emoji", "🤖"),
            help="Choose an emoji to represent your bot (1-2 characters)"
        )
    with col2:
        name_input = st.text_input(
            "Name",
            value=bot.get("name", ""),
            help=f"Give your bot a unique name (max {NAME_LIMIT} characters)",
            max_chars=NAME_LIMIT,
            key="name_input"
        )
        form_data["basic"]["name"] = name_input

    return form_data


def _render_avatar_section(form_data, bot):
    """Render the avatar selection section"""
    st.write("**Avatar:**")

    # Determine initial avatar type
    avatar_type_index = 0
    if bot.get('appearance', {}).get('avatar') or bot.get('appearance', {}).get('avatar_url'):
        avatar_type_index = 1

    avatar_option = st.radio(
        "Avatar Type",
        ["Emoji", "Upload Image"],
        index=avatar_type_index,
        horizontal=True,
        key="avatar_option"
    )

    # Initialize avatar data in form_data
    form_data["appearance"]["avatar_type"] = avatar_option
    form_data["appearance"]["avatar_emoji"] = form_data["basic"]["emoji"]

    if avatar_option == "Upload Image":
        uploaded_file = st.file_uploader(
            "Upload Avatar Image",
            type=["png", "jpg", "jpeg"],
            key="avatar_upload"
        )

        if uploaded_file:
            form_data["appearance"]["uploaded_file"] = uploaded_file
            # Show the uploaded image preview
            st.image(uploaded_file, width=100, caption="Uploaded Avatar")
            # Don't show emoji when image is uploaded
            form_data["appearance"]["avatar_emoji"] = None
        elif bot.get('appearance', {}).get('avatar'):
            # Show existing image if available
            avatar_info = bot['appearance']['avatar']
            if isinstance(avatar_info, dict) and 'filepath' in avatar_info:
                try:
                    from PIL import Image
                    image = Image.open(avatar_info['filepath'])
                    st.image(image, width=100, caption="Current Avatar")
                except:
                    st.write("Could not load current avatar image")
            form_data["appearance"]["uploaded_file"] = None
        else:
            # No file uploaded, fall back to emoji
            form_data["appearance"]["uploaded_file"] = None
            st.write(f"Preview: {form_data['basic']['emoji']}")
    else:
        # Emoji selected
        form_data["appearance"]["uploaded_file"] = None
        form_data["appearance"]["avatar_emoji"] = form_data["basic"]["emoji"]
        st.write(f"Preview: {form_data['basic']['emoji']}")

    return form_data


async def _render_appearance_section(form_data, bot):
    """Render the appearance section"""
    st.subheader("👀 Physical Appearance")
    appearance_col, enhance_col = st.columns([0.9, 0.1])

    # Initialize session state if not exists
    if "appearance_text" not in st.session_state:
        st.session_state.appearance_text = bot.get('appearance', {}).get('description', '')

    with appearance_col:
        st.markdown('<div class="text-area-container">', unsafe_allow_html=True)
        appearance_text = st.text_area(
            "Describe your character's looks",
            value=st.session_state.appearance_text,
            height=100,
            help=f"Include physical features, clothing, and distinctive attributes (max {APPEARANCE_LIMIT} characters)",
            max_chars=APPEARANCE_LIMIT,
            key="appearance_text_widget"
        )

    with enhance_col:
        if st.button("✨", key="enhance_appearance", help="Enhance description with AI"):
            with st.spinner("Enhancing description..."):
                chat_controller = LLMChatController()
                current_text = st.session_state.appearance_text_widget
                enhanced_text = await chat_controller.enhance_text(current_text, "appearance description")
                # Ensure enhanced text doesn't exceed the limit
                if len(enhanced_text) > APPEARANCE_LIMIT:
                    enhanced_text = enhanced_text[:APPEARANCE_LIMIT]
                st.session_state.appearance_text = enhanced_text
                st.rerun()

    form_data["appearance"]["description"] = st.session_state.appearance_text
    return form_data


async def _render_background_section(form_data, bot):
    """Render the character background section"""
    st.subheader("📖 Character Background")

    # Initialize session state if not exists
    if "desc_text" not in st.session_state:
        st.session_state.desc_text = bot.get('desc', '')

    desc_col, enhance_col = st.columns([0.9, 0.1])
    with desc_col:
        st.markdown('<div class="text-area-container">', unsafe_allow_html=True)
        desc_text = st.text_area(
            "Tell us about your character",
            value=st.session_state.desc_text,
            height=150,
            help=f"Include their personality, quirks, mannerisms, and any special characteristics (max {DESC_LIMIT} characters)",
            max_chars=DESC_LIMIT,
            key="desc_text_widget"
        )

    with enhance_col:
        if st.button("✨", key="enhance_desc", help="Enhance description with AI"):
            with st.spinner("Enhancing description..."):
                chat_controller = LLMChatController()
                current_text = st.session_state.desc_text_widget
                enhanced_text = await chat_controller.enhance_text(current_text, "character background")
                st.session_state.desc_text = enhanced_text
                st.rerun()

    form_data["basic"]["desc"] = st.session_state.desc_text
    return form_data


def _render_personality_section(form_data, bot):
    """Render the personality traits section"""
    st.subheader("🌟 Personality")
    form_data["personality"]["traits"] = st.multiselect(
        "Key Personality Traits",
        PERSONALITY_TRAITS,
        default=bot.get("personality", {}).get("traits", []),
        help="Select traits that define your character's personality"
    )
    return form_data


def _render_rules_section(form_data, bot):
    """Render the rules section"""
    st.subheader("🧠 Thought Process & Rules")
    with st.expander("⚙️ Configure Behavior Rules", expanded=False):
        st.markdown('<div class="text-area-container">', unsafe_allow_html=True)
        rules_text = st.text_area(
            "Custom Behavior Rules",
            value=bot.get("system_rules", DEFAULT_RULES),
            height=200,
            help="Define how your character thinks and responds",
            key="rules_text"
        )
        # Display character count for rules
        rules_count = len(rules_text)
        st.markdown(f'<div class="char-count">{rules_count} characters</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    form_data["system_rules"] = st.session_state.get("rules_text", rules_text)
    return form_data


async def _render_greeting_section(form_data, bot):
    """Render the greeting section"""
    st.subheader("👋 First Introduction")

    # Initialize session state if not exists
    if "greeting_text" not in st.session_state:
        st.session_state.greeting_text = bot.get("personality", {}).get("greeting", "")

    greeting_col, enhance_col = st.columns([0.9, 0.1])
    with greeting_col:
        st.markdown('<div class="text-area-container">', unsafe_allow_html=True)
        greeting_text = st.text_area(
            "How your character introduces itself",
            value=st.session_state.greeting_text,
            height=100,
            help=f"This will be the first message users see (max {GREETING_LIMIT} characters)",
            max_chars=GREETING_LIMIT,
            key="greeting_text_widget"
        )
        # Display character count for greeting
        greeting_count = len(greeting_text)
        st.markdown(f'<div class="char-count">{greeting_count}/{GREETING_LIMIT} characters</div>',
                    unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with enhance_col:
        if st.button("✨", key="enhance_greeting", help="Enhance greeting with AI"):
            with st.spinner("Crafting perfect greeting..."):
                chat_controller = LLMChatController()
                # Get all relevant context
                context = {
                    "name": form_data["basic"]["name"],
                    "appearance": st.session_state.get("appearance_text", ""),
                    "background": st.session_state.get("desc_text", ""),
                    "personality": ", ".join(form_data["personality"]["traits"]),
                    "current_greeting": st.session_state.greeting_text_widget
                }

                prompt = f"""Create an engaging greeting message for {context['name']} that:
                - Matches their personality: {context['personality']}
                - Reflects their background: {context['background']}
                - Optionally references their appearance: {context['appearance']}
                - Is 4-5 sentences maximum
                - Sounds in-character
                - Thoughts appear in italics format
                - Dialogue in "quotes"

                Current greeting (improve upon this):
                {context['current_greeting']}
                === Enhanced greeting ===

                === End Enhanced greeting ==="""

                enhanced_text = await chat_controller.enhance_text(prompt, "character greeting")
                st.session_state.greeting_text = enhanced_text
                st.rerun()

    form_data["personality"]["greeting"] = st.session_state.greeting_text
    return form_data


def _render_tags_section(form_data, bot):
    """Render the tags section"""
    st.subheader("🏷️ Tags")
    all_tags = TAG_OPTIONS + st.session_state.get('custom_tags', [])
    valid_bot_tags = [tag for tag in bot.get("tags", []) if tag in all_tags]
    form_data["tags"] = st.multiselect(
        "Select tags that describe your character",
        all_tags,
        default=valid_bot_tags
    )
    return form_data


def _render_voice_options(form_data, bot):
    """Render the voice options section"""
    with st.expander("🗣️ Voice Options"):
        if hasattr(st.session_state, 'voice_service') and st.session_state.voice_service is not None:
            voice_enabled = st.checkbox(
                "Enable Voice for this Character",
                value=bot.get("voice", {}).get("enabled", False),
                help="Add voice synthesis to your character",
                key="voice_enable_checkbox"
            )
            form_data["voice"]["enabled"] = voice_enabled

            if voice_enabled:
                try:
                    emotions = st.session_state.voice_service.get_available_emotions()
                    if emotions:
                        current_emotion = bot.get("voice", {}).get("emotion", "neutral")
                        default_idx = emotions.index(current_emotion) if current_emotion in emotions else 0

                        selected_emotion = st.selectbox(
                            "Select Voice Emotion",
                            options=emotions,
                            index=default_idx,
                            help="Select the emotional tone for your character's voice",
                            key="voice_emotion_select"
                        )
                        form_data["voice"]["emotion"] = selected_emotion
                        st.success(f"Voice will use: {selected_emotion.capitalize()} tone")
                    else:
                        st.warning("No voice emotions available")
                        form_data["voice"]["enabled"] = False
                except Exception as e:
                    st.error(f"Error loading voice options: {str(e)}")
                    form_data["voice"]["enabled"] = False
        else:
            st.info("Voice features are currently unavailable")
            form_data["voice"]["enabled"] = False

    return form_data


def _render_status_section(form_data, bot):
    """Render the status section"""
    st.subheader("🔄 Status")
    status_index = 0 if bot.get("status", "draft") == "draft" else 1
    form_data["status"] = st.radio(
        "Initial Status",
        ["Draft", "Published"],
        index=status_index,
        horizontal=True,
        help="Draft: Only visible to you | Published: Visible to all users"
    ).lower()
    return form_data


def _render_action_buttons():
    """Render the action buttons"""
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("❌ Cancel"):
            st.session_state.page = "my_bots"
            st.rerun()
    with col2:
        if st.button("💾 Save Changes", type="primary"):
            return True
    return False


def _render_custom_tags_form():
    """Render the custom tags form"""
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
                    disabled=not new_custom_tag or new_custom_tag in (
                            TAG_OPTIONS + st.session_state.get('custom_tags', []))
            ):
                if new_custom_tag and new_custom_tag not in st.session_state.get('custom_tags', []):
                    if 'custom_tags' not in st.session_state:
                        st.session_state.custom_tags = []
                    st.session_state.custom_tags.append(new_custom_tag)
                    st.rerun()


async def edit_bot_page():
    if 'editing_bot' not in st.session_state:
        st.error("No bot selected for editing")
        st.session_state.page = "my_bots"
        st.rerun()

    bot = st.session_state.editing_bot
    st.title(f"✏️ Editing {bot['name']}")

    # Initialize session state for custom tags if not exists
    if 'custom_tags' not in st.session_state:
        st.session_state.custom_tags = []

    # Initialize session state variables for text fields
    if "appearance_text" not in st.session_state:
        st.session_state.appearance_text = bot.get('appearance', {}).get('description', '')

    if "desc_text" not in st.session_state:
        st.session_state.desc_text = bot.get('desc', '')

    if "greeting_text" not in st.session_state:
        st.session_state.greeting_text = bot.get('personality', {}).get('greeting', '')

    # Main form for bot editing - matches create_bot structure
    form_data = {
        "basic": {},
        "appearance": {},
        "personality": {},
        "tags": [],
        "voice": {"enabled": False}
    }

    # Render all sections
    form_data = await _render_character_details_section(form_data, bot)
    form_data = _render_avatar_section(form_data, bot)
    form_data = await _render_appearance_section(form_data, bot)
    form_data = await _render_background_section(form_data, bot)
    form_data = _render_personality_section(form_data, bot)
    form_data = _render_rules_section(form_data, bot)
    form_data = await _render_greeting_section(form_data, bot)
    form_data = _render_tags_section(form_data, bot)
    form_data = _render_voice_options(form_data, bot)
    form_data = _render_status_section(form_data, bot)

    # Render action buttons
    should_save = _render_action_buttons()

    # Render custom tags form
    _render_custom_tags_form()

    # Handle form submission
    if should_save:
        if not form_data["basic"].get("name"):
            st.error("Please give your bot a name")
        else:
            # Update the bot data structure
            updated_bot = {
                "name": form_data["basic"]["name"],
                "emoji": form_data["basic"]["emoji"],
                "desc": form_data["basic"]["desc"],
                "status": form_data["status"],
                "appearance": {
                    "description": form_data["appearance"]["description"],
                    "avatar_type": form_data["appearance"]["avatar_type"],
                    "avatar_emoji": form_data["appearance"]["avatar_emoji"]
                },
                "tags": form_data["tags"],
                "personality": {
                    "traits": form_data["personality"]["traits"],
                    "greeting": form_data["personality"]["greeting"],
                    "tone": bot['personality'].get('tone', 'Friendly')  # Preserve existing tone
                },
                "system_rules": form_data["system_rules"],
                "voice": form_data["voice"],
                "custom": True,
                "creator": bot.get("creator", st.session_state.profile_data.get("username", "anonymous"))
            }

            # Handle uploaded file if changed - use the same logic as create_bot
            if (form_data["appearance"].get("avatar_type") == "Upload Image" and
                    form_data["appearance"].get("uploaded_file")):

                # Process the uploaded file using the same method as create_bot
                uploaded_file = form_data["appearance"]["uploaded_file"]
                file_info = await BotManager._handle_uploaded_file(uploaded_file, form_data["basic"]["name"])

                if file_info:
                    updated_bot["appearance"]["avatar"] = file_info
                    # Use the uploaded image, not the emoji
                    updated_bot["emoji"] = None
                    st.toast(f"Avatar image saved successfully!", icon="✅")
                else:
                    # Fall back to emoji if image upload fails
                    updated_bot["appearance"]["avatar"] = None
                    updated_bot["emoji"] = form_data["basic"]["emoji"]
                    st.toast("Failed to save avatar image, using emoji instead", icon="⚠️")
            else:
                # Use emoji as avatar or keep existing image
                if bot.get('appearance', {}).get('avatar'):
                    # Keep existing avatar
                    updated_bot["appearance"]["avatar"] = bot['appearance']['avatar']
                    updated_bot["emoji"] = None
                else:
                    # Use emoji
                    updated_bot["appearance"]["avatar"] = None
                    updated_bot["emoji"] = form_data["basic"]["emoji"]

            # Update the bot in user_bots
            bot_updated = False
            for i, b in enumerate(st.session_state.user_bots):
                if b['name'] == bot['name']:
                    st.session_state.user_bots[i] = updated_bot
                    bot_updated = True
                    break

            if not bot_updated:
                # If bot name was changed, we need to find it by some other identifier
                # For now, just add it as a new bot (this might not be the desired behavior)
                st.session_state.user_bots.append(updated_bot)

            # Clear session state variables
            for key in ["appearance_text", "desc_text", "greeting_text"]:
                if key in st.session_state:
                    del st.session_state[key]

            st.success(f"Character '{form_data['basic']['name']}' updated successfully!")
            st.session_state.page = "my_bots"
            st.rerun()