import os
import random
from collections import defaultdict
from enum import Enum
from functools import wraps
from pathlib import Path
from textwrap import dedent

from aiogram import Bot
from aiogram.enums import ChatAction
from aiogram.types import Message
from dotenv import load_dotenv
from loguru import logger
from openai import AsyncOpenAI

from bot_lib import App, Handler, HandlerDisplayMode
from bot_lib.plugins import Plugin

load_dotenv()


class StoryCompression(Enum):
    COMPLETE_STORY = 0
    FEW_LINES_PER_PART = 1
    LAST_PART_ONLY = 2


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

    # async def complete_text(self, text: str, max_tokens: int = 100):
    #     response = await self._gpt.chat.completions.create(
    #         model="gpt-3.5-turbo",
    #         messages=[
    #             {"role": "system", "content": "You are a helpful assistant."},
    #             {"role": "user", "content": text},
    #         ],
    #         max_tokens=max_tokens,
    #     )
    #     return response.choices[0].message.content


class MyApp(App):
    resources_path = Path(__file__).parent / "resources"

    DEFAULT_AUTHOR_STYLE = "No preferred style"

    DEFAULT_MAX_TOKENS = 200
    DEFAULT_COMPRESSION = StoryCompression.FEW_LINES_PER_PART
    DEFAULT_MODEL = "gpt-3.5-turbo"

    help_message = dedent(
        """
        Help! I need somebody! Help! Not just anybody! Help! You know I need someone! Help!
        """
    )
    start_message = dedent(
        # todo: use bot name from config or telegram app
        # todo: remove access to 'set_premium'
        """[
        Hi! This is a fairytale generator bot
        For now, use /randomize to generate random topic, moral and author style
        
        /begin - start a new story
        /continue - generate next part of the story
        /reset - reset the current story and start over
        /regenerate - regenerate the current part of the story
        /set_premium (upgrade) or /downgrade
        
        use /help to get a full list of possible commands]
        """
    )

    def set_default(self, user):
        self.max_tokens_per_user[user] = self.DEFAULT_MAX_TOKENS
        self.compression_per_user[user] = self.DEFAULT_COMPRESSION
        self.model_per_user[user] = self.DEFAULT_MODEL

    @wraps(App.__init__)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # todo: use a generalized storage solution to stora and access all data
        self.morals = {}
        self.topics = {}
        self.usage = defaultdict(int)
        self.authors = defaultdict(lambda: self.DEFAULT_AUTHOR_STYLE)
        self.user_limits = defaultdict(lambda: self.DEFAULT_USER_LIMIT)
        self.story_structures = {}
        self.story_stages = defaultdict(int)
        self.stories = defaultdict(list)  # one story per user - current
        self.story_archive = defaultdict(list)  # all stories per user

        self.max_tokens_per_user = defaultdict(lambda: self.DEFAULT_MAX_TOKENS)
        self.compression_per_user = defaultdict(lambda: self.DEFAULT_COMPRESSION)
        self.model_per_user = defaultdict(lambda: self.DEFAULT_MODEL)

        self._load_resources()

    def reset(self, user: str):
        """
        Reset the state for a user
        :param user:
        :return:
        """
        current_story = {
            "topic": self.topics.pop(user, None),
            "moral": self.morals.pop(user, None),
            "author": self.authors.pop(user, None),
            "structure": self.story_structures.pop(user, None),
            "stage": self.story_stages.pop(user, None),
            "story": self.stories.pop(user, None),
        }
        if current_story["story"]:
            self.story_archive[user].append(current_story)

    def _load_resource(self, resource_name: str):
        """
        Load a resource from the resources directory
        :param resource_name:
        :return:
        """
        return (self.resources_path / resource_name).read_text().strip()

    def _load_resources(self):
        """
        Load all resources
        :return:
        """
        self.random_authors = self._load_resource("random_authors.txt").splitlines()
        self.random_morals = self._load_resource("random_morals.txt").splitlines()
        self.random_plots = self._load_resource("random_plots.txt").splitlines()
        self.random_locations = self._load_resource("random_locations.txt").splitlines()
        self.random_fairytale_authors = self._load_resource(
            "random_fairytale_authors.txt"
        ).splitlines()

    def set_moral(self, topic: str, user: str):
        self.morals[user] = topic

    def get_moral(self, user: str):
        return self.morals.get(user)

    def set_topic(self, topic: str, user: str):
        self.morals[user] = topic

    def get_topic(self, user: str):
        return self.morals.get(user)

    def set_author(self, author: str, user: str):
        self.authors[user] = author

    def get_author(self, user: str):
        return self.authors.get(user)

    def get_random_moral(self):
        """
        Get a random topic from a predefined list
        :return:
        """
        return random.choice(self.random_morals)

    def get_random_topic(self):
        """
        Get a random topic from a predefined list
        :return:
        """
        plot = random.choice(self.random_plots)
        location = random.choice(self.random_locations)
        return f"{plot} in {location}"

    def get_random_author(self, fairytale_only: bool = False):
        """
        Get a random author from a predefined list
        :return:
        """
        if fairytale_only:
            return random.choice(self.random_fairytale_authors)
        return random.choice(self.random_authors + self.random_fairytale_authors)

    DEFAULT_USER_LIMIT = 10

    def get_user_limit(self, user: str):
        """
        Get the usage limit for a user
        :param user:
        :return:
        """
        return self.DEFAULT_USER_LIMIT

    def count_user_usage(self, user: str):
        """
        Count the usage for a user
        :param user:
        :return:
        """
        self.usage[user] += 1

    def get_user_usage(self, user: str):
        """
        Get the usage for a user
        :param user:
        :return:
        """
        return self.usage[user]

    def generate_random_topic(self, user: str):
        """
        Generate a random topic for a user using chatgpt
        :param user:
        :return:
        """
        raise NotImplemented
        # topic = self.get_random_topic()
        # self.set_topic(topic, user)
        # return topic

    TOPIC_MAX_LENGTH = 500

    def validate_topic(self, topic: str):
        """
        Validate the topic
        :param topic:
        :return:
        """
        if len(topic) > self.TOPIC_MAX_LENGTH:
            raise ValueError(
                "Text is too long. Are you sure it's a topic for a fairytale?"
            )
        # todo
        return True

    MORAL_MAX_LENGTH = 100

    def validate_moral(self, moral: str):
        """
        Validate the moral
        :param moral:
        :return:
        """
        if len(moral) > self.MORAL_MAX_LENGTH:
            raise ValueError(
                "Text is too long. Are you sure it's a moral for a fairytale?"
            )
        # todo
        return True

    AUTHOR_MAX_LENGTH = 20

    def validate_author(self, author: str):
        """
        Validate the author
        :param author:
        :return:
        """
        if len(author) > self.AUTHOR_MAX_LENGTH:
            raise ValueError(
                "Text is too long. Are you sure it's an author for a fairytale?"
            )
        # todo
        return True

    story_structure_template = dedent(
        """
        Generate the stucture or a story 
        with a specified topic and moral
        and in a style of a specified author.
        
        TOPIC:
        {topic}
        MORAL:
        {moral}
        AUTHOR:
        {author}
        
        OUTPUT FORMAT:
            [exposition]
            - step 1
            - step 2
            - step 3
            [climax]
            - step 1
            - step 2
            - step 3
            [resolution]
            - step 1
            - step 2
            - step 3
        
        STRUCTURE:
        """
    )
    STORY_STRUCTURE_MAX_TOKENS = 1000

    async def generate_story_structure(
        self, topic: str, moral: str, author: str, user: str
    ):
        """
        Generate a story structure
        :param topic:
        :param moral:
        :param author:
        :return:
        """
        prompt = self.story_structure_template.format(
            topic=topic, moral=moral, author=author
        )
        model = self.model_per_user[user]
        story_structure = await self.gpt.complete_text(
            prompt, model=model, max_tokens=self.STORY_STRUCTURE_MAX_TOKENS
        )
        return self._parse_story_structure(story_structure)

    def set_story_structure(self, user: str, story_structure: dict):
        """
        Set the story structure for a user
        :param user:
        :param story_structure:
        :return:
        """
        self.story_structures[user] = story_structure

    @staticmethod
    def _extract_story_parts(story_structure: str):
        """
        Extract the story parts from the story structure
        :param story_structure:
        :return:
        """
        lines = story_structure.splitlines()
        return [line for line in lines if line.strip().startswith("-")]

    def _parse_story_structure(self, story_structure_text: str):
        """
        Parse the story structure
        :param story_structure_text:
        :return:
        """
        # step 1: strip unnecessary parts

        headers = ["exposition", "climax", "resolution"]
        story_structure = {
            "raw": story_structure_text,
            "exposition": [],
            "climax": [],
            "resolution": [],
            "all_parts": [],
        }
        if all(header in story_structure_text for header in headers):

            import re

            parts = re.split("|".join(headers), story_structure_text)
            for header, part in zip(headers, parts[1:]):
                story_structure[header] = self._extract_story_parts(part)
                story_structure["all_parts"].extend(story_structure[header])
        else:
            # just get all the lines
            story_structure["all_parts"] = self._extract_story_parts(
                story_structure_text
            )

        self._validate_story_structure(story_structure)
        return story_structure

    def _validate_story_structure(self, story_structure):
        """
        Validate the story structure
        :param story_structure:
        :return:
        """
        # check that there are at least some parts..
        if len(story_structure["all_parts"]) == 0:
            raise ValueError(f"The story structure is empty, {story_structure}")
        if len(story_structure["all_parts"]) < 3:
            logger.warning(
                f"The story structure is less than 3 parts, {story_structure}"
            )
        return True

    story_generation_template = dedent(
        """
        Generate the next part of the story
        based on the specified structure and stage.
        
        STRUCTURE:
        {structure}
        STORY SO FAR:
        {story}
        CURRENT STAGE:
        {stage}
        
        """
    )

    def _build_story_summary(
        self,
        story_parts: list,
        compression: StoryCompression = StoryCompression.FEW_LINES_PER_PART,
    ):
        """
        Build a summary of the story
        :param story_parts:
        :param compression:
        :return:
        """
        if not story_parts:
            return ""
        if compression == StoryCompression.COMPLETE_STORY:
            return "\n".join(story_parts)
        elif compression == StoryCompression.FEW_LINES_PER_PART:
            result = ""
            for part in story_parts[:-1]:
                sentences = part.split(".")
                result += ". ".join(sentences[:3]) + "...\n"
            result += story_parts[-1]  # add the last part as is
            return result
        elif compression == StoryCompression.LAST_PART_ONLY:
            return story_parts[-1]
        raise ValueError(f"Invalid compression: {compression}")

    # def _build_story_prompt(self, user: str):
    #     """
    #     Build the story prompt
    #     :param user:
    #     :return:
    #     """
    #     story_structure = self.story_structures[user]
    #     story_stage = self.story_stages[user]
    #     story_parts = story_structure['all_parts'][story_stage]
    #     story_so_far = self.stories[user]
    #     return self.story_generation_template.format(
    #         structure=story_structure['raw'],
    #         story=story_so_far,
    #         stage=story_stage,
    #     )

    async def generate_next_story_part(self, user: str):
        """
        Generate the next story part
        :param user:
        :return:
        """
        story_structure = self.story_structures[user]
        story_stage_index = self.story_stages[user]
        story_stage = story_structure["all_parts"][story_stage_index]
        # todo: configure compression per user
        story_so_far = self._build_story_summary(self.stories[user])
        # generate using gpt
        prompt = self.story_generation_template.format(
            structure=story_structure["raw"],
            story=story_so_far,
            stage=story_stage,
        )
        # todo: use langchain instead of gpt to auto-enable the tracking etc...
        response = await self.gpt.complete_text(
            prompt,
            model=self.model_per_user[user],
            max_tokens=self.max_tokens_per_user[user],
        )

        # add the response to the story
        self.story_stages[user] += 1
        self.stories[user].append(response)
        return response

    PREMIUM_MAX_TOKENS = 1000
    PREMIUM_COMPRESSION = StoryCompression.COMPLETE_STORY
    PREMIUM_MODEL = "gpt-4"

    def set_premium(self, user):
        self.max_tokens_per_user[user] = self.PREMIUM_MAX_TOKENS
        self.compression_per_user[user] = self.PREMIUM_COMPRESSION
        self.model_per_user[user] = self.PREMIUM_MODEL


