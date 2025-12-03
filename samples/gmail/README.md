### Gmail + DeepSeek sample

This sample drafts an email with DeepSeek and sends it via Gmail SMTP using the `GmailAgent`.

### Dependencies

Install the DeepSeek dependency:
```commandline
pip install requests
```

### Environments

Set the following variables before running the sample:
```properties
DEEPSEEK_API_KEY=xx-XXXXXXXXXXXXXXXXXXXXXXXXXX
GMAIL_USERNAME=you@gmail.com
GMAIL_APP_PASSWORD=xxxxxxxxxxxxxxxx
GMAIL_RECIPIENT=recipient@example.com
# Optional
GMAIL_USE_TLS=true   # defaults to SSL on port 465; set true to use STARTTLS on port 587
GMAIL_SUBJECT=Custom subject line
```

> Use a Gmail App Password (not your regular password). Enable 2FA in your Google account, create an app password for "Mail", and paste it into `GMAIL_APP_PASSWORD`.
