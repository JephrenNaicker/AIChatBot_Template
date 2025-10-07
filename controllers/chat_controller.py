import streamlit as st
from functools import lru_cache

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import HumanMessage

from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnableSequence
from langchain_core.exceptions import OutputParserException, LangChainException
from langchain_community.llms import Ollama
from config import BOTS

class LLMChatController:
    def __init__(self):
        self.llm = Ollama(model="llama3:latest")
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
        all_bots = BOTS + st.session_state.user_bots
        current_bot = next((b for b in all_bots if b["name"] == bot_name), None)

        if current_bot:
            # Handle both default bots and user bots structure
            personality = current_bot.get("personality", {})

            # Default bots don't have system_rules, so use DEFAULT_RULES from config
            system_rules = current_bot.get("system_rules", "")
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
            scenario = current_bot.get('scenario', '')
            scenario_context = f"\n[Current Scenario]\n{scenario}\n" if scenario else ""

            # Clean up personality traits and quirks
            traits = personality.get('traits', [])
            if isinstance(traits, str):
                traits = [t.strip() for t in traits.split(',') if t.strip()]
            traits_str = ', '.join([t for t in traits if t]) or "friendly"

            quirks = personality.get('quirks', [])
            if isinstance(quirks, str):
                quirks = [q.strip() for q in quirks.split(',') if q.strip()]
            quirks_str = ', '.join([q for q in quirks if q]) or "none"

            speech_pattern = personality.get('speech_pattern', 'neutral') or "neutral"
            tone = personality.get('tone', 'neutral') or "neutral"

            # Get description - handle different possible field names
            desc = current_bot.get('desc') or current_bot.get('description') or "A helpful AI assistant"
            emoji = current_bot.get('emoji', '🤖')

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


    def _process_memory(self, user_input: str, response: str):
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

    async def generate_group_chat_response(self, bot: dict, prompt: str, shared_history: str) -> str:
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

    async def generate_greeting(self):
        try:
            bot_name = st.session_state.get('selected_bot', 'StoryBot')
            scenario_context = ""

            # Combine default bots and user bots
            all_bots = BOTS + st.session_state.user_bots
            current_bot = next((b for b in all_bots if b["name"] == bot_name), None)

            if current_bot:
                # Handle different personality structures
                personality = current_bot.get("personality", {})

                tone = personality.get('tone', 'neutral')
                quirks = personality.get('quirks', [])
                if isinstance(quirks, str):
                    quirks = [q.strip() for q in quirks.split(',') if q.strip()]

                    # Get scenario for context
                    scenario = current_bot.get('scenario', '')
                    scenario_context = f"this Is the situation: {scenario}" if scenario else ""

                prompt = f"""
                    As {bot_name}, create a friendly 4-5 sentence greeting that:
                    - Uses your emoji {current_bot.get('emoji', '🤖')}
                    - Mentions your name
                    - Reflects your personality tone: {tone}
                    - Includes one of your quirks: {', '.join(quirks) if quirks else 'none'}{scenario_context}
                    - Thoughts appear in italics format
                    - Dialogue in double quotes like "this"
                    Only return the output,response 
                    """
                return self._cached_llm_invoke(prompt, current_bot.get("desc", "A helpful AI assistant"))

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

    def clear_last_exchange(self):
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
