# components/avatar_utils.py
import streamlit as st
import os
import base64
from PIL import Image
import io


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

            return ("image", byte_im)
        except Exception as e:
            # Fallback to emoji
            emoji = get_bot_attribute(bot, 'emoji', '🤖')
            return ("emoji", emoji)

    # Handle emoji avatar
    else:
        emoji = get_bot_attribute(bot, 'emoji', '🤖')
        return ("emoji", emoji)


def get_avatar_display(bot, size=40):
    """
    Get avatar ready for display in Streamlit components
    Returns: Either image bytes or emoji string
    """
    avatar_type, avatar_content = get_bot_avatar(bot, size)

    if avatar_type == "image":
        return avatar_content
    else:
        return avatar_content


def get_avatar_type(bot):
    """Get the type of avatar (emoji, uploaded, generated)"""
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