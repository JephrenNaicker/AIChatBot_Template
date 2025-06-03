import streamlit as st
from langchain.memory import ConversationBufferWindowMemory
from controllers.chat_controller import LLMChatController
from config import BOTS

class GroupChatManager:
    @staticmethod
    async def show_group_setup():
        """Enhanced group chat setup with search and pagination"""
        st.title("👥 Setup Group Chat")

        # Search functionality
        with st.container():
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

        # Combine and filter bots based on selection
        if bot_source == "Default":
            all_bots = BOTS.copy()
        elif bot_source == "My Bots":
            all_bots = st.session_state.user_bots.copy()
        else:
            all_bots = BOTS + st.session_state.user_bots

        # Apply search filter
        if search_query:
            search_lower = search_query.lower()
            all_bots = [
                bot for bot in all_bots
                if (search_lower in bot['name'].lower() or
                    search_lower in bot['desc'].lower() or
                    any(search_lower in tag.lower() for tag in bot.get('tags', [])))
            ]

        # Pagination
        if 'bot_page' not in st.session_state:
            st.session_state.bot_page = 0

        BOTS_PER_PAGE = 9
        total_pages = max(1, (len(all_bots) + BOTS_PER_PAGE - 1) // BOTS_PER_PAGE)

        # Display pagination controls if needed
        if len(all_bots) > BOTS_PER_PAGE:
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

        # Display bots in a responsive grid with pagination
        st.subheader("Available Bots" + (f" (Filtered)" if search_query else ""))

        if not all_bots:
            st.info("No bots match your search criteria")
        else:
            # Get bots for current page
            start_idx = st.session_state.bot_page * BOTS_PER_PAGE
            end_idx = min(start_idx + BOTS_PER_PAGE, len(all_bots))
            current_page_bots = all_bots[start_idx:end_idx]

            # Display in 3-column grid using the same card style as home page
            cols = st.columns(3)
            for i, bot in enumerate(current_page_bots):
                with cols[i % 3]:
                    with st.container():
                        # Use the same card structure as home page
                        tags_html = ""
                        if bot.get('tags'):
                            tags_html = '<div class="tags-container">' + \
                                        ''.join([f'<span class="bot-tag">{tag}</span>' for tag in bot['tags']]) + \
                                        '</div>'

                        st.markdown(f"""
                        <div class="bot-card">
                            <div class="bot-emoji">{bot['emoji']}</div>
                            <h3>{bot['name']}</h3>
                            <p>{bot['desc']}</p>
                            {tags_html}
                        </div>
                        """, unsafe_allow_html=True)

                        # Select button (only if not already selected and under limit)
                        is_selected = bot['name'] in [b['name'] for b in st.session_state.group_chat['bots']]
                        select_disabled = is_selected or len(st.session_state.group_chat['bots']) >= 3

                        if st.button(
                                "✓ Selected" if is_selected else "➕ Select",
                                key=f"select_{bot['name']}_{i}",
                                disabled=select_disabled,
                                use_container_width=True
                        ):
                            st.session_state.group_chat['bots'].append(bot)
                            st.rerun()

        # Selected bots section - keep this as is since it's different from home page
        if st.session_state.group_chat['bots']:
            with st.container():
                st.subheader("Your Group (Selected Bots)")

                # Display selected bots in a horizontal scrollable container
                selected_cols = st.columns(min(3, len(st.session_state.group_chat['bots'])))
                for i, bot in enumerate(st.session_state.group_chat['bots']):
                    with selected_cols[i % len(selected_cols)]:
                        st.markdown(f"""
                        <div class="bot-card">
                            <div class="bot-emoji">{bot['emoji']}</div>
                            <h3>{bot['name']}</h3>
                        </div>
                        """, unsafe_allow_html=True)

                        if st.button(
                                "❌ Remove",
                                key=f"remove_{bot['name']}",
                                use_container_width=True
                        ):
                            st.session_state.group_chat['bots'].remove(bot)
                            st.rerun()

        # Action buttons
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
                st.session_state.group_chat['active'] = True
                st.session_state.group_chat['histories'] = {}
                st.session_state.group_chat['personality_memories'] = {}

                # Initialize each bot's memory
                for bot in st.session_state.group_chat['bots']:
                    bot_name = bot['name']
                    st.session_state.group_chat['histories'][bot_name] = []
                    st.session_state.group_chat['personality_memories'][bot_name] = (
                        ConversationBufferWindowMemory(
                            k=30,  # Larger memory for personality
                            return_messages=True,
                            memory_key="chat_history"
                        )
                    )

                # Reset shared memory
                st.session_state.group_chat['shared_memory'] = (
                    ConversationBufferWindowMemory(
                        k=20,
                        return_messages=True,
                        memory_key="shared_history"
                    )
                )

                st.session_state.group_chat['responder_idx'] = 0
                st.rerun()

    @staticmethod
    async def show_active_group_chat():
        """Display the active group chat without message echoing"""
        st.title("👥 Group Chat")

        bots = st.session_state.group_chat['bots']

        # Bot selector
        responder_options = [f"{bot['emoji']} {bot['name']}" for bot in bots]
        selected_bot = st.radio(
            "Select which bot should respond next:",
            responder_options,
            index=st.session_state.group_chat.get('responder_idx', 0),
            horizontal=True,
            key="bot_selector"
        )
        st.session_state.group_chat['responder_idx'] = responder_options.index(selected_bot)

        st.divider()

        # Display messages from the shared history
        shared_history = st.session_state.group_chat.get('shared_history', [])
        for msg in shared_history:
            role, content, bot_name = msg
            avatar = next((b['emoji'] for b in bots if b['name'] == bot_name), None) if role == "assistant" else None
            with st.chat_message(role, avatar=avatar):
                if role == "assistant":
                    st.markdown(f"**{bot_name}**: {content}")
                else:
                    st.markdown(content)

        # User input
        if prompt := st.chat_input("Type your message..."):
            # Add user message to shared history once
            st.session_state.group_chat.setdefault('shared_history', []).append(("user", prompt, None))

            # Generate response from selected bot
            responder_bot = bots[st.session_state.group_chat['responder_idx']]
            with st.spinner(f"{responder_bot['name']} is thinking..."):
                GroupChatManager.generate_bot_response(responder_bot, prompt)
                st.rerun()

        if st.button("❌ End Group Chat"):
            st.session_state.group_chat['active'] = False
            st.rerun()

    @staticmethod
    async def generate_bot_to_bot_response():
        """Generate a response from the selected bot to continue the conversation"""
        if not st.session_state.group_chat['bots']:
            return

        # Get the last assistant message in the conversation
        last_bot_message = None
        for bot in st.session_state.group_chat['bots']:
            history = st.session_state.group_chat['histories'].get(bot['name'], [])
            if history and history[-1][0] == "assistant":
                last_bot_message = history[-1][1]
                break

        if not last_bot_message:
            return  # No messages to respond to

        responder_bot = st.session_state.group_chat['bots'][st.session_state.group_chat['responder_idx']]
        with st.spinner(f"{responder_bot['name']} is thinking..."):
             GroupChatManager.generate_bot_response(responder_bot, last_bot_message)
             st.rerun()

    @staticmethod
    async def generate_bot_response(bot, prompt):
        """Generate response without message echoing"""
        bot_name = bot['name']

        # Initialize shared history if not exists
        if 'shared_history' not in st.session_state.group_chat:
            st.session_state.group_chat['shared_history'] = []

        # Initialize personality memory if not exists
        if 'personality_memories' not in st.session_state.group_chat:
            st.session_state.group_chat['personality_memories'] = {}
        if bot_name not in st.session_state.group_chat['personality_memories']:
            st.session_state.group_chat['personality_memories'][bot_name] = ConversationBufferWindowMemory(
                k=30,
                return_messages=True,
                memory_key="chat_history"
            )

        # Get recent context from shared history
        context = "\n".join(
            f"{'User' if role == 'user' else bot}: {content}"
            for role, content, bot in st.session_state.group_chat['shared_history'][-10:]
        )

        # Generate response
        chatbot = LLMChatController()
        response = chatbot.generate_group_chat_response(bot, f"Conversation Context:\n{context}\n\nNew Message: {prompt}",
                                                   "")

        # Clean response
        response = response.strip()
        if response.startswith(f"{bot_name}:"):
            response = response[len(bot_name) + 1:].strip()

        # Update memories
        st.session_state.group_chat['personality_memories'][bot_name].save_context(
            {"input": prompt},
            {"output": response}
        )

        # Add bot response to shared history
        st.session_state.group_chat['shared_history'].append(("assistant", response, bot_name))

    @staticmethod
    async def handle_group_chat_response(prompt):
        """Handle user message and generate bot response"""
        # Add user message to history
        st.session_state.group_chat['history'].append(("user", prompt, None))

        # Get current responder bot
        responder_idx = st.session_state.group_chat['responder_idx']
        responder_bot = st.session_state.group_chat['bots'][responder_idx]

        # Generate response
        with st.spinner(f"{responder_bot['name']} is thinking..."):
            response = GroupChatManager.generate_bot_response(responder_bot, prompt)
            st.session_state.group_chat['history'].append(
                ("assistant", response, responder_bot['name'])
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