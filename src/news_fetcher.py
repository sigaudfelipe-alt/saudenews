from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime, date
from html.parser import HTMLParser
from typing import Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse, parse_qs, unquote
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


# ------------------------------
# CURADORIA (reaproveita o seu modelo)
# ------------------------------

POSITIVE_KEYWORDS = [
    "telemedicina",
    "teleatendimento",
    "saúde digital",
    "saude digital",
    "healthtech",
    "prontuário eletrônico",
    "prontuario eletrônico",
    "prontuario eletronico",
    "inteligência artificial",
    "inteligencia artificial",
    " ia ",
    "machine learning",
    "algoritmo",
    "dados de saúde",
    "dados em saúde",
    "dados de saude",
    "dados em saude",
    "analytics",
    "big data",
    "plataforma digital",
    "app de saúde",
    "app de saude",
    "aplicativo de saúde",
    "aplicativo de saude",
    "monitoramento remoto",
    "monitorização remota",
    "monitorizacao remota",
    "atendimento virtual",
    "consulta virtual",
    "gestão de crônicos",
    "gestao de cronicos",
    "operadora",
    "plano de saúde",
    "plano de saude",
    "planos de saúde",
    "planos de saude",
    " ans ",
    "ans:",
    "sinistralidade",
    "autogestão",
    "autogestao",
    "coparticipação",
    "coparticipacao",
    "seguro saúde",
    "seguro saude",
    "seguros saúde",
    "seguros saude",
    "medicina de grupo",
    "hospital",
    "rede hospitalar",
    "gestão hospitalar",
    "gestao hospitalar",
    "acreditação",
    "acreditacao",
    "saúde mental",
    "saude mental",
    "burnout",
    "depressão",
    "depressao",
    "ansiedade",
    "compulsão",
    "compulsao",
    "bets",
    "jogo on-line",
    "jogo online",
    "wellness",
    "longevity",
    "longevidade",
    "performance",
    "alta performance",
    "sono",
    "sleep",
    "recovery",
    "fitness",
    "atividade física",
    "atividade fisica",
    "treinamento",
    "treino",
    "hábito saudável",
    "habito saudavel",
    "hábitos saudáveis",
    "habitos saudaveis",
    "prescrição eletrônica",
    "prescricao eletronica",
    "prescrição digital",
    "prescricao digital",
    "receita digital",
    "receituário digital",
    "receituario digital",
    "plataforma de prescrição",
    "plataforma de prescricao",
]

NEGATIVE_KEYWORDS = [
    "prefeitura",
    "prefeito",
    "governo de",
    "governo do ",
    "governo da ",
    "governador",
    "secretaria de saúde",
    "secretaria da saúde",
    "secretaria de saude",
    "secretaria da saude",
    "hospital municipal",
    "unidade básica de saúde",
    "unidade basica de saude",
    "ubs ",
    "inaugura novas instalações",
    "inaugura novas instalacoes",
    "inaugura novo hospital",
    "obra no hospital",
    "licitação",
    "licitacao",
    "concurso público",
    "concurso publico",
    "vacina contra hepatite",
    "vacina contra a hepatite",
    "cdc vaccine",
    "cdc ",
    "acip",
    "hepatite b",
    "sarampo",
    "pólio",
    "polio",
    "campanha de vacinação",
    "campanha de vacinacao",
    "imunização infantil",
    "imunizacao infantil",
    "rfk jr",
    "kennedy’s methodical",
    "kennedy's methodical",
    "veja quais alimentos",
    "alimentos que ajudam",
    "receita de",
    "como preparar",
    "cozinhar",
    "cozinha",
    "salada",
    "tomate, melancia e goiaba",
    "tomate, melancia, goiaba",
    "my therapist",
    "thicker, healthier hair",
    "best products for thicker, healthier hair",
    "melhores produtos para cabelo",
    "morte de criança",
    "morre criança",
    "morre paciente",
    "crime",
    "assassinato",
    "violência",
    "violencia",
    "câncer de próstata",
    "cancer de prostata",
    "próstata",
    "prostata",
    "indústria farmacêutica",
    "industria farmaceutica",
    " farmacêutica",
    " farmaceutica",
]


def is_relevant(text: str) -> bool:
    if not text:
        return False
    t = text.lower()

    for word in NEGATIVE_KEYWORDS:
        if word in t:
            return False

    return any(word in t for word in POSITIVE_KEYWORDS)


# ------------------------------
# BLOQUEIOS (novos)
# ------------------------------

