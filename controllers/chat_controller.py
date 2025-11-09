import streamlit as st
from functools import lru_cache

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import HumanMessage

from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnableSequence
from langchain_core.exceptions import OutputParserException, LangChainException
from langchain_community.llms import Ollama
from config import get_default_bots,DEFAULT_LLM_CONFIG
import asyncio


class LLMChatController:
    def __init__(self):
        self.llm = Ollama(**DEFAULT_LLM_CONFIG)
        self._init_session_state()
        self._init_dialog_chain()
        self._init_memory_buffer()

    @lru_cache(maxsize=100)
    def _init_memory_buffer(self):
        """Initialize enhanced conversation memory using ChatMessageHistory"""
        if "memory" not in st.session_state:
            st.session_state.memory = {
                'chat_history': ChatMessageHistory(),
                'window_size': 50  # Remember last 50 exchanges
            }

    @staticmethod
    def _init_session_state():
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

        # Combine default bots and user bots
        all_bots = get_default_bots() + st.session_state.user_bots

        # Helper function to safely get bot attributes
        def _get_bot_attr(bot, attr, default=None):
            if hasattr(bot, attr):
                return getattr(bot, attr, default)
            elif isinstance(bot, dict):
                return bot.get(attr, default)
            return default

        current_bot = next((b for b in all_bots if _get_bot_attr(b, 'name') == bot_name), None)

        if current_bot:
            # Handle both Bot objects and dictionaries
            personality = _get_bot_attr(current_bot, 'personality', {})

            # Default bots don't have system_rules, so use DEFAULT_RULES from config
            system_rules = _get_bot_attr(current_bot, 'system_rules', "")
            if not system_rules:
                from config import DEFAULT_RULES
                system_rules = DEFAULT_RULES

            # Clean up the system_rules to remove any empty variables
            if system_rules and isinstance(system_rules, str):
                # Remove any empty lines or problematic characters
                system_rules = "\n".join([line for line in system_rules.split("\n") if line.strip()])
            else:
                system_rules = ""

            # Get scenario
            scenario = _get_bot_attr(current_bot, 'scenario', '')
            scenario_context = f"\n[Current Scenario]\n{scenario}\n" if scenario else ""

            # Clean up personality traits and quirks
            traits = _get_bot_attr(personality, 'traits', [])
            if isinstance(traits, str):
                traits = [t.strip() for t in traits.split(',') if t.strip()]
            traits_str = ', '.join([t for t in traits if t]) or "friendly"

            quirks = _get_bot_attr(personality, 'quirks', [])
            if isinstance(quirks, str):
                quirks = [q.strip() for q in quirks.split(',') if q.strip()]
            quirks_str = ', '.join([q for q in quirks if q]) or "none"

            speech_pattern = _get_bot_attr(personality, 'speech_pattern', 'neutral') or "neutral"
            tone = _get_bot_attr(personality, 'tone', 'neutral') or "neutral"

            # Get description - handle different possible field names
            desc = _get_bot_attr(current_bot, 'desc') or _get_bot_attr(current_bot,
                                                                       'description') or "A helpful AI assistant"
            emoji = _get_bot_attr(current_bot, 'emoji', '🤖')

            # Unified template that works for both single and group chats
            prompt_template = f"""You are {bot_name} ({emoji}), {desc}.{scenario_context}

    [CHARACTER DIRECTIVES]
    {system_rules}

    [Your Personality Rules]
    - Always respond as {bot_name}
    - Tone: {tone}
    - Traits: {traits_str}
    - Speech: {speech_pattern}
    - Quirks: {quirks_str}
    - Never break character!
    - Never mention 'user_input' or ask for input - just respond as your character

    [Your Memory]
    {{chat_history}}

    User: {{user_input}}

    {bot_name}:"""

            # Debug: Print the template to check for issues
            print(f"DEBUG: Prompt template for {bot_name}:")
            print(prompt_template)

            # Create the prompt template with proper input variables
            try:
                prompt = PromptTemplate(
                    input_variables=["user_input", "chat_history"],
                    template=prompt_template
                )

                # Verify the template has the correct variables
                print(f"DEBUG: Template input variables: {prompt.input_variables}")

                self.dialog_chain = RunnableSequence(
                    prompt | self.llm
                )
            except Exception as e:
                print(f"ERROR creating prompt template: {str(e)}")
                # Fallback to simple template
                self.dialog_chain = RunnableSequence(
                    PromptTemplate(
                        input_variables=["user_input"],
                        template="Respond to the user: {{user_input}}"
                    ) | self.llm
                )
        else:
            # Fallback if bot not found
            print(f"WARNING: Bot '{bot_name}' not found in BOTS or user_bots")
            self.dialog_chain = RunnableSequence(
                PromptTemplate(
                    input_variables=["user_input"],
                    template="Respond to the user: {{user_input}}"
                ) | self.llm
            )

    @staticmethod
    def _process_memory(user_input: str, response: str):
        """Update conversation memory using LangGraph-style persistence"""
        try:
            # Add messages to history
            st.session_state.memory['chat_history'].add_user_message(user_input)
            st.session_state.memory['chat_history'].add_ai_message(response)

            # Trim to maintain window size
            messages = st.session_state.memory['chat_history'].messages
            if len(messages) > st.session_state.memory['window_size']:
                st.session_state.memory['chat_history'].messages = messages[-st.session_state.memory['window_size']:]

        except Exception as e:
            st.toast(f"Memory update failed: {str(e)}", icon="⚠️")

    def get_chat_history(self):
        """Get formatted chat history"""
        try:
            if 'memory' not in st.session_state:
                self._init_memory_buffer()

            messages = st.session_state.memory['chat_history'].messages
            return "\n".join(
                f"{'User' if isinstance(msg, HumanMessage) else 'AI'}: {msg.content}"
                for msg in messages
            )
        except Exception as e:
            print(f"ERROR in get_chat_history: {str(e)}")
            return ""  # Return empty history if there's an error

    @lru_cache(maxsize=100)  # Cache up to 100 responses
    def _cached_llm_invoke(self, prompt: str, bot_context: str) -> str:
        """Safe wrapper for LLM calls with caching"""
        try:
            combined_input = f"{bot_context}\n\n{prompt}"

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

    async def generate_single_response(self, user_input: str) -> str:
        """Generate response with memory support"""
        try:
            # Debug: Check if chat_histories exists and has the selected bot
            if 'chat_histories' not in st.session_state:
                st.session_state.chat_histories = {}

            # Get current chat history
            selected_bot = st.session_state.get('selected_bot')
            if not selected_bot:
                return "❌ No bot selected. Please select a bot first."

            chat_history = st.session_state.chat_histories.get(selected_bot, [])

            # Debug: Print current state for troubleshooting
            print(f"DEBUG: Selected bot: {selected_bot}")
            print(f"DEBUG: Chat history length: {len(chat_history)}")
            print(f"DEBUG: Memory exists: {'memory' in st.session_state}")
            if 'memory' in st.session_state:
                print(f"DEBUG: Memory messages: {len(st.session_state.memory['chat_history'].messages)}")

            # If this is the first exchange after greeting, ensure greeting is properly stored
            if len(chat_history) == 2:  # [Greeting, User message]
                greeting = chat_history[0][1]
                self._process_memory(
                    "(Conversation started)",
                    f"{selected_bot}: {greeting}"
                )

            # Get formatted chat history
            history = self.get_chat_history()

            # Prepare inputs
            chain_inputs = {
                "user_input": user_input,
                "chat_history": history
            }

            response = self.dialog_chain.invoke(chain_inputs)
            self._process_memory(user_input, response)
            return response

        except Exception as e:
            import traceback
            error_msg = f"Response generation failed: {str(e)}"
            print(f"ERROR: {error_msg}")
            print(traceback.format_exc())
            st.error(error_msg)
            return "❌ Sorry, I encountered an error. Please try again."

    async def generate_group_chat_response(self, bot, prompt: str, shared_history: str) -> str:
        """Specialized response generator for group chats - UPDATED FOR BOT OBJECTS"""
        try:
            # Get this bot's personality memory
            personality_memory = st.session_state.group_chat['personality_memories'][
                bot.name]  # CHANGED: bot['name'] to bot.name
            personality_history = personality_memory.load_memory_variables({}).get("chat_history", [])

            # Format the personality history
            formatted_personality_history = "\n".join(
                f"{msg.type.capitalize()}: {msg.content}"
                for msg in personality_history
                if hasattr(msg, 'type') and hasattr(msg, 'content')
            )

            # Create the full prompt with bot personality and both histories
            prompt_template = f"""You are {bot.name} ({bot.emoji}), {bot.desc}.

                [Your Personality Rules]
                - Always respond as {bot.name} 
                - Traits: {', '.join(bot.personality.get('traits', []))} 
                - Speech: {bot.personality.get('speech_pattern', 'neutral')}
                - Quirks: {', '.join(bot.personality.get('quirks', []))}

                [Group Conversation History]
                {shared_history}

                [Your Private Memory]
                {formatted_personality_history}

                User: {prompt}

                {bot.name}:"""

            # Generate response
            response = self.llm.invoke(prompt_template)

            # Update memories (handled by GroupChatManager)
            return response.strip()

        except Exception as e:
            st.error(f"Group response generation failed: {str(e)}")
            return f"❌ {bot.name} encountered an error. Please try again."  # CHANGED: bot['name'] to bot.name

    async def generate_greeting(self):
        try:
            bot_name = st.session_state.get('selected_bot', 'StoryBot')
            scenario_context = ""

            # Combine default bots and user bots
            all_bots = get_default_bots() + st.session_state.user_bots

            # Helper function to safely get bot attributes
            def _get_bot_attr(bot, attr, default=None):
                if hasattr(bot, attr):
                    return getattr(bot, attr, default)
                elif isinstance(bot, dict):
                    return bot.get(attr, default)
                return default

            current_bot = next((b for b in all_bots if _get_bot_attr(b, 'name') == bot_name), None)

            if current_bot:
                # Handle different personality structures
                personality = _get_bot_attr(current_bot, 'personality', {})

                tone = _get_bot_attr(personality, 'tone', 'neutral')
                quirks = _get_bot_attr(personality, 'quirks', [])
                if isinstance(quirks, str):
                    quirks = [q.strip() for q in quirks.split(',') if q.strip()]

                # Get scenario for context
                scenario = _get_bot_attr(current_bot, 'scenario', '')
                scenario_context = f"this Is the situation: {scenario}" if scenario else ""

                prompt = f"""
                    As {bot_name}, create a friendly 4-5 sentence greeting that:
                    - Uses your emoji {_get_bot_attr(current_bot, 'emoji', '🤖')}
                    - Mentions your name
                    - Reflects your personality tone: {tone}
                    - Includes one of your quirks: {', '.join(quirks) if quirks else 'none'}{scenario_context}
                    - Thoughts appear in italics format
                    - Dialogue in double quotes like "this"
                    Only return the output,response 
                    """
                return self._cached_llm_invoke(prompt, _get_bot_attr(current_bot, "desc", "A helpful AI assistant"))

            # Default fallback if bot not found
            return f"Hello! I'm {bot_name}! Let's chat!"

        except Exception as e:
            st.toast(f"Greeting generation failed: {str(e)}", icon="⚠️")
            # Safe fallback that doesn't depend on bot_name
            return "Hello! Let's chat!"

    async def enhance_text(self, current_text: str, field_name: str, context: dict = None) -> str:
        """Enhanced version with context support that returns ONLY the enhanced text"""
        if not current_text.strip() and not context:
            return current_text

        if field_name == "character greeting" and context:
            prompt = f"""Create an engaging greeting message for {context['name']} that:
            - Matches their personality: {context['personality']}
            - Reflects their background: {context['background']}
            - Optionally references their appearance: {context['appearance']}
            - Is 4-5 sentences maximum
            - Sounds in-character
            - Thoughts appear in italics format
            - Dialogue in "double quotes"

            IMPORTANT: Return ONLY the enhanced greeting text itself with no additional commentary.
            Do NOT include any introductory text like "Here is the enhanced version".

            Current greeting (improve upon this):
            {context['current_greeting']}

            Enhanced greeting:"""
        else:
            prompt = f"""Improve and enhance this {field_name} text:
            {current_text}

            Rules:
            - Make it more engaging and detailed
            - Maintain the original intent
            - Return ONLY the enhanced text with no additional commentary
            - Do NOT say "Enhanced version" or similar
            - Is 5-8 sentences maximum

            Enhanced text:"""

        return await self._async_llm_invoke(prompt, "Text enhancement")

    # Add this new async method for async calls
    async def _async_llm_invoke(self, prompt: str, context: str) -> str:
        """Async version of LLM invocation"""
        try:
            combined_input = f"{context}\n\n{prompt}"
            if not prompt.strip():
                raise ValueError("Empty prompt provided")

            # Use async invoke if available
            response = await self.llm.ainvoke(combined_input)
            return response.strip()

        except Exception as e:
            st.error(f"Enhancement failed: {str(e)}")
            return context  # Return original text if enhancement fails

    @staticmethod
    def clear_last_exchange():
        """Remove the last Q&A pair from memory and session state - FIXED VERSION"""
        try:
            selected_bot = st.session_state.get('selected_bot')

            # Clear from session state chat history
            if selected_bot and 'chat_histories' in st.session_state:
                chat_history = st.session_state.chat_histories.get(selected_bot, [])
                if len(chat_history) >= 2:
                    # Only remove the last exchange (last user + assistant messages)
                    # But be careful not to remove the greeting
                    if len(chat_history) > 2:  # More than just greeting + one exchange
                        st.session_state.chat_histories[selected_bot] = chat_history[:-2]
                        print(
                            f"DEBUG: Cleared last exchange from chat history. Remaining: {len(st.session_state.chat_histories[selected_bot])}")
                    else:
                        # If only greeting + one exchange, just remove the exchange but keep greeting
                        st.session_state.chat_histories[selected_bot] = [chat_history[0]]
                        print(f"DEBUG: Cleared exchange but kept greeting")

            # Clear from memory
            if 'memory' in st.session_state and st.session_state.memory['chat_history'].messages:
                messages = st.session_state.memory['chat_history'].messages
                if len(messages) >= 2:
                    st.session_state.memory['chat_history'].messages = messages[:-2]
                    print(
                        f"DEBUG: Cleared 2 messages from memory. Remaining: {len(st.session_state.memory['chat_history'].messages)}")

        except Exception as e:
            print(f"Error clearing last exchange: {str(e)}")

    # ========== NEW MESSAGE EDIT/DELETE METHODS ==========

    async def edit_user_message(self, bot_name: str, message_index: int, new_content: str):
        """Edit a user message and clear subsequent messages - ASYNC VERSION"""
        try:
            if bot_name not in st.session_state.chat_histories:
                raise ValueError(f"Bot {bot_name} not found in chat histories")

            chat_history = st.session_state.chat_histories[bot_name]

            # Validate index
            if message_index >= len(chat_history) or message_index < 0:
                raise ValueError(f"Invalid message index: {message_index}")

            # Ensure it's a user message
            role, old_content = chat_history[message_index]
            if role != "user":
                raise ValueError("Can only edit user messages")

            # Update the message content
            chat_history[message_index] = (role, new_content)

            # Clear all messages after this one (non-blocking operation)
            messages_to_remove = len(chat_history) - (message_index + 1)
            if messages_to_remove > 0:
                chat_history = chat_history[:message_index + 1]
                st.session_state.chat_histories[bot_name] = chat_history

            # Clear memory for removed messages (non-blocking)
            await self._clear_memory_after_index(message_index // 2)  # Each exchange = 2 messages (user + assistant)

            # Clear audio cache for removed messages (non-blocking)
            await self._clear_audio_cache_after_index(bot_name, message_index)

            print(f"DEBUG: Edited message at index {message_index}. Remaining messages: {len(chat_history)}")

        except Exception as e:
            print(f"Error editing message: {str(e)}")
            raise

    async def delete_message(self, bot_name: str, message_index: int):
        """Delete a message and all subsequent messages - ASYNC VERSION"""
        try:
            if bot_name not in st.session_state.chat_histories:
                raise ValueError(f"Bot {bot_name} not found in chat histories")

            chat_history = st.session_state.chat_histories[bot_name]

            # Validate index
            if message_index >= len(chat_history) or message_index < 0:
                raise ValueError(f"Invalid message index: {message_index}")

            # Calculate how many exchanges to remove from memory
            # Each exchange = 2 messages (user + assistant)
            exchanges_to_remove = (len(chat_history) - message_index + 1) // 2

            # Keep messages up to the deletion point (non-blocking)
            chat_history = chat_history[:message_index]
            st.session_state.chat_histories[bot_name] = chat_history

            # Clear memory for removed exchanges (non-blocking)
            await self._clear_memory_after_index(len(chat_history) // 2)

            # Clear audio cache for removed messages (non-blocking)
            await self._clear_audio_cache_after_index(bot_name, message_index)

            print(f"DEBUG: Deleted message at index {message_index}. Remaining messages: {len(chat_history)}")

        except Exception as e:
            print(f"Error deleting message: {str(e)}")
            raise

    @staticmethod
    async def _clear_memory_after_index(exchange_index: int):
        """Clear memory starting from a specific exchange index - ASYNC VERSION"""
        try:
            if 'memory' not in st.session_state:
                return

            messages = st.session_state.memory['chat_history'].messages
            if not messages:
                return

            # Each exchange = 2 messages (user + assistant)
            messages_to_keep = exchange_index * 2

            if messages_to_keep < len(messages):
                st.session_state.memory['chat_history'].messages = messages[:messages_to_keep]
                print(f"DEBUG: Cleared memory after exchange {exchange_index}. Remaining messages: {messages_to_keep}")

            # Small async sleep to yield control (non-blocking)
            await asyncio.sleep(0.001)

        except Exception as e:
            print(f"Error clearing memory: {str(e)}")

    @staticmethod
    async def _clear_audio_cache_after_index( bot_name: str, message_index: int):
        """Clear audio cache for messages after a specific index - ASYNC VERSION"""
        try:
            if "audio_cache" not in st.session_state:
                return

            keys_to_remove = []
            for key in st.session_state.audio_cache:
                if bot_name in key:
                    # Extract index from key format: "audio_{bot_name}_{index}"
                    try:
                        key_index = int(key.split('_')[-1])
                        if key_index >= message_index:
                            keys_to_remove.append(key)
                    except (ValueError, IndexError):
                        continue

            # Remove the keys (non-blocking batch operation)
            for key in keys_to_remove:
                # Also remove generating state if it exists
                generating_key = f"generating_{key}"
                if generating_key in st.session_state:
                    del st.session_state[generating_key]
                del st.session_state.audio_cache[key]

            # Small async sleep to yield control (non-blocking)
            await asyncio.sleep(0.001)

            print(f"DEBUG: Cleared audio cache for {len(keys_to_remove)} messages after index {message_index}")

        except Exception as e:
            print(f"Error clearing audio cache: {str(e)}")

    async def regenerate_after_edit(self, bot_name: str, user_message_index: int):
        """Regenerate AI response after user message edit - ASYNC VERSION"""
        try:
            if bot_name not in st.session_state.chat_histories:
                raise ValueError(f"Bot {bot_name} not found in chat histories")

            chat_history = st.session_state.chat_histories[bot_name]

            # Validate index and ensure it's a user message
            if user_message_index >= len(chat_history) or user_message_index < 0:
                raise ValueError(f"Invalid message index: {user_message_index}")

            role, user_message = chat_history[user_message_index]
            if role != "user":
                raise ValueError("Can only regenerate after user messages")

            # Generate new response (this is already async)
            new_response = await self.generate_single_response(user_message)

            # If there was a previous AI response after this user message, replace it
            # Otherwise, add a new response
            next_index = user_message_index + 1
            if next_index < len(chat_history) and chat_history[next_index][0] == "assistant":
                chat_history[next_index] = ("assistant", new_response)
            else:
                chat_history.append(("assistant", new_response))

            # Update memory with the new exchange
            self._process_memory(user_message, new_response)

            return new_response

        except Exception as e:
            print(f"Error regenerating after edit: {str(e)}")
            raise