class MyHandler(Handler):
    name = "myBot"
    display_mode = HandlerDisplayMode.FULL
    commands = {
        # "custom_handler": "custom",
        # "gpt_complete_handler": ["gpt_complete", "gpt"],
        # "fairytale_handler": "fairytale",
        "randomize_handler": "randomize",
        "generate_next_story_part_handler": [
            "continue",
            "next",
            "generate_next_story_part",
        ],
        "downgrade_handler": "downgrade",
    }

    def __init__(self):
        super().__init__()
        self._build_commands_and_add_to_list()

    async def randomize_handler(self, message: Message, app: MyApp, bot: Bot):
        moral = app.get_random_moral()
        topic = app.get_random_topic()
        author = app.get_random_author()
        response_text = dedent(
            f"""
            Moral set to {moral}
            Topic set to {topic}
            Author set to {author}
            """
        )
        await message.answer(response_text)
        user = self.get_user(message)
        story_structure = await app.generate_story_structure(topic, moral, author, user)
        # precalc
        app.set_story_structure(user=user, story_structure=story_structure)
        # start generating the story right away - why wait?
        temp_message_text = "Generating the next part of the story..."
        # send typing action
        temp_message = await message.answer(temp_message_text)
        await self.generate_next_story_part_handler(message, app, bot)
        await temp_message.delete()

    # async def custom_handler(self, message: Message, app: MyApp):
    #     await message.answer(app.my_plugin.secret_message)

    # async def gpt_complete_handler(self, message: Message, app: MyApp):
    #     text = message.text
    #     response = await app.gpt.complete_text(text)
    #     # todo: use send_safe util instead
    #     await message.answer(response)

    # fairytale_prompt = dedent(
    #     """
    #     Tell a fairytale on a specified topic and fabulate it.
    #     TOPIC:
    #     {text}
    #     """
    # )
    #
    # async def fairytale_handler(self, message: Message, app: MyApp):
    #     """Tell a fairytale on a sepcified topic and fabulate it."""
    #     text = message.text
    #     prompt = self.fairytale_prompt.format(text=text)
    #     response = await app.gpt.complete_text(
    #         prompt,
    #     )
    #     # todo: use send_safe util instead
    #     await message.answer(response)

    @staticmethod
    def get_user(message):
        user = message.from_user
        return user.username or user.id

    async def set_moral_handler(self, message: Message, app: MyApp):
        """Set a topic for the fairytale."""
        # set a topic for a particular user
        text = message.text
        # todo: some tricky validation that this is actually a fairytale topic

        # todo: what if the user doesn't have username
        user = self.get_user(message)
        app.set_moral(text, user)
        await message.answer(f"Topic set to {text}")

    async def set_random_topic(self, message: Message, app: MyApp):
        """Set a random topic for the fairytale."""
        user = self.get_user(message)
        topic = app.get_random_topic()
        app.set_topic(topic, user)
        await message.answer(f"Random topic set to {topic}")

    def _build_simple_set_handler(self, name: str):
        async def handler(message: Message, app: MyApp):
            text = message.text
            # todo: strip the command from the text
            if text.startswith("/"):
                _, text = text.split(" ", 1)
            user = self.get_user(message)
            func = getattr(app, name)
            result = func(text, user)
            await message.answer(result)

        return handler

    def _build_simple_get_handler(self, name: str):
        async def handler(message: Message, app: MyApp):
            user = self.get_user(message)
            func = getattr(app, name)
            result = func(user)
            await message.answer(result)

        return handler

    # todo: build this automatically from app?
    get_commands = [  # app_func_name, handler_func_name
        ("get_moral", "get_moral_handler"),
        ("get_topic", "get_topic_handler"),
        ("get_author", "get_author_handler"),
        ("get_user_limit", "get_user_limit_handler"),
        ("get_user_usage", "get_user_usage_handler"),
    ]
    set_commands = [
        ("set_moral", "set_moral_handler"),
        ("set_topic", "set_topic_handler"),
        ("set_author", "set_author_handler"),
        ("set_user_limit", "set_user_limit_handler"),
        ("set_user_usage", "set_user_usage_handler"),
        # ("set_premium", "set_premium_handler"),
    ]

    def _build_commands_and_add_to_list(self):
        for app_func_name, handler_func_name in self.get_commands:
            handler = self._build_simple_get_handler(app_func_name)
            setattr(self, handler_func_name, handler)
            self.commands[handler_func_name] = app_func_name
        for app_func_name, handler_func_name in self.set_commands:
            handler = self._build_simple_set_handler(app_func_name)
            setattr(self, handler_func_name, handler)
            self.commands[handler_func_name] = app_func_name

    async def generate_next_story_part_handler(
        self, message: Message, app: MyApp, bot: Bot
    ):
        """
        Generate the next story part
        :param user:
        :return:
        """
        user = self.get_user(message)

        # todo: if this is the first part
        #  - notify the user of the parameters of the generation

        # todo: add emoji - 'generating' - ⌛ - extract id from message via debug
        # temp_message_text = "Generating the next part of the story..."
        # temp_message = await message.answer(temp_message_text)

        chat_id = message.chat.id
        # set bot typing effect
        await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        try:
            response_text = ""
            response_text += await app.generate_next_story_part(user)

            response_text += "\n\n/continue ..."
            await message.answer(response_text)
        except Exception as e:
            error_message = "Failed, sorry :("
            await message.answer(error_message)
        # await temp_message.delete()
        # unset bot typing effect
        # todo: test if i need to do that?
        # bot.send_chat_action(message.chat.id, action=ChatAction.)

    async def upgrade_handler(self, message: Message, app: MyApp):
        user = self.get_user(message)
        app.set_premium(user)
        response_text = "Upgraded to the premium plan."
        await message.answer(response_text)

    commands["upgrade_handler"] = "upgrade"

    async def downgrade_handler(self, message: Message, app: MyApp):
        user = self.get_user(message)
        app.set_default(user)
        response_text = "Downgraded to the default plan."
        await message.answer(response_text)

    commands["downgrade_handler"] = "downgrade"

    async def reset_handler(self, message: Message, app: MyApp):
        user = self.get_user(message)
        app.reset(user)
        response_text = "Story reset."
        await message.answer(response_text)

    commands["reset_handler"] = "reset"
