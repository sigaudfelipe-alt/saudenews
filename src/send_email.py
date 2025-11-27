import os
import requests


def _get_contacts_from_brevo_list(api_key: str, list_id: str, limit: int = 500):
    """
    Busca contatos da lista da Brevo via API v3.
    Usa GET /contacts/lists/{listId}/contacts
    """
    url = f"https://api.brevo.com/v3/contacts/lists/{list_id}/contacts"
    params = {
        "limit": limit,
        "offset": 0,
        "sort": "asc",
    }
    headers = {
        "api-key": api_key,
        "accept": "application/json",
    }

    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    contacts = data.get("contacts", [])
    emails = []

    for c in contacts:
        email = c.get("email")
        if email:
            emails.append(email.strip())

    return emails


def send_newsletter_email(subject: str, html_content: str):
    """
    Envia a newsletter usando a API v3 da Brevo.

    Regras:
    - Se RUN_MODE == 'workflow_dispatch'  -> usa TO_EMAILS_MANUAL (teste só com você)
    - Caso contrário (envio agendado)     -> busca todos os contatos da lista BREVO_LIST_ID
    """

    api_key = os.getenv("BREVO_API_KEY")
    sender_email = os.getenv("BREVO_SENDER_EMAIL")
    sender_name = os.getenv("BREVO_SENDER_NAME", "News Saúde")
    run_mode = os.getenv("RUN_MODE", "schedule")
    list_id = os.getenv("BREVO_LIST_ID")

    if not api_key or not sender_email:
        raise ValueError("Faltam BREVO_API_KEY ou BREVO_SENDER_EMAIL nos secrets.")

    # 1) Define destinatários
    to_list = []

    if run_mode == "workflow_dispatch":
        # Modo teste manual: envia só para TO_EMAILS_MANUAL
        to_emails_raw = os.getenv("TO_EMAILS_MANUAL", "")
        to_list = [
            {"email": e.strip()}
            for e in to_emails_raw.split(",")
            if e.strip()
        ]
        print(f"RUN_MODE=workflow_dispatch → {len(to_list)} destinatário(s) (TO_EMAILS_MANUAL).")
    else:
        # Modo agendado: busca todos da lista da Brevo
        if not list_id:
            raise ValueError("BREVO_LIST_ID não configurado nos secrets.")
        try:
            emails = _get_contacts_from_brevo_list(api_key, list_id)
        except Exception as e:
            print("Erro ao buscar contatos da lista da Brevo:", e)
            raise
        to_list = [{"email": e} for e in emails]
        print(f"RUN_MODE=schedule → {len(to_list)} destinatário(s) da lista {list_id}.")

    if not to_list:
        print("Nenhum destinatário encontrado. E-mail não será enviado.")
        return

    # 2) Monta payload do e-mail
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
        print("Falha ao enviar e-mail via Brevo:", e)
        try:
            print("Resposta da Brevo:", resp.status_code, resp.text)
        except Exception:
            pass
        raise
