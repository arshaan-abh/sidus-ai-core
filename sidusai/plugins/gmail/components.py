import smtplib
from email.message import EmailMessage
from typing import Callable

__default_smtp_host__ = 'smtp.gmail.com'
__default_smtp_ssl_port__ = 465
__default_smtp_tls_port__ = 587


class GmailClient:
    """
    Lightweight Gmail SMTP client with injectable transport for tests.
    """

    def __init__(self, username: str, app_password: str,
                 smtp_host: str | None = None, smtp_port: int | None = None,
                 use_tls: bool = False, sender: str | None = None,
                 smtp_factory: Callable[[str, int], any] | None = None):
        if username is None:
            raise ValueError('Username can not be None')
        if app_password is None:
            raise ValueError('App password can not be None')

        self.username = username
        self.app_password = app_password
        self.use_tls = use_tls
        self.sender = sender if sender is not None else username

        self.smtp_host = smtp_host if smtp_host is not None else __default_smtp_host__
        default_port = __default_smtp_tls_port__ if use_tls else __default_smtp_ssl_port__
        self.smtp_port = smtp_port if smtp_port is not None else default_port
        self.smtp_factory = smtp_factory if smtp_factory is not None else self._default_smtp_factory

    def send_email(self, subject: str, body: str, recipients: list[str],
                   cc: list[str] | None = None, bcc: list[str] | None = None,
                   sender: str | None = None) -> EmailMessage:
        to_list = self._normalize_addresses(recipients)
        cc_list = self._normalize_addresses(cc)
        bcc_list = self._normalize_addresses(bcc)

        if len(to_list) + len(cc_list) + len(bcc_list) == 0:
            raise ValueError('Recipients can not be empty')

        if subject is None:
            raise ValueError('Subject can not be None')

        if body is None:
            raise ValueError('Body can not be None')

        message = self._build_message(
            subject=subject,
            body=body,
            to_list=to_list,
            cc_list=cc_list,
            sender=sender if sender is not None else self.sender
        )

        all_recipients = to_list + cc_list + bcc_list
        with self.smtp_factory(self.smtp_host, self.smtp_port) as smtp:
            if self.use_tls and hasattr(smtp, 'starttls'):
                smtp.starttls()
            smtp.login(self.username, self.app_password)
            smtp.sendmail(message['From'], all_recipients, message.as_string())
        return message

    def _build_message(self, subject: str, body: str, to_list: list[str],
                       cc_list: list[str], sender: str) -> EmailMessage:
        msg = EmailMessage()
        msg['Subject'] = str(subject)
        msg['From'] = sender
        if len(to_list) > 0:
            msg['To'] = ', '.join(to_list)
        if len(cc_list) > 0:
            msg['Cc'] = ', '.join(cc_list)

        msg.set_content(str(body))
        return msg

    def _normalize_addresses(self, recipients) -> list[str]:
        if recipients is None:
            return []
        if isinstance(recipients, str):
            recipients = [recipients]
        return [str(addr).strip() for addr in recipients if addr is not None and str(addr).strip() != '']

    def _default_smtp_factory(self, host, port):
        if self.use_tls:
            return smtplib.SMTP(host, port)
        return smtplib.SMTP_SSL(host, port)
