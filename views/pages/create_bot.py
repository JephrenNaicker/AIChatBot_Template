# views/pages/create_bot.py
import streamlit as st
from config import TAG_OPTIONS, PERSONALITY_TRAITS, DEFAULT_RULES
from controllers.bot_manager_controller import BotManager
from controllers.chat_controller import LLMChatController

# Character limits
NAME_LIMIT = 80
GREETING_LIMIT = 1000
DESC_LIMIT = 6000
APPEARANCE_LIMIT = DESC_LIMIT
async def _render_character_details_section(form_data):
    """Render the character details section"""
    st.subheader("🧍 Character Details")
    col1, col2 = st.columns([1, 3])
    with col1:
        form_data["basic"]["emoji"] = st.text_input(
            "Emoji",
            value=st.session_state.get('preset_data', {}).get("emoji", "🤖"),
            help="Choose an emoji to represent your bot (1-2 characters)"
        )
    with col2:
        name_input = st.text_input(
            "Name",
            value=st.session_state.get('preset_data', {}).get("name", ""),
            help=f"Give your bot a unique name (max {NAME_LIMIT} characters)",
            max_chars=NAME_LIMIT,
            key="name_input"
        )

        form_data["basic"]["name"] = name_input

    return form_data


def _render_avatar_section(form_data):
    """Render the avatar selection section"""
    st.write("**Avatar:**")
    avatar_option = st.radio(
        "Avatar Type",
        ["Emoji", "Upload Image"],
        index=0,
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


async def _render_appearance_section(form_data):
    """Render the appearance section"""
    st.subheader("👀 Physical Appearance")
    appearance_col, enhance_col = st.columns([0.9, 0.1])
    with appearance_col:
        st.markdown('<div class="text-area-container">', unsafe_allow_html=True)
        appearance_text = st.text_area(
            "Describe your character's looks",
            value=st.session_state.get("appearance_text",
                                       st.session_state.get('preset_data', {}).get("appearance", "")),
            height=100,
            help=f"Include physical features, clothing, and distinctive attributes (max {APPEARANCE_LIMIT} characters)",
            max_chars=APPEARANCE_LIMIT,
            key="appearance_text_widget"
        )
        # Display character count for appearance
        appearance_count = len(appearance_text)
        st.markdown(f'<div class="char-count">{appearance_count}/{APPEARANCE_LIMIT} characters</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
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

    form_data["appearance"]["description"] = st.session_state.get("appearance_text", appearance_text)
    return form_data

async def _render_background_section(form_data):
    """Render the character background section"""
    st.subheader("📖 Character Background")
    desc_col, enhance_col = st.columns([0.9, 0.1])
    with desc_col:
        st.markdown('<div class="text-area-container">', unsafe_allow_html=True)
        desc_text = st.text_area(
            "Tell us about your character",
            value=st.session_state.get("desc_text", st.session_state.get('preset_data', {}).get("desc", "")),
            height=150,
            help=f"Include their personality, quirks, mannerisms, and any special characteristics (max {DESC_LIMIT} characters)",
            max_chars=DESC_LIMIT,
            key="desc_text_widget"
        )
        # Display character count for description
        desc_count = len(desc_text)
        st.markdown(f'<div class="char-count">{desc_count}/{DESC_LIMIT} characters</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with enhance_col:
        if st.button("✨", key="enhance_desc", help="Enhance description with AI"):
            with st.spinner("Enhancing description..."):
                chat_controller = LLMChatController()
                current_text = st.session_state.desc_text_widget
                enhanced_text = await chat_controller.enhance_text(current_text, "character background")
                st.session_state.desc_text = enhanced_text
                st.rerun()

    form_data["basic"]["desc"] = st.session_state.get("desc_text", desc_text)
    return form_data


def _render_personality_section(form_data):
    """Render the personality traits section"""
    st.subheader("🌟 Personality")
    form_data["personality"]["traits"] = st.multiselect(
        "Key Personality Traits",
        PERSONALITY_TRAITS,
        default=st.session_state.get('preset_data', {}).get("personality", {}).get("traits", []),
        help="Select traits that define your character's personality"
    )
    return form_data


def _render_rules_section(form_data):
    """Render the rules section"""
    st.subheader("🧠 Thought Process & Rules")
    with st.expander("⚙️ Configure Behavior Rules", expanded=False):
        st.markdown('<div class="text-area-container">', unsafe_allow_html=True)
        rules_text = st.text_area(
            "Custom Behavior Rules",
            value=DEFAULT_RULES,
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


async def _render_greeting_section(form_data):
    """Render the greeting section"""
    st.subheader("👋 First Introduction")
    greeting_col, enhance_col = st.columns([0.9, 0.1])
    with greeting_col:
        st.markdown('<div class="text-area-container">', unsafe_allow_html=True)
        greeting_text = st.text_area(
            "How your character introduces itself",
            value=st.session_state.get("greeting_text", st.session_state.get('preset_data', {}).get("greeting", "")),
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

    form_data["personality"]["greeting"] = st.session_state.get("greeting_text", greeting_text)
    return form_data


def _render_tags_section(form_data):
    """Render the tags section"""
    st.subheader("🏷️ Tags")
    all_tags = TAG_OPTIONS + st.session_state.get('custom_tags', [])
    preset_tags = st.session_state.get('preset_data', {}).get("tags", [])
    valid_preset_tags = [tag for tag in preset_tags if tag in all_tags]
    form_data["tags"] = st.multiselect(
        "Select tags that describe your character",
        all_tags,
        default=valid_preset_tags
    )
    return form_data


def _render_voice_options(form_data):
    """Render the voice options section"""
    with st.expander("🗣️ Voice Options"):
        if hasattr(st.session_state, 'voice_service') and st.session_state.voice_service is not None:
            voice_enabled = st.checkbox(
                "Enable Voice for this Character",
                value=False,
                help="Add voice synthesis to your character",
                key="voice_enable_checkbox"
            )
            form_data["voice"]["enabled"] = voice_enabled

            if voice_enabled:
                try:
                    emotions = st.session_state.voice_service.get_available_emotions()
                    if emotions:
                        selected_emotion = st.selectbox(
                            "Select Voice Emotion",
                            options=emotions,
                            index=emotions.index('neutral') if 'neutral' in emotions else 0,
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


def _render_status_section(form_data):
    """Render the status section"""
    st.subheader("🔄 Status")
    form_data["status"] = st.radio(
        "Initial Status",
        ["Draft", "Published"],
        index=0,
        horizontal=True,
        help="Draft: Only visible to you | Published: Visible to all users"
    ).lower()
    return form_data


def _render_action_buttons():
    """Render the action buttons"""
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("❌ Cancel"):
            if 'preset_data' in st.session_state:
                del st.session_state.preset_data
            st.session_state.page = "my_bots"
            st.rerun()
    with col2:
        if st.button("✨ Create Character", type="primary"):
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
                    disabled=not new_custom_tag or new_custom_tag in (TAG_OPTIONS + st.session_state.custom_tags)
            ):
                if new_custom_tag and new_custom_tag not in st.session_state.custom_tags:
                    st.session_state.custom_tags.append(new_custom_tag)
                    st.rerun()


async def create_bot_page():
    st.title("🤖 Create Your Own Chat Bot")


    # Initialize session state variables
    BotManager._init_bot_creation_session()

    # Show preset options
    await BotManager._display_preset_options()

    # Main creation form
    form_data = {
        "basic": {},
        "appearance": {},
        "personality": {},
        "tags": [],
        "voice": {"enabled": False}
    }

    # Render all sections
    form_data = await _render_character_details_section(form_data)
    form_data = _render_avatar_section(form_data)
    form_data = await _render_appearance_section(form_data)
    form_data = await _render_background_section(form_data)
    form_data = _render_personality_section(form_data)
    form_data = _render_rules_section(form_data)
    form_data = await _render_greeting_section(form_data)
    form_data = _render_tags_section(form_data)
    form_data = _render_voice_options(form_data)
    form_data = _render_status_section(form_data)

    # Render action buttons
    should_create = _render_action_buttons()

    # Render custom tags form
    _render_custom_tags_form()

    # Handle form submission
    if should_create:
        await BotManager._handle_form_submission(form_data)