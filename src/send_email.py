"""
Envio de e-mail da newsletter via Brevo (Sendinblue) API.

Secrets usados (GitHub Actions):

Obrigatórios:
- BREVO_API_KEY       -> API Key da Brevo
- BREVO_SENDER_EMAIL  -> e-mail do remetente
- BREVO_SENDER_NAME   -> nome do remetente

Destinatários:
- TO_EMAILS           -> e-mails de produção, separados por vírgula
- TO_EMAILS_MANUAL    -> seu e-mail (para testes manuais)

Lógica:

- RUN_MODE == "workflow_dispatch"  -> execução MANUAL
    -> envia para TO_EMAILS_MANUAL (ou TO_EMAILS se o manual não existir)

- Qualquer outro RUN_MODE          -> execução NORMAL / agendada
    -> envia para TO_EMAILS (ou TO_EMAILS_MANUAL se TO_EMAILS não existir)

Em TODOS os casos, a requisição sempre terá um campo "to".
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


def _resolve_recipients() -> List[str]:
    """
    Decide a lista de destinatários usando RUN_MODE.

    - RUN_MODE == "workflow_dispatch": prioriza TO_EMAILS_MANUAL
    - Outro valor / vazio: prioriza TO_EMAILS

    Se o prioritário não existir, cai no outro.
    Se nenhum dos dois existir, dá erro.
    """
    run_mode = (_get_env("RUN_MODE", "") or "").lower()

    to_manual = os.getenv("TO_EMAILS_MANUAL", "").strip()
    to_prod = os.getenv("TO_EMAILS", "").strip()

    if run_mode == "workflow_dispatch":
        raw = to_manual or to_prod
    else:
        raw = to_prod or to_manual

    if not raw:
        raise RuntimeError("No recipients configured: set TO_EMAILS and/or TO_EMAILS_MANUAL")

    emails = [e.strip() for e in raw.split(",") if e.strip()]
    if not emails:
        raise RuntimeError("Recipients list is empty after parsing TO_EMAILS/TO_EMAILS_MANUAL")

    return emails


def send_email(subject: str, html_body: str) -> None:
    api_key = _get_env("BREVO_API_KEY", required=True)
    sender_email = _get_env("BREVO_SENDER_EMAIL", required=True)
    sender_name = _get_env("BREVO_SENDER_NAME", required=True)

    recipients = _resolve_recipients()

    payload: dict = {
        "sender": {
            "email": sender_email,
            "name": sender_name,
        },
        "to": [{"email": email} for email in recipients],
        "subject": subject,
        "htmlContent": html_body,
    }

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
