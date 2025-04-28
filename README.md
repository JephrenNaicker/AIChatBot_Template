# AIChatBot_Template
AI Chat-Bot Template


pip install -r requirements.txt

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
FluffyAi/
├── main.py                 # Entry point
├── bots/                   # Bot definitions and logic
├── pages/                  # Streamlit pages
├── components/             # Reusable UI components
├── config/                 # Configuration files
├── utils/                  # Utility functions
└── assets/                 # Images and static files
Requirements 📋
Python 3.8+

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