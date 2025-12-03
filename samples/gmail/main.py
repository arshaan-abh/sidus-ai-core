import os
import sidusai as sai
import sidusai.plugins.deepseek as ds
import sidusai.plugins.gmail as gm

deepseek_api_key = os.environ.get('DEEPSEEK_API_KEY')
gmail_username = os.environ.get('GMAIL_USERNAME')
gmail_app_password = os.environ.get('GMAIL_APP_PASSWORD')
gmail_recipient = os.environ.get('GMAIL_RECIPIENT')

use_tls = str(os.environ.get('GMAIL_USE_TLS', 'false')).lower() == 'true'
email_subject = os.environ.get('GMAIL_SUBJECT', 'SidusAI Gmail sample')

# Agent used to send the final email
gmail_agent = gm.GmailAgent(
    username=gmail_username,
    app_password=gmail_app_password,
    use_tls=use_tls,
)

# Agent used to draft the email body with LLM
draft_agent = ds.DeepSeekSingleChatAgent(
    api_key=deepseek_api_key,
    system_prompt='You craft short, polite emails in a professional tone.',
    temperature=0.3
)


def send_email_with_draft(chat: sai.ChatAgentValue):
    draft_body = chat.last_content()
    if draft_body is None:
        raise ValueError('Draft body is empty')

    print('Draft ready. Sending email...')
    gmail_agent.send_email(
        subject=email_subject,
        body=draft_body,
        recipients=[gmail_recipient],
        handler=lambda value: print('Email task queued')
    )


if __name__ == '__main__':
    if None in [deepseek_api_key, gmail_username, gmail_app_password, gmail_recipient]:
        raise EnvironmentError('Please set DEEPSEEK_API_KEY, GMAIL_USERNAME, GMAIL_APP_PASSWORD, and GMAIL_RECIPIENT')

    gmail_agent.application_build()
    draft_agent.application_build()

    prompt = 'Draft a short follow-up email thanking the recipient for their time.'
    draft_agent.send_to_chat(
        message=prompt,
        handler=send_email_with_draft
    )
