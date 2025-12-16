from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
import feedparser

# =========================
# SEÇÕES
# =========================

SECTION_BRASIL = "Brasil – Saúde & Operadoras"
SECTION_MUNDO = "Mundo – Saúde Global"
SECTION_HEALTHTECHS = "Healthtechs – Brasil & Mundo"
SECTION_WELLNESS = "Wellness – EUA / Europa"


# =========================
# MODELO DE ARTIGO (compatível com render_news.py)
# =========================

@dataclass
class Article:
    title: str
    url: str
    source_name: str
    section: str
    score: float = 0.0
    published_at: Optional[datetime] = None  # vem do RSS quando disponível

    @property
    def source(self) -> str:
        return self.source_name


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


# =========================
# FONTES POR SEÇÃO (OPÇÃO 2)
# =========================

sources_by_section: Dict[str, List[Source]] = {
    # 🇧🇷 Brasil — foco em operadoras, hospitais, negócios e saúde digital
    SECTION_BRASIL: [
        Source("Medicina S/A", "https://medicinasa.com.br/feed/", SECTION_BRASIL),
        Source("Saúde Digital News", "https://saudedigitalnews.com.br/feed/", SECTION_BRASIL),

        # Valor é amplo; seu news_fetcher filtra por relevância + entidades estratégicas
        Source("Valor Econômico – Empresas", "https://valor.globo.com/rss/empresas/", SECTION_BRASIL),

        # Future Health (pode variar; se algum feed não retornar, ele só reduz volume sem quebrar o pipeline)
        Source("Future Health", "https://futurehealth.cc/feed/", SECTION_BRASIL),
    ],

    # 🌍 Mundo — políticas, sistemas de saúde, mercado e regulação
    SECTION_MUNDO: [
        # FierceHealthcare (RSS oficial listado pela própria Fierce) :contentReference[oaicite:3]{index=3}
        Source("Fierce Healthcare – All", "https://www.fiercehealthcare.com/rss/xml", SECTION_MUNDO),

        # STAT (RSS oficial) :contentReference[oaicite:4]{index=4}
        Source("STAT – All", "https://www.statnews.com/feed/", SECTION_MUNDO),

        # Modern Healthcare (nem sempre tem RSS aberto; se não retornar, não quebra)
        Source("Modern Healthcare", "https://www.modernhealthcare.com/section/rss", SECTION_MUNDO),

        # MobiHealthNews (geralmente WP feed; se não retornar, não quebra)
        Source("MobiHealthNews", "https://www.mobihealthnews.com/feed", SECTION_MUNDO),
    ],

    # 🚀 Healthtechs — IA, startups, investimentos, transformação digital
    SECTION_HEALTHTECHS: [
        Source("Fierce Healthcare – Health Tech", "https://www.fiercehealthcare.com/rss/topic/health-tech", SECTION_HEALTHTECHS),
        Source("STAT – Health Tech", "https://www.statnews.com/category/health-tech/feed/", SECTION_HEALTHTECHS),
        Source("MobiHealthNews – Digital Health", "https://www.mobihealthnews.com/rss.xml", SECTION_HEALTHTECHS),
    ],

    # 🧘‍♀️ Wellness — performance, fitness, longevidade (EUA/Europa)
    SECTION_WELLNESS: [
        # Fitt Insider Podcast RSS (oficial via Libsyn) :contentReference[oaicite:5]{index=5}
        Source("Fitt Insider Podcast", "https://fittinsider.libsyn.com/rss", SECTION_WELLNESS),

        # STAT – Health (puxa mais geral, mas você filtra por relevância)
        Source("STAT – Health", "https://www.statnews.com/category/health/feed/", SECTION_WELLNESS),
    ],
}
