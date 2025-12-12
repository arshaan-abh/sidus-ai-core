import sidusai as sai

__required_modules__ = ['discord']
sai.utils.validate_modules(__required_modules__)

import discord
import sidusai.core.plugin as _cp

import sidusai.plugins.discord.components as components

__default_agent_name__ = 'discord_ai_agent_name'
__default_message_store_limit__ = 100
__default_processing_message__ = 'processing...'
__default_busy_message__ = 'You have already sent a request. Expect a response'


class DiscordChatAgentValue(sai.ChatAgentValue):
    """
    Chat wrapper carrying Discord-specific response metadata.
    """

    def __init__(self, messages, user_id, channel_id, pending_message):
        super().__init__(messages)
        self.user_id = user_id
        self.channel_id = channel_id
        self.pending_message = pending_message


class DiscordUserRequestTransformTask(sai.CompletedAgentTask):
    pass


class DiscordRequest:
    """
    Minimal Discord request wrapper.
    """

    def __init__(self, message: discord.Message):
        self.text = str(message.content).strip()
        self.user_id = message.author.id
        self.channel_id = message.channel.id
        self.username = message.author.name
        self.display_name = message.author.display_name


class DiscordAiAgent(sai.Agent):
    """
    Discord bot agent. It listens for messages, forwards them to the skill pipeline,
    and replies in the originating channel.
    """

    def __init__(self, bot_token: str, system_prompt: str, plugins: [sai.AgentPlugin],
                 prepare_task_skills: [] = None, message_store_limit: int = __default_message_store_limit__,
                 processing_message: str = __default_processing_message__,
                 busy_message: str = __default_busy_message__):
        super().__init__(__default_agent_name__)

        self.bot_token = bot_token
        self.system_prompt = system_prompt
        self.processing_message = processing_message
        self.busy_message = busy_message

        intents = discord.Intents.default()
        intents.message_content = True
        self.client = discord.Client(intents=intents)

        self.memory = components.DiscordChatMemory(message_store_limit)
        self.responder = components.DiscordResponder(self.client)

        self.add_component_builder(self._build_responder)
        self.add_component_builder(self._build_memory)

        for plugin in plugins:
            plugin.apply_plugin(self)

        task_skills = prepare_task_skills if prepare_task_skills is not None else []
        skill_names = _cp.build_and_register_task_skill_names(task_skills, self)
        self.task_registration(DiscordUserRequestTransformTask, skill_names=skill_names)

        self._bind_handlers()

    def run(self):
        if not self.is_builded:
            self.application_build()
        self.client.run(self.bot_token)

    def _bind_handlers(self):
        @self.client.event
        async def on_message(message: discord.Message):
            if message.author == self.client.user:
                return
            await self._handle_message(message)

    async def _handle_message(self, message: discord.Message):
        request = DiscordRequest(message)
        user_id = request.user_id

        if self.memory.is_locking(user_id):
            await message.channel.send(self.busy_message)
            return

        self._set_prompt_if_cache_not_exist(user_id)
        self.memory.put_user(user_id, request.text)
        chat_messages = self.memory[user_id]

        pending_message = await message.channel.send(self.processing_message)
        chat = DiscordChatAgentValue(chat_messages, user_id, request.channel_id, pending_message)
        task = DiscordUserRequestTransformTask(self).data(chat).then(self._on_complete_task)

        self.memory.lock(user_id)
        self.task_execute(task)

    def _on_complete_task(self, chat: DiscordChatAgentValue, responder: components.DiscordResponder):
        self.memory.unlock(chat.user_id)
        responder.delete_message(chat.pending_message)

        msg = chat.last_content()
        msg = msg if msg is not None else 'Content is empty. Please check code.'
        responder.send_message(chat.channel_id, msg)

    def _set_prompt_if_cache_not_exist(self, user_id):
        chat_messages = self.memory[user_id]
        if chat_messages is None and self.system_prompt is not None:
            self.memory.put_system(user_id=user_id, content=self.system_prompt)

    def _build_responder(self) -> components.DiscordResponder:
        return self.responder

    def _build_memory(self) -> components.DiscordChatMemory:
        return self.memory
