"""
Envio de e-mail da newsletter via Brevo (Sendinblue) API.

Secrets usados (GitHub / ambiente):

- BREVO_API_KEY       -> API Key da Brevo (obrigatório)
- BREVO_SENDER_EMAIL  -> e-mail do remetente (obrigatório)
- BREVO_SENDER_NAME   -> nome do remetente (obrigatório)

Controle de destinatários:

- TO_EMAILS           -> lista de e-mails (prod), separados por vírgula
- TO_EMAILS_MANUAL    -> seu e-mail (ou poucos e-mails) para testes manuais

Controle de ambiente:

- NEWS_ENV:
    - "prod" / "production"  -> usa TO_EMAILS
    - qualquer outro valor   -> usa TO_EMAILS_MANUAL (fallback para TO_EMAILS)

OBS: Secrets antigos de SMTP (SMTP_SERVER, SMTP_PORT, EMAIL_PASSWORD etc.)
não são mais utilizados por este módulo.
"""

from __future__ import annotations

import json
import os
from typing import List
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BREVO_ENDPOINT = "https://api.brevo.com/v3/smtp/email"


# ---------------------------------------------------------------------------
# Helpers de ambiente
# ---------------------------------------------------------------------------


def _get_env(name: str, default: str | None = None, required: bool = False) -> str:
    value = os.getenv(name, default)
    if required and not value:
        raise RuntimeError(f"Environment variable {name} is required but not set")
    return value or ""


def get_recipients() -> List[str]:
    """
    Resolve a lista de destinatários com base em NEWS_ENV.

    NEWS_ENV:
      - "prod" / "production" -> TO_EMAILS
      - qualquer outro valor  -> TO_EMAILS_MANUAL (fallback em TO_EMAILS)

    Isso garante que, ao rodar manualmente com NEWS_ENV diferente de "prod",
    o envio seja apenas para o seu e-mail (TO_EMAILS_MANUAL).
    """
    env = _get_env("NEWS_ENV", "manual").lower()

    if env in {"prod", "production", "live"}:
        raw = _get_env("TO_EMAILS", required=True)
    else:
        # modo manual / teste: usa TO_EMAILS_MANUAL
        raw = _get_env("TO_EMAILS_MANUAL", _get_env("TO_EMAILS", ""), required=True)

    emails = [e.strip() for e in raw.split(",") if e.strip()]
    if not emails:
        raise RuntimeError("No recipients resolved for newsletter")
    return emails


# ---------------------------------------------------------------------------
# Envio via Brevo API
# ---------------------------------------------------------------------------


def send_email(subject: str, html_body: str) -> None:
    """
    Envia a newsletter via Brevo (Sendinblue) API /smtp/email.
    """
    api_key = _get_env("BREVO_API_KEY", required=True)
    sender_email = _get_env("BREVO_SENDER_EMAIL", required=True)
    sender_name = _get_env("BREVO_SENDER_NAME", required=True)

    recipients = get_recipients()

    # Monta payload da Brevo
    payload: dict = {
        "sender": {
            "email": sender_email,
            "name": sender_name,
        },
        "to": [{"email": email} for email in recipients],
        "subject": subject,
        "htmlContent": html_body,
    }

    # Opcional: se quiser usar uma lista da Brevo em produção
    env = (_get_env("NEWS_ENV", "manual") or "manual").lower()
    list_id = _get_env("BREVO_LIST_ID", "")
    if env in {"prod", "production", "live"} and list_id:
        try:
            payload["listIds"] = [int(list_id)]
        except ValueError:
            # Se o ID não for inteiro, simplesmente ignora
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
            # se quiser logar algo, dá para ler o body:
            resp.read()
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Brevo API HTTP error: {e.code} {e.reason} – {body}") from e
    except URLError as e:
        raise RuntimeError(f"Brevo API URL error: {e}") from e