# Remover “hubs”, páginas institucionais e páginas repetidas/sem conteúdo
URL_BLOCKLIST_SUBSTR = [
    # Saúde Digital News (CTA repetido)
    "saudedigitalnews.com.br/receba-saude-digital-news-no-seu-e-mail",
    # O Globo hubs / tags / assunto
    "oglobo.globo.com/tudo-sobre/",
    "/tudo-sobre/",
    "/assunto/",
    "/tag/",
    # Medicina S/A – páginas evergreen que já apareceram antigas
    "medicinasa.com.br/conexa-edi",
    "medicinasa.com.br/unip-longevidade",
    "medicinasa.com.br/conexa-assefaz",
    "medicinasa.com.br/noa-notes",
    "medicinasa.com.br/noa-notes-recursos",
]

TITLE_BLOCKLIST_SUBSTR = [
    "receba saúde digital news",
    "receba saude digital news",
    "saiba mais sobre",
]

BLOCKED_DOMAINS_SUBSTR = [
    # Bloqueio hard de Folha Equilíbrio (mesmo se alguém reintroduzir fonte)
    "folha.uol.com.br/equilibrio",
    "folha.uol.com.br/equilibrioesaude",
]


def is_blacklisted(url: str, title: str) -> bool:
    u = (url or "").lower()
    t = (title or "").lower()

    if any(d in u for d in BLOCKED_DOMAINS_SUBSTR):
        return True
    if any(p in u for p in URL_BLOCKLIST_SUBSTR):
        return True
    if any(p in t for p in TITLE_BLOCKLIST_SUBSTR):
        return True
    return False


def normalize_amp_url(url: str) -> str:
    """
    Normaliza URLs AMP (ex.: Bloomberg via cdn.ampproject.org).
    """
    if not url:
        return url
    u = url.strip()
    if "cdn.ampproject.org" in u:
        parsed = urlparse(u)
        qs = parse_qs(parsed.query)
        if "url" in qs and qs["url"]:
            return unquote(qs["url"][0])
    # fallback simples para /amp/
    return u.replace("/amp/", "/")


# ------------------------------
# FILTRO DE DATA (D-1 / D-2)
# ------------------------------

MONTHS_PT = {
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

MONTHS_EN = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}


def _parse_date_from_text(text: str) -> Optional[date]:
    if not text:
        return None
    t = text.lower()

    # PT: 2.dez.2025
    m = re.search(r"(\d{1,2})\.(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)\.(\d{4})", t)
    if m:
        day = int(m.group(1))
        month = MONTHS_PT[m.group(2)]
        year = int(m.group(3))
        return date(year, month, day)

    # Numérico: 02.12.2025
    m = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", t)
    if m:
        day = int(m.group(1))
        month = int(m.group(2))
        year = int(m.group(3))
        return date(year, month, day)

    # ISO: 2025-12-11
    m = re.search(r"(20\d{2})-(\d{2})-(\d{2})", t)
    if m:
        year = int(m.group(1))
        month = int(m.group(2))
        day = int(m.group(3))
        return date(year, month, day)

    # EN: December 4, 2025 / Dec. 4, 2025
    m = re.search(
        r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|"
        r"sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\.?\s+(\d{1,2}),\s+(\d{4})",
        t,
    )
    if m:
        month_name = m.group(1)
        day = int(m.group(2))
        year = int(m.group(3))
        month = MONTHS_EN[month_name]
        return date(year, month, day)

    return None


def _parse_date_from_url(url: str) -> Optional[date]:
    """
    Captura datas no formato /YYYY/MM/DD/ em URLs.
    """
    if not url:
        return None
    m = re.search(r"/(20\d{2})/(\d{1,2})/(\d{1,2})/", url)
    if not m:
        return None
    year = int(m.group(1))
    month = int(m.group(2))
    day = int(m.group(3))
    return date(year, month, day)


def fetch_html(url: str, timeout: int = 15) -> Optional[str]:
    try:
        req = Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (NewsSaudeBot)"},
        )
        with urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="ignore")
    except (HTTPError, URLError, TimeoutError) as e:
        logger.warning(f"Erro ao buscar {url}: {e}")
        return None


def is_recent_with_article_fetch(title: str, url: str, max_days: int = 2) -> bool:
    """
    ✅ NOVO COMPORTAMENTO:
    - Data é obrigatória.
    - Se não encontrar data em lugar nenhum -> DESCARTA.
    """
    today = datetime.now().date()

    # 1) título + URL
    d = _parse_date_from_text(title) or _parse_date_from_url(url)
    if d:
        delta = (today - d).days
        return 0 <= delta <= max_days

    # 2) conteúdo da página
    html = fetch_html(url)
    if html:
        d2 = _parse_date_from_text(html) or _parse_date_from_url(url)
        if d2:
            delta = (today - d2).days
            return 0 <= delta <= max_days

    # 3) não achou data -> descarta
    return False


