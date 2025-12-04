from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime, date
from html.parser import HTMLParser
from typing import Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from sources import (
    Source,
    sources_by_section,
    SECTION_BRASIL,
    SECTION_MUNDO,
    SECTION_HEALTHTECHS,
    SECTION_WELLNESS,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@dataclass
class Article:
    title: str
    url: str
    source_name: str
    section: str
    score: float = 0.0


# Palavras que indicam que a notícia é de SAÚDE
HEALTH_KEYWORDS = [
    "saúde",
    "health",
    "hospital",
    "hospita",
    "médic",
    "doctor",
    "enferm",
    "nurse",
    "plano de saúde",
    "plano de saude",
    "operadora",
    "sus",
    "ans",
    "clinic",
    "clínica",
    "clinica",
    "telemedicina",
    "digital health",
    "healthtech",
    "obesidade",
    "obesity",
    "diabetes",
    "câncer",
    "cancer",
    "mental health",
    "saúde mental",
    "saude mental",
    "wellness",
    "fitness",
    "medicare",
    "medicaid",
    "drug",
    "medication",
    "vaccine",
]

# Operadoras e planos – para dar mais peso a estas notícias
OPERATOR_KEYWORDS = [
    "hapvida",
    "notredame",
    "ixcmed",
    "intermédica",
    "intermedica",
    "amil",
    "bradesco saúde",
    "bradesco saude",
    "sulamérica saúde",
    "sulamerica saude",
    "sulamerica saúde",
    "unimed",
    "prevent senior",
    "sami saúde",
    "sami saude",
    "alice saúde",
    "alice saude",
    "qsaúde",
    "qsaude",
    "cassi",
    "postal saúde",
    "postal saude",
    "geap",
    "vivest",
    "golden cross",
]

# Notícias que queremos excluir totalmente (polícia / morte / crime)
NEGATIVE_HARD = [
    "polícia",
    "police",
    "delegado",
    "prisão",
    "homicídio",
    "homicide",
    "assassinato",
    "morte",
    "morto",
    "mortos",
    "dead",
    "murder",
]


class LinkExtractor(HTMLParser):
    """Coleta links de notícias com texto razoável."""

    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url
        self.in_a = False
        self.current_href: Optional[str] = None
        self.current_text_parts: List[str] = []
        self.links: List[tuple[str, str]] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            href = None
            for k, v in attrs:
                if k.lower() == "href":
                    href = v
                    break
            if href:
                self.in_a = True
                self.current_href = href
                self.current_text_parts = []

    def handle_data(self, data):
        if self.in_a:
            self.current_text_parts.append(data.strip())

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self.in_a:
            text = " ".join([t for t in self.current_text_parts if t])
            href = self.current_href
            self.in_a = False
            self.current_href = None
            self.current_text_parts = []

            if not href or not text:
                return

            # evita links muito curtos / de navegação
            if len(text) < 35:
                return

            lowered = text.lower()
            blacklist = [
                "assine",
                "assinar",
                "login",
                "cadastre-se",
                "cookies",
                "política de privacidade",
                "newsletter",
                "podcast",
            ]
            if any(b in lowered for b in blacklist):
                return

            full_url = urljoin(self.base_url, href)
            self.links.append((text.strip(), full_url))


def _http_get(url: str, timeout: int = 15) -> Optional[str]:
    logger.info("Fetching %s", url)
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; SaudeNewsBot/1.0)",
    }
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            html = resp.read().decode(charset, errors="replace")
            return html
    except HTTPError as e:
        logger.warning("HTTP error fetching %s: %s", url, e)
    except URLError as e:
        logger.warning("URL error fetching %s: %s", url, e)
    except Exception as e:  # noqa: BLE001
        logger.exception("Unexpected error fetching %s: %s", url, e)
    return None


def _score_title(title: str, section: str) -> tuple[float, int]:
    """Retorna (score, health_hits)."""
    t = title.lower()
    score = 0.0
    health_hits = 0

    # Saúde em geral
    for kw in HEALTH_KEYWORDS:
        if kw in t:
            score += 2.0
            health_hits += 1

    # Operadoras – mais peso
    for kw in OPERATOR_KEYWORDS:
        if kw in t:
            score += 3.0
            health_hits += 1

    # Negativos "soft" que jogam score para baixo
    negatives_soft = [
        "eleição",
        "trump",
        "biden",
        "republican",
        "democrat",
        "crime",
        "investigation",
        "lawsuit",
    ]
    for n in negatives_soft:
        if n in t:
            score -= 3.0

    # Regras extras para mundo (evitar notícias muito "operacionais" tipo layoffs)
    if section == SECTION_MUNDO:
        mundo_neg = [
            "layoff",
            "layoffs",
            "to close",
            "closure",
            "closing",
            "shutting",
            "shut down",
            "strike",
            "walkout",
            "union dispute",
        ]
        if any(w in t for w in mundo_neg):
            score -= 2.0

        mundo_pos = [
            "medicare",
            "medicaid",
            "nhs",
            "healthcare costs",
            "health costs",
            "primary care",
            "health system",
            "health systems",
            "value-based care",
            "value based care",
            "coverage",
            "universal health",
        ]
        if any(w in t for w in mundo_pos):
            score += 1.5

    # Wellness: pequenos bônus se título bate com temas de performance / hábitos
    if section == SECTION_WELLNESS:
        if any(w in t for w in ["sleep", "stress", "workout", "diet", "exercise", "mental"]):
            score += 1.0

    return score, health_hits


