# views/pages/create_bot.py
import streamlit as st
from config import TAG_OPTIONS, PERSONALITY_TRAITS, DEFAULT_RULES
from controllers.bot_manager_controller import BotManager
from controllers.chat_controller import LLMChatController

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

    # ===== Character Details Section =====
    st.subheader("🧍 Character Details")
    col1, col2 = st.columns([1, 3])
    with col1:
        form_data["basic"]["emoji"] = st.text_input(
            "Emoji",
            value=st.session_state.get('preset_data', {}).get("emoji", "🤖"),
            help="Choose an emoji to represent your bot (1-2 characters)"
        )
    with col2:
        form_data["basic"]["name"] = st.text_input(
            "Name",
            value=st.session_state.get('preset_data', {}).get("name", ""),
            help="Give your bot a unique name (max 30 characters)"
        )

    # Avatar selection - moved up near the top
    st.subheader("🖼️ Avatar")
    avatar_option = st.radio(
        "Avatar Type",
        ["Emoji", "Upload Image"],
        index=0,
        horizontal=True
    )
    if avatar_option == "Upload Image":
        form_data["appearance"]["uploaded_file"] = st.file_uploader(
            "Upload Avatar Image",
            type=["png", "jpg", "jpeg"]
        )
        if form_data["appearance"]["uploaded_file"]:
            st.image(form_data["appearance"]["uploaded_file"], width=100)
    else:
        st.write(f"Preview: {form_data['basic']['emoji']}")

    # ===== Appearance Section =====
    st.subheader("👀 Physical Appearance")
    appearance_col, enhance_col = st.columns([0.9, 0.1])
    with appearance_col:
        appearance_text = st.text_area(
            "Describe your character's looks",
            value=st.session_state.get("appearance_text",
                                       st.session_state.get('preset_data', {}).get("appearance", "")),
            height=100,
            help="Include physical features, clothing, and distinctive attributes",
            key="appearance_text_widget"  # Different key for the widget
        )
    with enhance_col:
        if st.button("✨", key="enhance_appearance", help="Enhance description with AI"):
            with st.spinner("Enhancing description..."):
                chat_controller = LLMChatController()
                current_text = st.session_state.appearance_text_widget  # Get current text from widget
                enhanced_text = await chat_controller.enhance_text(current_text, "appearance description")
                st.session_state.appearance_text = enhanced_text  # Store in separate session state variable
                st.rerun()

        form_data["appearance"]["description"] = st.session_state.get("appearance_text", appearance_text)

    # ===== Back Story Section =====
    st.subheader("📖 Character Background")
    desc_col, enhance_col = st.columns([0.9, 0.1])
    with desc_col:
        desc_text = st.text_area(
            "Tell us about your character",
            value=st.session_state.get("desc_text", st.session_state.get('preset_data', {}).get("desc", "")),
            height=150,
            help="Include their personality, quirks, mannerisms, and any special characteristics",
            key="desc_text_widget"  # Different key
        )
    with enhance_col:
        if st.button("✨", key="enhance_desc", help="Enhance description with AI"):
            with st.spinner("Enhancing description..."):
                chat_controller = LLMChatController()
                current_text = st.session_state.desc_text_widget
                enhanced_text = await chat_controller.enhance_text(current_text, "character background")
                st.session_state.desc_text = enhanced_text
                st.rerun()

    form_data["basic"]["desc"] = st.session_state.get("desc_text", desc_text)

    # ===== Personality Traits Section =====
    st.subheader("🌟 Personality")
    form_data["personality"]["traits"] = st.multiselect(
        "Key Personality Traits",
        PERSONALITY_TRAITS,
        default=st.session_state.get('preset_data', {}).get("personality", {}).get("traits", []),
        help="Select traits that define your character's personality"
    )

    # ===== Thought Process & Rules Section =====
    st.subheader("🧠 Thought Process & Rules")
    with st.expander("⚙️ Configure Behavior Rules", expanded=False):
        rules_text = st.text_area(
            "Custom Behavior Rules",
            value=DEFAULT_RULES,
            height=200,
            help="Define how your character thinks and responds",
            key="rules_text"
        )
    form_data["system_rules"] = st.session_state.get("rules_text", rules_text)

    # ===== First Introduction Message =====
    st.subheader("👋 First Introduction")
    greeting_col, enhance_col = st.columns([0.9, 0.1])
    with greeting_col:
        greeting_text = st.text_area(
            "How your character introduces itself",
            value=st.session_state.get("greeting_text", st.session_state.get('preset_data', {}).get("greeting", "")),
            height=100,
            help="This will be the first message users see",
            key="greeting_text_widget"
        )
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

    # ===== Tags Section =====
    st.subheader("🏷️ Tags")
    all_tags = TAG_OPTIONS + st.session_state.get('custom_tags', [])
    preset_tags = st.session_state.get('preset_data', {}).get("tags", [])
    valid_preset_tags = [tag for tag in preset_tags if tag in all_tags]
    form_data["tags"] = st.multiselect(
        "Select tags that describe your character",
        all_tags,
        default=valid_preset_tags
    )

    # ===== Advanced Options =====
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

    st.subheader("🔄 Status")
    form_data["status"] = st.radio(
        "Initial Status",
        ["Draft", "Published"],
        index=0,
        horizontal=True,
        help="Draft: Only visible to you | Published: Visible to all users"
    ).lower()

    # Create and Cancel buttons
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("❌ Cancel"):
            if 'preset_data' in st.session_state:
                del st.session_state.preset_data
            st.session_state.page = "my_bots"
            st.rerun()
    with col2:
        if st.button("✨ Create Character", type="primary"):
            await BotManager._handle_form_submission(form_data)

    # Tag addition form
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