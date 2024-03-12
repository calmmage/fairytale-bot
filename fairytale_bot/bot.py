from aiogram import Dispatcher
from dotenv import load_dotenv

from bot_lib import (
    BotConfig,
    setup_dispatcher,
)
from bot_lib.demo import create_bot, run_bot
from bot_lib.plugins import GptPlugin

from fairytale_bot.fairytale_settings import FairytaleSettingsHandler
from fairytale_bot.lib import MainApp, MainHandler
from fairytale_bot.user_settings import UserSettingsHandler


plugins = [GptPlugin]
app = MainApp(plugins=plugins)
bot_config = BotConfig(app=app)

# set up dispatcher
dp = Dispatcher()

handlers = [MainHandler(), UserSettingsHandler(), FairytaleSettingsHandler()]
setup_dispatcher(dp, bot_config, extra_handlers=handlers)

load_dotenv()
bot = create_bot()

if __name__ == "__main__":
    run_bot(dp, bot)
