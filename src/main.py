"""Entry point da newsletter de Saúde.

Orquestra:
1. Busca notícias.
2. Renderiza HTML.
3. Envia por e-mail via SMTP.

Mantive o nome `main.py` com um `main()` simples + bloco `if __name__ == '__main__'`
para funcionar bem tanto em GitHub Actions (python -m src.main ou python src/main.py)
quanto localmente.
"""

from __future__ import annotations

import logging
import sys

from .news_fetcher import fetch_all_news
from .render_news import render_html, build_subject
from .send_email import send_email


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

    logger.info("Enviando e-mail da newsletter...")
    send_email(subject=subject, html_body=html)

    logger.info("Newsletter enviada com sucesso.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Erro ao gerar/enviar newsletter: %s", exc)
        sys.exit(1)
