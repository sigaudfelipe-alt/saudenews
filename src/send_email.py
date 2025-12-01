"""
Envio de e-mail da newsletter via Brevo (Sendinblue) API.

Secrets usados:

- BREVO_API_KEY       -> API Key da Brevo (obrigatório)
- BREVO_SENDER_EMAIL  -> e-mail do remetente (obrigatório)
- BREVO_SENDER_NAME   -> nome do remetente (obrigatório)
- BREVO_LIST_ID       -> opcional (id de lista da Brevo)

Destinatários:

- TO_EMAILS        -> lista de e-mails (produção), separados por vírgula
- TO_EMAILS_MANUAL -> seu e-mail (ou poucos e-mails) para testes manuais

RUN_MODE (igual já aparece no seu workflow):

- "workflow_dispatch" -> execução manual: envia para TO_EMAILS_MANUAL
- qualquer outro valor -> execução normal: envia para TO_EMAILS
"""

from __future__ import annotations

import json
import os
from typing import List
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BREVO_ENDPOINT = "https://api.brevo.com/v3/smtp/email"


def _get_env(name: str, default: str | None = None, required: bool = False) -> str:
    value = os.getenv(name, default)
    if required and not value:
        raise RuntimeError(f"Environment variable {name} is required but not set")
    return value or ""


def get_recipients() -> List[str]:
    """
    Decide a lista de destinatários usando RUN_MODE.

    - Se RUN_MODE == "workflow_dispatch" (execução manual do workflow),
      envia para TO_EMAILS_MANUAL.

    - Caso contrário, envia para TO_EMAILS (produção).
    """
    run_mode = (_get_env("RUN_MODE", "") or "").lower()

    if run_mode == "workflow_dispatch":
        raw = _get_env("TO_EMAILS_MANUAL", _get_env("TO_EMAILS", ""), required=True)
    else:
        raw = _get_env("TO_EMAILS", required=True)

    emails = [e.strip() for e in raw.split(",") if e.strip()]
    if not emails:
        raise RuntimeError("No recipients resolved for newsletter")
    return emails


def send_email(subject: str, html_body: str) -> None:
    api_key = _get_env("BREVO_API_KEY", required=True)
    sender_email = _get_env("BREVO_SENDER_EMAIL", required=True)
    sender_name = _get_env("BREVO_SENDER_NAME", required=True)

    recipients = get_recipients()

    payload: dict = {
        "sender": {
            "email": sender_email,
            "name": sender_name,
        },
        "to": [{"email": email} for email in recipients],
        "subject": subject,
        "htmlContent": html_body,
    }

    list_id = _get_env("BREVO_LIST_ID", "")
    if list_id:
        try:
            payload["listIds"] = [int(list_id)]
        except ValueError:
            pass

    data = json.dumps(payload).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "accept": "application/json",
        "api-key": api_key,
    }

    req = Request(BREVO_ENDPOINT, data=data, headers=headers, method="POST")

    try:
        with urlopen(req, timeout=20) as resp:
            resp.read()
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Brevo API HTTP error: {e.code} {e.reason} – {body}") from e
    except URLError as e:
        raise RuntimeError(f"Brevo API URL error: {e}") from e
