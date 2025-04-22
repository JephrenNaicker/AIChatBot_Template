import hashlib
import os
from functools import lru_cache

import streamlit as st
from PIL import Image, ImageDraw
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnableSequence
from langchain_core.exceptions import (
    OutputParserException,
    LangChainException
)
from langchain_ollama import OllamaLLM
from TTS.api import TTS

PAGES = {
    "home": "🏠 Home",
    "profile": "👤 Profile",
    "my_bots": "🌟 My Bots",
    "voice": "🎙️ Voice",
    "bot_setup": "🧙 Character Setup",  # New
    "generate_concept": "🪄 Generate Concept"  # New
}


PROFILE_SCHEMA = {
    "username": {"type": str, "editable": False},
    "display_name": {"type": str, "editable": True},
    "bio": {"type": str, "editable": True, "multiline": True},
    "avatar": {"type": str, "editable": True, "options": ["👨", "👩", "🧑‍💻", "🧙", "🦸"]},
    "theme": {"type": str, "editable": True, "options": ["light", "dark", "system"]},
    "created_at": {"type": str, "editable": False}
}

BOTS = [
    {
        "name": "StoryBot",
        "emoji": "📖",
        "desc": "A friendly storytelling assistant",
        "tags": ["story", "creative"],
        "personality": {
            "tone": "whimsical",
            "speech_pattern": "long, descriptive sentences",
            "quirks": [
                "Starts responses with 'Once upon a time...' 30% of the time",
                "Uses fairy tale metaphors"
            ]
        }
    },
    {
        "name": "SciFiBot",
        "emoji": "🚀",
        "desc": "Your futuristic sci-fi adventure buddy",
        "tags": ["scifi", "space"],
        "personality": {
            "tone": "analytical",
            "speech_pattern": "short, technical phrases",
            "quirks": [
                "Uses words like 'interstellar' and 'quantum'",
                "Ends messages with 'Fascinating!' 20% of the time"
            ]
        }
    },
    {
        "name": "MysteryBot",
        "emoji": "🕵️",
        "desc": "Solve mysteries and uncover secrets",
        "tags": ["mystery", "puzzle"],
        "personality": {
            "tone": "cryptic",
            "speech_pattern": "short, suspenseful phrases",
            "quirks": [
                "Ends messages with a riddle or question",
                "Uses words like 'red herring' and 'alibi'"
            ]
        }
    },
    {
        "name": "HistoryBot",
        "emoji": "🏛️",
        "desc": "Travel through time and explore history",
        "tags": ["history", "education"],
        "personality": {
            "tone": "wise",
            "speech_pattern": "formal, educational",
            "quirks": [
                "References historical events (e.g., 'As Napoleon once said...')",
                "Uses phrases like 'In the year...' or 'Centuries ago...'",
                "Corrects user gently if they make historical inaccuracies"
            ]
        }
    },
    {
        "name": "CodingBot",
        "emoji": "💻",
        "desc": "Get help with programming and algorithms",
        "tags": ["coding", "tech"],
        "personality": {
            "tone": "precise",
            "speech_pattern": "concise, technical",
            "quirks": [
                "Formats responses like code comments 30% of the time",
                "Uses analogies like 'This works like a recursive function...'",
                "Ends messages with '// Happy coding!'"
            ]
        }
    },
    {
        "name": "PoetryBot",
        "emoji": "✒️",
        "desc": "Create beautiful poems and verses",
        "tags": ["poetry", "writing"],
        "personality": {
            "tone": "lyrical",
            "speech_pattern": "rhythmic, metaphorical",
            "quirks": [
                "Responds in haiku format 20% of the time",
                "Uses words like 'verse', 'stanza', and 'metaphor'",
                "Ends messages with '~ The End ~' for dramatic effect"
            ]
        }
    }
]

# =====  User-created bots storage =====
if 'user_bots' not in st.session_state:
    st.session_state.user_bots = []

# ===== Tone options for bot creation =====
# TONE_OPTIONS = [
#     "Friendly", "Professional", "Humorous", "Serious",
#     "Whimsical", "Sarcastic", "Enthusiastic", "Calm"
# ]

# ===== Personality trait options =====
PERSONALITY_TRAITS = [
    "Creative", "Logical", "Adventurous", "Cautious",
    "Empathetic", "Analytical", "Optimistic", "Pessimistic",
    "Sarcastic", "Witty", "Humorous", "Serious",
    "Whimsical", "Enthusiastic", "Calm", "Blunt",
    "Philosophical", "Dramatic", "Mysterious", "Wise"
]

# ===== Tag options =====
TAG_OPTIONS = [
    "storytelling", "education", "tech", "gaming",
    "productivity", "health", "music", "art"
]



# ===== Create a placeholder avatar =====
def create_placeholder_avatar():
    # Create a simple image with emoji
    img = Image.new('RGB', (100, 100), color=(73, 109, 137))
    d = ImageDraw.Draw(img)
    d.text((50,50), "👑", fill=(255,255,0), anchor="mm", font_size=40)
    return img

