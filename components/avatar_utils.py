# components/avatar_utils.py
import streamlit as st
import os
import base64
from PIL import Image
import io


def get_bot_avatar(bot, size=40):
    """
    Get bot avatar as either image or emoji
    Returns: (avatar_type, avatar_content) where avatar_type is 'image' or 'emoji'
    """
    avatar_data = bot.get("appearance", {}).get("avatar")

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
            return ("emoji", bot.get("emoji", "🤖"))

    # Handle emoji avatar
    else:
        return ("emoji", bot.get("emoji", "🤖"))


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