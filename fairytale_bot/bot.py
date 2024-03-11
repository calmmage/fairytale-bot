from aiogram import Dispatcher
from dotenv import load_dotenv
from fairytale_bot.lib import MyPlugin, MyApp, MyHandler

from bot_lib import (
    BotConfig,
    setup_dispatcher,
)
from bot_lib.demo import create_bot, run_bot
from bot_lib.plugins import GptPlugin

plugins = [MyPlugin, GptPlugin]
app = MyApp(plugins=plugins)
bot_config = BotConfig(app=app)

# set up dispatcher
dp = Dispatcher()

my_handler = MyHandler()
handlers = [my_handler]
setup_dispatcher(dp, bot_config, extra_handlers=handlers)

load_dotenv()
bot = create_bot()

if __name__ == "__main__":
    run_bot(dp, bot)
