from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from urllib.request import Request, urlopen

from sources import Article, sources_by_section

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# =========================
# CONFIGURAÇÕES GLOBAIS
# =========================

MAX_DAYS_OLD = 2  # D-1/D-2

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
    "/2022/",
    "/2023/",
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
    "operadora",
    "plano de saúde",
    "telemedicina",
    "ia",
    "inteligência artificial",
    "healthtech",
    "oncologia",
    "clínica",
]

# 🔒 REGRA FIXA — se mencionar, não cai por “irrelevante”
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


def is_relevant(title: str) -> bool:
    t = title.lower()

    # regra fixa
    if any(e in t for e in STRATEGIC_ENTITIES):
        return True

    return any(k in t for k in POSITIVE_KEYWORDS)


def extract_date_from_text(text: str) -> Optional[datetime]:
    patterns = [
        r"(\d{2}/\d{2}/\d{4})",
        r"(\d{4}-\d{2}-\d{2})",
    ]
    for p in patterns:
        m = re.search(p, text)
        if not m:
            continue
        raw = m.group(1)
        for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(raw, fmt)
            except Exception:
                pass
    return None


def is_recent(article: Article) -> bool:
    try:
        req = Request(article.url, headers={"User-Agent": "Mozilla/5.0"})
        html = urlopen(req, timeout=12).read().decode("utf-8", errors="ignore")

        date = extract_date_from_text(html)
        if not date:
            logger.info(f"[DESCARTE][SEM DATA] {article.source} | {article.title}")
            return False

        if date < datetime.now() - timedelta(days=MAX_DAYS_OLD):
            logger.info(f"[DESCARTE][ANTIGA {date.date()}] {article.source} | {article.title}")
            return False

        return True
    except Exception as e:
        logger.info(f"[DESCARTE][ERRO DATA] {article.source} | {article.title} | {e}")
        return False


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
                articles = source.fetch()
            except Exception as e:
                logger.error(f"[ERRO][FONTE] {source.name} | {e}")
                continue

            for a in articles:
                norm_title = normalize_title(a.title)

                # dedupe por URL + título
                if a.url in seen_urls or norm_title in seen_titles:
                    logger.info(f"[DESCARTE][DUPLICADA] {a.source} | {a.title}")
                    continue

                if is_blocked_url(a.url):
                    logger.info(f"[DESCARTE][URL BLOCK] {a.source} | {a.title}")
                    continue

                if contains_negative_terms(a.title):
                    logger.info(f"[DESCARTE][NEGATIVA] {a.source} | {a.title}")
                    continue

                if not is_relevant(a.title):
                    logger.info(f"[DESCARTE][IRRELEVANTE] {a.source} | {a.title}")
                    continue

                if not is_recent(a):
                    continue

                seen_urls.add(a.url)
                seen_titles.add(norm_title)
                section_articles.append(a)

        results[section] = section_articles

    return results
