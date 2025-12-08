"""
Envio de e-mail da newsletter via Brevo (Sendinblue) API.

Secrets usados (GitHub Actions):

Obrigatórios:
- BREVO_API_KEY       -> API Key da Brevo
- BREVO_SENDER_EMAIL  -> e-mail do remetente
- BREVO_SENDER_NAME   -> nome do remetente

Destinatários diretos:
- TO_EMAILS           -> e-mails de produção, separados por vírgula
- TO_EMAILS_MANUAL    -> seu e-mail (para testes manuais)

Listas Brevo:
- BREVO_LIST_IDS      -> IDs de lista da Brevo, separados por vírgula (ex: "12" ou "12,34")

Lógica:

- Se BREVO_LIST_IDS estiver preenchido:
    -> o e-mail é enviado para essas listas (listIds)
    -> o campo "to" é preenchido com o próprio remetente, apenas para log/auditoria

- Se BREVO_LIST_IDS NÃO estiver preenchido:
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
    Decide a lista de destinatários usando RUN_MODE quando NÃO estamos usando listas da Brevo.
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


def _parse_list_ids() -> List[int]:
    """
    Lê BREVO_LIST_IDS (ex: "12,34") e converte em lista de inteiros.
    """
    raw = os.getenv("BREVO_LIST_IDS", "").strip()
    if not raw:
        return []

    list_ids: List[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            list_ids.append(int(part))
        except ValueError as e:  # noqa: PERF203
            raise RuntimeError(f"Invalid BREVO_LIST_IDS entry (must be integer): {part}") from e
    return list_ids


def send_email(subject: str, html_body: str) -> None:
    api_key = _get_env("BREVO_API_KEY", required=True)
    sender_email = _get_env("BREVO_SENDER_EMAIL", required=True)
    sender_name = _get_env("BREVO_SENDER_NAME", required=True)

    list_ids = _parse_list_ids()

    # Se tivermos listas configuradas, usamos o próprio remetente no "to"
    # e a Brevo dispara para as listas via listIds.
    if list_ids:
        recipients = [sender_email]
    else:
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

    if list_ids:
        payload["listIds"] = list_ids

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
    except URLError as e:  # noqa: PERF203
        raise RuntimeError(f"Brevo API URL error: {e}") from e
