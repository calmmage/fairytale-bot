from aiogram import Dispatcher
from bot_lib import (
    BotConfig,
    setup_dispatcher,
)
from bot_lib.demo import create_bot, run_bot
from dotenv import load_dotenv

from lib import MyPlugin, MyApp, MyHandler

plugins = [MyPlugin]
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
