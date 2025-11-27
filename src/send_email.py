import os
import requests


def send_newsletter_email(subject: str, html_content: str):
    """
    Envia a newsletter usando a API v3 da Brevo (Sendinblue).

    Docs base:
    - https://developers.brevo.com/reference/sendtransacemail
    """

    api_key = os.getenv("BREVO_API_KEY")
    sender_email = os.getenv("BREVO_SENDER_EMAIL")
    sender_name = os.getenv("BREVO_SENDER_NAME", "News Saúde")
    to_emails_raw = os.getenv("TO_EMAILS", "")

    if not api_key or not sender_email or not to_emails_raw:
        raise ValueError(
            "Faltam BREVO_API_KEY, BREVO_SENDER_EMAIL ou TO_EMAILS nos secrets."
        )

    # Constrói a lista de destinatários a partir da string TO_EMAILS
    to_list = [
        {"email": e.strip()}
        for e in to_emails_raw.split(",")
        if e.strip()
    ]

    if not to_list:
        raise ValueError("TO_EMAILS está vazio depois do parse.")

    payload = {
        "sender": {"email": sender_email, "name": sender_name},
        "to": to_list,
        "subject": subject,
        "htmlContent": html_content,
    }

    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
        "accept": "application/json",
    }

    try:
        resp = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            json=payload,
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        print("E-mail enviado via Brevo com sucesso. Status:", resp.status_code)
    except Exception as e:
        # Log simples para aparecer no GitHub Actions
        print("Falha ao enviar e-mail via Brevo:", e)
        try:
            print("Resposta da Brevo:", resp.status_code, resp.text)
        except Exception:
            pass
        raise
