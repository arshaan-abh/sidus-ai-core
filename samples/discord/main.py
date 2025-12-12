import os
import sidusai.plugins.deepseek as ds
import sidusai.plugins.discord as dc

bot_token = os.environ.get('DISCORD_BOT_TOKEN')
deepseek_api_key = os.environ.get('DEEPSEEK_API_KEY')

system_prompt = 'You are a very helpful assistant. You answer briefly.'

deepseek_plugin = ds.DeepSeekPlugin(
    api_key=deepseek_api_key
)

agent = dc.DiscordAiAgent(
    bot_token=bot_token,
    system_prompt=system_prompt,
    plugins=[deepseek_plugin],
    prepare_task_skills=[ds.skills.ds_chat_transform_skill],
)


if __name__ == '__main__':
    agent.run()
