from sidusai.plugins.gmail.components import GmailClient
from sidusai.plugins.gmail.values import GmailMessageValue


def gmail_send_email_skill(value: GmailMessageValue, client: GmailClient) -> GmailMessageValue:
    client.send_email(
        subject=value.subject,
        body=value.body,
        recipients=value.recipients,
        cc=value.cc,
        bcc=value.bcc,
        sender=value.sender
    )
    return value