def compute_score(article: Article) -> float:
    title = (article.title or "").lower()
    score = 0.0

    for word in POSITIVE_KEYWORDS:
        if word in title:
            score += 1.0

    if "telemedicina" in title or "atendimento virtual" in title:
        score += 6.0

    if "saúde mental" in title or "saude mental" in title or "bets" in title:
        score += 5.0

    if "operadora" in title or "plano de saúde" in title or "plano de saude" in title:
        score += 5.0

    if "inteligência artificial" in title or "inteligencia artificial" in title or " ia " in title:
        score += 4.0

    if "prescrição eletrônica" in title or "prescricao eletronica" in title or "receita digital" in title:
        score += 3.0

    if article.section == SECTION_HEALTHTECHS:
        score += 2.0

    return score


# ------------------------------
# FETCH DE LINKS
# ------------------------------

MAX_ARTICLES_PER_SOURCE = 3


class LinkExtractor(HTMLParser):
    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url
        self.current_href: Optional[str] = None
        self.current_text_parts: List[str] = []
        self.links: List[Dict[str, str]] = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        href = None
        for name, value in attrs:
            if name == "href":
                href = value
                break
        if href:
            self.current_href = urljoin(self.base_url, href)
            self.current_text_parts = []

    def handle_data(self, data):
        if self.current_href:
            self.current_text_parts.append((data or "").strip())

    def handle_endtag(self, tag):
        if tag == "a" and self.current_href:
            text = " ".join([t for t in self.current_text_parts if t]).strip()
            if text:
                self.links.append({"href": self.current_href, "text": text})
            self.current_href = None
            self.current_text_parts = []


def extract_domain(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def fetch_articles_from_source(source: Source) -> List[Article]:
    html = fetch_html(source.base_url)
    if not html:
        return []

    parser = LinkExtractor(source.base_url)
    parser.feed(html)

    articles: List[Article] = []
    seen_urls = set()
    base_domain = extract_domain(source.base_url)

    for link in parser.links:
        if len(articles) >= MAX_ARTICLES_PER_SOURCE:
            break

        href = normalize_amp_url(link["href"])
        text = link["text"]

        # só links do próprio domínio da fonte
        if not href.startswith(base_domain):
            continue

        if href in seen_urls:
            continue

        title = re.sub(r"\s+", " ", (text or "")).strip()
        if len(title) < 25:
            continue

        # bloqueios gerais (URL/título)
        if is_blacklisted(href, title):
            continue

        # curadoria por relevância
        if not is_relevant(title):
            continue

        # data obrigatória + D-2
        if not is_recent_with_article_fetch(title, href, max_days=2):
            continue

        seen_urls.add(href)
        articles.append(
            Article(
                title=title,
                url=href,
                source_name=source.name,
                section=source.section,
            )
        )

    return articles


def fetch_all_articles() -> List[Article]:
    all_articles: List[Article] = []

    for section, sources in sources_by_section.items():
        for src in sources:
            logger.info(f"Buscando notícias em {src.name} ({section})")
            try:
                src_articles = fetch_articles_from_source(src)
            except Exception as e:  # noqa: BLE001
                logger.exception(f"Erro ao processar fonte {src.name}: {e}")
                continue

            for art in src_articles:
                # bloqueio hard (caso fonte volte)
                if is_blacklisted(art.url, art.title):
                    continue

                art.score = compute_score(art)
                all_articles.append(art)

    all_articles.sort(key=lambda a: a.score, reverse=True)
    return all_articles


def group_articles_by_section(articles: List[Article]) -> Dict[str, List[Article]]:
    grouped: Dict[str, List[Article]] = {
        SECTION_BRASIL: [],
        SECTION_MUNDO: [],
        SECTION_HEALTHTECHS: [],
        SECTION_WELLNESS: [],
    }

    seen_urls = set()

    for art in articles:
        if not is_relevant(art.title):
            continue

        if art.url in seen_urls:
            continue
        seen_urls.add(art.url)

        grouped.setdefault(art.section, []).append(art)

    for sec in grouped:
        grouped[sec] = grouped[sec][:20]

    return grouped


def fetch_all_news() -> Dict[str, List[Article]]:
    articles = fetch_all_articles()
    return group_articles_by_section(articles)


if __name__ == "__main__":
    arts = fetch_all_articles()
    print(f"Total de artigos relevantes: {len(arts)}")
    for a in arts[:10]:
        print(f"- ({a.section}) [{a.score:.1f}] {a.title} -> {a.url}")
