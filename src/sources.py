from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict
import feedparser

# =========================
# SEÇÕES
# =========================

SECTION_BRASIL = "Brasil – Saúde & Operadoras"
SECTION_MUNDO = "Mundo – Saúde Global"
SECTION_HEALTHTECHS = "Healthtechs – Brasil & Mundo"
SECTION_WELLNESS = "Wellness – EUA / Europa"


# =========================
# MODELO DE ARTIGO (fica aqui para evitar circular import)
# =========================

@dataclass
class Article:
    title: str
    url: str
    source: str
    section: str
    score: float = 0.0


# =========================
# SOURCE
# =========================

@dataclass
class Source:
    name: str
    rss: str
    section: str

    def fetch(self) -> List[Article]:
        feed = feedparser.parse(self.rss)
        articles: List[Article] = []

        for e in getattr(feed, "entries", []):
            title = getattr(e, "title", None)
            link = getattr(e, "link", None)
            if not title or not link:
                continue

            articles.append(
                Article(
                    title=title,
                    url=link,
                    source=self.name,
                    section=self.section,
                )
            )

        return articles


# =========================
# FONTES POR SEÇÃO
# =========================

sources_by_section: Dict[str, List[Source]] = {
    SECTION_BRASIL: [
        Source(
            name="Medicina S/A",
            rss="https://medicinasa.com.br/feed/",
            section=SECTION_BRASIL,
        ),
        Source(
            name="Saúde Digital News",
            rss="https://saudedigitalnews.com.br/feed/",
            section=SECTION_BRASIL,
        ),
        Source(
            name="Valor Econômico",
            rss="https://valor.globo.com/rss/empresas/",
            section=SECTION_BRASIL,
        ),
    ],
    SECTION_MUNDO: [],
    SECTION_HEALTHTECHS: [],
    SECTION_WELLNESS: [],
}