class StoryChatBot:
    def __init__(self):
        self.llm = OllamaLLM(model="llama3:latest")
        self._init_session_state()
        self._init_chains()
        self._init_memory()

    @lru_cache(maxsize=100)  # Cache up to 100 responses
    def _init_memory(self):
        """Initialize enhanced conversation memory"""
        if "memory" not in st.session_state:
            st.session_state.memory = ConversationBufferWindowMemory(
                k=50,  # Remember last 50 exchanges
                return_messages=True,
                memory_key="chat_history",
                output_key="output"
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

    def _init_chains(self):
        bot_name = st.session_state.get('selected_bot', '')
        current_bot = next((b for b in BOTS + st.session_state.user_bots if b["name"] == bot_name), None)

        if current_bot:
            personality = current_bot.get("personality", {})
            # Enhanced prompt template with stronger personality enforcement
            prompt_template = f"""
               You are {bot_name} ({current_bot['emoji']}), {current_bot['desc']}.

               Personality Rules (MUST FOLLOW):
               - Name: Always respond as {bot_name}
               - Personality Traits: {', '.join(personality.get('traits', []))}
               - Speech Pattern: {personality.get('speech_pattern', 'neutral')}
               - Quirks: {', '.join(personality.get('quirks', []))}
               - Never break character!
               - Never mention 'user_input' or ask for input - just respond naturally
               - If asked about your name, respond with "{bot_name}"

               Chat History: {{chat_history}}

               User: {{user_input}}

               {bot_name}:
               """
        else:
            prompt_template = "Respond to the user: {{user_input}}"

        self.dialog_chain = RunnableSequence(
            PromptTemplate(
                input_variables=["user_input", "chat_history"],
                template=prompt_template
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

    def generate_response(self, user_input: str) -> str:
        """Generate response with memory support"""
        try:
            # Get conversation history from memory
            history = st.session_state.memory.load_memory_variables({})

            # Use the dialog chain with memory context
            response = self.dialog_chain.invoke({
                "user_input": user_input,
                "chat_history": history.get("chat_history", "")
            })

            # Update memory
            self._process_memory(user_input, response)
            return response

        except Exception as e:
            st.error(f"Response generation failed: {str(e)}")
            return "❌ Sorry, I encountered an error. Please try again."

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


def home_page():
    """Home page with title/search in centered container and full-width grid"""
    # Title and search in normal centered container
    st.title("🤖 Chat Bot Gallery")
    search_query = st.text_input("🔍 Search bots...",
                                 placeholder="Type to filter bots",
                                 key="bot_search")

    # Combine default bots with published user bots
    all_bots = BOTS + [
        bot for bot in st.session_state.user_bots
        if bot.get("status", "draft") == "published" or
           bot.get("creator", "") == st.session_state.profile_data.get("username", "")
    ]

    # Filter bots
    filtered_bots = [
        bot for bot in all_bots
        if not search_query or
           (search_query.lower() in bot["name"].lower() or
            search_query.lower() in bot["desc"].lower() or
            any(search_query.lower() in tag.lower() for tag in bot["tags"]))
    ]

    # Custom CSS to make the grid full-width
    st.markdown("""
    <style>
        .full-width-grid {
            width: 100%;
            margin-left: -1rem;
            margin-right: -1rem;
            padding: 0 1rem;
        }
        .bot-card {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 1rem;
            height: 180px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            background: white;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }
        .bot-card h3 {
            margin: 8px 0;
            font-size: 1.1rem;
        }
        .bot-card p {
            margin: 0;
            font-size: 0.85rem;
            color: #555;
        }
        .bot-emoji {
            font-size: 2.2rem;
            margin-bottom: 8px;
        }
    </style>
    """, unsafe_allow_html=True)

    # Create full-width container for the grid
    st.markdown('<div class="full-width-grid">', unsafe_allow_html=True)

    # Create columns for the grid (5 columns)
    cols = st.columns(3)

    for i, bot in enumerate(filtered_bots):
        with cols[i % 3]:
            with st.container():
                st.markdown(f"""
                <div class="bot-card">
                    <div class="bot-emoji">{bot['emoji']}</div>
                    <h3>{bot['name']}</h3>
                    <p>{bot['desc']}</p>
                </div>
                """, unsafe_allow_html=True)

                if st.button(f"Chat with {bot['name']}",
                             key=f"start_{bot['name']}",
                             use_container_width=True):
                    st.session_state.selected_bot = bot['name']
                    st.session_state.page = "chat"
                    st.rerun()

    # Close our full-width div
    st.markdown('</div>', unsafe_allow_html=True)

    # Empty state
    if search_query and not filtered_bots:
        st.warning("No bots match your search. Try different keywords.")
        if st.button("Clear search", key="clear_search"):
            st.rerun()


def profile_page():
    """Profile Page with editable fields"""
    st.markdown("### 👤 User Profile")

    # Initialize profile data in session state if not exists
    if 'profile_data' not in st.session_state:
        st.session_state.profile_data = {
            "username": "user_123",
            "display_name": "StoryLover",
            "bio": "I love chatting with AI characters!",
            "avatar": "🧙",
            "age": 30,
            "gender": "Other",
            "created_at": "2024-01-01"
        }

    # Avatar selection
    st.write("**Choose Avatar:**")
    avatar_cols = st.columns(5)
    avatars = ['👤', '👨', '👩', '🧙', '🦸']
    for i, avatar in enumerate(avatars):
        with avatar_cols[i]:
            if st.button(avatar, key=f"avatar_{i}"):
                st.session_state.profile_data["avatar"] = avatar
                st.toast(f"Avatar changed to {avatar}!", icon="👍")

    st.divider()

    # Editable fields
    with st.form(key="profile_form"):
        # Username (non-editable)
        st.write(f"**Username:** {st.session_state.profile_data['username']}")

        # Display name (editable)
        st.session_state.profile_data['display_name'] = st.text_input(
            "Display Name",
            value=st.session_state.profile_data['display_name'],
            help="This is how your name will appear to others"
        )

        # Bio (editable)
        st.session_state.profile_data['bio'] = st.text_area(
            "Bio",
            value=st.session_state.profile_data['bio'],
            height=100,
            help="Tell others about yourself"
        )

        # Age (editable)
        st.session_state.profile_data['age'] = st.number_input(
            "Age",
            min_value=1,
            max_value=120,
            value=st.session_state.profile_data['age'],
            step=1
        )

        # Gender (editable)
        st.session_state.profile_data['gender'] = st.selectbox(
            "Gender",
            ["Male", "Female", "Non-binary", "Other", "Prefer not to say"],
            index=["Male", "Female", "Non-binary", "Other", "Prefer not to say"].index(
                st.session_state.profile_data['gender']
            )
        )

        # Created at (non-editable)
        st.write(f"**Member since:** {st.session_state.profile_data['created_at']}")

        # Form buttons
        col1, col2 = st.columns(2)
        with col1:
            save_button = st.form_submit_button("💾 Save Profile")
        with col2:
            reset_button = st.form_submit_button("🔄 Reset Changes")

        if save_button:
            st.toast("Profile saved successfully!", icon="💾")
            # In a real app, you would save to database here
            st.rerun()

        if reset_button:
            # Reset to default values
            st.session_state.profile_data = {
                "username": "user_123",
                "display_name": "StoryLover",
                "bio": "I love chatting with AI characters!",
                "avatar": "🧙",
                "theme": "system",
                "age": 30,
                "gender": "Other",
                "created_at": "2024-01-01"
            }
            st.toast("Profile reset to default values!", icon="🔄")
            st.rerun()

    st.divider()

    # Current avatar preview
    st.markdown("### Your Profile Preview")
    with st.container(border=True):
        cols = st.columns([1, 3])
        with cols[0]:
            st.markdown(
                f"<div style='font-size: 3rem; text-align: center;'>{st.session_state.profile_data['avatar']}</div>",
                unsafe_allow_html=True
            )
        with cols[1]:
            st.markdown(f"**{st.session_state.profile_data['display_name']}**")
            st.caption(f"Age: {st.session_state.profile_data['age']} | {st.session_state.profile_data['gender']}")
            st.write(st.session_state.profile_data['bio'])

    # Back button (outside the form)
    if st.button("🔙 Back to Home"):
        st.session_state.page = "home"
        st.rerun()


# ===== Create Bot Page =====
def bot_setup_page():
    st.title("🧙 Character Creation")
    st.write("Choose your creation method:")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🪄 AI-Assisted Creation",
                     help="Generate a character concept with AI",
                     use_container_width=True):
            st.session_state.page = "generate_concept"
            st.rerun()

    with col2:
        if st.button("✏️ Manual Creation",
                     help="Build from scratch",
                     use_container_width=True):
            st.session_state.page = "create_bot"
            st.rerun()


def generate_concept_page():
    st.title("🪄 Generate Character Concept")

    # Concept generation form
    with st.form("concept_seed"):
        col1, col2 = st.columns(2)
        with col1:
            genre = st.selectbox(
                "Genre",
                ["Fantasy", "Sci-Fi", "Modern", "Historical", "Horror", "Mystery", "Adventure"]
            )
            role = st.selectbox(
                "Primary Role",
                ["Companion", "Mentor", "Adversary", "Guide", "Entertainer", "Assistant"]
            )

        with col2:
           # tone = st.selectbox("Overall Tone", TONE_OPTIONS)
            traits = st.multiselect("Key Traits", PERSONALITY_TRAITS, max_selections=3)

        # Additional creative options
        with st.expander("✨ Advanced Options"):
            inspiration = st.text_input(
                "Inspiration (optional)",
                placeholder="e.g., 'wise wizard', 'sassy AI assistant'"
            )
            appearance_hint = st.text_input(
                "Appearance Hint (optional)",
                placeholder="e.g., 'elderly with long beard', 'robot with glowing eyes'"
            )
            special_ability = st.text_input(
                "Special Ability (optional)",
                placeholder="e.g., 'time travel', 'mind reading'"
            )

        if st.form_submit_button("✨ Generate Concept"):
            with st.spinner("Creating your unique character..."):
                try:
                    prompt = f"""Create a detailed character profile with these specifications:

                       Genre: {genre}
                       Role: {role}
                       Key Personality Traits: {', '.join(traits)}
                       {f"Inspiration: {inspiration}" if inspiration else ""}
                       {f"Appearance Hint: {appearance_hint}" if appearance_hint else ""}
                       {f"Special Ability: {special_ability}" if special_ability else ""}

                       Format your response EXACTLY like this example:

                       === CHARACTER PROFILE ===
                       Name: Merlin
                       Emoji: 🧙
                       Description: A wise old wizard with a penchant for riddles and a mysterious past
                       Appearance: Elderly man with a long white beard, wearing flowing blue robes and a pointed hat
                       Personality:
                       - Tone: Mysterious but kind
                       - Speech Pattern: Uses old English phrases
                       - Quirks: Often speaks in rhymes, disappears in smoke when leaving
                       Sample Greeting: "Ah, traveler! What brings you to my humble abode on this fine day?"
                       Tags: fantasy, magic, mentor
                       === END PROFILE ===
                       """

                    response = StoryChatBot()._cached_llm_invoke(prompt, "Character generation")
                    st.session_state.generated_concept = parse_generated_concept(response)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to generate concept: {str(e)}")
                    st.toast("Concept generation failed", icon="⚠️")

    # Display generated concept if available
    if 'generated_concept' in st.session_state:
        concept = st.session_state.generated_concept
        st.subheader("✨ Generated Concept")

        # Display in a nice card
        with st.container(border=True):
            cols = st.columns([1, 4])
            with cols[0]:
                st.markdown(f"<div style='font-size: 3rem; text-align: center;'>{concept['emoji']}</div>",
                            unsafe_allow_html=True)
            with cols[1]:
                st.markdown(f"**{concept['name']}**")
                st.caption(concept['desc'])

            st.divider()

            # Appearance section (new)
            if 'appearance' in concept:
                st.markdown("**Appearance**")
                st.info(concept['appearance'])

            st.divider()

            # Personality section
            st.markdown("**Personality**")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"- **Tone:** {concept['personality']['tone']}")
                st.markdown(f"- **Speech Pattern:** {concept['personality']['speech_pattern']}")
            with col2:
                st.markdown("**Quirks:**")
                for quirk in concept['personality']['quirks']:
                    st.markdown(f"- {quirk}")

            # Sample greeting
            st.divider()
            st.markdown("**Sample Greeting**")
            st.info(concept['greeting'])

            # Tags
            st.markdown("**Tags:** " + ", ".join([f"`{tag}`" for tag in concept['tags']]))

        # Action buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("🔄 Generate Again", use_container_width=True):
                del st.session_state.generated_concept
                st.rerun()
        with col2:
            # When the "Use This Concept" button is clicked:
            if st.button("✅ Use This Concept", type="primary", use_container_width=True):
                st.session_state.preset_data = {
                    "name": concept["name"],
                    "emoji": concept["emoji"],
                    "desc": concept["desc"],
                    "appearance": concept.get("appearance", ""),
                    "personality": {
                        "tone": concept["personality"]["tone"],
                        "traits": concept["personality"].get("traits", []),  # Include traits
                        "speech_pattern": concept["personality"].get("speech_pattern", ""),
                        "quirks": concept["personality"].get("quirks", [])
                    },
                    "tags": concept["tags"],
                    "greeting": concept["greeting"]
                }
                st.session_state.page = "create_bot"
                st.rerun()
        with col3:
            if st.button("📋 Copy to Clipboard", use_container_width=True):
                import pyperclip
                pyperclip.copy(
                    f"{concept['name']} {concept['emoji']}\n\n{concept['desc']}\n\n"
                    f"Appearance: {concept.get('appearance', 'Not specified')}\n\n"
                    f"Personality:\n- Tone: {concept['personality']['tone']}\n"
                    f"- Speech: {concept['personality']['speech_pattern']}\n"
                    f"- Quirks: {', '.join(concept['personality']['quirks'])}\n\n"
                    f"Tags: {', '.join(concept['tags'])}"
                )
                st.toast("Copied to clipboard!", icon="📋")

    if st.button("← Back"):
        st.session_state.page = "bot_setup"
        st.rerun()

def parse_generated_concept(response):
    """Parse LLM response into structured format with error handling"""
    try:
        # Extract sections from the response
        name = emoji = desc = greeting = appearance = ""
        tone = speech_pattern = ""
        quirks = []
        tags = []
        traits = []  # Initialize traits list

        # Try to parse the structured format
        if "=== CHARACTER PROFILE ===" in response:
            parts = response.split("=== CHARACTER PROFILE ===")[1].split("=== END PROFILE ===")[0]
            lines = [line.strip() for line in parts.split("\n") if line.strip()]

            current_section = None
            for line in lines:
                if line.startswith("Name:"):
                    name = line.split("Name:")[1].strip()
                elif line.startswith("Emoji:"):
                    emoji = line.split("Emoji:")[1].strip()
                elif line.startswith("Description:"):
                    desc = line.split("Description:")[1].strip()
                elif line.startswith("Appearance:"):
                    appearance = line.split("Appearance:")[1].strip()
                elif line.startswith("Sample Greeting:"):
                    greeting = line.split("Sample Greeting:")[1].strip().strip('"')
                elif line.startswith("Tags:"):
                    tags = [tag.strip() for tag in line.split("Tags:")[1].split(",")]
                elif line.startswith("- Tone:"):
                    tone = line.split("- Tone:")[1].strip()
                    # Map tone to traits
                    tone_lower = tone.lower()
                    if 'sarcast' in tone_lower:
                        traits.append("Sarcastic")
                    if 'wit' in tone_lower or 'humor' in tone_lower:
                        traits.append("Witty")
                    if 'friendly' in tone_lower:
                        traits.append("Friendly")
                    if 'mysterious' in tone_lower:
                        traits.append("Mysterious")
                    if 'wise' in tone_lower:
                        traits.append("Wise")
                elif line.startswith("- Speech Pattern:"):
                    speech_pattern = line.split("- Speech Pattern:")[1].strip()
                elif line.startswith("- Quirks:"):
                    quirks.append(line.split("- Quirks:")[1].strip())
                elif line.startswith("- ") and ":" not in line:
                    quirks.append(line[2:].strip())
                elif line.startswith("- ") and "Trait" in line:
                    # Handle traits if explicitly listed
                    trait = line.split("- Trait:")[1].strip() if "Trait:" in line else line[2:].strip()
                    if trait in PERSONALITY_TRAITS:
                        traits.append(trait)

        # Ensure we have at least some personality traits
        if not traits:
            # Fallback based on tone
            if tone:
                if 'friendly' in tone.lower():
                    traits.append("Friendly")
                if 'professional' in tone.lower():
                    traits.append("Professional")
                if 'humorous' in tone.lower():
                    traits.append("Humorous")
            else:
                traits = ["Friendly"]  # Default fallback

        return {
            "name": name,
            "emoji": emoji,
            "desc": desc,
            "appearance": appearance,
            "personality": {
                "tone": tone,
                "traits": traits,  # Include the traits list
                "speech_pattern": speech_pattern,
                "quirks": quirks
            },
            "greeting": greeting,
            "tags": tags
        }

    except Exception as e:
        st.error(f"Error parsing generated concept: {str(e)}")
        # Return a default concept if parsing fails
        return {
            "name": "Mystery Character",
            "emoji": "🕵️",
            "desc": "A fascinating character with hidden depths",
            "appearance": "A mysterious figure whose features are hard to discern",
            "personality": {
                "tone": "Mysterious",
                "traits": ["Mysterious", "Wise"],  # Default traits
                "speech_pattern": "Cryptic hints",
                "quirks": ["Leaves riddles", "Disappears unexpectedly"]
            },
            "greeting": "Ah, you've found me... what shall we discuss?",
            "tags": ["mystery"]
        }


def create_bot_page():
    st.title("🤖 Create Your Own Chat Bot")

    # Initialize session state variables
    _init_bot_creation_session()

    # Show preset options
    _display_preset_options()

    # Main creation form
    with st.form(key="main_bot_form"):
        form_data = _display_creation_form()
        submitted = st.form_submit_button("✨ Create Character")

        if submitted:
            _handle_form_submission(form_data)

    # Tag addition form (outside main form)
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

    # Cancel button (outside both forms)
    if st.button("❌ Cancel"):
        if 'preset_data' in st.session_state:
            del st.session_state.preset_data
        st.session_state.page = "my_bots"
        st.rerun()


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


def _display_creation_form():
    """Display the main bot creation form and return collected data"""
    form_data = {
        "basic": {},
        "appearance": {},
        "personality": {},
        "tags": []
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
    with st.expander("⚙️ Advanced Options (Coming Soon)"):
        st.write("Future features:")
        st.selectbox("Voice Style", ["Default", "Friendly", "Professional"], disabled=True)
        st.multiselect("Emotional Range", ["Happy", "Sad", "Angry", "Excited"], disabled=True)

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


def _handle_form_submission(form_data):
    """Handle form submission and bot creation"""
    if not form_data["basic"]["name"]:
        st.error("Please give your bot a name")
    elif len(form_data["basic"]["emoji"]) > 2:
        st.error("Emoji should be 1-2 characters max")
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
            "appearance": {
                "description": form_data["appearance"]["description"],
            },
            "custom": True,
            "creator": st.session_state.profile_data.get("username", "anonymous")  # Track creator
        }

        # Handle uploaded file if exists
        if form_data["appearance"].get("uploaded_file"):
            new_bot["appearance"]["avatar"] = _handle_uploaded_file(
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

def _handle_uploaded_file(uploaded_file, bot_name):
    """Handle avatar file upload"""
    # In a real app, you would save this file and return the path
    return {
        "filename": uploaded_file.name,
        "content_type": uploaded_file.type,
        "size": uploaded_file.size
    }


# ===== My Bots Page (Refactored) =====
def my_bots_page():
    """Main entry point for the My Bots page"""
    st.title("🌟 My Custom Bots")

    if not st.session_state.user_bots:
        _show_empty_state()
        return

    filtered_bots = _filter_bots_by_status()

    if not filtered_bots:
        st.info(f"No bots match the filter: {st.session_state.get('bot_status_filter', 'All')}")
        return

    _display_bots_grid(filtered_bots)

    if st.button("➕ Create Another Bot"):
        st.session_state.page = "bot_setup"
        st.rerun()


def _show_empty_state():
    """Show empty state when user has no bots"""
    st.info("You haven't created any bots yet.")
    if st.button("Create Your First Bot"):
        st.session_state.page = "bot_setup"
        st.rerun()


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


def _display_bots_grid(bots):
    """Display bots in a responsive grid layout"""
    cols = st.columns(2)

    for i, bot in enumerate(bots):
        with cols[i % 2]:
            _display_bot_card(bot, i)


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
                    _update_bot_status(bot["name"], "published")
            else:
                if st.button("📦 Unpub", key=f"unpublish_{unique_key_suffix}"):
                    _update_bot_status(bot["name"], "draft")

            # Gear icon positioned at the end
            st.markdown('<div class="btn-popover">', unsafe_allow_html=True)
            with st.popover("⚙️"):
                if st.button("🗑️ Delete", key=f"delete_{unique_key_suffix}"):
                    _delete_bot(bot["name"])
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)  # Close btn-row
            st.markdown('</div>', unsafe_allow_html=True)  # Close bot-card

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


def _display_bot_header(bot):
    """Display the bot's emoji and name"""
    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        st.markdown(f"<div style='text-align: center; font-size: 2rem;'>{bot['emoji']}</div>",
                    unsafe_allow_html=True)
        st.markdown(f"<h3 style='text-align: center;'>{bot['name']}</h3>",
                    unsafe_allow_html=True)


def _display_bot_description(bot):
    """Display the bot's description"""
    st.caption(bot['desc'])


def _display_bot_tags(bot):
    """Display the bot's tags if they exist"""
    if bot.get('tags'):
        for tag in bot['tags']:
            st.markdown(f'<div class="bot-tag" title="{tag}">{tag}</div>',
                        unsafe_allow_html=True)


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
            _update_bot_status(bot["name"], "published")
    else:
        if st.button("📦 Unpublish", key=f"unpublish_{unique_key_suffix}"):
            _update_bot_status(bot["name"], "draft")

    st.markdown('</div>', unsafe_allow_html=True)

    # More options dropdown
    with st.popover("⚙️", help="More options"):
        if st.button("🗑️ Delete Bot", key=f"delete_{unique_key_suffix}"):
            _delete_bot(bot["name"])

def _update_bot_status(bot_name, new_status):
    """Update a bot's status in the user_bots list"""
    for i, b in enumerate(st.session_state.user_bots):
        if b["name"] == bot_name:
            st.session_state.user_bots[i]["status"] = new_status
            st.toast(f"{bot_name} {'published' if new_status == 'published' else 'unpublished'}!",
                     icon="🚀" if new_status == "published" else "📦")
            st.rerun()


def _delete_bot(bot_name):
    """Delete a bot from the user_bots list"""
    st.session_state.user_bots = [
        b for b in st.session_state.user_bots if b["name"] != bot_name
    ]
    st.rerun()


def edit_bot_page():
    if 'editing_bot' not in st.session_state:
        st.error("No bot selected for editing")
        st.session_state.page = "my_bots"
        st.rerun()

    bot = st.session_state.editing_bot
    st.title(f"✏️ Editing {bot['name']}")

    # Initialize custom tags in session state if not exists
    if 'custom_tags' not in st.session_state:
        st.session_state.custom_tags = []

    # Combine standard and custom tags
    all_tag_options = TAG_OPTIONS + st.session_state.custom_tags

    # Main form for bot editing
    with st.form(key="edit_bot_form"):
        # Basic Info
        st.subheader("Basic Information")
        col1, col2 = st.columns([1, 3])
        with col1:
            emoji = st.text_input("Emoji",
                                  value=bot['emoji'],
                                  help="Choose an emoji to represent your bot")
        with col2:
            name = st.text_input("Bot Name",
                                 value=bot['name'],
                                 help="Give your bot a unique name")

        # Appearance Section
        st.subheader("Appearance")
        appearance_desc = st.text_area(
            "Physical Description",
            value=bot.get('appearance', {}).get('description', ''),
            height=100,
            help="Describe your character's physical appearance"
        )

        # Background Section
        st.subheader("Background")
        description = st.text_area(
            "Character Description",
            value=bot['desc'],
            height=150,
            help="Tell us about your character's personality and background"
        )

        # Personality Section
        st.subheader("Personality")

        # Personality traits multiselect
        traits = st.multiselect(
            "Key Personality Traits",
            PERSONALITY_TRAITS,
            default=[t for t in bot['personality'].get('traits', []) if t in PERSONALITY_TRAITS],
            help="Select traits that define your character's personality"
        )

        # Greeting Message
        st.subheader("Greeting")
        greeting = st.text_area(
            "Introduction Message",
            value=bot['personality'].get('greeting', ''),
            height=100,
            help="How your character introduces itself"
        )

        # Tags Section
        st.subheader("Tags")
        # Current tags with validation
        current_tags = [t for t in bot['tags'] if t in all_tag_options]
        tags = st.multiselect(
            "Select Tags",
            all_tag_options,
            default=current_tags
        )

        # Status selection
        st.subheader("Status")
        status = st.radio(
            "Bot Status",
            ["Draft", "Published"],
            index=0 if bot.get("status", "draft") == "draft" else 1,
            horizontal=True,
            help="Draft: Only visible to you | Published: Visible to all users"
        )

        # Form submission button
        submitted = st.form_submit_button("💾 Save Changes")

    # Separate form for tag addition
    with st.container(border=True):
        st.subheader("Add New Tag")
        tag_cols = st.columns([4, 1])
        with tag_cols[0]:
            new_custom_tag = st.text_input(
                "Custom Tag Name",
                placeholder="Type new tag name",
                label_visibility="collapsed"
            )
        with tag_cols[1]:
            if st.button(
                    "Add",
                    disabled=not new_custom_tag or new_custom_tag in all_tag_options
            ):
                if new_custom_tag and new_custom_tag not in st.session_state.custom_tags:
                    st.session_state.custom_tags.append(new_custom_tag)
                    st.rerun()

    # Handle main form submission
    if submitted:
        if not name:
            st.error("Please give your bot a name")
        else:
            # Update the bot in user_bots
            updated_bot = {
                "name": name,
                "emoji": emoji,
                "desc": description,
                "status": status.lower(),
                "appearance": {
                    "description": appearance_desc,
                    "avatar": bot.get('appearance', {}).get('avatar')
                },
                "tags": tags + ([new_custom_tag] if new_custom_tag and new_custom_tag not in tags else []),
                "personality": {
                    "traits": traits,
                    "greeting": greeting
                },
                "custom": True,
                "creator": bot.get("creator", st.session_state.profile_data.get("username", "anonymous"))
            }

            # Find and replace the bot in user_bots
            for i, b in enumerate(st.session_state.user_bots):
                if b['name'] == bot['name']:
                    st.session_state.user_bots[i] = updated_bot
                    break

            st.success(f"Bot '{name}' updated successfully!")
            st.session_state.page = "my_bots"
            st.rerun()

    # Cancel button
    if st.button("❌ Cancel"):
        st.session_state.page = "my_bots"
        st.rerun()

# Audio storage configuration
AUDIO_BASE_DIR = r"C:\Users\YOURPATH\Audio"
DEFAULT_BOT_DIR = os.path.join(AUDIO_BASE_DIR, "DefaultBot")
os.makedirs(DEFAULT_BOT_DIR, exist_ok=True)

def get_audio_path(voice_name: str, emotion: str = None) -> str:
    """Generate consistent audio file paths"""
    filename = f"{voice_name.lower()}"
    if emotion:
        filename += f"_{emotion.lower()}"
    filename += ".wav"
    return os.path.join(DEFAULT_BOT_DIR, filename)

def voice_page():
    st.title("🎙️ Voice Selection")
    # Initialize TTS with error handling
    tts = None
    tts_available = False

    try:
        # Try to initialize with a simpler model first
        with st.spinner("Loading voice engine..."):
            tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False)
            tts_available = True
    except Exception as e:
        st.warning(f"⚠️ Could not initialize TTS: {str(e)}")
        st.info("Voice previews will not be available, but you can still select voices.")

    # Define the path to your audio file
    STORYTELLER_AUDIO_PATH = "Audio/Storyteller_Audio.wav"  # Relative path from your script

    # Voice options with emotional variants
    VOICE_OPTIONS = {
        "Friendly": {
            "description": "Warm and approachable tone",
            "sample": "Hey...I'm very shy",
            "speaker_idx": 5,  # VITS speaker ID
            "icon": "😊",
            "color": "#4CAF50"
        },
        "Professional": {
            "description": "Clear and articulate delivery",
            "samples": {
                "default": "The quarterly report shows a 12% increase.",
                "serious": "<speak><prosody rate='slow' pitch='low'>This matter requires immediate attention.</prosody></speak>",
                "confident": "<speak><prosody rate='medium' pitch='medium'>I'm certain we can meet our targets.</prosody></speak>"
            },
            "speaker_idx": 10,
            "icon": "💼",
            "color": "#2196F3"
        },
        "Storyteller": {
            "description": "Expressive and dramatic",
            "samples": {
                "default": "Once upon a time, in a land far away...",
                "mysterious": "<speak><prosody rate='slow' pitch='low'>Something lurked in the shadows...</prosody></speak>",
                "excited": "<speak><prosody rate='fast' pitch='high'>And then the dragon appeared!</prosody></speak>"
            },
            "speaker_idx": 15,
            "icon": "📖",
            "color": "#9C27B0"
        },
        "Robotic": {
            "description": "Futuristic digital voice",
            "samples": {
                "default": "Beep boop. Systems operational.",
                "alert": "<speak><prosody rate='fast' pitch='high'>Warning! Warning!</prosody></speak>",
                "mechanical": "<speak><prosody rate='slow' pitch='low'>Processing.complete.</prosody></speak>"
            },
            "speaker_idx": 20,
            "icon": "🤖",
            "color": "#607D8B"
        }
    }

    # CSS (same as before)
    st.markdown("""
        <style>
            /* Your existing CSS styles */
            .emotion-btn {
                margin: 0.2rem;
                padding: 0.3rem 0.5rem;
                font-size: 0.8rem;
            }
        </style>
        """, unsafe_allow_html=True)

    # CSS for voice cards (same as before)
    st.markdown("""
       <style>
           .voice-card {
               border: 1px solid #e0e0e0;
               border-radius: 8px;
               padding: 1rem;
               margin-bottom: 1rem;
               background: white;
           }
           .voice-header {
               display: flex;
               align-items: center;
               gap: 10px;
               margin-bottom: 0.5rem;
           }
           .voice-name {
               font-weight: bold;
               font-size: 1.1rem;
               color: #333;
           }
           .voice-desc {
               color: #555;
               margin-bottom: 0.5rem;
           }
           .voice-preview {
               margin-top: 0.5rem;
               border-left: 3px solid #7B1FA2;
               padding-left: 1rem;
           }
           audio {
               width: 100%;
               margin-top: 0.5rem;
           }
           .audio-container {
               background: #f5f5f5;
               padding: 1rem;
               border-radius: 8px;
               margin: 0.5rem 0;
           }
           .selected-badge {
               color: #4CAF50;
               font-weight: bold;
               margin-left: auto;
           }
       </style>
       """, unsafe_allow_html=True)

    # Create audio directory if it doesn't exist
    os.makedirs(DEFAULT_BOT_DIR, exist_ok=True)
    selected_voice = st.session_state.get("selected_voice", "Friendly")

    for voice_name, voice_data in VOICE_OPTIONS.items():
        with st.container():
            # Voice display
            st.markdown(f"""
                   <div style="color:{voice_data['color']}; font-size:1.2rem;">
                       {voice_data['icon']} {voice_name}
                   </div>
                   <div style="color:#555; margin-bottom:0.5rem;">
                       {voice_data['description']}
                   </div>
               """, unsafe_allow_html=True)

            # Preview button
            if st.button(
                    "▶️ Preview",
                    key=f"preview_{voice_name}",
                    disabled=not tts_available,
                    help="Preview voice (requires TTS)" if tts_available else "TTS not available"
            ):
                try:
                    audio_path = os.path.join(DEFAULT_BOT_DIR, f"{voice_name}.wav")

                    # Generate the audio file
                    with st.spinner("Generating voice preview..."):
                        tts.tts_to_file(
                            text=voice_data["sample"],
                            file_path=audio_path
                        )

                    # Play the audio
                    st.audio(audio_path, format='audio/wav')

                except Exception as e:
                    st.error(f"Failed to generate preview: {str(e)}")
                    st.error(f"Debug info - Model: {tts.model_name}, Sample: {voice_data['sample']}")

            # Select button
            if st.button(
                    "✅ Select" if voice_name != selected_voice else "✓ Selected",
                    key=f"select_{voice_name}",
                    disabled=voice_name == selected_voice
            ):
                st.session_state.selected_voice = voice_name
                st.toast(f"{voice_name} voice selected!", icon="🎙️")
                st.rerun()

            st.divider()

    # Troubleshooting section
    with st.expander("ℹ️ Troubleshooting"):
        st.write("If voice previews aren't working:")
        st.write("1. Make sure you have a stable internet connection")
        st.write("2. Models will download automatically on first use")
        st.write("3. Try refreshing the page if previews fail")

        if st.button("🔄 Retry TTS Initialization"):
            st.rerun()

    if st.button("🔙 Back"):
        st.session_state.page = "home"
        st.rerun()


