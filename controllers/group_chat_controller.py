import streamlit as st
from langchain.memory import ConversationBufferWindowMemory
from controllers.chat_controller import LLMChatController
from config import get_default_bots


class GroupChatUIBuilder:
    """Handles UI component building for group chat"""

    @staticmethod
    def build_search_interface():
        """Build search and filter interface"""
        st.subheader("Find Bots for Your Group Chat")
        search_col, filter_col = st.columns([3, 1])

        with search_col:
            search_query = st.text_input(
                "🔍 Search bots...",
                placeholder="Type to filter by name, description or tags",
                key="group_chat_search"
            )

        with filter_col:
            bot_source = st.radio(
                "Show:",
                ["All", "Default", "My Bots"],
                horizontal=True,
                key="bot_source_filter"
            )

        return search_query, bot_source

    @staticmethod
    def build_bot_card(bot, index, is_selected=False, select_disabled=False):
        """Build individual bot card UI"""
        tags_html = ""
        if bot.tags:
            tags_html = '<div class="tags-container">' + \
                        ''.join([f'<span class="bot-tag">{tag}</span>' for tag in bot.tags]) + \
                        '</div>'

        st.markdown(f"""
        <div class="bot-card">
            <div class="bot-emoji">{bot.emoji}</div>
            <h3>{bot.name}</h3>
            <p>{bot.desc}</p>
            {tags_html}
        </div>
        """, unsafe_allow_html=True)

        # Select button
        button_text = "✓ Selected" if is_selected else "➕ Select"
        if st.button(
                button_text,
                key=f"select_{bot.name}_{index}",
                disabled=select_disabled,
                use_container_width=True
        ):
            return True
        return False

    @staticmethod
    def build_selected_bots_section():
        """Build UI for selected bots section"""
        if not st.session_state.group_chat['bots']:
            return

        st.subheader("Your Group (Selected Bots)")
        selected_cols = st.columns(min(3, len(st.session_state.group_chat['bots'])))

        for i, bot in enumerate(st.session_state.group_chat['bots']):
            with selected_cols[i % len(selected_cols)]:
                st.markdown(f"""
                <div class="bot-card">
                    <div class="bot-emoji">{bot.emoji}</div>
                    <h3>{bot.name}</h3>
                </div>
                """, unsafe_allow_html=True)

                if st.button(
                        "❌ Remove",
                        key=f"remove_{bot.name}",
                        use_container_width=True
                ):
                    st.session_state.group_chat['bots'].remove(bot)
                    st.rerun()

    @staticmethod
    def build_action_buttons():
        """Build action buttons at the bottom"""
        action_cols = st.columns([1, 1, 2])

        with action_cols[0]:
            if st.button("🔙 Back to Home"):
                st.session_state.page = "home"
                st.rerun()

        with action_cols[1]:
            if st.button("🔄 Reset Selection"):
                st.session_state.group_chat['bots'] = []
                st.rerun()

        with action_cols[2]:
            if st.button("🚀 Start Group Chat", type="primary"):
                return True
        return False


class BotFilterService:
    """Handles bot filtering and search logic"""

    @staticmethod
    def get_filtered_bots(bot_source, search_query=None):
        """Get bots based on source filter and search query"""
        # Get bots based on source
        if bot_source == "Default":
            all_bots = get_default_bots().copy()
        elif bot_source == "My Bots":
            all_bots = st.session_state.user_bots.copy()
        else:
            all_bots = get_default_bots() + st.session_state.user_bots

        # Apply search filter
        if search_query:
            search_lower = search_query.lower()
            all_bots = [
                bot for bot in all_bots
                if (search_lower in bot.name.lower() or
                    search_lower in bot.desc.lower() or
                    any(search_lower in tag.lower() for tag in bot.tags))
            ]

        return all_bots

    @staticmethod
    def get_current_page_bots(all_bots, page):
        """Get bots for current page"""
        bots_per_page = PaginationService.BOTS_PER_PAGE
        start_idx = page * bots_per_page
        end_idx = min(start_idx + bots_per_page, len(all_bots))
        return all_bots[start_idx:end_idx]


