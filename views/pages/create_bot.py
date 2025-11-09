# views/pages/create_bot.py
import streamlit as st
from config import TAG_OPTIONS, PERSONALITY_TRAITS, DEFAULT_RULES
from controllers.bot_manager_controller import BotManager
from controllers.chat_controller import LLMChatController
from controllers.image_controller import ImageController

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
        ["Emoji", "Upload Image", "Generate with AI"],
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
            form_data["appearance"]["generated_avatar"] = None
            # Clear any confirmed avatar when switching to upload
            if 'confirmed_avatar' in st.session_state:
                st.session_state.confirmed_avatar = None
        else:
            # No file uploaded, fall back to emoji
            form_data["appearance"]["uploaded_file"] = None
            st.write(f"Preview: {form_data['basic']['emoji']}")

    elif avatar_option == "Generate with AI":
        # Use ONLY confirmed avatar in the main avatar section
        if st.session_state.get('confirmed_avatar'):
            st.image(st.session_state.confirmed_avatar, width=100, caption="AI Generated Avatar")
            form_data["appearance"]["generated_avatar"] = st.session_state.confirmed_avatar
            form_data["appearance"]["uploaded_file"] = None
            form_data["appearance"]["avatar_emoji"] = None
        else:
            st.info("👆 Generate and confirm an avatar in the Appearance section above!")
            form_data["appearance"]["uploaded_file"] = None
            form_data["appearance"]["avatar_emoji"] = form_data["basic"]["emoji"]
            form_data["appearance"]["generated_avatar"] = None

    else:
        # Emoji selected - clear any generated/confirmed avatars
        form_data["appearance"]["uploaded_file"] = None
        form_data["appearance"]["generated_avatar"] = None
        if 'confirmed_avatar' in st.session_state:
            st.session_state.confirmed_avatar = None
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

    # Add avatar generation button if AI avatar is selected - MOVED TO BOTTOM
    if st.session_state.get("avatar_option") == "Generate with AI":
        st.markdown("---")

        # Display areas in two columns for clear separation
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🔄 AI Generated Avatar")
            # Display latest generated avatar (preview - dynamic)
            if st.session_state.get('generated_avatar'):
                st.image(st.session_state.generated_avatar, width=150, caption="Latest Generated Preview")

                # Confirm button for the generated avatar
                if st.button("✅ Confirm This Avatar", key="confirm_avatar", type="primary"):
                    st.session_state.confirmed_avatar = st.session_state.generated_avatar
                    st.session_state.generated_avatar = None
                    st.success("Avatar confirmed!")
                    st.rerun()
            else:
                st.info("No avatar generated yet")

            # Generate new avatar button
            if st.button("🎨 Generate New Avatar", key="generate_avatar_btn"):
                # Get the current values directly from the form data and session state
                character_name = form_data["basic"]["name"].strip()
                appearance_desc = form_data["appearance"]["description"].strip()

                # Validate inputs
                if not character_name:
                    st.error("❌ Please provide a character name first")
                    st.stop()

                if not appearance_desc:
                    st.error("❌ Please provide a physical appearance description first")
                    st.stop()

                if len(appearance_desc) < 10:
                    st.warning(
                        "📝 For best results, please provide a more detailed appearance description (at least 10 characters)")
                    st.stop()

                # If validation passes, generate the avatar
                with st.spinner("Generating avatar with AI..."):
                    try:
                        image_controller = ImageController()

                        # Generate the avatar
                        generated_image, error = image_controller.generate_avatar(
                            character_name,
                            appearance_desc
                        )

                        if generated_image:
                            # Convert PIL Image to bytes for session state storage
                            from io import BytesIO
                            import base64

                            buffered = BytesIO()
                            generated_image.save(buffered, format="PNG")
                            img_str = base64.b64encode(buffered.getvalue()).decode()

                            # Set as generated avatar (preview) - does NOT affect confirmed avatar
                            st.session_state.generated_avatar = f"data:image/png;base64,{img_str}"
                            st.success("New avatar generated! Click 'Confirm' to use it.")
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to generate avatar: {error}")
                    except Exception as e:
                        st.error(f"❌ Error generating avatar: {str(e)}")

        with col2:
            st.subheader("✅ Confirmed Avatar")
            # Display current confirmed avatar (static - only changes when confirmed)
            if st.session_state.get('confirmed_avatar'):
                st.image(st.session_state.confirmed_avatar, width=150, caption="Confirmed Avatar")
                st.success("✓ This avatar will be used for your character")
            else:
                st.info("No avatar confirmed yet")

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

