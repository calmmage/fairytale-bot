from textwrap import dedent

from aiogram.types import Message
from dotenv import load_dotenv
from openai import AsyncOpenAI
import os


from bot_lib import App, Handler, HandlerDisplayMode
from bot_lib.plugins import Plugin

load_dotenv()


class MyPlugin(Plugin):
    secret_message = "Hello, Plugin world!"
    name = "my_plugin"

    def __init__(self, api_key: str = None):
        # todo: use plugin config instead
        if api_key is None:
            load_dotenv()
            api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "API key is required for GPT plugin. "
                "Please provide it as an argument "
                "or in the environment variable OPENAI_API_KEY."
            )
        self._gpt = AsyncOpenAI(api_key=api_key)
        # self._gpt.api_key = api_key

    async def complete_text(self, text: str, max_tokens: int = 100):
        response = await self._gpt.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": text},
            ],
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content


class MyApp(App):
    @property
    def my_plugin(self) -> MyPlugin:
        if "my_plugin" not in self.plugins:
            raise AttributeError("MyPlugin is not enabled.")
        return self.plugins["my_plugin"]

    gpt = my_plugin


class MyHandler(Handler):
    name = "myBot"
    display_mode = HandlerDisplayMode.FULL
    commands = {
        "custom_handler": "custom",
        "gpt_complete_handler": ["gpt_complete", "gpt"],
        "fairytale_handler": "fairytale",
    }

    async def custom_handler(self, message: Message, app: MyApp):
        await message.answer(app.my_plugin.secret_message)

    async def gpt_complete_handler(self, message: Message, app: MyApp):
        text = message.text
        response = await app.gpt.complete_text(text)
        # todo: use send_safe util instead
        await message.answer(response)

    fairytale_prompt = dedent(
        """
        Tell a fairytale on a specified topic and fabulate it.
        TOPIC:
        {text}
        """
    )

    async def fairytale_handler(self, message: Message, app: MyApp):
        """Tell a fairytale on a sepcified topic and fabulate it."""
        text = message.text
        prompt = self.fairytale_prompt.format(text=text)
        response = await app.gpt.complete_text(
            prompt,
        )
        # todo: use send_safe util instead
        await message.answer(response)
