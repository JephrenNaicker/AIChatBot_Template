from PIL import Image, ImageDraw
import streamlit as st
from config import PERSONALITY_TRAITS


class Utils:
    @staticmethod
    def create_placeholder_avatar(emoji="👑", bg_color=(73, 109, 137), text_color=(255, 255, 0)):
        """
        Create a placeholder avatar image with an emoji

        Args:
            emoji (str): The emoji to display
            bg_color (tuple): RGB background color
            text_color (tuple): RGB text color

        Returns:
            PIL.Image: Generated avatar image
        """
        img = Image.new('RGB', (100, 100), color=bg_color)
        d = ImageDraw.Draw(img)
        d.text((50, 50), emoji, fill=text_color, anchor="mm")
        return img

    @staticmethod
    def parse_generated_concept(response):
        """
        Parse LLM response into structured character concept format with error handling

        Args:
            response (str): Raw LLM response text

        Returns:
            dict: Structured character concept with fallback values if parsing fails
        """
        try:
            # Initialize all fields with empty defaults
            concept = {
                "name": "",
                "emoji": "",
                "desc": "",
                "appearance": "",
                "personality": {
                    "tone": "",
                    "traits": [],
                    "speech_pattern": "",
                    "quirks": []
                },
                "greeting": "",
                "tags": []
            }

            if not response:
                raise ValueError("Empty response provided")

            # Try to parse the structured format
            if "=== CHARACTER PROFILE ===" in response:
                parts = response.split("=== CHARACTER PROFILE ===")[1].split("=== END PROFILE ===")[0]
                lines = [line.strip() for line in parts.split("\n") if line.strip()]

                for line in lines:
                    # Parse each line based on its prefix
                    if line.startswith("Name:"):
                        concept["name"] = line.split("Name:")[1].strip()
                    elif line.startswith("Emoji:"):
                        concept["emoji"] = line.split("Emoji:")[1].strip()
                    elif line.startswith("Description:"):
                        concept["desc"] = line.split("Description:")[1].strip()
                    elif line.startswith("Appearance:"):
                        concept["appearance"] = line.split("Appearance:")[1].strip()
                    elif line.startswith("Sample Greeting:"):
                        concept["greeting"] = line.split("Sample Greeting:")[1].strip().strip('"')
                    elif line.startswith("Tags:"):
                        concept["tags"] = [tag.strip() for tag in line.split("Tags:")[1].split(",")]
                    elif line.startswith("- Tone:"):
                        concept["personality"]["tone"] = line.split("- Tone:")[1].strip()
                        Utils._map_tone_to_traits(concept)
                    elif line.startswith("- Speech Pattern:"):
                        concept["personality"]["speech_pattern"] = line.split("- Speech Pattern:")[1].strip()
                    elif line.startswith("- Quirks:"):
                        concept["personality"]["quirks"].append(line.split("- Quirks:")[1].strip())
                    elif line.startswith("- ") and ":" not in line:
                        concept["personality"]["quirks"].append(line[2:].strip())
                    elif line.startswith("- ") and "Trait" in line:
                        trait = line.split("- Trait:")[1].strip() if "Trait:" in line else line[2:].strip()
                        if trait in PERSONALITY_TRAITS:
                            concept["personality"]["traits"].append(trait)

            # Ensure minimum viable concept
            concept = Utils._validate_concept(concept)
            return concept

        except Exception as e:
            st.error(f"Error parsing generated concept: {str(e)}")
            return Utils._get_fallback_concept()

    @staticmethod
    def _map_tone_to_traits(concept):
        """Map tone description to personality traits"""
        tone_lower = concept["personality"]["tone"].lower()
        traits = concept["personality"]["traits"]

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

    @staticmethod
    def _validate_concept(concept):
        """Ensure the concept has minimum required fields"""
        # Set default name if empty
        if not concept["name"]:
            concept["name"] = "Mystery Character"

        # Set default emoji if empty
        if not concept["emoji"]:
            concept["emoji"] = "🤖"

        # Ensure we have at least some personality traits
        if not concept["personality"]["traits"]:
            if concept["personality"]["tone"]:
                tone_lower = concept["personality"]["tone"].lower()
                if 'friendly' in tone_lower:
                    concept["personality"]["traits"].append("Friendly")
                if 'professional' in tone_lower:
                    concept["personality"]["traits"].append("Professional")
                if 'humorous' in tone_lower:
                    concept["personality"]["traits"].append("Humorous")
            else:
                concept["personality"]["traits"] = ["Friendly"]  # Default fallback

        return concept

    @staticmethod
    def _get_fallback_concept():
        """Return a default concept when parsing fails"""
        return {
            "name": "Mystery Character",
            "emoji": "🕵️",
            "desc": "A fascinating character with hidden depths",
            "appearance": "A mysterious figure whose features are hard to discern",
            "personality": {
                "tone": "Mysterious",
                "traits": ["Mysterious", "Wise"],
                "speech_pattern": "Cryptic hints",
                "quirks": ["Leaves riddles", "Disappears unexpectedly"]
            },
            "greeting": "Ah, you've found me... what shall we discuss?",
            "tags": ["mystery"]
        }