def display_chat_list():
    """Display the list of chat histories in the sidebar"""
    st.subheader("Your Chats")

    # Initialize chat histories if not exists
    if 'chat_histories' not in st.session_state:
        st.session_state.chat_histories = {}

    # Display all chats with delete option
    for bot_name in list(st.session_state.chat_histories.keys()):
        # Search in both default BOTS and user_bots
        bot = next((b for b in BOTS + st.session_state.user_bots if b["name"] == bot_name), None)
        emoji = bot["emoji"] if bot else "🤖"  # Default to robot emoji

        cols = st.columns([1, 4, 1])
        with cols[0]:
            st.write(emoji)
        with cols[1]:
            if st.button(bot_name, key=f"select_{bot_name}"):
                st.session_state.selected_bot = bot_name
                st.session_state.page = "chat"
                st.rerun()
        with cols[2]:
            if st.button("🗑️", key=f"delete_{bot_name}"):
                # Check if we're deleting the currently viewed chat
                if st.session_state.get('selected_bot') == bot_name:
                    # Clear the current chat selection
                    st.session_state.selected_bot = None
                    # Go back to home page
                    st.session_state.page = "home"

                # Delete the chat history
                del st.session_state.chat_histories[bot_name]
                st.rerun()

def create_sidebar():
    with st.sidebar:
        st.header("📚 StoryBot")

        # Navigation buttons - now using PAGES constant
        nav_cols = st.columns(2)
        with nav_cols[0]:
            if st.button(PAGES["home"], use_container_width=True, key="nav_home"):
                st.session_state.page = "home"
                st.rerun()
        with nav_cols[1]:
            if st.button(PAGES["profile"], use_container_width=True, key="nav_profile"):
                st.session_state.page = "profile"
                st.rerun()

        # Additional navigation items
        if st.button(PAGES["my_bots"], use_container_width=True, key="nav_my_bots"):
            st.session_state.page = "my_bots"
            st.rerun()

        if st.button(PAGES["voice"], use_container_width=True, key="nav_voice"):  # New
            st.session_state.page = "voice"
            st.rerun()

        st.divider()
        # Call the extracted chat list method
        display_chat_list()


