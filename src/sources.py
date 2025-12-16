from dataclasses import dataclass
from typing import List, Dict
import feedparser

from news_fetcher import Article

# =========================
# SEÇÕES
# =========================

SECTION_BRASIL = "Brasil – Saúde & Operadoras"
SECTION_MUNDO = "Mundo – Saúde Global"
SECTION_HEALTHTECHS = "Healthtechs – Brasil & Mundo"
SECTION_WELLNESS = "Wellness – EUA / Europa"


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

        for e in feed.entries:
            if not hasattr(e, "title") or not hasattr(e, "link"):
                continue

            articles.append(
                Article(
                    title=e.title,
                    url=e.link,
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
