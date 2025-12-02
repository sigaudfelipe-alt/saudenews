"""
Envio de e-mail da newsletter via Brevo (Sendinblue) API.

Secrets usados (GitHub Actions):

Obrigatórios:
- BREVO_API_KEY       -> API Key da Brevo
- BREVO_SENDER_EMAIL  -> e-mail do remetente
- BREVO_SENDER_NAME   -> nome do remetente
- TO_EMAILS_MANUAL    -> seu e-mail (para testes manuais)

Opcionais:
- TO_EMAILS           -> e-mails diretos (produção), separados por vírgula
- BREVO_LIST_ID       -> ID da lista da Brevo (produção)

Lógica:

- RUN_MODE == "workflow_dispatch"  -> execução MANUAL
    - envia APENAS para TO_EMAILS_MANUAL (não usa lista)

- Qualquer outro RUN_MODE          -> execução NORMAL / agendada
    - se TO_EMAILS estiver setado  -> envia para esses e-mails
    - senão, se BREVO_LIST_ID estiver setado -> envia para a LISTA da Brevo
    - se nenhum dos dois estiver setado      -> erro
"""

from __future__ import annotations

import json
import os
from typing import List, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BREVO_ENDPOINT = "https://api.brevo.com/v3/smtp/email"


def _get_env(name: str, default: str | None = None, required: bool = False) -> str:
    value = os.getenv(name, default)
    if required and not value:
        raise RuntimeError(f"Environment variable {name} is required but not set")
    return value or ""


def _resolve_recipients_and_lists() -> Tuple[List[str], List[int]]:
    """
    Resolve destinatários diretos (to) e listas (listIds) com base em RUN_MODE.

    Retorna:
        (emails_to, list_ids)
    """
    run_mode = (_get_env("RUN_MODE", "") or "").lower()

    to_manual = os.getenv("TO_EMAILS_MANUAL", "").strip()
    to_prod = os.getenv("TO_EMAILS", "").strip()
    list_id_raw = os.getenv("BREVO_LIST_ID", "").strip()

    emails_to: List[str] = []
    list_ids: List[int] = []

    # Execução manual: só vai pra você
    if run_mode == "workflow_dispatch":
        raw = to_manual or to_prod  # fallback em TO_EMAILS se manual não existir
        if not raw:
            raise RuntimeError("TO_EMAILS_MANUAL/TO_EMAILS must be set for manual runs")
        emails_to = [e.strip() for e in raw.split(",") if e.strip()]
        # não envia pra lista em modo manual
        return emails_to, list_ids

    # Execução normal / agendada
    if to_prod:
        emails_to = [e.strip() for e in to_prod.split(",") if e.strip()]

    if list_id_raw:
        try:
            list_ids = [int(list_id_raw)]
        except ValueError:
            # se não for inteiro, simplesmente ignoramos
            list_ids = []

    if not emails_to and not list_ids:
        raise RuntimeError("No recipients configured: set TO_EMAILS and/or BREVO_LIST_ID")

    return emails_to, list_ids


def send_email(subject: str, html_body: str) -> None:
    api_key = _get_env("BREVO_API_KEY", required=True)
    sender_email = _get_env("BREVO_SENDER_EMAIL", required=True)
    sender_name = _get_env("BREVO_SENDER_NAME", required=True)

    emails_to, list_ids = _resolve_recipients_and_lists()

    payload: dict = {
        "sender": {
            "email": sender_email,
            "name": sender_name,
        },
        "subject": subject,
        "htmlContent": html_body,
    }

    if emails_to:
        payload["to"] = [{"email": email} for email in emails_to]

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
    except URLError as e:
        raise RuntimeError(f"Brevo API URL error: {e}") from e
