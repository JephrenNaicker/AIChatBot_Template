import streamlit as st
import os

from config import TAG_OPTIONS, PERSONALITY_TRAITS, DEFAULT_RULES
from controllers.bot_manager_controller import BotManager
from controllers.chat_controller import LLMChatController
from models.bot import Bot

# Character limits (same as create_bot.py)
NAME_LIMIT = 80
GREETING_LIMIT = 1000
DESC_LIMIT = 6000
APPEARANCE_LIMIT = DESC_LIMIT


async def _render_character_details_section(form_data, bot: Bot):
    """Render the character details section"""
    st.subheader("🧍 Character Details")
    col1, col2 = st.columns([1, 3])
    with col1:
        form_data["basic"]["emoji"] = st.text_input(
            "Emoji",
            value=bot.emoji,
            help="Choose an emoji to represent your bot (1-2 characters)"
        )
    with col2:
        name_input = st.text_input(
            "Name",
            value=bot.name,
            help=f"Give your bot a unique name (max {NAME_LIMIT} characters)",
            max_chars=NAME_LIMIT,
            key="name_input"
        )
        form_data["basic"]["name"] = name_input

    return form_data


def _render_avatar_section(form_data, bot: Bot):
    """Render the avatar selection section"""
    st.write("**Avatar:**")

    # Determine initial avatar type
    avatar_type_index = 0
    if bot.appearance.get("avatar_type") == "Upload Image" or bot.appearance.get("avatar_data"):
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
        elif bot.appearance.get("avatar_data"):
            # Show existing image if available
            avatar_data = bot.appearance.get("avatar_data", {})

            try:
                # Handle dictionary format
                if isinstance(avatar_data, dict):
                    filepath = avatar_data.get('filepath')

                    # Normalize path separators
                    if filepath:
                        filepath = filepath.replace('\\', '/')

                    if filepath and os.path.exists(filepath):
                        st.image(filepath, width=100, caption="Current Avatar")
                    else:
                        st.write("Current avatar image (file not found)")
                else:
                    st.write("Current avatar image (invalid format)")

            except Exception as e:
                st.write("Current avatar image (display error)")

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

async def _render_appearance_section(form_data, bot: Bot):
    """Render the appearance section"""
    st.subheader("👀 Physical Appearance")
    appearance_col, enhance_col = st.columns([0.9, 0.1])

    # Initialize session state if not exists
    if "appearance_text" not in st.session_state:
        st.session_state.appearance_text = bot.appearance.get("description", "")

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

    if st.session_state.appearance_text_widget != st.session_state.appearance_text:
        st.session_state.appearance_text = st.session_state.appearance_text_widget

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


