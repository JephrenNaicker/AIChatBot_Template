# CONSTANTS
PAGES = {
    "home": "🏠 Home",
    "profile": "👤 Profile",
    "my_bots": "🌟 My Bots",
    "voice": "🎙️ Voice",
    "image_studio": "🎨 Image Studio",
    "bot_setup": "🧙 Character Setup",
    "generate_concept": "🪄 Generate Concept",
    "group_chat": "👥 Group Chat"
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
]  # Bots list here

PERSONALITY_TRAITS = [
    "Creative", "Logical", "Adventurous", "Cautious",
    "Empathetic", "Optimistic", "Pessimistic",
    "Sarcastic", "Witty", "Humorous", "Serious",
    "Whimsical", "Enthusiastic", "Calm", "Blunt",
    "Philosophical", "Dramatic", "Mysterious","Friendly"
]

TAG_OPTIONS = [
    "storytelling", "education", "tech", "gaming",
    "productivity", "health", "music", "art","voice"
]

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

AUDIO_BASE_DIR = "/FluffyAi/Audio"
DEFAULT_BOT_DIR = "default_bot"  # Modified to be relative path
# Default template with placeholders
DEFAULT_RULES = """(Analyzes the user's tone and context carefully)
- Thoughts appear in italics format
- Dialogue in double quotes like "this"
- Dont Speak for the User
        """

IMAGE_STUDIO_CONFIG = {
    "default_negative_prompt": "ugly, tiling, poorly drawn hands, poorly drawn feet, poorly drawn face, out of frame,extra limbs, disfigured, deformed, body out of frame, bad anatomy, watermark, grain, signature, cut off, draft",
    "default_api_url": "http://127.0.0.1:7860"
}