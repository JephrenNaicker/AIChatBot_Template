import streamlit as st
import os
import base64
from datetime import datetime
from config import DEFAULT_RULES, BOT_PRESETS


class BotManager:

    @staticmethod
    def _fix_coroutine_avatars():
        """Fix any bots that have coroutines stored as avatars"""
        for bot in st.session_state.user_bots:
            # We should only have Bot objects here now
            if hasattr(bot, 'appearance'):
                avatar_data = bot.appearance.get("avatar_data")
                if hasattr(avatar_data, '__await__'):
                    bot.appearance["avatar_data"] = None
                    if not bot.emoji:
                        bot.emoji = "🤖"

    @staticmethod
    async def _handle_uploaded_file(uploaded_file, bot_name):
        """Handle avatar file upload using ImageService"""
        if not uploaded_file or not hasattr(st.session_state, 'image_service'):
            return None

        try:
            # Use the image service to handle the upload
            file_info = st.session_state.image_service.save_uploaded_file(uploaded_file, bot_name)
            return file_info
        except Exception as e:
            st.error(f"Error handling uploaded file: {str(e)}")
            return None

    @staticmethod
    def update_bot_status(bot_name, is_public):
        """Update a bot's public status in the user_bots list"""
        for bot in st.session_state.user_bots:
            if bot.name == bot_name:
                bot.is_public = is_public  # CHANGED: status -> is_public
                st.toast(f"{bot_name} {'published' if is_public else 'unpublished'}!",
                         icon="🚀" if is_public else "📦")
                st.rerun()

    @staticmethod
    def _delete_bot(bot_name):
        """Delete a bot from the user_bots list"""
        st.session_state.user_bots = [
            bot for bot in st.session_state.user_bots if bot.name != bot_name
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
    async def _display_preset_options():
        """Display preset options at the top of the page"""

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
    async def _display_voice_options():
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
    async def _handle_form_submission(form_data):
        """Orchestrate the form submission process"""
        if not BotManager._validate_form_data(form_data):
            return

        # Create bot instance
        new_bot = BotManager._create_bot_instance(form_data)

        # Handle avatar setup
        new_bot = await BotManager._setup_bot_avatar(new_bot, form_data)

        # Handle voice configuration
        new_bot = BotManager._setup_bot_voice(new_bot, form_data)

        # Finalize bot creation
        BotManager._finalize_bot_creation(new_bot)

    @staticmethod
    def _validate_form_data(form_data):
        """Validate required form fields"""
        if not form_data["basic"]["name"]:
            st.error("Please give your bot a name")
            return False
        return True

    @staticmethod
    def _create_bot_instance(form_data):
        """Create a new Bot instance from form data"""
        from models.bot import Bot

        return Bot(
            name=form_data["basic"]["name"],
            emoji=form_data["basic"]["emoji"],
            desc=form_data["basic"]["desc"],
            tags=form_data["tags"],
            is_public=form_data["is_public"],
            scenario=form_data.get("scenario", ""),
            personality={
                "tone": form_data["personality"].get("tone", "Friendly"),
                "traits": form_data["personality"]["traits"],
                "greeting": form_data["personality"]["greeting"]
            },
            system_rules=form_data["system_rules"] or DEFAULT_RULES,
            appearance={
                "description": form_data["appearance"]["description"],
                "avatar_type": form_data["appearance"].get("avatar_type", "emoji"),
                "avatar_data": None
            },
            creator=st.session_state.profile_data.get("username", "anonymous")
        )

    @staticmethod
    async def _setup_bot_avatar(bot, form_data):
        """Handle bot avatar configuration (emoji vs uploaded image vs AI-generated)"""
        avatar_type = form_data["appearance"].get("avatar_type")
        uploaded_file = form_data["appearance"].get("uploaded_file")

        if avatar_type == "Upload Image" and uploaded_file:
            return await BotManager._handle_uploaded_avatar(bot, form_data)
        elif avatar_type == "Generate with AI" and st.session_state.get('confirmed_avatar'):
            return await BotManager._handle_ai_generated_avatar(bot, form_data)
        else:
            return BotManager._setup_emoji_avatar(bot, form_data)

    @staticmethod
    async def _handle_uploaded_avatar(bot, form_data):
        """Process uploaded avatar image"""
        uploaded_file = form_data["appearance"]["uploaded_file"]
        file_info = await BotManager._handle_uploaded_file(
            uploaded_file, form_data["basic"]["name"]
        )

        if file_info:
            bot.appearance["avatar_data"] = file_info
            bot.appearance["avatar_type"] = "uploaded"
            bot.emoji = None
            st.toast("Avatar image saved successfully!", icon="✅")
        else:
            # Fallback to emoji if upload fails
            bot = BotManager._setup_emoji_avatar(bot, form_data)
            st.toast("Failed to save avatar image, using emoji instead", icon="⚠️")

        return bot

    @staticmethod
    def _setup_emoji_avatar(bot, form_data):
        """Configure bot to use emoji as avatar"""
        bot.appearance["avatar_data"] = None
        bot.appearance["avatar_type"] = "emoji"
        bot.emoji = form_data["basic"]["emoji"]
        return bot

    @staticmethod
    def _setup_bot_voice(bot, form_data):
        """Configure bot voice settings"""
        voice_config = form_data.get("voice", {})

        if voice_config.get("enabled", False):
            bot.voice = {
                "enabled": True,
                "emotion": voice_config["emotion"]
            }
            # Ensure voice tag is present
            if "voice" not in bot.tags:
                bot.tags.append("voice")
            st.toast(f"Voice enabled with {voice_config['emotion']} emotion!", icon="🔊")
        else:
            bot.voice = {"enabled": False}
            # Remove voice tag if present
            bot.tags = [tag for tag in bot.tags if tag != "voice"]
            st.toast("Voice not enabled for this character", icon="🔇")

        return bot

    @staticmethod
    def _finalize_bot_creation(bot):
        """Complete the bot creation process"""
        st.session_state.user_bots.append(bot)
        st.success(f"Character '{bot.name}' created successfully!")

        # Clean up preset data if it exists
        if 'preset_data' in st.session_state:
            del st.session_state.preset_data

        # Navigate back to bots list
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
        """Filter bots based on public status selection"""
        status_filter = st.radio(
            "Show:",
            ["All", "Drafts", "Published"],
            horizontal=True,
            key="bot_status_filter"
        )

        return [
            bot for bot in st.session_state.user_bots
            if status_filter == "All" or
               (status_filter == "Drafts" and not bot.is_public) or  #not is_public
               (status_filter == "Published" and bot.is_public)  #is_public
        ]

    @staticmethod
    def _display_bots_grid(bots):
        """Display bots in a responsive grid layout using the bot_card component"""
        # Lazy import to avoid circular dependency
        from components.bot_card import bot_card

        cols = st.columns(2)

        for i, bot in enumerate(bots):
            with cols[i % 2]:
                # Use the unified bot_card component with manage mode - PASS BOT OBJECT
                bot_card(bot=bot, mode="manage", key_suffix=str(i))

                # Additional actions specific to my_bots page
                action_cols = st.columns([1, 1, 1])
                with action_cols[0]:
                    if st.button("💬", key=f"chat_{bot.name}_{i}", help="Chat", use_container_width=True):
                        st.session_state.selected_bot = bot.name
                        st.session_state.page = "chat"
                        st.rerun()

                with action_cols[1]:
                    if st.button("✏️", key=f"edit_{bot.name}_{i}", help="Edit", use_container_width=True):
                        st.session_state.editing_bot = bot
                        st.session_state.page = "edit_bot"
                        st.rerun()

                with action_cols[2]:
                    if not bot.is_public:
                        if st.button("🚀", key=f"publish_{bot.name}_{i}", help="Publish", use_container_width=True):
                            st.session_state.pending_bot_action = {
                                "type": "update_status",
                                "bot_name": bot.name,
                                "is_public": True  # CHANGED: new_status -> is_public
                            }
                    else:
                        if st.button("📦", key=f"unpublish_{bot.name}_{i}", help="Unpublish",
                                     use_container_width=True):
                            st.session_state.pending_bot_action = {
                                "type": "update_status",
                                "bot_name": bot.name,
                                "is_public": False  # CHANGED: new_status -> is_public
                            }

                # Delete button in a separate row
                if st.button("🗑️ Delete", key=f"delete_{bot.name}_{i}", use_container_width=True):
                    st.session_state.pending_bot_action = {
                        "type": "delete",
                        "bot_name": bot.name
                    }

    @staticmethod
    async def _handle_ai_generated_avatar(bot, form_data):
        """Process AI-generated avatar and save to file system"""
        if not st.session_state.get('confirmed_avatar'):
            return BotManager._setup_emoji_avatar(bot, form_data)

        try:
            # Extract base64 data from the confirmed avatar
            base64_data = st.session_state.confirmed_avatar
            if base64_data.startswith('data:image/png;base64,'):
                base64_data = base64_data.replace('data:image/png;base64,', '')

            # Decode base64 to image bytes
            image_bytes = base64.b64decode(base64_data)

            # Create avatars directory if it doesn't exist
            avatars_dir = "images/avatars"
            os.makedirs(avatars_dir, exist_ok=True)

            # Generate filename (sanitize bot name and add timestamp)
            sanitized_name = "".join(c for c in bot.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            sanitized_name = sanitized_name.replace(' ', '_')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{sanitized_name}_{timestamp}.png"
            filepath = os.path.join(avatars_dir, filename)

            # Save the image
            with open(filepath, "wb") as f:
                f.write(image_bytes)

            # Store file info in bot appearance
            bot.appearance["avatar_data"] = {
                "filename": filename,
                "filepath": filepath,
                "type": "ai_generated"
            }
            bot.appearance["avatar_type"] = "ai_generated"
            bot.emoji = None

            st.toast("AI-generated avatar saved successfully!", icon="✅")
            return bot

        except Exception as e:
            st.error(f"Error saving AI-generated avatar: {str(e)}")
            # Fallback to emoji
            return BotManager._setup_emoji_avatar(bot, form_data)

    @staticmethod
    def fix_coroutine_avatars():
        """Public method to fix coroutine avatars"""
        BotManager._fix_coroutine_avatars()

    @staticmethod
    def show_empty_state():
        """Public method to show empty state"""
        BotManager._show_empty_state()

    @staticmethod
    def filter_bots_by_status():
        """Public method to filter bots by status"""
        return BotManager._filter_bots_by_status()

    @staticmethod
    def display_bots_grid(bots):
        """Public method to display bots grid"""
        BotManager._display_bots_grid(bots)
