"""
Utility class for safely extracting bot attributes from both objects and dictionaries.
This provides a consistent interface for working with bots regardless of their type.
"""


class BotAttributeHelper:
    """Helper class for safely extracting bot attributes across the application"""

    @staticmethod
    def get_bot_attr(bot, attr, default=None):
        """
        Safely get bot attributes from both objects and dictionaries

        Args:
            bot: Either a Bot object or dictionary
            attr: Attribute name to retrieve
            default: Default value if attribute doesn't exist

        Returns:
            The attribute value or default
        """
        if hasattr(bot, attr):
            return getattr(bot, attr, default)
        elif isinstance(bot, dict):
            return bot.get(attr, default)
        return default

    @staticmethod
    def get_personality_traits(personality, trait_type, default=None):
        """
        Extract and format personality traits from personality data

        Args:
            personality: Personality dict or object
            trait_type: Type of trait ('traits', 'quirks', etc.)
            default: Default value if trait doesn't exist

        Returns:
            List of traits
        """
        if default is None:
            default = []

        # Handle both dict and object access
        if isinstance(personality, dict):
            traits = personality.get(trait_type, default)
        else:
            traits = getattr(personality, trait_type, default)

        # Convert string to list if needed
        if isinstance(traits, str):
            traits = [t.strip() for t in traits.split(',') if t.strip()]

        return traits

    @staticmethod
    def find_bot_by_name(bot_name, all_bots):
        """
        Find a bot by name in a list of bots

        Args:
            bot_name: Name of bot to find
            all_bots: List of bots (objects or dicts)

        Returns:
            Bot object/dict or None if not found
        """
        for bot in all_bots:
            if BotAttributeHelper.get_bot_attr(bot, 'name') == bot_name:
                return bot
        return None

    @staticmethod
    def get_bot_description(bot):
        """
        Get bot description with fallbacks

        Args:
            bot: Bot object or dict

        Returns:
            Description string
        """
        return (BotAttributeHelper.get_bot_attr(bot, 'desc') or
                BotAttributeHelper.get_bot_attr(bot, 'description') or
                "A helpful AI assistant")

    @staticmethod
    def get_system_rules(bot, default_rules=None):
        """
        Extract and clean system rules from bot

        Args:
            bot: Bot object or dict
            default_rules: Default rules to use if none found

        Returns:
            Cleaned system rules string
        """
        system_rules = BotAttributeHelper.get_bot_attr(bot, 'system_rules', "")

        if not system_rules and default_rules:
            system_rules = default_rules

        if system_rules and isinstance(system_rules, str):
            # Remove empty lines and clean up
            system_rules = "\n".join([line for line in system_rules.split("\n") if line.strip()])

        return system_rules or ""