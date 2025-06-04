import hashlib
import streamlit as st
from functools import lru_cache

from langchain.memory import ChatMessageHistory
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
        messages = st.session_state.memory['chat_history'].messages
        return "\n".join(
            f"{'User' if isinstance(msg, HumanMessage) else 'AI'}: {msg.content}"
            for msg in messages
        )

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
            # Get current chat history
            chat_history = st.session_state.chat_histories.get(st.session_state.selected_bot, [])

            # If this is the first exchange after greeting, ensure greeting is properly stored
            if len(chat_history) == 2:  # [Greeting, User message]
                greeting = chat_history[0][1]
                self._process_memory(
                    "(Conversation started)",
                    f"{st.session_state.selected_bot}: {greeting}"
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
            st.error(f"Response generation failed: {str(e)}")
            st.text(traceback.format_exc())
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

    def clear_last_exchange(self):
        """Remove the last Q&A pair from memory"""
        if 'memory' in st.session_state and st.session_state.memory['chat_history'].messages:
            messages = st.session_state.memory['chat_history'].messages
            messages.pop()  # Remove AI response
            messages.pop()  # Remove user message
