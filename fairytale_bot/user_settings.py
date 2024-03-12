from collections import defaultdict
from enum import Enum

from aiogram.types import Message
from bot_lib import Handler, App


class StoryCompression(Enum):
    COMPLETE_STORY = 0
    FEW_LINES_PER_PART = 1
    LAST_PART_ONLY = 2


class UserSettings(App):
    """
    user settings
    """

    DEFAULT_MAX_TOKENS = 200
    DEFAULT_COMPRESSION = StoryCompression.FEW_LINES_PER_PART
    DEFAULT_MODEL = "gpt-3.5-turbo"
    DEFAULT_USER_LIMIT = 10

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.max_tokens_per_user = defaultdict(lambda: self.DEFAULT_MAX_TOKENS)
        self.compression_per_user = defaultdict(lambda: self.DEFAULT_COMPRESSION)
        self.model_per_user = defaultdict(lambda: self.DEFAULT_MODEL)
        self.user_limits = defaultdict(lambda: self.DEFAULT_USER_LIMIT)

    def set_default(self, user):
        self.max_tokens_per_user[user] = self.DEFAULT_MAX_TOKENS
        self.compression_per_user[user] = self.DEFAULT_COMPRESSION
        self.model_per_user[user] = self.DEFAULT_MODEL
        self.user_limits[user] = self.DEFAULT_USER_LIMIT

    PREMIUM_MAX_TOKENS = 1000
    PREMIUM_COMPRESSION = StoryCompression.COMPLETE_STORY
    PREMIUM_MODEL = "gpt-4"
    PREMIUM_USER_LIMIT = 100
    # todo: refresh every month?  week?

    def set_premium(self, user):
        self.max_tokens_per_user[user] = self.PREMIUM_MAX_TOKENS
        self.compression_per_user[user] = self.PREMIUM_COMPRESSION
        self.model_per_user[user] = self.PREMIUM_MODEL
        self.user_limits[user] = self.PREMIUM_USER_LIMIT


class UserSettingsHandler(Handler):
    commands = {"downgrade_handler": "downgrade", "upgrade_handler": "upgrade"}

    get_commands = [  # app_func_name, handler_func_name
        ("get_user_limit", "get_user_limit_handler"),
        ("get_user_usage", "get_user_usage_handler"),
    ]
    set_commands = [
        ("set_user_limit", "set_user_limit_handler"),
        ("set_user_usage", "set_user_usage_handler"),
        # ("set_premium", "set_premium_handler"),
    ]

    async def upgrade_handler(self, message: Message, app: UserSettings):
        user = self.get_user(message)
        app.set_premium(user)
        response_text = "Upgraded to the premium plan."
        await message.answer(response_text)

    commands["upgrade_handler"] = "upgrade"

    async def downgrade_handler(self, message: Message, app: UserSettings):
        user = self.get_user(message)
        app.set_default(user)
        response_text = "Downgraded to the default plan."
        await message.answer(response_text)

    commands["downgrade_handler"] = "downgrade"