async def _render_scenario_section(form_data):
    """Render the scenario section"""
    st.subheader("🎭 Scenario Context")
    scenario_col, enhance_col = st.columns([0.9, 0.1])
    with scenario_col:
        st.markdown('<div class="text-area-container">', unsafe_allow_html=True)
        scenario_text = st.text_area(
            "Optional: Set the scene or scenario",
            value=st.session_state.get("scenario_text", st.session_state.get('preset_data', {}).get("scenario", "")),
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

    form_data["scenario"] = st.session_state.get("scenario_text", scenario_text)
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
    st.markdown("**Required: Select 1-5 tags**")

    all_tags = TAG_OPTIONS + st.session_state.get('custom_tags', [])
    preset_tags = st.session_state.get('preset_data', {}).get("tags", [])
    valid_preset_tags = [tag for tag in preset_tags if tag in all_tags]

    # Use multiselect with validation
    selected_tags = st.multiselect(
        "Select tags that describe your character (1-5 required)",
        all_tags,
        default=valid_preset_tags,
        help="Choose at least 1 tag and up to 5 tags to help users discover your character"
    )

    # Validation message
    if len(selected_tags) == 0:
        st.error("❌ Please select at least 1 tag")
    elif len(selected_tags) > 5:
        st.error("❌ Maximum 5 tags allowed")
        # Truncate to 5 if user selects more
        selected_tags = selected_tags[:5]

    form_data["tags"] = selected_tags
    return form_data


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
    form_data["is_public"] = st.radio(
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

    # Get current tags from session state to validate
    current_tags = st.session_state.get('tags_section_tags', [])

    with col1:
        if st.button("❌ Cancel"):
            if 'preset_data' in st.session_state:
                del st.session_state.preset_data
            st.session_state.page = "my_bots"
            st.rerun()

    with col2:
        # Disable create button if tags validation fails
        create_disabled = len(current_tags) == 0 or len(current_tags) > 5

        if st.button("✨ Create Character",
                     type="primary",
                     disabled=create_disabled,
                     help="Please select 1-5 tags to continue" if create_disabled else "Create your character"):
            if len(current_tags) == 0:
                st.error("❌ Please select at least 1 tag before creating your character")
                st.stop()
            elif len(current_tags) > 5:
                st.error("❌ Maximum 5 tags allowed. Please remove some tags.")
                st.stop()
            return True

    return False


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
        "voice": {"enabled": False},
        "scenario": ""
    }

    # Render all sections
    form_data = await _render_character_details_section(form_data)
    form_data = _render_avatar_section(form_data)
    form_data = await _render_appearance_section(form_data)
    form_data = await _render_background_section(form_data)
    form_data = _render_personality_section(form_data)
    form_data = _render_rules_section(form_data)
    form_data = await _render_greeting_section(form_data)
    form_data = await _render_scenario_section(form_data)
    form_data = _render_tags_section(form_data)
    form_data = _render_voice_options(form_data)
    form_data = _render_status_section(form_data)

    # Store current tags for validation
    st.session_state.tags_section_tags = form_data["tags"]
    # Render action buttons
    should_create = _render_action_buttons()

    # Render custom tags form
    _render_custom_tags_form()

    # Handle form submission
    if should_create:
        await BotManager._handle_form_submission(form_data)