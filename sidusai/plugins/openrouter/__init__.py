import sidusai as sai

__required_modules__ = ['requests']
sai.utils.validate_modules(__required_modules__)

import sidusai.core.plugin as _cp
import sidusai.plugins.openrouter.components as components
import sidusai.plugins.openrouter.skills as skills

__openrouter_agent_name__ = 'or_ai_agent_name'


class OpenRouterPlugin(sai.AgentPlugin):
    """
    Plugin that wires an OpenRouter client component and a default chat skill into an agent.
    """

    def __init__(self, api_key: str, model_name: str = None, **kwargs):
        super().__init__()
        self.api_key = api_key
        self.model_name = model_name
        # Additional request params (temperature, top_p, max_tokens, etc.)
        self.params = kwargs

    def apply_plugin(self, agent: sai.Agent):
        agent.add_component_builder(self._build_openrouter_client)
        agent.add_skill(skills.openrouter_chat_transform_skill)

    def _build_openrouter_client(self) -> components.OpenRouterClientComponent:
        return components.OpenRouterClientComponent(
            api_key=self.api_key,
            model_name=self.model_name,
            **self.params
        )


class OpenRouterChatTask(sai.CompletedAgentTask):
    """
    A ready-made chat task that passes the chat value through the OpenRouter chat skill chain.
    """
    pass


class OpenRouterSingleChatAgent(sai.Agent):
    """
    Convenience agent for single chat completion flows through OpenRouter.
    """

    def __init__(self, api_key: str, system_prompt: str = None, prepare_task_skills: [] = None,
                 model_name: str = None, **kwargs):
        super().__init__(__openrouter_agent_name__)

        self.system_prompt = system_prompt
        self.chat = sai.ChatAgentValue([])

        or_plugin = OpenRouterPlugin(
            api_key=api_key,
            model_name=model_name,
            **kwargs
        )

        or_plugin.apply_plugin(self)
        if system_prompt is not None:
            self.chat.append_system(system_prompt)

        task_skills = prepare_task_skills if prepare_task_skills is not None else []
        task_skills.append(skills.openrouter_chat_transform_skill)

        task_skill_names = _cp.build_and_register_task_skill_names(task_skills, self)
        self.task_registration(OpenRouterChatTask, skill_names=task_skill_names)

    def send_to_chat(self, message: str, handler):
        if message is None:
            raise ValueError('Message can not be None')

        self.chat.append_user(message)
        task = OpenRouterChatTask(self).data(self.chat).then(handler)
        self.task_execute(task)
