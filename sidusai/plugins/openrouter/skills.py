from sidusai.core.plugin import ChatAgentValue
from sidusai.plugins.openrouter.components import OpenRouterClientComponent


def openrouter_chat_transform_skill(value: ChatAgentValue, client: OpenRouterClientComponent) -> ChatAgentValue:
    response = client.request(value)
    if response.last_message is not None and 'content' in response.last_message:
        content = response.last_message['content']
        value.append_assistant(content)

    return value
