import asyncio
from dotenv import load_dotenv

load_dotenv()
from fairytale_bot.bot import bot, dp


if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