def chat_page(bot_name):
    """Chat page with the selected bot"""
    bot = StoryChatBot()

    # Get the bot's details from either BOTS or user_bots
    current_bot = next(
        (b for b in BOTS + st.session_state.user_bots if b["name"] == bot_name),
        None
    )
    bot_emoji = current_bot["emoji"] if current_bot else "🤖"

    # Initialize chat history for this bot if not exists
    if bot_name not in st.session_state.chat_histories:
        st.session_state.chat_histories[bot_name] = []
        st.session_state.greeting_sent = False

    # Get current chat history
    chat_history = st.session_state.chat_histories[bot_name]

    # Display messages
    for role, message in chat_history:
        avatar = bot_emoji if role == "assistant" else None
        with st.chat_message(role, avatar=avatar):
            st.write(message)

    # Send greeting if first time
    if not st.session_state.greeting_sent or not chat_history:
        # Use the predefined greeting if available, otherwise generate one
        greeting = current_bot["personality"].get("greeting", "") if current_bot else ""
        if not greeting:
            greeting = bot.generate_greeting()

        chat_history.append(("assistant", greeting))
        st.session_state.greeting_sent = True
        st.rerun()


    # Add the icon toolbar at the bottom of the chat
    create_icon_toolbar(bot)

    # User input handling
    if prompt := st.chat_input("Type your message..."):
        chat_history.append(("user", prompt))

        with st.spinner(f"{bot_name} is thinking..."):
            # Uses the new memory-aware method
            response = bot.generate_response(prompt)
            chat_history.append(("assistant", response))
            st.rerun()


