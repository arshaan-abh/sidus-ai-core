import sidusai as sai


class GmailMessageValue(sai.AgentValue):
    """
    Envelope for an email message used by Gmail skills.
    """

    def __init__(self, subject: str, body: str, recipients: list[str],
                 cc: list[str] | None = None, bcc: list[str] | None = None,
                 sender: str | None = None):
        super().__init__()
        self.subject = subject
        self.body = body
        self.recipients = self._cleanup_addresses(recipients)
        self.cc = self._cleanup_addresses(cc)
        self.bcc = self._cleanup_addresses(bcc)
        self.sender = sender

        if self.subject is None:
            raise ValueError('Subject can not be None')
        if self.body is None:
            raise ValueError('Body can not be None')
        if len(self.all_recipients()) == 0:
            raise ValueError('Recipients can not be empty')

    def all_recipients(self) -> list[str]:
        return self.recipients + self.cc + self.bcc

    def _cleanup_addresses(self, addresses) -> list[str]:
        if addresses is None:
            return []
        if isinstance(addresses, str):
            addresses = [addresses]
        return [str(addr).strip() for addr in addresses if addr is not None and str(addr).strip() != '']
