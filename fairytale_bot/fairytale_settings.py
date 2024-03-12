import random
from collections import defaultdict
from pathlib import Path

from aiogram.types import Message

from bot_lib import App, Handler


class FairytaleSettings(App):
    """
    Fairytale configuration

    """

    resources_path = Path(__file__).parent / "resources"
    DEFAULT_AUTHOR_STYLE = "No preferred style"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # todo: use a generalized storage solution to stora and access all data
        self.morals = {}
        self.topics = {}
        self.authors = defaultdict(lambda: self.DEFAULT_AUTHOR_STYLE)

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


class FairytaleSettingsHandler(Handler):
    get_commands = [  # app_func_name, handler_func_name
        ("get_moral", "get_moral_handler"),
        ("get_topic", "get_topic_handler"),
        ("get_author", "get_author_handler"),
    ]
    set_commands = [
        ("set_moral", "set_moral_handler"),
        ("set_topic", "set_topic_handler"),
        ("set_author", "set_author_handler"),
    ]

    async def set_random_topic(self, message: Message, app: FairytaleSettings):
        """Set a random topic for the fairytale."""
        user = self.get_user(message)
        topic = app.get_random_topic()
        app.set_topic(topic, user)
        await message.answer(f"Random topic set to {topic}")

    async def set_random_moral(self, message: Message, app: FairytaleSettings):
        """Set a random moral for the fairytale."""
        user = self.get_user(message)
        moral = app.get_random_moral()
        app.set_moral(moral, user)
        await message.answer(f"Random moral set to {moral}")

    async def set_random_author(self, message: Message, app: FairytaleSettings):
        """Set a random author for the fairytale."""
        user = self.get_user(message)
        author = app.get_random_author()
        app.set_author(author, user)
        await message.answer(f"Random author set to {author}")

    # async def set_moral_handler(self, message: Message, app: App1):
    #     """Set a moral for the fairytale."""
    #     # set a topic for a particular user
    #     text = message.text
    #     # todo: some tricky validation that this is actually a fairytale topic
    #
    #     # todo: what if the user doesn't have username
    #     user = self.get_user(message)
    #     app.set_moral(text, user)
    #     await message.answer(f"Moral set to {text}")
