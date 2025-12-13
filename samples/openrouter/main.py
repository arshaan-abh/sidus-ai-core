import os

import sidusai as sai
import sidusai.plugins.openrouter as orp

openrouter_api_key = os.environ.get('OPENROUTER_API_KEY')

system_prompt = 'You are a concise assistant.'

agent = orp.OpenRouterSingleChatAgent(
    api_key=openrouter_api_key,
    system_prompt=system_prompt,
    # Override defaults if needed:
    # model_name='openrouter/auto',
    # temperature=0.3,
    # top_p=1,
    # max_tokens=256,
)


def accept_response(value: sai.ChatAgentValue):
    message = value.last_content()
    print(f'Assistant: \n{message}')


if __name__ == '__main__':
    agent.application_build()
    agent.send_to_chat(
        message='Say hello in one short sentence.',
        handler=accept_response
    )