async def _render_scenario_section(form_data, bot: Bot):
    """Render the scenario section"""
    st.subheader("🎭 Scenario Context")

    # Initialize session state if not exists
    if "scenario_text" not in st.session_state:
        st.session_state.scenario_text = bot.scenario

    scenario_col, enhance_col = st.columns([0.9, 0.1])
    with scenario_col:
        st.markdown('<div class="text-area-container">', unsafe_allow_html=True)
        scenario_text = st.text_area(
            "Optional: Set the scene or scenario",
            value=st.session_state.scenario_text,
            height=100,
            help=f"Describe the situation, setting, or context for this interaction (max {DESC_LIMIT} characters)",
            max_chars=DESC_LIMIT,
            placeholder="Example: We're exploring an ancient temple together. You're my guide who knows the secrets of this place...",
            key="scenario_text_widget"
        )
        # Display character count for scenario
        scenario_count = len(scenario_text)
        st.markdown(f'<div class="char-count">{scenario_count}/{DESC_LIMIT} characters</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.scenario_text_widget != st.session_state.scenario_text:
            st.session_state.scenario_text = st.session_state.scenario_text_widget

    with enhance_col:
        if st.button("✨", key="enhance_scenario", help="Enhance scenario with AI"):
            with st.spinner("Enhancing scenario..."):
                chat_controller = LLMChatController()
                current_text = st.session_state.scenario_text_widget
                enhanced_text = await chat_controller.enhance_text(current_text, "scenario context")
                # Ensure enhanced text doesn't exceed the limit
                if len(enhanced_text) > DESC_LIMIT:
                    enhanced_text = enhanced_text[:DESC_LIMIT]
                st.session_state.scenario_text = enhanced_text
                st.rerun()

    form_data["scenario"] = st.session_state.scenario_text
    return form_data


async def _render_background_section(form_data, bot: Bot):
    """Render the character background section"""
    st.subheader("📖 Character Background")

    # Initialize session state if not exists
    if "desc_text" not in st.session_state:
        st.session_state.desc_text = bot.desc

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

    if st.session_state.desc_text_widget != st.session_state.desc_text:
        st.session_state.desc_text = st.session_state.desc_text_widget

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


def _render_personality_section(form_data, bot: Bot):
    """Render the personality traits section"""
    st.subheader("🌟 Personality")
    form_data["personality"]["traits"] = st.multiselect(
        "Key Personality Traits",
        PERSONALITY_TRAITS,
        default=bot.personality.get("traits", []),
        help="Select traits that define your character's personality"
    )
    return form_data


def _render_rules_section(form_data, bot: Bot):
    """Render the rules section"""
    st.subheader("🧠 Thought Process & Rules")
    with st.expander("⚙️ Configure Behavior Rules", expanded=False):
        st.markdown('<div class="text-area-container">', unsafe_allow_html=True)
        rules_text = st.text_area(
            "Custom Behavior Rules",
            value=bot.system_rules or DEFAULT_RULES,
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


async def _render_greeting_section(form_data, bot: Bot):
    """Render the greeting section"""
    st.subheader("👋 First Introduction")

    # Initialize session state if not exists
    if "greeting_text" not in st.session_state:
        st.session_state.greeting_text = bot.personality.get("greeting", "")

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

        if st.session_state.greeting_text_widget != st.session_state.greeting_text:
            st.session_state.greeting_text = st.session_state.greeting_text_widget

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


def _render_tags_section(form_data, bot: Bot):
    """Render the tags section"""
    st.subheader("🏷️ Tags")
    all_tags = TAG_OPTIONS + st.session_state.get('custom_tags', [])
    valid_bot_tags = [tag for tag in bot.tags if tag in all_tags]
    form_data["tags"] = st.multiselect(
        "Select tags that describe your character",
        all_tags,
        default=valid_bot_tags
    )
    return form_data


def _render_voice_options(form_data, bot: Bot):
    """Render the voice options section"""
    with st.expander("🗣️ Voice Options"):
        if hasattr(st.session_state, 'voice_service') and st.session_state.voice_service is not None:
            voice_enabled = st.checkbox(
                "Enable Voice for this Character",
                value=bot.voice.get("enabled", False),
                help="Add voice synthesis to your character",
                key="voice_enable_checkbox"
            )
            form_data["voice"]["enabled"] = voice_enabled

            if voice_enabled:
                try:
                    emotions = st.session_state.voice_service.get_available_emotions()
                    if emotions:
                        current_emotion = bot.voice.get("emotion", "neutral")
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


def _render_status_section(form_data, bot: Bot):
    """Render the status section"""
    st.subheader("🔄 Status")
    form_data["is_public"] = st.toggle(
        "Make Public",
        value=bot.is_public,
        help="Off: Only visible to you (Draft) | On: Visible to all users (Published)"
    )
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
    st.title(f"✏️ Editing {bot.name}")

    # Initialize session state for custom tags if not exists
    if 'custom_tags' not in st.session_state:
        st.session_state.custom_tags = []

    # Initialize session state variables for text fields
    if "appearance_text" not in st.session_state:
        st.session_state.appearance_text = bot.appearance.get("description", "")

    if "desc_text" not in st.session_state:
        st.session_state.desc_text = bot.desc

    if "greeting_text" not in st.session_state:
        st.session_state.greeting_text = bot.personality.get("greeting", "")

    if "scenario_text" not in st.session_state:
        st.session_state.scenario_text = bot.scenario

    # Main form for bot editing - matches create_bot structure
    form_data = {
        "basic": {},
        "appearance": {},
        "personality": {"tone": bot.personality.get("tone", "Friendly")},
        "tags": [],
        "voice": {"enabled": False},
        "scenario": "",
        "is_public": bot.is_public
    }

    # Render all sections
    form_data = await _render_character_details_section(form_data, bot)
    form_data = _render_avatar_section(form_data, bot)
    form_data = await _render_appearance_section(form_data, bot)
    form_data = await _render_background_section(form_data, bot)
    form_data = _render_personality_section(form_data, bot)
    form_data = _render_rules_section(form_data, bot)
    form_data = await _render_greeting_section(form_data, bot)
    form_data = await _render_scenario_section(form_data, bot)
    form_data = _render_tags_section(form_data, bot)
    form_data = _render_voice_options(form_data, bot)
    form_data = _render_status_section(form_data, bot)

    # Render action buttons
    should_save = _render_action_buttons()

    # Render custom tags form
    _render_custom_tags_form()

    # Handle form submission - FIXED AVATAR HANDLING
    if should_save:
        if not form_data["basic"].get("name"):
            st.error("Please give your bot a name")
        else:
            # Update the bot using the Bot object's update method
            try:
                # Create form data structure that matches Bot.update_from_form_data expectations
                update_form_data = {
                    "basic": {
                        "name": form_data["basic"]["name"],
                        "emoji": form_data["basic"]["emoji"],
                        "desc": form_data["basic"]["desc"]
                    },
                    "tags": form_data["tags"],
                    "is_public": form_data["is_public"],
                    "scenario": form_data["scenario"],
                    "personality": {
                        "tone": bot.personality.get("tone", "Friendly"),
                        "traits": form_data["personality"]["traits"],
                        "greeting": form_data["personality"]["greeting"]
                    },
                    "system_rules": form_data["system_rules"],
                    "appearance": {
                        "description": form_data["appearance"]["description"],
                        "avatar_type": form_data["appearance"]["avatar_type"],
                        "avatar_data": bot.appearance.get("avatar_data")  # Preserve existing avatar data initially
                    },
                    "voice": form_data["voice"]
                }

                # Handle avatar data - FIXED LOGIC
                if form_data["appearance"].get("avatar_type") == "Upload Image":
                    if form_data["appearance"].get("uploaded_file"):
                        # Process new uploaded file
                        uploaded_file = form_data["appearance"]["uploaded_file"]
                        file_info = await BotManager._handle_uploaded_file(uploaded_file, form_data["basic"]["name"])

                        if file_info:
                            update_form_data["appearance"]["avatar_data"] = file_info
                            update_form_data["appearance"]["avatar_type"] = "uploaded"
                            st.toast("New avatar image saved successfully!", icon="✅")
                        else:
                            # Fall back to existing avatar or emoji
                            if bot.appearance.get("avatar_data"):
                                update_form_data["appearance"]["avatar_type"] = "uploaded"
                                st.toast("Failed to save new avatar, keeping existing image", icon="⚠️")
                            else:
                                update_form_data["appearance"]["avatar_type"] = "emoji"
                                update_form_data["appearance"]["avatar_data"] = None
                                st.toast("Failed to save avatar image, using emoji instead", icon="⚠️")
                    else:
                        # No new file uploaded, keep existing avatar data
                        if bot.appearance.get("avatar_data"):
                            update_form_data["appearance"]["avatar_type"] = "uploaded"
                            update_form_data["appearance"]["avatar_data"] = bot.appearance.get("avatar_data")
                        else:
                            # No existing avatar, use emoji
                            update_form_data["appearance"]["avatar_type"] = "emoji"
                            update_form_data["appearance"]["avatar_data"] = None
                else:
                    # Emoji selected
                    update_form_data["appearance"]["avatar_type"] = "emoji"
                    update_form_data["appearance"]["avatar_data"] = None

                # Update the bot object
                bot.update_from_form_data(update_form_data)

                # Update the bot in user_bots list
                bot_updated = False
                for i, user_bot in enumerate(st.session_state.user_bots):
                    if user_bot.bot_id == bot.bot_id:
                        st.session_state.user_bots[i] = bot
                        bot_updated = True
                        break

                if not bot_updated:
                    # If not found by ID, try to find by name (fallback)
                    original_bot_name = st.session_state.get('original_bot_name', bot.name)
                    for i, user_bot in enumerate(st.session_state.user_bots):
                        if user_bot.name == original_bot_name:
                            st.session_state.user_bots[i] = bot
                            bot_updated = True
                            break

                # Clear session state variables
                for key in ["appearance_text", "desc_text", "greeting_text", "scenario_text"]:
                    if key in st.session_state:
                        del st.session_state[key]

                st.success(f"Character '{bot.name}' updated successfully!")
                st.session_state.page = "my_bots"
                st.rerun()

            except Exception as e:
                st.error(f"Error updating bot: {str(e)}")