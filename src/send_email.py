from __future__ import annotations

import json
import logging
import os
import re
from typing import List

import requests

logger = logging.getLogger(__name__)

BREVO_BASE_URL = "https://api.brevo.com/v3"
BREVO_EMAIL_URL = f"{BREVO_BASE_URL}/smtp/email"

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _parse_and_validate_emails(raw: str | None) -> List[str]:
    """
    Converte "a@b.com, c@d.com" em lista e valida formato básico.
    """
    if not raw:
        return []

    emails = [e.strip() for e in raw.split(",") if e.strip()]
    invalid = [e for e in emails if not EMAIL_REGEX.match(e)]

    if invalid:
        raise RuntimeError(
            f"Invalid recipient emails in TO_EMAILS/TO_EMAILS_MANUAL: {invalid}"
        )
    return emails


def _fetch_emails_from_brevo_list(api_key: str, list_id: int) -> List[str]:
    """
    Busca todos os contatos de uma lista da Brevo (Contacts > Lists).
    Usa paginação (limit/offset) até acabar.
    """
    headers = {
        "api-key": api_key,
        "Accept": "application/json",
    }

    limit = 100
    offset = 0
    emails: List[str] = []

    while True:
        params = {
            "limit": limit,
            "offset": offset,
            "sort": "asc",
        }

        url = f"{BREVO_BASE_URL}/contacts/lists/{list_id}/contacts"
        resp = requests.get(url, headers=headers, params=params, timeout=30)

        if resp.status_code >= 300:
            logger.error(
                "Erro ao buscar contatos da lista Brevo %s. Status: %s, body: %s",
                list_id,
                resp.status_code,
                resp.text,
            )
            raise RuntimeError(
                f"Brevo contacts API error {resp.status_code} ao buscar lista {list_id}"
            )

        data = resp.json()
        # A resposta tem um array de 'contacts' com campo 'email'
        contacts = data.get("contacts", [])
        if not contacts:
            break

        for c in contacts:
            email = c.get("email")
            if email:
                emails.append(email)

        # Se veio menos que o limite, acabou a paginação
        if len(contacts) < limit:
            break

        offset += limit

    # Remove duplicados, se existirem
    emails = list(dict.fromkeys(emails))
    return emails


def send_email(html: str, subject: str) -> None:
    """Envie a newsletter combinando destinatários manuais e da lista da Brevo.

    A lógica considera dois conjuntos de destinatários:
      * TO_EMAILS_MANUAL – lista de e-mails separados por vírgula para envios
        de teste. Estes serão sempre incluídos, não anulam os demais destinatários.
      * TO_EMAILS – pode ser uma lista estática de e-mails ou o ID de uma lista
        da Brevo. Quando for um ID numérico, todos os contatos dessa lista serão
        buscados via API.

    Todos os destinatários coletados são combinados em um único conjunto sem
    duplicados. Se nenhum destinatário for encontrado, levanta um RuntimeError.
    """
    api_key = os.environ["BREVO_API_KEY"]
    sender_email = os.environ["BREVO_SENDER_EMAIL"]
    sender_name = os.environ.get("BREVO_SENDER_NAME", "Saúde News")

    recipients: List[str] = []

    # 1) Coleta destinatários manuais (para cópias/testes)
    manual_raw = os.environ.get("TO_EMAILS_MANUAL", "").strip()
    if manual_raw:
        manual_emails = _parse_and_validate_emails(manual_raw)
        recipients.extend(manual_emails)
        logger.info(
            "Encontrados %d destinatários em TO_EMAILS_MANUAL.", len(manual_emails)
        )

    # 2) Coleta destinatários configurados em TO_EMAILS
    to_raw = os.environ.get("TO_EMAILS", "").strip()
    if to_raw:
        if "@" in to_raw:
            # Lista fixa de e-mails
            static_emails = _parse_and_validate_emails(to_raw)
            recipients.extend(static_emails)
            logger.info(
                "Encontrados %d destinatários em TO_EMAILS estático.",
                len(static_emails),
            )
        else:
            # ID de lista da Brevo
            try:
                brevo_list_id = int(to_raw)
            except ValueError:
                raise RuntimeError(
                    "TO_EMAILS deve ser OU uma lista de e-mails "
                    "(a@b.com,b@c.com) OU o ID numérico de uma lista da Brevo."
                )
            logger.info("Buscando contatos na lista da Brevo ID %s...", brevo_list_id)
            list_emails = _fetch_emails_from_brevo_list(api_key, brevo_list_id)
            if not list_emails:
                raise RuntimeError(
                    f"Nenhum contato encontrado na lista Brevo {brevo_list_id}."
                )
            recipients.extend(list_emails)
            logger.info(
                "Encontrados %d contatos na lista Brevo %s.",
                len(list_emails),
                brevo_list_id,
            )

    if not recipients:
        raise RuntimeError(
            "Nenhum destinatário configurado. Defina TO_EMAILS e/ou TO_EMAILS_MANUAL."
        )

    # Remove duplicados preservando ordem
    recipients = list(dict.fromkeys(recipients))

    # Monta payload de envio
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload = {
        "sender": {"email": sender_email, "name": sender_name},
        "to": [{"email": e} for e in recipients],
        "subject": subject,
        "htmlContent": html,
    }

    logger.info(
        "Enviando newsletter via Brevo para %d destinatários combinados...",
        len(recipients),
    )
    resp = requests.post(
        BREVO_EMAIL_URL, headers=headers, data=json.dumps(payload), timeout=30
    )

    if resp.status_code >= 300:
        logger.error(
            "Erro ao enviar e-mail via Brevo. Status: %s, body: %s",
            resp.status_code,
            resp.text,
        )
        raise RuntimeError(f"Brevo API error: {resp.status_code}")

    logger.info("Newsletter enviada com sucesso via Brevo.")
