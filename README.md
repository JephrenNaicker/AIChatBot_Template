
# FluffyAI - Interactive Chatbot Platform

![Demo Screenshot](assets/demo.png) <!-- Add a screenshot later -->

## Features ✨
- 🧩 Multiple pre-built bot personalities (Storyteller, Sci-Fi, Mystery, etc.)
- 🛠️ Create custom bots with unique personalities
- 🎙️ Text-to-speech voice customization
- 👥 Group chat with multiple bots
- 💾 Save and manage your chat histories

## Installation ⚙️

1. Clone the repository:
```bash
git clone https://github.com/yourusername/FluffyAi.git
cd FluffyAi
Set up virtual environment:

bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.\.venv\Scripts\activate  # Windows
Install dependencies:

bash
pip install -r requirements.txt
Run the app:

bash
streamlit run main.py
Project Structure 🗂️
fluffy_app/
├── __init__.py
├── main.py               # Entry point (contains the main() function)
├── config.py             # Constants and configurations
├── models/               # Data models/schemas
│   ├── __init__.py
│   ├── bot.py           # Bot data structure
│   └── profile.py       # Profile data structure
├── controllers/          # Business logic
│   ├── __init__.py
│   ├── chat_controller.py          
│   ├── bot_manager_controller.py  
│   ├── group_chat_controller.py 
│   └── voice_controller.py
├── services/            # Utility classes
│   ├── __init__.py
│   ├── Image_Service.py #avatar Image Upload
│   ├── utils.py         # Utils class
├── views/               # UI/presentation layer
│   ├── __init__.py
│   ├── pages/           # Page components
│   ├── home.py
│   ├── profile.py
│   ├── chat.py
│   ├── bot_setup.py
│   ├── create_bot.py
│   ├── edit_bot.py
│   ├── generate_concept.py
│   ├── my_bots.py
│   ├── profile.py
│   ├── voice.py
│   └── group_chat.py
├── components/      # Reusable components
│   ├── bot_card.py  #functionality and CSS for all bot cards
│   ├── bot_card_home.py   # main gallery page
│   ├── bot_card_manage.py #"My Bots" management page
│   ├── audio_player.py
│   ├── sidebar.py
│   ├── avatar_utils.py
│   └── chat_toolbar.py
└── tests/               # Uni
Requirements 📋
Python 3.8+
#limits

--Key words not working
-- add a overlay bg for the chats
Add a scenario section:
Image location thing, and the mood thing 

1. The "Location-Based" Model (Simple & Logical)
Instead of being tied to a number of messages, the background changes when the conversation logically moves to a new place.

How it works: The AI bot is responsible for narrating location changes within the chat itself (e.g., "Let's step out into the garden," or "The portal swirls, and you find yourself in a dusty library.").

The Trigger: Your chat_controller watches the bot's messages for key phrases or you explicitly add a command (e.g., [SETTING: ancient ruins]) that the controller can parse.

Why it's cool: It puts narrative control in the hands of the AI (or the user, if they type the command), making the background change feel like an organic part of the story. It's very intuitive.

2. The "Mood-Based" Model (Atmospheric & Subtle)
The background reflects the emotional tone of the conversation.

How it works: You analyze the conversation for sentiment. Is it tense, romantic, joyful, melancholic?

The Trigger: After each message (or every few messages), a lightweight sentiment analysis model/function assigns a "mood" score. A significant shift in mood triggers a regeneration.

Prompting: The prompt becomes less about objects and more about style and color: "digital art of a melancholic, rainy cityscape at dusk, blue tones, cinematic, moody."

Why it's cool: It creates a powerful, subconscious emotional feedback loop. The user feels the tone shift not just in the text, but in the entire environment of the app.



Streamlit

Ollama

TTS library

Contributing 🤝
Fork the project

Create your feature branch (git checkout -b feature/AmazingFeature)

Commit your changes (git commit -m 'Add some amazing feature')

Push to the branch (git push origin feature/AmazingFeature)

Open a Pull Request

License 📄
MIT License - see LICENSE for details


## Key Fixes Summary

1. **Import Resolution**:
   - Ensure your root folder is in Python path
   - Use either absolute imports (`FluffyAi.bots.default_bots`) or path modification
   - Verify `__init__.py` exists in all subdirectories

2. **READEME Best Practices**:
   - Clear installation instructions
   - Visual project structure
   - Contribution guidelines
   - License information

3. **Next Steps**:
   - Add a `requirements.txt` with:
streamlit
ollama
TTS
Pillow

add the pause at the end done
have an Avter in the background chat, add manybe have about 4 emotial image that can switch.