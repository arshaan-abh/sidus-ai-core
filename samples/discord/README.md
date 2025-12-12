### Discord Bot integration sample

A simple Discord bot that forwards user messages into a language-model skill chain
and posts the response back to the channel.

### Dependencies

The core stays lightweight. Install plugin dependencies in your project:

```requirements
discord.py==2.4.0
requests==2.32.3
```

```commandline
pip install discord.py requests
```

### Environments

Set up the following environment variables before running the sample:

```properties
DISCORD_BOT_TOKEN=XXXXXXXXXXXXXXXXXXXXXXXX
DEEPSEEK_API_KEY=xx-XXXXXXXXXXXXXXXXXXXXXXXXXX
```

Make sure your Discord bot has the `MESSAGE CONTENT INTENT` enabled.
