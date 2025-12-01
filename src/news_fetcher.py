from __future__ import annotations

import logging
from dataclasses import dataclass
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


class LinkExtractor(HTMLParser):
    """Coleta links de notícias com texto razoável."""

    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url
        self.in_a = False
        self.current_href: Optional[str] = None
        self.current_text_parts: List[str] = []
        self.links: List[Article] = []

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
    headers = {"User-Agent": "Mozilla/5.0 (compatible; SaudeNewsBot/1.0)"}
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


def _score_title(title: str, section: str) -> float:
    t = title.lower()
    score = 0.0

    positives = [
        "saúde digital",
        "telemedicina",
        "healthtech",
        "plano de saúde",
        "operadora",
        "hospita",
        "sus",
        "startup",
        "ia",
        "inteligência artificial",
        "mental health",
        "wellness",
        "fitness",
        "obesity",
        "longevity",
        "insurance",
        "payer",
        "medicare",
        "value-based",
    ]
    for p in positives:
        if p in t:
            score += 2.0

    negatives = [
        "eleição",
        "trump",
        "biden",
        "republican",
        "democrat",
        "crime",
        "investigation",
        "lawsuit",
    ]
    for n in negatives:
        if n in t:
            score -= 3.0

    if section == SECTION_WELLNESS:
        if any(w in t for w in ["sleep", "stress", "workout", "diet", "exercise", "mental"]):
            score += 1.0

    return score


def _domain(url: str) -> str:
    return urlparse(url).netloc


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

        score = _score_title(text, source.section)
        if score < -1:
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

    for section, src_list in sections.items():
        for src in src_list:
            try:
                articles = fetch_from_source(src)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Error fetching from %s: %s", src.url, exc)
                continue
            results[section].extend(articles)

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