def _domain(url: str) -> str:
    return urlparse(url).netloc


def _parse_pt_en_date_tokens(day: int, mon_str: str, year: int) -> Optional[datetime]:
    """Converte algo como '24 nov 2025' ou '24 novembro 2025' em datetime."""
    mon_key = mon_str.strip().lower()[:3]

    months_pt = {
        "jan": 1,
        "fev": 2,
        "mar": 3,
        "abr": 4,
        "mai": 5,
        "jun": 6,
        "jul": 7,
        "ago": 8,
        "set": 9,
        "out": 10,
        "nov": 11,
        "dez": 12,
    }
    months_en = {
        "jan": 1,
        "feb": 2,
        "mar": 3,
        "apr": 4,
        "may": 5,
        "jun": 6,
        "jul": 7,
        "aug": 8,
        "sep": 9,
        "oct": 10,
        "nov": 11,
        "dec": 12,
    }

    mon = months_pt.get(mon_key) or months_en.get(mon_key)
    if not mon:
        return None
    try:
        return datetime(year, mon, day)
    except Exception:  # noqa: BLE001
        return None


def _extract_date_from_string(text: str) -> Optional[datetime]:
    """Tenta extrair uma data explícita de um texto (título, trechos)."""
    t = text.lower()

    # dd.mon.yyyy pt/en (ex: 24.nov.2025 ou 24 nov 2025)
    m = re.search(
        r"(\d{1,2})[.\s](jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)[.\s,]*(20\d{2})",
        t,
    )
    if not m:
        m = re.search(
            r"(\d{1,2})[.\s](jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[.\s,]*(20\d{2})",
            t,
        )
    if m:
        day = int(m.group(1))
        mon_str = m.group(2)
        year = int(m.group(3))
        dt = _parse_pt_en_date_tokens(day, mon_str, year)
        if dt:
            return dt

    # pt-BR: 20 de outubro de 2025
    m = re.search(
        r"(\d{1,2})\s+de\s+([a-zç]+)\s+de\s+(20\d{2})",
        t,
    )
    if m:
        day = int(m.group(1))
        mon_str = m.group(2)
        year = int(m.group(3))
        dt = _parse_pt_en_date_tokens(day, mon_str, year)
        if dt:
            return dt

    # en-US: October 20, 2025
    m = re.search(
        r"(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2}),\s*(20\d{2})",
        t,
    )
    if m:
        mon_str = m.group(1)
        day = int(m.group(2))
        year = int(m.group(3))
        dt = _parse_pt_en_date_tokens(day, mon_str, year)
        if dt:
            return dt

    return None


def _extract_date_from_url(url: str) -> Optional[datetime]:
    """Tenta extrair data da URL (muito comum em portais de notícia)."""
    # /2025/11/24/ ou similar
    m = re.search(r"/(20\d{2})/(\d{1,2})/(\d{1,2})/", url)
    if m:
        year = int(m.group(1))
        month = int(m.group(2))
        day = int(m.group(3))
        try:
            return datetime(year, month, day)
        except Exception:  # noqa: BLE001
            return None

    # /24/11/2025/
    m = re.search(r"/(\d{1,2})/(\d{1,2})/(20\d{2})/", url)
    if m:
        day = int(m.group(1))
        month = int(m.group(2))
        year = int(m.group(3))
        try:
            return datetime(year, month, day)
        except Exception:  # noqa: BLE001
            return None

    return None


