import json
import requests

from sidusai.core.plugin import ChatAgentValue

__default_url__ = 'https://openrouter.ai/api/v1/chat/completions'

# Default text generation params
__default_model_name__ = 'openrouter/auto'
__default_max_tokens__ = 1024
__default_temperature__ = 0.9
__default_top_p__ = 1
__frequency_penalty__ = 0
__presence_penalty__ = 0


class OpenRouterResponse:
    """
    Thin response wrapper that exposes useful OpenRouter fields and the last message content.
    """

    def __init__(self, response: requests.Response):
        obj = json.loads(response.text)

        self.status_code = response.status_code
        self.id = obj['id'] if 'id' in obj else None
        self.object = obj['object'] if 'object' in obj else None
        self.created = obj['created'] if 'created' in obj else None
        self.model = obj['model'] if 'model' in obj else None

        if 'usage' in obj:
            usage = obj['usage']
            self.prompt_tokens = usage['prompt_tokens'] if 'prompt_tokens' in usage else None
            self.completion_tokens = usage['completion_tokens'] if 'completion_tokens' in usage else None
            self.total_tokens = usage['total_tokens'] if 'total_tokens' in usage else None

        self.choices = []
        self.messages = []
        self.last_message = None

        if 'choices' in obj:
            choices = obj['choices']
            self.choices = choices
            self.messages = []
            for choice in choices:
                if 'message' in choice:
                    self.messages.append(choice['message'])

            if len(self.messages) > 0:
                self.last_message = self.messages[-1]


class OpenRouterClientComponent:
    """
    Component that holds OpenRouter connection details and performs chat completion requests.
    """

    def __init__(self, api_key: str, model_name: str = None, site_url: str = None, app_name: str = None, **kwargs):
        self.api_key = api_key
        self.model_name = model_name if model_name is not None else __default_model_name__
        self.site_url = site_url
        self.app_name = app_name
        # Additional request params such as temperature, top_p, max_tokens, etc.
        self.params = kwargs

    def request(self, chat: ChatAgentValue) -> OpenRouterResponse:
        payload = json.dumps(self._build_payload(chat))
        headers = self._build_headers()

        response = requests.request('POST', __default_url__, headers=headers, data=payload)
        return OpenRouterResponse(response)

    def _build_payload(self, chat: ChatAgentValue):
        messages = [{'role': v['role'], 'content': v['content']} for v in chat.messages]
        payload = {
            "messages": messages,
            "model": self.model_name,
            "frequency_penalty": __frequency_penalty__,
            "max_tokens": __default_max_tokens__,
            "presence_penalty": __presence_penalty__,
            "temperature": __default_temperature__,
            "top_p": __default_top_p__,
        }

        for key, value in self.params.items():
            payload[key] = value

        return payload

    def _build_headers(self):
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }

        if self.site_url is not None:
            headers['HTTP-Referer'] = self.site_url
        if self.app_name is not None:
            headers['X-Title'] = self.app_name

        return headers
