import streamlit as st
from config import PERSONALITY_TRAITS
from controllers.chat_controller import LLMChatController
from services.utils import Utils

async def generate_concept_page():

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
                          System Rules: thoughts appear in italics format and Dialogue in "quotes"
                          Sample Greeting: *This traveler seems trustworthy, but I should test their intentions first.* "Ah, traveler! What brings you to my humble abode on this fine day?" 
                          Tags: fantasy, magic, mentor
                          === END PROFILE ===
                          """

                    response = LLMChatController()._cached_llm_invoke(prompt, "Character generation")
                    st.session_state.generated_concept = Utils.parse_generated_concept(response)
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
