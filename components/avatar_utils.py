# components/avatar_utils.py
import io
import os
import streamlit as st
from PIL import Image


def get_bot_attribute(bot, attribute, default=None):
    """Safely get attribute from bot whether it's a Bot object or dictionary"""
    if hasattr(bot, attribute):
        return getattr(bot, attribute, default)
    elif isinstance(bot, dict):
        return bot.get(attribute, default)
    return default


def get_bot_avatar(bot, size=40):
    """
    Get bot avatar as either image or emoji
    Returns: (avatar_type, avatar_content) where avatar_type is 'image' or 'emoji'
    """
    # Safely get appearance data
    if hasattr(bot, 'appearance'):
        appearance = bot.appearance
    elif isinstance(bot, dict):
        appearance = bot.get("appearance", {})
    else:
        appearance = {}

    # Safely get avatar data
    avatar_data = get_bot_attribute(appearance, 'avatar', None)

    # Handle image avatar
    if (avatar_data and
            isinstance(avatar_data, dict) and
            "filepath" in avatar_data and
            os.path.exists(avatar_data["filepath"])):

        try:
            # Open and resize image
            image = Image.open(avatar_data["filepath"])
            image.thumbnail((size, size))

            # Convert to bytes for Streamlit
            buf = io.BytesIO()
            image.save(buf, format="PNG")
            byte_im = buf.getvalue()

            return "image", byte_im
        except (IOError, OSError, Image.DecompressionBombError) as e:
            print(f"Error loading avatar image: {e}")
            # Fallback to emoji
            emoji = get_bot_attribute(bot, 'emoji', '🤖')
            return "emoji", emoji

    # Handle emoji avatar
    else:
        emoji = get_bot_attribute(bot, 'emoji', '🤖')
        return "emoji", emoji


def get_avatar_display(bot, size=40):
    """Get avatar display for a Bot object only"""
    try:
        # Only handle Bot objects - no legacy dictionary support
        if not hasattr(bot, 'appearance'):
            return bot.emoji if hasattr(bot, 'emoji') else '🤖'

        appearance = bot.appearance
        avatar_type = appearance.get('avatar_type', 'emoji')
        avatar_data = appearance.get('avatar_data')

        if avatar_type == 'emoji':
            return bot.emoji if hasattr(bot, 'emoji') else '🤖'

        elif avatar_type in ['uploaded', 'ai_generated'] and avatar_data:
            # Handle dictionary avatar data from uploaded files or AI-generated
            if isinstance(avatar_data, dict):
                filepath = avatar_data.get('filepath')
                if filepath and os.path.exists(filepath):
                    try:
                        image = Image.open(filepath)
                        # Resize image to requested size for consistency
                        image.thumbnail((size, size), Image.Resampling.LANCZOS)
                        return image
                    except (IOError, OSError, Image.DecompressionBombError) as e:
                        print(f"Error loading avatar image from {filepath}: {e}")
                        # Fall back to emoji
                        return bot.emoji if hasattr(bot, 'emoji') else '🤖'
                else:
                    # File doesn't exist, fall back to emoji
                    return bot.emoji if hasattr(bot, 'emoji') else '🤖'

            # If we get here, avatar_data exists but is invalid
            return bot.emoji if hasattr(bot, 'emoji') else '🤖'

        else:
            # Default case - use emoji
            return bot.emoji if hasattr(bot, 'emoji') else '🤖'

    except (AttributeError, KeyError, TypeError) as e:
        print(f"Error in get_avatar_display: {e}")
        return '🤖'  # Default emoji fallback


def get_avatar_type(bot):
    """Get the type of avatar (emoji, uploaded, ai_generated)"""
    if hasattr(bot, 'appearance'):
        avatar_type = getattr(bot.appearance, 'avatar_type', 'emoji')
    elif isinstance(bot, dict) and 'appearance' in bot:
        avatar_type = bot['appearance'].get('avatar_type', 'emoji')
    else:
        avatar_type = 'emoji'
    return avatar_type


def get_avatar_emoji(bot):
    """Safely get emoji from bot"""
    return get_bot_attribute(bot, 'emoji', '🤖')


def display_avatar(bot, width=80):
    """Display bot avatar in Streamlit (for use in pages/components)"""
    avatar_display = get_avatar_display(bot, size=width)

    if isinstance(avatar_display, Image.Image):
        # It's an image - display it
        st.image(avatar_display, width=width)
    else:
        # It's an emoji - display as large text
        st.write(f"<div style='font-size: {width}px; text-align: center;'>{avatar_display}</div>",
                 unsafe_allow_html=True)


def get_avatar_filepath(bot):
    """Get the filepath of the avatar image if it exists"""
    try:
        if hasattr(bot, 'appearance'):
            avatar_data = bot.appearance.get('avatar_data')
            avatar_type = bot.appearance.get('avatar_type')

            if avatar_type in ['uploaded', 'ai_generated'] and avatar_data and isinstance(avatar_data, dict):
                filepath = avatar_data.get('filepath')
                if filepath and os.path.exists(filepath):
                    return filepath
    except (AttributeError, KeyError, TypeError) as e:
        print(f"Error getting avatar filepath: {e}")

    return None