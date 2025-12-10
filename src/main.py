"""
Entry point da newsletter de Saúde.

Fluxo:
1. Busca notícias.
2. Renderiza HTML.
3. Envia por e-mail (Brevo API).
"""

from __future__ import annotations

import logging
import sys

from news_fetcher import fetch_all_news
from render_news import render_html, build_subject
from send_email import send_email

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    )

    logger.info("Buscando notícias nas fontes configuradas...")
    sections = fetch_all_news()

    logger.info("Renderizando HTML da newsletter...")
    html = render_html(sections)
    subject = build_subject()

    logger.info("Enviando e-mail da newsletter via Brevo API...")
    # >>> correção: assinatura do send_email(html, subject)
    send_email(html=html, subject=subject)

    logger.info("Newsletter enviada com sucesso.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Erro ao gerar/enviar newsletter: %s", exc)
        sys.exit(1)
