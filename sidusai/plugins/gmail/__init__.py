import sidusai as sai
import sidusai.core.plugin as _cp

import sidusai.plugins.gmail.components as components
import sidusai.plugins.gmail.skills as skills
import sidusai.plugins.gmail.values as values
from sidusai.plugins.gmail.components import GmailClient
from sidusai.plugins.gmail.values import GmailMessageValue

__default_gmail_agent_name__ = 'gmail_ai_agent_name'


class GmailPlugin(sai.AgentPlugin):

    def __init__(self, username: str, app_password: str,
                 smtp_host: str | None = None, smtp_port: int | None = None,
                 use_tls: bool = False, sender: str | None = None,
                 smtp_factory=None):
        super().__init__()
        self.username = username
        self.app_password = app_password
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.use_tls = use_tls
        self.sender = sender
        self.smtp_factory = smtp_factory

    def apply_plugin(self, agent: sai.Agent):
        agent.add_component_builder(self._build_gmail_client)
        agent.add_skill(skills.gmail_send_email_skill)

    def _build_gmail_client(self) -> components.GmailClient:
        return components.GmailClient(
            username=self.username,
            app_password=self.app_password,
            smtp_host=self.smtp_host,
            smtp_port=self.smtp_port,
            use_tls=self.use_tls,
            sender=self.sender,
            smtp_factory=self.smtp_factory
        )


class GmailSendEmailTask(sai.CompletedAgentTask):
    pass


class GmailAgent(sai.Agent):

    def __init__(self, username: str, app_password: str,
                 plugins: list[sai.AgentPlugin] | None = None, task_skills: list = None,
                 smtp_host: str | None = None, smtp_port: int | None = None,
                 use_tls: bool = False, sender: str | None = None,
                 smtp_factory=None):
        super().__init__(__default_gmail_agent_name__)

        if plugins is None:
            plugins = []

        self._gmail_plugin = GmailPlugin(
            username=username,
            app_password=app_password,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            use_tls=use_tls,
            sender=sender,
            smtp_factory=smtp_factory
        )

        for plugin in plugins:
            plugin.apply_plugin(self)
        self._gmail_plugin.apply_plugin(self)

        skills_for_task = task_skills if task_skills is not None else []
        skills_for_task.append(skills.gmail_send_email_skill)
        skill_names = _cp.build_and_register_task_skill_names(skills_for_task, self)
        self.task_registration(GmailSendEmailTask, skill_names=skill_names)

    def send_email(self, subject: str, body: str, recipients: list[str],
                   cc: list[str] | None = None, bcc: list[str] | None = None,
                   sender: str | None = None, handler=None):
        value = values.GmailMessageValue(
            subject=subject,
            body=body,
            recipients=recipients,
            cc=cc,
            bcc=bcc,
            sender=sender
        )

        task = GmailSendEmailTask(self).data(value).then(handler)
        self.task_execute(task)