def create_icon_toolbar(bot):
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
                                new_response = bot.generate_response(last_user_msg)

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


def main():
    # Apply custom CSS at the very start
    st.markdown("""
      <style>
          /* Card container */
          .bot-card {
              border: 1px solid #444;
              border-radius: 10px;
              padding: 1.2rem;
              height: 280px;
              display: flex;
              flex-direction: column;
              margin-bottom: 1.5rem;
              background: #1e1e1e;  /* Dark card background */
              box-shadow: 0 2px 12px rgba(0,0,0,0.3);
              transition: all 0.2s;
          }
          .bot-card:hover {
              transform: translateY(-3px);
              box-shadow: 0 6px 16px rgba(0,0,0,0.4);
              border-color: #555;
          }

          /* Bot header */
          .bot-emoji {
              font-size: 2.4rem;
              text-align: center;
              margin-bottom: 0.5rem;
              filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
          }
          .bot-name {
              font-weight: 600;
              font-size: 1.3rem;
              text-align: center;
              margin-bottom: 0.8rem;
              color: #f0f0f0;
              text-shadow: 0 1px 2px rgba(0,0,0,0.3);
          }

          /* Description */
          .bot-desc {
              color: #bbb;
              font-size: 0.95rem;
              flex-grow: 1;
              margin-bottom: 1rem;
              line-height: 1.5;
              overflow-y: auto;
              padding-right: 0.8rem;
              scrollbar-width: thin;
              scrollbar-color: #555 #333;
          }
          .bot-desc::-webkit-scrollbar {
              width: 6px;
          }
          .bot-desc::-webkit-scrollbar-thumb {
              background-color: #555;
              border-radius: 3px;
          }
          .bot-desc::-webkit-scrollbar-track {
              background-color: #333;
          }

          /* Tags */
          .bot-tags {
              display: flex;
              flex-wrap: wrap;
              gap: 0.5rem;
              margin-bottom: 1.2rem;
              justify-content: center;
          }
          .bot-tag {
              background: #2a3b4d;
              color: #7fbbde;
              padding: 0.3rem 0.8rem;
              border-radius: 1rem;
              font-size: 0.85rem;
              border: 1px solid #3a4b5d;
              white-space: nowrap;
              box-shadow: 0 1px 2px rgba(0,0,0,0.2);
          }

          /* Buttons */
          .bot-actions {
              display: flex;
              justify-content: center;
              gap: 0.8rem;
              margin-top: auto;
          }
          .bot-btn {
              border: none;
              border-radius: 8px;
              padding: 0.4rem 0.9rem;
              font-size: 0.95rem;
              cursor: pointer;
              transition: all 0.2s;
              box-shadow: 0 2px 4px rgba(0,0,0,0.2);
              display: flex;
              align-items: center;
              justify-content: center;
              min-width: 80px;
          }
          .bot-btn-edit {
              background: #3a4b5d;
              color: #f0f0f0;
          }
          .bot-btn-edit:hover {
              background: #4a5b6d;
              transform: translateY(-1px);
          }
          .bot-btn-chat {
              background: #f63366;
              color: white;
          }
          .bot-btn-chat:hover {
              background: #ff4275;
              transform: translateY(-1px);
          }
          .bot-btn-delete {
              background: #ff4b4b;
              color: white;
          }
          .bot-btn-delete:hover {
              background: #ff5a5a;
              transform: translateY(-1px);
          }

          /* Create Another Bot button */
          .stButton>button {
              border-radius: 8px !important;
              padding: 0.6rem 1.2rem !important;
              font-size: 1rem !important;
              background: linear-gradient(135deg, #6e48aa, #9d50bb) !important;
              color: white !important;
              border: none !important;
              box-shadow: 0 3px 6px rgba(0,0,0,0.2) !important;
              transition: all 0.2s !important;
          }
          .stButton>button:hover {
              transform: translateY(-2px) !important;
              box-shadow: 0 5px 10px rgba(0,0,0,0.3) !important;
          }
      </style>
      """, unsafe_allow_html=True)
    # Initialize all session state variables
    if 'page' not in st.session_state:
        st.session_state.page = "home"
    if 'selected_bot' not in st.session_state:
        st.session_state.selected_bot = None
    if 'greeting_sent' not in st.session_state:
        st.session_state.greeting_sent = False

    # Create sidebar once
    create_sidebar()

    # Page routing - all at same indentation level
    if st.session_state.page == "home":
        home_page()
    elif st.session_state.page == "profile":
        profile_page()
    elif st.session_state.page == "chat":
        chat_page(st.session_state.selected_bot)
    elif st.session_state.page == "bot_setup":
        bot_setup_page()
    elif st.session_state.page == "generate_concept":
        generate_concept_page()
    elif st.session_state.page == "create_bot":
        create_bot_page()
    elif st.session_state.page == "my_bots":
        my_bots_page()
    elif st.session_state.page == "edit_bot":
        edit_bot_page()
    elif st.session_state.page == "voice":
        voice_page()
    else:
        st.warning("Please select a page")
        home_page()

if __name__ == "__main__":
    main()