class PaginationService:
    """Handles pagination logic"""

    BOTS_PER_PAGE = 9  # Constant for consistency

    @staticmethod
    def initialize_pagination():
        """Initialize pagination state"""
        if 'bot_page' not in st.session_state:
            st.session_state.bot_page = 0

    @staticmethod
    def build_pagination_controls(total_bots):
        """Build pagination UI controls"""
        if total_bots <= PaginationService.BOTS_PER_PAGE:
            return

        total_pages = max(1, (total_bots + PaginationService.BOTS_PER_PAGE - 1) // PaginationService.BOTS_PER_PAGE)

        page_cols = st.columns([1, 2, 1])
        with page_cols[1]:
            st.caption(f"Page {st.session_state.bot_page + 1} of {total_pages}")
            prev_col, page_display, next_col = st.columns([1, 2, 1])

            with prev_col:
                if st.button("◀ Previous", disabled=st.session_state.bot_page == 0):
                    st.session_state.bot_page -= 1
                    st.rerun()

            with next_col:
                if st.button("Next ▶", disabled=st.session_state.bot_page == total_pages - 1):
                    st.session_state.bot_page += 1
                    st.rerun()


class MemoryInitializer:
    """Handles memory initialization for group chat"""

    @staticmethod
    def initialize_group_memories():
        """Initialize all required memories for group chat"""
        st.session_state.group_chat['active'] = True
        st.session_state.group_chat['histories'] = {}
        st.session_state.group_chat['personality_memories'] = {}

        # Initialize each bot's memory
        for bot in st.session_state.group_chat['bots']:
            bot_name = bot.name
            st.session_state.group_chat['histories'][bot_name] = []
            st.session_state.group_chat['personality_memories'][bot_name] = (
                ConversationBufferWindowMemory(
                    k=30,
                    return_messages=True,
                    memory_key="chat_history"
                )
            )

        # Initialize shared memory
        st.session_state.group_chat['shared_memory'] = (
            ConversationBufferWindowMemory(
                k=20,
                return_messages=True,
                memory_key="shared_history"
            )
        )

        st.session_state.group_chat['responder_idx'] = 0


class GroupChatManager:
    """Main controller class coordinating all group chat functionality"""

    def __init__(self):
        self.ui_builder = GroupChatUIBuilder()
        self.bot_filter = BotFilterService()
        self.pagination = PaginationService()
        self.memory_initializer = MemoryInitializer()

    async def show_group_setup(self):
        """Enhanced group chat setup with search and pagination"""
        st.title("👥 Setup Group Chat")

        # Build search interface
        search_query, bot_source = self.ui_builder.build_search_interface()

        # Get filtered bots
        all_bots = self.bot_filter.get_filtered_bots(bot_source, search_query)

        # Initialize and build pagination
        self.pagination.initialize_pagination()
        self.pagination.build_pagination_controls(len(all_bots))

        # Display available bots
        self._display_available_bots(all_bots, search_query)

        # Display selected bots
        self.ui_builder.build_selected_bots_section()

        # Handle action buttons
        if self.ui_builder.build_action_buttons():
            self.memory_initializer.initialize_group_memories()
            st.rerun()

    def _display_available_bots(self, all_bots, search_query):
        """Display available bots in a grid"""
        st.subheader("Available Bots" + (f" (Filtered)" if search_query else ""))

        if not all_bots:
            st.info("No bots match your search criteria")
            return

        # Get current page bots
        current_page_bots = self.bot_filter.get_current_page_bots(
            all_bots, st.session_state.bot_page
        )

        # Display in 3-column grid
        cols = st.columns(3)
        for i, bot in enumerate(current_page_bots):
            with cols[i % 3]:
                with st.container():
                    is_selected = bot.name in [b.name for b in st.session_state.group_chat['bots']]
                    select_disabled = is_selected or len(st.session_state.group_chat['bots']) >= 3

                    if self.ui_builder.build_bot_card(bot, i, is_selected, select_disabled):
                        st.session_state.group_chat['bots'].append(bot)
                        st.rerun()

    async def show_active_group_chat(self):
        """Display the active group chat without message echoing"""
        st.title("👥 Group Chat")

        bots = st.session_state.group_chat['bots']

        # Bot selector
        self._build_bot_selector(bots)

        st.divider()

        # Display conversation history
        self._display_conversation_history(bots)

        # Handle user input
        await self._handle_user_input(bots)

        # End chat button
        if st.button("❌ End Group Chat"):
            st.session_state.group_chat['active'] = False
            st.rerun()

    @staticmethod
    def _build_bot_selector(bots):
        """Build bot selection interface"""
        responder_options = [f"{bot.emoji} {bot.name}" for bot in bots]
        selected_bot = st.radio(
            "Select which bot should respond next:",
            responder_options,
            index=st.session_state.group_chat.get('responder_idx', 0),
            horizontal=True,
            key="bot_selector"
        )
        st.session_state.group_chat['responder_idx'] = responder_options.index(selected_bot)

    @staticmethod
    def _display_conversation_history(bots):
        """Display the conversation history"""
        shared_history = st.session_state.group_chat.get('shared_history', [])
        for msg in shared_history:
            role, content, bot_name = msg
            avatar = next((b.emoji for b in bots if b.name == bot_name), None) if role == "assistant" else None
            with st.chat_message(role, avatar=avatar):
                if role == "assistant":
                    st.markdown(f"**{bot_name}**: {content}")
                else:
                    st.markdown(content)

    async def _handle_user_input(self, bots):
        """Handle user input and generate bot response"""
        if prompt := st.chat_input("Type your message..."):
            # Add user message to shared history once
            st.session_state.group_chat.setdefault('shared_history', []).append(("user", prompt, None))

            # Generate response from selected bot
            responder_bot = bots[st.session_state.group_chat['responder_idx']]
            with st.spinner(f"{responder_bot.name} is thinking..."):
                await self.generate_bot_response(responder_bot, prompt)
                st.rerun()

    async def generate_bot_to_bot_response(self):
        """Generate a response from the selected bot to continue the conversation"""
        if not st.session_state.group_chat['bots']:
            return

        last_bot_message = self._get_last_bot_message()
        if not last_bot_message:
            return

        responder_bot = st.session_state.group_chat['bots'][st.session_state.group_chat['responder_idx']]
        with st.spinner(f"{responder_bot.name} is thinking..."):
            await self.generate_bot_response(responder_bot, last_bot_message)
            st.rerun()

    @staticmethod
    def _get_last_bot_message():
        """Get the last assistant message from any bot's history"""
        for bot in st.session_state.group_chat['bots']:
            history = st.session_state.group_chat['histories'].get(bot.name, [])
            if history and history[-1][0] == "assistant":
                return history[-1][1]
        return None

    async def generate_bot_response(self, bot, prompt):
        """Generate response without message echoing"""
        bot_name = bot.name

        # Initialize shared history if not exists
        if 'shared_history' not in st.session_state.group_chat:
            st.session_state.group_chat['shared_history'] = []

        # Initialize personality memory if not exists
        self._ensure_personality_memory_exists(bot_name)

        # Get recent context from shared history
        context = self._build_conversation_context()

        # Generate response
        chatbot = LLMChatController()
        response = await chatbot.generate_group_chat_response(
            bot,
            f"Conversation Context:\n{context}\n\nNew Message: {prompt}",
            ""
        )

        # Clean and process response
        response = self._clean_bot_response(response, bot_name)

        # Update memories and history
        self._update_bot_memory(bot_name, prompt, response)
        st.session_state.group_chat['shared_history'].append(("assistant", response, bot_name))

    @staticmethod
    def _ensure_personality_memory_exists(bot_name):
        """Ensure personality memory exists for bot"""
        if 'personality_memories' not in st.session_state.group_chat:
            st.session_state.group_chat['personality_memories'] = {}
        if bot_name not in st.session_state.group_chat['personality_memories']:
            st.session_state.group_chat['personality_memories'][bot_name] = ConversationBufferWindowMemory(
                k=30,
                return_messages=True,
                memory_key="chat_history"
            )

    @staticmethod
    def _build_conversation_context():
        """Build conversation context from shared history"""
        return "\n".join(
            f"{'User' if role == 'user' else bot}: {content}"
            for role, content, bot in st.session_state.group_chat['shared_history'][-10:]
        )

    @staticmethod
    def _clean_bot_response(response, bot_name):
        """Clean and format bot response"""
        response = response.strip()
        if response.startswith(f"{bot_name}:"):
            response = response[len(bot_name) + 1:].strip()
        return response

    @staticmethod
    def _update_bot_memory(bot_name, prompt, response):
        """Update bot's personality memory"""
        st.session_state.group_chat['personality_memories'][bot_name].save_context(
            {"input": prompt},
            {"output": response}
        )

    async def handle_group_chat_response(self, prompt):
        """Handle user message and generate bot response"""
        # Add user message to history
        st.session_state.group_chat['history'].append(("user", prompt, None))

        # Get current responder bot
        responder_idx = st.session_state.group_chat['responder_idx']
        responder_bot = st.session_state.group_chat['bots'][responder_idx]

        # Generate response
        with st.spinner(f"{responder_bot.name} is thinking..."):
            response = await self.generate_bot_response(responder_bot, prompt)
            st.session_state.group_chat['history'].append(
                ("assistant", response, responder_bot.name)
            )

        # Move to next bot (round-robin)
        st.session_state.group_chat['responder_idx'] = (
                (responder_idx + 1) % len(st.session_state.group_chat['bots'])
        )
        st.rerun()

    @staticmethod
    async def end_group_chat():
        """Clean up group chat session"""
        st.session_state.group_chat['active'] = False
        st.rerun()