def _extract_date_from_html(html: str) -> Optional[datetime]:
    """Tenta extrair data do HTML do artigo (meta tags + textos)."""

    # 1) Meta tags com ISO-8601
    meta_patterns = [
        r'property=["\']article:published_time["\'][^>]*content=["\']([^"\']+)["\']',
        r'name=["\']date["\'][^>]*content=["\']([^"\']+)["\']',
        r'itemprop=["\']datePublished["\'][^>]*content=["\']([^"\']+)["\']',
    ]
    for pat in meta_patterns:
        m = re.search(pat, html, re.IGNORECASE)
        if m:
            content = m.group(1)
            m_iso = re.search(r"(20\d{2})-(\d{2})-(\d{2})", content)
            if m_iso:
                year = int(m_iso.group(1))
                month = int(m_iso.group(2))
                day = int(m_iso.group(3))
                try:
                    return datetime(year, month, day)
                except Exception:  # noqa: BLE001
                    pass

    # 2) Texto em pt-BR: 20 de outubro de 2025
    m = re.search(
        r"(\d{1,2})\s+de\s+([a-zç]+)\s+de\s+(20\d{2})",
        html,
        re.IGNORECASE,
    )
    if m:
        day = int(m.group(1))
        mon_str = m.group(2)
        year = int(m.group(3))
        dt = _parse_pt_en_date_tokens(day, mon_str, year)
        if dt:
            return dt

    # 3) Texto em inglês: October 20, 2025
    m = re.search(
        r"(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2}),\s*(20\d{2})",
        html,
        re.IGNORECASE,
    )
    if m:
        mon_str = m.group(1)
        day = int(m.group(2))
        year = int(m.group(3))
        dt = _parse_pt_en_date_tokens(day, mon_str, year)
        if dt:
            return dt

    return None


def _is_recent_enough(title: str, url: str, max_days: int = 1) -> bool:
    """
    Garante D-0 / D-1.
    - Tenta extrair data do título, da URL e do HTML da matéria.
    - Se a data for mais antiga que max_days, descarta.
    - Se não encontrar data nenhuma, descarta (comportamento conservador).
    """
    now: date = datetime.now().date()

    # 1) Título
    dt = _extract_date_from_string(title)
    if not dt:
        # 2) URL
        dt = _extract_date_from_url(url)

    if dt is not None:
        delta_days = (now - dt.date()).days
        # Aceita apenas hoje ou ontem (0 ou 1 dia de diferença)
        return 0 <= delta_days <= max_days

    # 3) HTML do artigo – tentativa mais pesada
    html = _http_get(url)
    if html:
        dt = _extract_date_from_html(html)
        if dt is not None:
            delta_days = (now - dt.date()).days
            return 0 <= delta_days <= max_days

        # fallback leve: se achar um ano antigo (< ano atual) bem claro, corta
        current_year = datetime.now().year
        m = re.search(r"(20\d{2})", html)
        if m:
            year = int(m.group(1))
            if year < current_year:
                return False

    # Se não conseguimos determinar data, melhor excluir para garantir D-1
    return False


def fetch_from_source(source: Source) -> List[Article]:
    html = _http_get(source.url)
    if not html:
        return []

    parser = LinkExtractor(base_url=source.url)
    parser.feed(html)
    candidates: List[Article] = []
    seen_urls = set()

    for text, href in parser.links:
        if href in seen_urls:
            continue
        seen_urls.add(href)

        lowered = text.lower()

        # corta notícias policiais / morte
        if any(bad in lowered for bad in NEGATIVE_HARD):
            continue

        # corta coisas mais antigas que D-1
        if not _is_recent_enough(text, href, max_days=1):
            continue

        score, health_hits = _score_title(text, source.section)

        # FONTES GENERALISTAS: exigem pelo menos 1 palavra de saúde/operadora
        if not source.health_focus and health_hits == 0:
            continue

        # limiar mais duro: só mantemos score >= 0
        if score < 0:
            continue

        candidates.append(
            Article(
                title=text,
                url=href,
                source_name=source.name,
                section=source.section,
                score=score,
            )
        )

    candidates.sort(key=lambda a: (a.score, a.title), reverse=True)
    return candidates[: source.max_articles]


def fetch_all_news() -> Dict[str, List[Article]]:
    sections = sources_by_section()
    results: Dict[str, List[Article]] = {
        SECTION_BRASIL: [],
        SECTION_MUNDO: [],
        SECTION_HEALTHTECHS: [],
        SECTION_WELLNESS: [],
    }

    # para evitar duplicadas por título dentro da seção
    seen_titles_by_section: Dict[str, set[str]] = {
        SECTION_BRASIL: set(),
        SECTION_MUNDO: set(),
        SECTION_HEALTHTECHS: set(),
        SECTION_WELLNESS: set(),
    }

    for section, src_list in sections.items():
        for src in src_list:
            try:
                articles = fetch_from_source(src)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Error fetching from %s: %s", src.url, exc)
                continue

            for art in articles:
                norm_title = " ".join(art.title.lower().split())
                if norm_title in seen_titles_by_section[section]:
                    continue
                seen_titles_by_section[section].add(norm_title)
                results[section].append(art)

        if section == SECTION_BRASIL:
            max_total = 12
        elif section == SECTION_MUNDO:
            max_total = 10
        elif section == SECTION_HEALTHTECHS:
            max_total = 8
        else:
            max_total = 8

        results[section].sort(key=lambda a: (a.score, a.title), reverse=True)
        results[section] = results[section][:max_total]

    return results
