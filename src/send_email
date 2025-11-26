import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os


def send_newsletter_email(subject, html_content):
    """Envia a newsletter por e-mail usando SMTP (Gmail por padrão)."""
    from_addr = os.getenv("FROM_EMAIL")
    password = os.getenv("EMAIL_PASSWORD")
    to_emails_raw = os.getenv("TO_EMAILS", "")

    if not from_addr or not password or not to_emails_raw:
        raise ValueError("FROM_EMAIL, EMAIL_PASSWORD ou TO_EMAILS não configurados nos secrets.")

    to_list = [e.strip() for e in to_emails_raw.split(",") if e.strip()]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_list)

    msg.attach(MIMEText(html_content, "html", "utf-8"))

    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))

    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(from_addr, password)
    server.sendmail(from_addr, to_list, msg.as_string())
    server.quit()
