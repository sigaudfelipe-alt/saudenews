from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
import feedparser

SECTION_BRASIL = "Brasil – Saúde & Operadoras"
SECTION_MUNDO = "Mundo – Saúde Global"
SECTION_HEALTHTECHS = "Healthtechs – Brasil & Mundo"
SECTION_WELLNESS = "Wellness – EUA / Europa"


@dataclass
class Article:
    title: str
    url: str
    source_name: str
    section: str
    score: float = 0.0
    published_at: Optional[datetime] = None

    @property
    def source(self) -> str:
        return self.source_name


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

            published_at: Optional[datetime] = None
            published_parsed = getattr(e, "published_parsed", None) or getattr(e, "updated_parsed", None)
            if published_parsed:
                try:
                    published_at = datetime(
                        published_parsed.tm_year,
                        published_parsed.tm_mon,
                        published_parsed.tm_mday,
                        published_parsed.tm_hour,
                        published_parsed.tm_min,
                        published_parsed.tm_sec,
                    )
                except Exception:
                    published_at = None

            articles.append(
                Article(
                    title=title,
                    url=link,
                    source_name=self.name,
                    section=self.section,
                    published_at=published_at,
                )
            )

        return articles


sources_by_section: Dict[str, List[Source]] = {
    SECTION_BRASIL: [
        Source("Medicina S/A", "https://medicinasa.com.br/feed/", SECTION_BRASIL),
        Source("Saúde Digital News", "https://saudedigitalnews.com.br/feed/", SECTION_BRASIL),
        Source("Valor Econômico – Empresas", "https://valor.globo.com/rss/empresas/", SECTION_BRASIL),
        Source("Future Health", "https://futurehealth.cc/feed/", SECTION_BRASIL),
    ],
    SECTION_MUNDO: [
        Source("Fierce Healthcare – All", "https://www.fiercehealthcare.com/rss/xml", SECTION_MUNDO),
        Source("STAT – All", "https://www.statnews.com/feed/", SECTION_MUNDO),
        Source("Modern Healthcare", "https://www.modernhealthcare.com/section/rss", SECTION_MUNDO),
        Source("MobiHealthNews", "https://www.mobihealthnews.com/feed", SECTION_MUNDO),
    ],
    SECTION_HEALTHTECHS: [
        Source("Fierce – Health Tech", "https://www.fiercehealthcare.com/rss/topic/health-tech", SECTION_HEALTHTECHS),
        Source("STAT – Health Tech", "https://www.statnews.com/category/health-tech/feed/", SECTION_HEALTHTECHS),
        Source("MobiHealthNews – RSS", "https://www.mobihealthnews.com/rss.xml", SECTION_HEALTHTECHS),
    ],
    SECTION_WELLNESS: [
        Source("Fitt Insider Podcast", "https://fittinsider.libsyn.com/rss", SECTION_WELLNESS),
        Source("STAT – Health", "https://www.statnews.com/category/health/feed/", SECTION_WELLNESS),
    ],
}
