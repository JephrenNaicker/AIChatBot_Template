import streamlit as st
from config import TAG_OPTIONS, PERSONALITY_TRAITS,DEFAULT_RULES

class BotManager:
    @staticmethod
    def _handle_uploaded_file(uploaded_file, bot_name):
        """Handle avatar file upload"""
        # In a real app, you would save this file and return the path
        return {
            "filename": uploaded_file.name,
            "content_type": uploaded_file.type,
            "size": uploaded_file.size
        }

    @staticmethod
    def _update_bot_status(bot_name, new_status):
        """Update a bot's status in the user_bots list"""
        for i, b in enumerate(st.session_state.user_bots):
            if b["name"] == bot_name:
                st.session_state.user_bots[i]["status"] = new_status
                st.toast(f"{bot_name} {'published' if new_status == 'published' else 'unpublished'}!",
                         icon="🚀" if new_status == "published" else "📦")
                st.rerun()

    @staticmethod
    def _delete_bot(bot_name):
        """Delete a bot from the user_bots list"""
        st.session_state.user_bots = [
            b for b in st.session_state.user_bots if b["name"] != bot_name
        ]
        st.rerun()

    @staticmethod
    def _init_bot_creation_session():
        """Initialize session state for bot creation"""
        if 'custom_tags' not in st.session_state:
            st.session_state.custom_tags = []

            # Initialize status tracking
        if 'bot_status' not in st.session_state:
            st.session_state.bot_status = "draft"  # Default to draft

        # Initialize with preset data if available
        if 'preset_data' in st.session_state:
            st.session_state.preset_applied = "Generated Concept"
            st.toast("Generated concept loaded!", icon="✨")

    @staticmethod
    def _display_preset_options():
        """Display preset options at the top of the page"""
        BOT_PRESETS = {
            "Dating Sim": {
                "tone": "Flirtatious",
                "traits": ["Charming", "Empathetic", "Romantic"],
                "greeting": "Hello there, darling~ What brings you my way today? *winks*"
            },
            "Game Guide": {
                "tone": "Helpful",
                "traits": ["Knowledgeable", "Patient", "Encouraging"],
                "greeting": "Welcome traveler! How can I assist you on your quest today?"
            },
            "Mystery Solver": {
                "tone": "Cryptic",
                "traits": ["Perceptive", "Logical", "Observant"],
                "greeting": "Hmm... interesting you should appear now. What mystery shall we unravel?"
            },
            "Sci-Fi Companion": {
                "tone": "Futuristic",
                "traits": ["Analytical", "Curious", "Adventurous"],
                "greeting": "Greetings, organic lifeform. I am ready to explore the cosmos with you."
            }
        }

        st.subheader("🎭 Character Presets")
        preset_cols = st.columns(4)
        for i, (preset_name, preset_data) in enumerate(BOT_PRESETS.items()):
            with preset_cols[i % 4]:
                if st.button(preset_name,
                             help=f"Apply {preset_name} preset",
                             use_container_width=True):
                    st.session_state.preset_applied = preset_name
                    st.session_state.preset_data = preset_data
                    st.toast(f"{preset_name} preset applied!", icon="✨")
                    st.rerun()

        if st.button("🎨 Generate AI Image (Coming Soon)",
                     help="Will generate an image based on appearance description",
                     disabled=True):
            st.toast("This feature will generate an AI image based on your description!", icon="🎨")

    @staticmethod
    def _display_voice_options():
        """Display voice/emotion selection options"""
        voice_data = {"enabled": False}  # Default return value

        # Check if voice service is available
        if not hasattr(st.session_state, 'voice_service') or st.session_state.voice_service is None:
            return voice_data

        voice_service = st.session_state.voice_service

        # Simple toggle and dropdown
        enable_voice = st.toggle(
            "Enable Voice for this bot",
            value=False,
            help="Add voice synthesis to your bot",
            key="voice_toggle"
        )

        if enable_voice:
            try:
                emotions = voice_service.get_available_emotions()
                if not emotions:
                    st.warning("No voice emotions available")
                    return voice_data

                emotion = st.selectbox(
                    "Voice Emotion",
                    options=emotions,
                    index=emotions.index('neutral') if 'neutral' in emotions else 0,
                    help="Select the emotional tone for your bot's voice",
                    key="voice_emotion"
                )

                voice_data = {
                    "enabled": True,
                    "emotion": emotion
                }
            except Exception as e:
                st.error(f"Error loading voice options: {str(e)}")
                return {"enabled": False}

        return voice_data

    @staticmethod
    def _display_creation_form():
        """Display the main bot creation form and return collected data"""
        form_data = {
            "basic": {},
            "appearance": {},
            "personality": {},
            "tags": [],
            "voice": {"enabled": False, "emotion": None}  # Initialize with proper structure
        }

        # Get default values from preset if available
        preset = st.session_state.get('preset_data', {})

        # ===== Character Details Section =====
        st.subheader("🧍 Character Details")
        col1, col2 = st.columns([1, 3])
        with col1:
            form_data["basic"]["emoji"] = st.text_input(
                "Emoji",
                value=preset.get("emoji", "🤖"),
                help="Choose an emoji to represent your bot (1-2 characters)"
            )
        with col2:
            form_data["basic"]["name"] = st.text_input(
                "Name",
                value=preset.get("name", ""),
                help="Give your bot a unique name (max 30 characters)"
            )

        # Simplified Appearance section
        st.subheader("👀 Physical Appearance")
        form_data["appearance"]["description"] = st.text_area(
            "Describe your character's looks",
            value=preset.get("appearance", ""),
            height=100,
            help="Include physical features, clothing, and distinctive attributes"
        )

        # Avatar selection
        st.write("**Avatar:**")
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

        # ===== Back Story Section =====
        st.subheader("📖 Character Background")
        form_data["basic"]["desc"] = st.text_area(
            "Tell us about your character",
            value=preset.get("desc", ""),
            height=150,
            help="Include their personality, quirks, mannerisms, and any special characteristics"
        )

        # ===== Personality Traits Section =====
        st.subheader("🌟 Personality")

        # Get traits from preset if available, otherwise empty list
        default_traits = preset.get("personality", {}).get("traits", [])

        form_data["personality"]["traits"] = st.multiselect(
            "Key Personality Traits",
            PERSONALITY_TRAITS,
            default=default_traits,  # This ensures traits are passed from generated concept
            help="Select traits that define your character's personality"
        )

        # ===== Thought Process & Rules Section =====

        st.subheader("🧠 Thought Process & Rules")

        with st.expander("⚙️ Configure Behavior Rules", expanded=False):
            # Help text with examples
            st.markdown("""
            **Format Guide:**
            - `(Thoughts appear in italics format)`
            - `"Spoken dialogue in quotes"`
            """)

            # Editable rules area with smart default
            rules = st.text_area(
                "Custom Behavior Rules",
                value=DEFAULT_RULES,
                height=200,
                help="Define how your character thinks and responds",
                key="bot_rules"
            )

            # Live preview
            st.caption("Example Behavior:")
            st.code(f"""User: Hello!
        Bot: *Noticing the friendly tone* "Well hello there!" 
        """, language="markdown")

        # Store in form data
        form_data["system_rules"] = rules

        # ===== First Introduction Message =====
        st.subheader("👋 First Introduction")
        form_data["personality"]["greeting"] = st.text_area(
            "How your character introduces itself",
            value=preset.get("greeting", "Hello! I'm excited to chat with you!"),
            height=100,
            help="This will be the first message users see"
        )

        # ===== Tags Section =====
        st.subheader("🏷️ Tags")
        all_tags = TAG_OPTIONS + st.session_state.get('custom_tags', [])

        # Filter preset tags to only include valid options
        preset_tags = preset.get("tags", [])
        valid_preset_tags = [tag for tag in preset_tags if tag in all_tags]

        form_data["tags"] = st.multiselect(
            "Select tags that describe your character",
            all_tags,
            default=valid_preset_tags
        )

        # ===== Advanced Options =====
        with st.expander("⚙️ Voice Options"):
            # Voice options section
            if hasattr(st.session_state, 'voice_service') and st.session_state.voice_service is not None:
                # Use a checkbox that's more visible than toggle
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
                            # Add visual feedback about the selected emotion
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
        status = st.radio(
            "Initial Status",
            ["Draft", "Published"],
            index=0,  # Default to Draft
            horizontal=True,
            help="Draft: Only visible to you | Published: Visible to all users"
        )
        form_data["status"] = status.lower()

        return form_data

    @staticmethod
    def _handle_form_submission(form_data):
        """Handle form submission and bot creation"""
        if not form_data["basic"]["name"]:
            st.error("Please give your bot a name")
        else:
            new_bot = {
                "name": form_data["basic"]["name"],
                "emoji": form_data["basic"]["emoji"],
                "desc": form_data["basic"]["desc"],
                "tags": form_data["tags"],
                "status": form_data["status"],
                "personality": {
                    "tone": form_data["personality"].get("tone", "Friendly"),
                    "traits": form_data["personality"]["traits"],
                    "greeting": form_data["personality"]["greeting"]
                },
                "system_rules": form_data["system_rules"] or DEFAULT_RULES,
                "appearance": {
                    "description": form_data["appearance"]["description"],
                },
                "custom": True,
                "creator": st.session_state.profile_data.get("username", "anonymous")
            }

            # Handle voice options - with debug output
            if form_data.get("voice", {}).get("enabled", False):
                new_bot["voice"] = {
                    "enabled": True,  # Explicitly set enabled
                    "emotion": form_data["voice"]["emotion"]
                }
                # Add voice tag if not already present
                if "voice" not in new_bot["tags"]:
                    new_bot["tags"].append("voice")
                st.toast(f"Voice enabled with {form_data['voice']['emotion']} emotion!", icon="🔊")
            else:
                # Ensure voice is disabled if not enabled
                new_bot["voice"] = {"enabled": False}
                # Remove voice tag if present
                new_bot["tags"] = [tag for tag in new_bot["tags"] if tag != "voice"]
                st.toast("Voice not enabled for this character", icon="🔇")

            # Debug output
            st.write("Final bot voice settings:", new_bot.get("voice", "NO VOICE SETTINGS"))
            # Handle uploaded file if exists
            if form_data["appearance"].get("uploaded_file"):
                new_bot["appearance"]["avatar"] = BotManager._handle_uploaded_file(
                    form_data["appearance"]["uploaded_file"],
                    form_data["basic"]["name"]
                )

            st.session_state.user_bots.append(new_bot)
            st.success(f"Character '{new_bot['name']}' created successfully!")

            # Clear preset data after successful creation
            if 'preset_data' in st.session_state:
                del st.session_state.preset_data

            st.session_state.page = "my_bots"
            st.rerun()

    @staticmethod
    def _show_empty_state():
        """Show empty state when user has no bots"""
        st.info("You haven't created any bots yet.")
        if st.button("Create Your First Bot"):
            st.session_state.page = "bot_setup"
            st.rerun()

    @staticmethod
    def _filter_bots_by_status():
        """Filter bots based on status selection"""
        status_filter = st.radio(
            "Show:",
            ["All", "Drafts", "Published"],
            horizontal=True,
            key="bot_status_filter"
        )

        return [
            bot for bot in st.session_state.user_bots
            if status_filter == "All" or
               (status_filter == "Drafts" and bot.get("status", "draft") == "draft") or
               (status_filter == "Published" and bot.get("status", "draft") == "published")
        ]

    @staticmethod
    def _display_bots_grid(bots):
        """Display bots in a responsive grid layout"""
        cols = st.columns(2)

        for i, bot in enumerate(bots):
            with cols[i % 2]:
                BotManager._display_bot_card(bot, i)

    @staticmethod
    def _display_bot_card(bot, index):
        """Display a bot card with perfect button layout"""
        with st.container():
            unique_key_suffix = f"{bot['name']}_{index}"

            # Main card container with custom styling
            with st.container(border=True):
                st.markdown(f"""
                <style>
                    .bot-card {{
                        padding: 1.5rem;
                        min-height: 280px;
                        width: 100%;
                        display: flex;
                        flex-direction: column;
                    }}
                    .bot-header {{
                        display: flex;
                        align-items: center;
                        gap: 1rem;
                        margin-bottom: 1rem;
                    }}
                    .bot-emoji {{
                        font-size: 2.5rem;
                        flex-shrink: 0;
                    }}
                    .bot-name {{
                        font-size: 1.3rem;
                        font-weight: bold;
                    }}
                    .bot-desc {{
                        color: #666;
                        font-size: 0.95rem;
                        line-height: 1.4;
                        margin-bottom: 1rem;
                    }}
                    .tags-container {{
                        display: flex;
                        flex-wrap: wrap;
                        gap: 0.5rem;
                        margin-bottom: 1.5rem;
                    }}
                    .bot-tag {{
                        background: #2a3b4d;
                        color: #7fbbde;
                        padding: 0.3rem 0.8rem;
                        border-radius: 1rem;
                        font-size: 0.85rem;
                        white-space: nowrap;
                        overflow: hidden;
                        text-overflow: ellipsis;
                        max-width: 100px;
                    }}
                    /* New button row styling */
                    .btn-row {{
                        display: flex;
                        gap: 0.8rem;
                        margin-top: auto;
                    }}
                    .btn-row button {{
                        min-width: 80px;
                        padding: 0.4rem 0.8rem;
                        font-size: 0.9rem;
                    }}
                    .btn-popover {{
                        margin-left: auto;
                    }}
                </style>
                <div class="bot-card">
                    <div class="bot-header">
                        <div class="bot-emoji">{bot['emoji']}</div>
                        <div>
                            <div class="bot-name">{bot['name']}</div>
                            <div style="color: {'#f39c12' if bot.get('status', 'draft') == 'draft' else '#2ecc71'}; 
                                          font-weight: bold; font-size: 0.85rem;">
                                {bot.get('status', 'draft').upper()}
                            </div>
                        </div>
                    </div>
                    <div class="bot-desc">{bot['desc']}</div>
                """, unsafe_allow_html=True)

                # Tags (using your preferred style)
                if bot.get('tags'):
                    st.markdown('<div class="tags-container">', unsafe_allow_html=True)
                    for tag in bot['tags']:
                        st.markdown(f'<div class="bot-tag" title="{tag}">{tag}</div>',
                                    unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                # New improved button row
                st.markdown('<div class="btn-row">', unsafe_allow_html=True)

                # Edit Button
                if st.button("✏️ Edit", key=f"edit_{unique_key_suffix}"):
                    st.session_state.editing_bot = bot
                    st.session_state.page = "edit_bot"
                    st.rerun()

                # Chat Button
                if st.button("💬 Chat", key=f"chat_{unique_key_suffix}"):
                    st.session_state.selected_bot = bot["name"]
                    st.session_state.page = "chat"
                    st.rerun()

                # Publish/Unpublish Button
                if bot.get('status', 'draft') == 'draft':
                    if st.button("🚀 Publish", key=f"publish_{unique_key_suffix}"):
                        BotManager._update_bot_status(bot["name"], "published")
                else:
                    if st.button("📦 Unpub", key=f"unpublish_{unique_key_suffix}"):
                        BotManager._update_bot_status(bot["name"], "draft")

                # Gear icon positioned at the end
                st.markdown('<div class="btn-popover">', unsafe_allow_html=True)
                with st.popover("⚙️"):
                    if st.button("🗑️ Delete", key=f"delete_{unique_key_suffix}"):
                        BotManager._delete_bot(bot["name"])
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True)  # Close btn-row
                st.markdown('</div>', unsafe_allow_html=True)  # Close bot-card

    @staticmethod
    def _display_status_badge(bot):
        """Display the status badge for a bot"""
        status = bot.get("status", "draft")
        status_color = "orange" if status == "draft" else "green"
        st.markdown(
            f"<div style='text-align: right; margin-bottom: -20px;'>"
            f"<span style='color: {status_color}; font-weight: bold;'>"
            f"{status.upper()}</span></div>",
            unsafe_allow_html=True
        )

    @staticmethod
    def _display_bot_header(bot):
        """Display the bot's emoji and name"""
        col1, col2, col3 = st.columns([1, 4, 1])
        with col2:
            st.markdown(f"<div style='text-align: center; font-size: 2rem;'>{bot['emoji']}</div>",
                        unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align: center;'>{bot['name']}</h3>",
                        unsafe_allow_html=True)

    @staticmethod
    def _display_bot_description(bot):
        """Display the bot's description"""
        st.caption(bot['desc'])

    @staticmethod
    def _display_bot_tags(bot):
        """Display the bot's tags if they exist"""
        if bot.get('tags'):
            for tag in bot['tags']:
                st.markdown(f'<div class="bot-tag" title="{tag}">{tag}</div>',
                            unsafe_allow_html=True)

    @staticmethod
    def _display_bot_actions(bot, unique_key_suffix):
        """Display action buttons for a bot"""
        status = bot.get("status", "draft")

        # Main action buttons
        st.markdown('<div class="main-actions">', unsafe_allow_html=True)

        if st.button(f"✏️ Edit", key=f"edit_{unique_key_suffix}"):
            st.session_state.editing_bot = bot
            st.session_state.page = "edit_bot"
            st.rerun()

        if st.button(f"💬 Chat", key=f"chat_{unique_key_suffix}", type="secondary"):
            st.session_state.selected_bot = bot["name"]
            st.session_state.page = "chat"
            st.rerun()

        if status == "draft":
            if st.button("🚀 Publish", key=f"publish_{unique_key_suffix}"):
                BotManager._update_bot_status(bot["name"], "published")
        else:
            if st.button("📦 Unpublish", key=f"unpublish_{unique_key_suffix}"):
                BotManager._update_bot_status(bot["name"], "draft")

        st.markdown('</div>', unsafe_allow_html=True)

        # More options dropdown
        with st.popover("⚙️", help="More options"):
            if st.button("🗑️ Delete Bot", key=f"delete_{unique_key_suffix}"):
                BotManager._delete_bot(bot["name"])