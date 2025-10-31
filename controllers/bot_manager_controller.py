import streamlit as st
from config import TAG_OPTIONS, PERSONALITY_TRAITS,DEFAULT_RULES,BOT_PRESETS
from PIL import Image
from components.bot_card import bot_card

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
    def _update_bot_status(bot_name, new_status):
        """Update a bot's status in the user_bots list"""
        for bot in st.session_state.user_bots:
            if bot.name == bot_name:
                bot.status = new_status
                st.toast(f"{bot_name} {'published' if new_status == 'published' else 'unpublished'}!",
                         icon="🚀" if new_status == "published" else "📦")
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
        """Handle form submission and bot creation using Bot object"""
        if not form_data["basic"]["name"]:
            st.error("Please give your bot a name")
        else:
            # Create new Bot object instead of dictionary
            from models.bot import Bot
            new_bot = Bot(
                name=form_data["basic"]["name"],
                emoji=form_data["basic"]["emoji"],
                desc=form_data["basic"]["desc"],
                tags=form_data["tags"],
                status=form_data["status"],
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
                    "avatar_data": None  # Initialize as None
                },
                creator=st.session_state.profile_data.get("username", "anonymous")
            )

            # Handle avatar based on selection
            if (form_data["appearance"].get("avatar_type") == "Upload Image" and
                    form_data["appearance"].get("uploaded_file")):
                uploaded_file = form_data["appearance"]["uploaded_file"]
                file_info = await BotManager._handle_uploaded_file(uploaded_file, form_data["basic"]["name"])

                if file_info:
                    new_bot.appearance["avatar_data"] = file_info
                    new_bot.appearance["avatar_type"] = "uploaded"
                    new_bot.emoji = None
                    st.toast("Avatar image saved successfully!", icon="✅")
                else:
                    new_bot.appearance["avatar_data"] = None
                    new_bot.appearance["avatar_type"] = "emoji"
                    new_bot.emoji = form_data["basic"]["emoji"]
                    st.toast("Failed to save avatar image, using emoji instead", icon="⚠️")
            else:
                # Use emoji as avatar
                new_bot.appearance["avatar_data"] = None
                new_bot.appearance["avatar_type"] = "emoji"
                new_bot.emoji = form_data["basic"]["emoji"]

            # Handle voice options
            if form_data.get("voice", {}).get("enabled", False):
                new_bot.voice = {
                    "enabled": True,
                    "emotion": form_data["voice"]["emotion"]
                }
                if "voice" not in new_bot.tags:
                    new_bot.tags.append("voice")
                st.toast(f"Voice enabled with {form_data['voice']['emotion']} emotion!", icon="🔊")
            else:
                new_bot.voice = {"enabled": False}
                new_bot.tags = [tag for tag in new_bot.tags if tag != "voice"]
                st.toast("Voice not enabled for this character", icon="🔇")

            st.session_state.user_bots.append(new_bot)
            st.success(f"Character '{new_bot.name}' created successfully!")

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
               (status_filter == "Drafts" and bot.status == "draft") or
               (status_filter == "Published" and bot.status == "published")
        ]

    @staticmethod
    def _display_bots_grid(bots):
        """Display bots in a responsive grid layout using the bot_card component"""
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
                    if bot.status == 'draft':
                        if st.button("🚀", key=f"publish_{bot.name}_{i}", help="Publish", use_container_width=True):
                            st.session_state.pending_bot_action = {
                                "type": "update_status",
                                "bot_name": bot.name,
                                "new_status": "published"
                            }
                    else:
                        if st.button("📦", key=f"unpublish_{bot.name}_{i}", help="Unpublish",
                                     use_container_width=True):
                            st.session_state.pending_bot_action = {
                                "type": "update_status",
                                "bot_name": bot.name,
                                "new_status": "draft"
                            }

                # Delete button in a separate row
                if st.button("🗑️ Delete", key=f"delete_{bot.name}_{i}", use_container_width=True):
                    st.session_state.pending_bot_action = {
                        "type": "delete",
                        "bot_name": bot.name
                    }

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