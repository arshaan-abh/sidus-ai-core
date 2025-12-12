import asyncio


class DiscordChatMemory:
    """
    In-memory store for per-user message history with an optional cap.
    """

    def __init__(self, message_store_limit: int | None = None):
        self.message_store_limit = message_store_limit
        self.cache = {}
        self.locks = {}

    def lock(self, user_id):
        self.locks[user_id] = True

    def unlock(self, user_id):
        self.locks[user_id] = False

    def is_locking(self, user_id):
        if user_id not in self.locks:
            self.unlock(user_id)
        return self.locks[user_id]

    def put_system(self, user_id, content: str):
        self.put(user_id, {'role': 'system', 'content': content})

    def put_user(self, user_id, content: str):
        self.put(user_id, {'role': 'user', 'content': content})

    def put_assistant(self, user_id, content: str):
        self.put(user_id, {'role': 'assistant', 'content': content})

    def put(self, user_id, message: dict):
        if 'role' not in message or 'content' not in message:
            raise ValueError('Message dict can be contain \'role\' and \'content\' keys')
        messages = []
        if user_id in self.cache:
            messages = self.cache[user_id]

        messages.append(message)
        if self.message_store_limit is not None and 0 < self.message_store_limit < len(messages):
            s_index = 0
            for index, msg in enumerate(messages):
                if 'role' in msg and msg['role'] == 'system':
                    s_index = index
                    continue
                break
            if s_index + 1 >= self.message_store_limit:
                s_index = self.message_store_limit - 2
            messages = messages[:s_index + 1] + messages[(-self.message_store_limit + s_index + 1):]

        self.cache[user_id] = messages

    def __getitem__(self, item):
        if item in self.cache:
            return self.cache[item]
        return None

    def __setitem__(self, key, value):
        if type(value) != list:
            raise ValueError('Invalid cached value')

        self.cache[key] = value


class DiscordResponder:
    """
    Thread-safe message sender/deleter that bridges worker threads to the Discord event loop.
    """

    def __init__(self, client):
        self.client = client

    def send_message(self, channel_id: int, content: str):
        channel = self.client.get_channel(channel_id)
        if channel is None:
            return
        asyncio.run_coroutine_threadsafe(channel.send(content), self.client.loop)

    def delete_message(self, message):
        if message is None:
            return
        asyncio.run_coroutine_threadsafe(message.delete(), self.client.loop)
