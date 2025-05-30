import hashlib
import streamlit as st
from functools import lru_cache
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnableSequence
from langchain_core.exceptions import OutputParserException, LangChainException
from langchain_community.llms import Ollama
from config import BOTS,DEFAULT_RULES

class LLMChatController:
    def __init__(self):
        self.llm = Ollama(model="llama3:latest")
        self._init_session_state()
        self._init_dialog_chain()
        self._init_memory_buffer()

    @lru_cache(maxsize=100)
    def _init_memory_buffer(self):
        """Initialize enhanced conversation memory"""
        if "memory" not in st.session_state:
            st.session_state.memory = ConversationBufferWindowMemory(
                k=50,  # Remember last 50 exchanges
                return_messages=True,
                memory_key="chat_history"
            )

    def _init_session_state(self):
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        if "greeting_sent" not in st.session_state:
            st.session_state.greeting_sent = False
        if "performance_metrics" not in st.session_state:  # New
            st.session_state.performance_metrics = {
                "cache_hits": 0,
                "llm_errors": 0
            }

    def _init_dialog_chain(self):
        bot_name = st.session_state.get('selected_bot', '')
        current_bot = next((b for b in BOTS + st.session_state.user_bots if b["name"] == bot_name), None)

        if current_bot:
            personality = current_bot.get("personality", {})
            system_rules = current_bot.get("system_rules", {})
            # Unified template that works for both single and group chats
            prompt_template = f"""You are {bot_name} ({current_bot['emoji']}), {current_bot['desc']}.
                
                [CHARACTER DIRECTIVES]
                {system_rules}
    			[Your Personality Rules]
    			- Always respond as {bot_name}
    			- Traits: {', '.join(personality.get('traits', []))}
    			- Speech: {personality.get('speech_pattern', 'neutral')}
    			- Quirks: {', '.join(personality.get('quirks', []))}
    		     - Never break character!
                 - Never mention 'user_input' or ask for input - just respond as your character
    			[Your Memory]
    			{{chat_history}}

    			User: {{user_input}}

    			{bot_name}:"""

            self.dialog_chain = RunnableSequence(
                PromptTemplate(
                    input_variables=["user_input", "chat_history"],
                    template=prompt_template
                ) | self.llm
            )
        else:
            self.dialog_chain = RunnableSequence(
                PromptTemplate(
                    input_variables=["user_input"],
                    template="Respond to the user: {{user_input}}"
                ) | self.llm
            )

    def _process_memory(self, user_input: str, response: str):
        """Update conversation memory"""
        try:
            st.session_state.memory.save_context(
                {"input": user_input},
                {"output": response}
            )
        except Exception as e:
            st.toast(f"Memory update failed: {str(e)}", icon="⚠️")

    def _cached_llm_invoke(self, prompt: str, bot_context: str) -> str:
        """Safe wrapper for LLM calls with caching"""
        try:
            combined_input = f"{bot_context}\n\n{prompt}"
            input_hash = hashlib.md5(combined_input.encode()).hexdigest()  # Unique key for cache

            if not prompt.strip():
                raise ValueError("Empty prompt provided")

            response = self.llm.invoke(combined_input)
            return response.strip()

        except (LangChainException, OutputParserException) as e:
            st.error(f"AI service error: {str(e)}")
            return "🔧 My circuits are acting up. Try again?"

        except ValueError as e:
            return "Please type something meaningful."

        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            return "🌌 Whoops! Something unexpected happened."

    def generate_single_response(self, user_input: str) -> str:
        """Generate response with memory support"""
        try:
            # Debug: Print memory state
            print("Memory state:", st.session_state.memory)

            # Get conversation history from memory
            history = st.session_state.memory.load_memory_variables({})
            print("Loaded history:", history)

            # Prepare inputs
            chain_inputs = {
                "user_input": user_input,
                "chat_history": history.get("chat_history", []),
            }

            # Use the dialog chain with memory context
            response = self.dialog_chain.invoke(chain_inputs)

            # Update memory
            self._process_memory(user_input, response)
            return response

        except Exception as e:
            import traceback
            st.error(f"Response generation failed: {str(e)}")
            st.text(traceback.format_exc())  # Show full traceback
            return "❌ Sorry, I encountered an error. Please try again."

    def generate_group_chat_response(self, bot: dict, prompt: str, shared_history: str) -> str:
        """Specialized response generator for group chats"""
        try:
            # Get this bot's personality memory
            personality_memory = st.session_state.group_chat['personality_memories'][bot['name']]
            personality_history = personality_memory.load_memory_variables({}).get("chat_history", [])

            # Format the personality history
            formatted_personality_history = "\n".join(
                f"{msg.type.capitalize()}: {msg.content}"
                for msg in personality_history
                if hasattr(msg, 'type') and hasattr(msg, 'content')
            )

            # Create the full prompt with bot personality and both histories
            prompt_template = f"""You are {bot['name']} ({bot['emoji']}), {bot['desc']}.

                [Your Personality Rules]
                - Always respond as {bot['name']}
                - Traits: {', '.join(bot['personality'].get('traits', []))}
                - Speech: {bot['personality'].get('speech_pattern', 'neutral')}
                - Quirks: {', '.join(bot['personality'].get('quirks', []))}

                [Group Conversation History]
                {shared_history}

                [Your Private Memory]
                {formatted_personality_history}

                User: {prompt}

                {bot['name']}:"""

            # Generate response
            response = self.llm.invoke(prompt_template)

            # Update memories (handled by GroupChatManager)
            return response.strip()

        except Exception as e:
            st.error(f"Group response generation failed: {str(e)}")
            return f"❌ {bot['name']} encountered an error. Please try again."

    def generate_greeting(self):
        try:
            bot_name = st.session_state.get('selected_bot', 'StoryBot')
            current_bot = next((b for b in BOTS + st.session_state.user_bots if b["name"] == bot_name), None)

            if current_bot:
                prompt = f"""
                    As {bot_name}, create a friendly 1-sentence greeting that:
                    - Uses your emoji {current_bot['emoji']}
                    - Mentions your name
                    - Reflects your personality: {current_bot['personality'].get('tone', 'neutral')}
                    - Includes one of your quirks: {', '.join(current_bot['personality'].get('quirks', []))}
                    """
                return self._cached_llm_invoke(prompt, current_bot["desc"])

            # Default fallback if bot not found
            return f"Hello! I'm {bot_name}! Let's chat!"

        except Exception as e:
            st.toast(f"Greeting generation failed: {str(e)}", icon="⚠️")
            # Safe fallback that doesn't depend on bot_name
            return "Hello! Let's chat!"

    def display_chat_icon_toolbar(self):
        """Create a toolbar with chat action buttons at the bottom of the chat interface"""
        with st.container():
            # Create columns for the toolbar layout
            left_group, center_spacer, right_options = st.columns([4, 2, 2])

            with left_group:
                # Action buttons in a horizontal layout
                action_cols = st.columns(4)
                with action_cols[0]:
                    if st.button(
                            "🖼️",
                            help="Generate image based on conversation",
                            key="img_gen_btn"
                    ):
                        st.toast("Image generation coming soon!", icon="🖼️")

                with action_cols[1]:
                    if st.button(
                            "🎙️",
                            help="Enable voice input",
                            key="voice_input_btn"
                    ):
                        st.toast("Voice input coming soon!", icon="🎙️")

                with action_cols[2]:
                    # Get current chat history length
                    chat_history = st.session_state.chat_histories.get(
                        st.session_state.selected_bot, []
                    )
                    disabled = len(chat_history) < 2  # Need at least 1 exchange to regenerate

                    if st.button(
                            "🔄",
                            help="Regenerate bot's last response",
                            disabled=disabled,
                            key="regenerate_btn"
                    ):
                        if not disabled:
                            try:
                                with st.spinner("Re-generating response..."):
                                    last_user_msg = chat_history[-2][1]  # Get last user message

                                    # Regenerate response
                                    new_response = self.generate_single_response(last_user_msg)

                                    # Replace last assistant message
                                    chat_history[-1] = ("assistant", new_response)
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Failed to regenerate: {str(e)}")

                with action_cols[3]:
                    if st.button(
                            "📋",
                            help="Copy chat history to clipboard",
                            key="copy_chat_btn"
                    ):
                        try:
                            import pyperclip
                            chat_text = "\n".join(
                                f"{role}: {msg}" for role, msg in chat_history
                            )
                            pyperclip.copy(chat_text)
                            st.toast("Chat copied to clipboard!", icon="📋")
                        except Exception as e:
                            st.error(f"Failed to copy: {str(e)}")

            with right_options:
                # More options dropdown
                with st.popover("⚙️", help="More options"):
                    # Clear chat confirmation flow
                    if 'confirm_clear' not in st.session_state:
                        st.session_state.confirm_clear = False

                    if st.button(
                            "🗑️ Clear Chat",
                            help="Start a fresh conversation",
                            use_container_width=True,
                            key="clear_chat_main"
                    ):
                        st.session_state.confirm_clear = True

                    if st.session_state.confirm_clear:
                        st.warning("This will erase all messages in this chat.")
                        confirm_cols = st.columns(2)
                        with confirm_cols[0]:
                            if st.button(
                                    "✅ Confirm",
                                    type="primary",
                                    use_container_width=True,
                                    key="confirm_clear_yes"
                            ):
                                bot_name = st.session_state.selected_bot
                                st.session_state.chat_histories[bot_name] = []
                                st.session_state.greeting_sent = False
                                st.session_state.confirm_clear = False
                                st.toast("Chat cleared!", icon="🗑️")
                                st.rerun()
                        with confirm_cols[1]:
                            if st.button(
                                    "❌ Cancel",
                                    use_container_width=True,
                                    key="confirm_clear_no"
                            ):
                                st.session_state.confirm_clear = False
                                st.rerun()

                    st.divider()

                    # Additional options
                    st.caption("Advanced Options")
                    if st.button(
                            "💾 Export Chat",
                            disabled=True,
                            help="Export conversation history (coming soon)",
                            use_container_width=True
                    ):
                        st.toast("Export feature coming soon!", icon="💾")

                    if st.button(
                            "🔄 Switch Bot",
                            disabled=True,
                            help="Change character mid-conversation (coming soon)",
                            use_container_width=True
                    ):
                        st.toast("Bot switching coming soon!", icon="🔄")