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
import re
from datetime import datetime

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

    # ----- Filtro de fontes e de notícias antigas -----

    current_year = datetime.now().year
    # Aceitar apenas notícias do ano corrente e dos 2 anteriores
    # Ex.: em 2025 -> MIN_YEAR = 2023
    MIN_YEAR = current_year - 2

    def _extract_year_from_url(url: str) -> int | None:
        """
        Tenta extrair o ano da URL.
        Prioriza padrão /dd/mm/aaaa/, depois /aaaa/.
        """
        if not url:
            return None

        # Ex.: /03/02/2019/
        m = re.search(r"/(\d{2})/(\d{2})/(20\d{2})/", url)
        if m:
            try:
                return int(m.group(3))
            except ValueError:
                pass

        # Ex.: /2019/
        m = re.search(r"/(20\d{2})/", url)
        if m:
            try:
                return int(m.group(1))
            except ValueError:
                pass

        return None

    def _is_valid_article(art) -> bool:
        source = getattr(art, "source_name", "") or ""
        url = getattr(art, "url", "") or ""

        # 1) Tirar Folha Equilíbrio Saúde (se aparecer com variações)
        src_norm = source.lower()
        if "folha" in src_norm and "equilibr" in src_norm:
            return False

        # 2) Tirar notícias antigas com ano explícito na URL
        year = _extract_year_from_url(url)
        if year is not None and year < MIN_YEAR:
            # Ex.: 2019, 2020, 2021 (se MIN_YEAR = 2023)
            return False

        # Se não deu pra extrair ano, consideramos válida
        return True

    for sec, arts in sections.items():
        sections[sec] = [art for art in arts if _is_valid_article(art)]

    # ----- Fim do filtro -----

    logger.info("Renderizando HTML da newsletter...")
    html = render_html(sections)
    subject = build_subject()

    logger.info("Enviando e-mail da newsletter via Brevo API...")
    send_email(html=html, subject=subject)

    logger.info("Newsletter enviada com sucesso.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Erro ao gerar/enviar newsletter: %s", exc)
        sys.exit(1)

