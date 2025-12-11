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
    """
    Envia a newsletter via Brevo combinando destinatários de teste e da lista principal.

    Durante execuções manuais (`workflow_dispatch`), apenas os destinatários de
    `TO_EMAILS_MANUAL` são usados; a lista principal não é acionada para evitar
    disparos acidentais durante testes.

    Durante execuções agendadas (`schedule`), os destinatários de teste (quando
    presentes) são combinados com a lista principal (lista estática ou ID de
    lista da Brevo). Caso nenhuma fonte de e‑mails esteja configurada,
    levanta RuntimeError.
    """
    api_key = os.environ["BREVO_API_KEY"]
    sender_email = os.environ["BREVO_SENDER_EMAIL"]
    sender_name = os.environ.get("BREVO_SENDER_NAME", "Saúde News")

    # Detecta se é execução manual pela variável GITHUB_EVENT_NAME
    event_name = os.environ.get("GITHUB_EVENT_NAME", "")

    # Coleta destinatários manuais para cópias de teste
    manual_raw = os.environ.get("TO_EMAILS_MANUAL", "").strip()
    manual_emails = _parse_and_validate_emails(manual_raw) if manual_raw else []

    recipients: List[str] = []

    if event_name == "workflow_dispatch":
        # Execução manual: envia apenas para e-mails manuais
        if manual_emails:
            recipients = manual_emails
            logger.info(
                "Execução manual – enviando somente para TO_EMAILS_MANUAL (%d destinatários)…",
                len(recipients),
            )
        else:
            raise RuntimeError(
                "Execução manual sem TO_EMAILS_MANUAL configurado. "
                "Defina ao menos um e-mail em TO_EMAILS_MANUAL para testar."
            )
    else:
        # Execução agendada: combina destinatários manuais e da lista principal
        if manual_emails:
            recipients.extend(manual_emails)
            logger.info(
                "Incluindo %d destinatários em TO_EMAILS_MANUAL.", len(manual_emails)
            )

        # Coleta destinatários em TO_EMAILS
        to_raw = os.environ.get("TO_EMAILS", "").strip()
        if not to_raw:
            if recipients:
                # Apenas destinatários manuais presentes, prossegue com eles
                logger.info(
                    "Nenhum TO_EMAILS configurado. Enviando apenas para TO_EMAILS_MANUAL."
                )
            else:
                raise RuntimeError(
                    "Nenhum destinatário configurado. Defina TO_EMAILS ou TO_EMAILS_MANUAL."
                )
        else:
            if "@" in to_raw:
                # Lista estática de e-mails
                static_emails = _parse_and_validate_emails(to_raw)
                recipients.extend(static_emails)
                logger.info(
                    "Encontrados %d destinatários em TO_EMAILS estático.",
                    len(static_emails),
                )
            else:
                # ID numérico de lista da Brevo
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
        "Enviando newsletter via Brevo para %d destinatários...", len(recipients)
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
