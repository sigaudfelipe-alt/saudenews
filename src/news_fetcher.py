from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from urllib.request import Request, urlopen

from sources import Article, sources_by_section

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# =========================
# CONFIG
# =========================

MAX_DAYS_OLD = 2
MAX_PER_SOURCE = 3  # ✅ trava por fonte (como era antes)

URL_BLOCKLIST_KEYWORDS = [
    "newsletter",
    "assine",
    "cadastro",
    "especial",
    "panorama",
    "revista",
    "edicao",
    "edição",
    "arquivo",
    "retrospectiva",
    "medicinasa.com.br/saudedigital",
    "/2020/",
    "/2021/",
]

NEGATIVE_KEYWORDS = [
    "morre",
    "morte",
    "assassin",
    "crime",
    "polícia",
    "tiroteio",
]

POSITIVE_KEYWORDS = [
    "saúde",
    "health",
    "hospital",
    "hospitais",
    "operadora",
    "operadoras",
    "plano de saúde",
    "planos de saúde",
    "sus",
    "telemedicina",
    "ia",
    "inteligência artificial",
    "healthtech",
    "oncologia",
    "clínica",
]

# 🔒 Regra fixa (Conexa e afins)
STRATEGIC_ENTITIES = [
    "conexa",
    "unimed",
    "amil",
    "dasa",
    "rede américas",
    "oncoclínicas",
    "fleury",
    "hcor",
]

# Em quais fontes vale a pena checar "entidade no corpo"
BODY_ENTITY_SOURCES = {
    "Valor Econômico – Empresas",
    "Valor Econômico",
}

# =========================
# HELPERS
# =========================

def normalize_title(title: str) -> str:
    return re.sub(r"\W+", "", title.lower())


def is_blocked_url(url: str) -> bool:
    u = url.lower()
    return any(k in u for k in URL_BLOCKLIST_KEYWORDS)


def contains_negative_terms(title: str) -> bool:
    t = title.lower()
    return any(k in t for k in NEGATIVE_KEYWORDS)


def title_has_strategic_entity(title: str) -> bool:
    t = title.lower()
    return any(e in t for e in STRATEGIC_ENTITIES)


def is_relevant_by_title(title: str) -> bool:
    t = title.lower()
    if title_has_strategic_entity(title):
        return True
    return any(k in t for k in POSITIVE_KEYWORDS)


def extract_date_from_text(text: str) -> Optional[datetime]:
    patterns = [
        (r"(\d{2}/\d{2}/\d{4})", "%d/%m/%Y"),
        (r"(\d{4}-\d{2}-\d{2})", "%Y-%m-%d"),
    ]
    for p, fmt in patterns:
        m = re.search(p, text)
        if m:
            try:
                return datetime.strptime(m.group(1), fmt)
            except Exception:
                pass
    return None


def fetch_html(url: str) -> Optional[str]:
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        return urlopen(req, timeout=12).read().decode("utf-8", errors="ignore")
    except Exception:
        return None


def body_has_strategic_entity(article: Article, html: Optional[str]) -> bool:
    if not html:
        return False
    text = html.lower()
    return any(e in text for e in STRATEGIC_ENTITIES)


def is_recent(article: Article, html: Optional[str]) -> bool:
    cutoff = datetime.now() - timedelta(days=MAX_DAYS_OLD)

    # ✅ Preferir data do RSS
    if article.published_at:
        if article.published_at < cutoff:
            logger.info(
                f"[DESCARTE][ANTIGA RSS {article.published_at.date()}] {article.source_name} | {article.title}"
            )
            return False
        return True

    # Fallback: tentar data no HTML
    if not html:
        logger.info(f"[DESCARTE][SEM HTML] {article.source_name} | {article.title}")
        return False

    date = extract_date_from_text(html)
    if not date:
        logger.info(f"[DESCARTE][SEM DATA] {article.source_name} | {article.title}")
        return False

    if date < cutoff:
        logger.info(
            f"[DESCARTE][ANTIGA HTML {date.date()}] {article.source_name} | {article.title}"
        )
        return False

    return True


def enforce_max_per_source(articles: List[Article]) -> List[Article]:
    """
    ✅ trava de 3 notícias por fonte.
    Ordena por published_at desc (quando existir) e depois aplica o limite.
    """
    def sort_key(a: Article):
        # sem published_at, joga para o fim
        return a.published_at or datetime(1970, 1, 1)

    ordered = sorted(articles, key=sort_key, reverse=True)

    counts: Dict[str, int] = {}
    limited: List[Article] = []

    for a in ordered:
        src = a.source_name
        counts.setdefault(src, 0)
        if counts[src] >= MAX_PER_SOURCE:
            logger.info(f"[DESCARTE][LIMITE {MAX_PER_SOURCE}/FONTE] {src} | {a.title}")
            continue
        counts[src] += 1
        limited.append(a)

    return limited


# =========================
# MAIN
# =========================

def fetch_all_news() -> Dict[str, List[Article]]:
    results: Dict[str, List[Article]] = {}

    seen_urls = set()
    seen_titles = set()

    for section, sources in sources_by_section.items():
        section_articles: List[Article] = []

        for source in sources:
            try:
                raw_articles = source.fetch()
            except Exception as e:
                logger.error(f"[ERRO][FONTE] {source.name} | {e}")
                continue

            for a in raw_articles:
                norm_title = normalize_title(a.title)

                if a.url in seen_urls or norm_title in seen_titles:
                    logger.info(f"[DESCARTE][DUPLICADA] {a.source_name} | {a.title}")
                    continue

                if is_blocked_url(a.url):
                    logger.info(f"[DESCARTE][URL BLOCK] {a.source_name} | {a.title}")
                    continue

                if contains_negative_terms(a.title):
                    logger.info(f"[DESCARTE][NEGATIVA] {a.source_name} | {a.title}")
                    continue

                # ✅ relevância: título primeiro
                title_relevant = is_relevant_by_title(a.title)

                # ✅ se for fonte do tipo Valor (ou outra que você quiser), checa corpo para Conexa/entidades
                html: Optional[str] = None
                if (not title_relevant) and (a.source_name in BODY_ENTITY_SOURCES):
                    html = fetch_html(a.url)
                    if body_has_strategic_entity(a, html):
                        title_relevant = True
                        logger.info(f"[BOOST][ENTIDADE NO CORPO] {a.source_name} | {a.title}")

                if not title_relevant:
                    logger.info(f"[DESCARTE][IRRELEVANTE] {a.source_name} | {a.title}")
                    continue

                # Recência (usa RSS quando tem; senão usa HTML)
                if html is None:
                    # só busca html se precisar (quando RSS não trouxe published_at)
                    if a.published_at is None:
                        html = fetch_html(a.url)
                if not is_recent(a, html):
                    continue

                seen_urls.add(a.url)
                seen_titles.add(norm_title)
                section_articles.append(a)

        # ✅ aplica limite por fonte dentro da seção
        results[section] = enforce_max_per_source(section_articles)

    return results

