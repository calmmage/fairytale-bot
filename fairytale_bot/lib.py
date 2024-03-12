from collections import defaultdict
from functools import wraps
from textwrap import dedent

from aiogram import Bot
from aiogram.enums import ChatAction
from aiogram.types import Message
from aiogram.utils.markdown import hbold
from dotenv import load_dotenv
from loguru import logger
from bot_lib import App, Handler, HandlerDisplayMode

from fairytale_bot.fairytale_settings import FairytaleSettings
from fairytale_bot.user_settings import UserSettings, StoryCompression

load_dotenv()


class MainApp(UserSettings, FairytaleSettings):
    help_message = dedent(
        """
        Help! I need somebody! Help! Not just anybody! Help! You know I need someone! Help!
        """
    )
    start_message = dedent(
        # todo: use bot name from config or telegram app
        # todo: remove access to 'set_premium'
        """
        Hi! This is a fairytale generator bot
        For now, use /randomize to generate random topic, moral and author style
        
        /begin - start a new story
        /continue - generate next part of the story
        /reset - reset the current story and start over
        /regenerate - regenerate the current part of the story
        /upgrade or /downgrade
        
        use /help to get a full list of possible commands
        """
    )

    @wraps(App.__init__)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # todo: use a generalized storage solution to stora and access all data
        self.usage = defaultdict(int)
        self.story_structures = {}
        self.story_stages = defaultdict(int)
        self.stories = defaultdict(list)  # one story per user - current
        self.story_archive = defaultdict(list)  # all stories per user

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
        self,
        # topic: str, moral: str, author: str,
        user: str,
    ):
        """
        Generate a story structure
        :param topic:
        :param moral:
        :param author:
        :return:
        """
        if (
            not self.get_topic(user)
            or not self.get_moral(user)
            or not self.get_author(user)
        ):
            raise ValueError("The topic, moral or author are not set.")
        topic = self.get_topic(user)
        moral = self.get_moral(user)
        author = self.get_author(user)
        model = self.model_per_user[user]

        prompt = self.story_structure_template.format(
            topic=topic, moral=moral, author=author
        )
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

    def _build_story_prompt(self, user: str, story_stage_index: int):
        """
        Build the story prompt
        :param user:
        :return:
        """
        story_structure = self.story_structures[user]
        story_stage = story_structure["all_parts"][story_stage_index]
        story_so_far = self._build_story_summary(
            self.stories[user], compression=self.compression_per_user[user]
        )
        return self.story_generation_template.format(
            structure=story_structure["raw"],
            story=story_so_far,
            stage=story_stage,
        )

    STORY_BEGINNING = hbold("Here comes a majestic fairytale!\n\n")

    async def generate_next_story_part(self, user: str):
        """
        Generate the next story part
        :param user:
        :return:
        """
        story_stage_index = self.story_stages[user]
        # check if story is already started
        result = ""
        if story_stage_index == 0:
            # check if the user has the topic, moral and author set
            if (
                not self.get_topic(user)
                or not self.get_moral(user)
                or not self.get_author(user)
            ):
                result += (
                    "The topic, moral or author are not set. "
                    "Use /randomize to generate them."
                    "Or set them manually using /set_topic, /set_moral, /set_author"
                )
                return result
            result += self.STORY_BEGINNING

        elif story_stage_index >= len(self.story_structures[user]["all_parts"]):
            result += "The story is already complete"
            result += "Use /begin or /randomize to start over"
            # todo: keep telling the story if the user really wants to?
            result += "Psst.. /sequel command is in development. Don't tell anyone!"
            return result

        # generate using gpt
        prompt = self._build_story_prompt(user, story_stage_index)
        # todo: use langchain instead of gpt to auto-enable the tracking etc...
        result += await self.gpt.complete_text(
            prompt,
            model=self.model_per_user[user],
            max_tokens=self.max_tokens_per_user[user],
        )

        # add the response to the story
        self.story_stages[user] += 1
        self.stories[user].append(result)
        return result


class MainHandler(Handler):
    name = "main"
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
    }

    # def __init__(self):
    #     super().__init__()

    async def randomize_handler(self, message: Message, app: MainApp, bot: Bot):
        user = self.get_user(message)

        moral = app.get_random_moral()
        app.set_moral(moral, user)
        topic = app.get_random_topic()
        app.set_topic(topic, user)
        author = app.get_random_author()
        app.set_author(author, user)
        response_text = dedent(
            f"""
            Moral set to {moral}
            Topic set to {topic}
            Author set to {author}
            """
        )
        await message.answer(response_text)
        story_structure = await app.generate_story_structure(
            # topic, moral, author,
            user
        )
        # precalc
        app.set_story_structure(user=user, story_structure=story_structure)
        # start generating the story right away - why wait?
        temp_message_text = "Generating the next part of the story..."
        # send typing action
        temp_message = await message.answer(temp_message_text)
        await self.generate_next_story_part_handler(message, app, bot)
        await temp_message.delete()

    async def generate_next_story_part_handler(
        self, message: Message, app: MainApp, bot: Bot
    ):
        """
        Generate the next story part
        """
        user = self.get_user(message)
        # check usage

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
            app.count_user_usage(user)
        except Exception as e:
            error_message = "Failed, sorry :("
            await message.answer(error_message)
        # await temp_message.delete()
        # unset bot typing effect
        # todo: test if i need to do that?
        # bot.send_chat_action(message.chat.id, action=ChatAction.)

    async def reset_handler(self, message: Message, app: MainApp):
        user = self.get_user(message)
        app.reset(user)
        response_text = "Story reset."
        await message.answer(response_text)

    commands["reset_handler"] = "reset"

    # @staticmethod
    # def strip_command(text: str):
    #     if text.startswith("/"):
    #         parts = text.split(" ", 1)
    #         if len(parts) > 1:
    #             return parts[1].strip()
    #         return ""

    async def archive_handler(self, message: Message, app: MainApp):
        user = self.get_user(message)
        # await self._extract_message_text(message) - support voice messages?
        text = self.strip_command(message.text)
        if text and text.isdigit():
            index = int(text) - 1
            story = app.story_archive[user][index]
            story_text = "\n\n".join(story["story"])
            await self._send_as_file(
                chat_id=message.chat.id,
                text=story_text,
                filename=f"story_{text}.txt",
            )
        else:
            N = len(app.story_archive[user])
            response_text = (
                f"Your archive contains {N} stories. "
                "Use /archive i to view the i-th story."
            )
            await message.answer(response_text)
