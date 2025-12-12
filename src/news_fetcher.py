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
# CURADORIA
# ------------------------------

POSITIVE_KEYWORDS = [
    # Digital health / tecnologia
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

    # Operadoras / mercado privado
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

    # Hospitais / provedores privados com viés de gestão/tecnologia
    "hospital",
    "rede hospitalar",
    "gestão hospitalar",
    "gestao hospitalar",
    "acreditação",
    "acreditacao",

    # Saúde mental
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

    # Wellness / longevity / performance
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

    # Prescrição eletrônica
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
    # Política pública generalista / ruído
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
    "obra no hospital",
    "licitação",
    "licitacao",
    "concurso público",
    "concurso publico",

    # Conteúdo policial / tragédia
    "morte de criança",
    "morre criança",
    "morre paciente",
    "crime",
    "assassinato",
    "violência",
    "violencia",

    # Nutrição/casa (muito genérico)
    "receita de",
    "como preparar",
    "cozinhar",
    "cozinha",
    "salada",

    # Polarização vacinas genéricas
    "cdc ",
    "acip",
    "sarampo",
    "pólio",
    "polio",
    "campanha de vacinação",
    "campanha de vacinacao",

    # Foco fora (próstata)
    "câncer de próstata",
    "cancer de prostata",
    "próstata",
    "prostata",
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
# DATA (D-1 / D-2 por seção)
# ------------------------------

MONTHS_PT = {
    "jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6,
    "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12,
}
MONTHS_EN = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}


def _parse_date_from_text(text: str) -> Optional[date]:
    if not text:
        return None
    t = text.lower()

    # PT: 2.dez.2025
    m = re.search(r"(\d{1,2})\.(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)\.(\d{4})", t)
    if m:
        return date(int(m.group(3)), MONTHS_PT[m.group(2)], int(m.group(1)))

    # Numérico: 02.12.2025
    m = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", t)
    if m:
        return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))

    # ISO: 2025-12-11
    m = re.search(r"(20\d{2})-(\d{2})-(\d{2})", t)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    # EN: Dec 4, 2025 / December 4, 2025
    m = re.search(
        r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|"
        r"sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\.?\s+(\d{1,2}),\s+(\d{4})",
        t,
    )
    if m:
        month = MONTHS_EN[m.group(1)]
        day = int(m.group(2))
        year = int(m.group(3))
        return date(year, month, day)

    return None


def _parse_date_from_url(url: str) -> Optional[date]:
    if not url:
        return None
    m = re.search(r"/(20\d{2})/(\d{1,2})/(\d{1,2})/", url)
    if not m:
        return None
    return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))


def fetch_html(url: str, timeout: int = 15) -> Optional[str]:
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 (NewsSaudeBot)"})
        with urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="ignore")
    except (HTTPError, URLError, TimeoutError) as e:
        logger.warning(f"Erro ao buscar {url}: {e}")
        return None


def normalize_amp_url(url: str) -> str:
    if not url:
        return url

    if "cdn.ampproject.org" in url:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        if "url" in qs and qs["url"]:
            return unquote(qs["url"][0])

    return url.replace("/amp/", "/")


def is_recent_with_article_fetch(title: str, url: str, max_days: int) -> bool:
    """
    Data é obrigatória:
    - tenta achar em título/URL
    - se não achou, busca no HTML do artigo
    - se ainda não achou -> REPROVA (evita evergreen/sem data)
    """
    today = datetime.now().date()

    d = _parse_date_from_text(title) or _parse_date_from_url(url)
    if d:
        delta = (today - d).days
        return 0 <= delta <= max_days

    html = fetch_html(url)
    if html:
        d2 = _parse_date_from_text(html) or _parse_date_from_url(url)
        if d2:
            delta = (today - d2).days
            return 0 <= delta <= max_days

    return False


# ------------------------------
# SCORE (estratégico > evento físico)
# ------------------------------

STRATEGIC_TERMS = {
    # M&A / investimentos
    "aquisição": 7.0, "aquisicao": 7.0, "compra": 6.0, "fusão": 7.0, "fusao": 7.0,
    "m&a": 7.0, "merge": 6.0, "acquire": 6.0, "acquisition": 6.0,
    "capta": 6.0, "captação": 6.0, "captacao": 6.0, "rodada": 6.0,
    "investimento": 5.0, "investidor": 5.0, "venture": 5.0, "funding": 5.0,

    # Estratégia comercial / produto
    "assinatura": 6.0, "subscription": 6.0, "lança": 5.0, "lanca": 5.0,
    "lançamento": 5.0, "lancamento": 5.0, "expansão": 6.0, "expansao": 6.0,
    "parceria": 6.0, "joint venture": 7.0, "contrato": 5.0, "acordo": 5.0,
    "modelo": 4.0, "precificação": 4.0, "precificacao": 4.0, "marketplace": 4.0,

    # Regulação / operadoras
    "ans": 6.0, "rn": 5.0, "norma": 5.0, "regulação": 5.0, "regulacao": 5.0,
    "plano de saúde": 5.0, "plano de saude": 5.0, "operadora": 5.0,
    "sinistralidade": 5.0, "coparticipação": 4.0, "coparticipacao": 4.0,
}

PHYSICAL_EVENT_TERMS = {
    "inaugura": -5.0, "inauguração": -5.0, "inauguracao": -5.0,
    "abre novo": -4.0, "abertura": -3.0, "cerimônia": -3.0, "cerimonia": -3.0,
    "evento": -3.0, "congresso": -3.0, "feira": -3.0, "seminário": -3.0, "seminario": -3.0,
    "workshop": -3.0, "prêmio": -3.0, "premio": -3.0, "premiação": -3.0, "premiacao": -3.0,
}


def compute_score(article: Article) -> float:
    title = (article.title or "").lower()
    url = (article.url or "").lower()
    source = (article.source_name or "").lower()

    score = 0.0

    # Base por palavras positivas
    for word in POSITIVE_KEYWORDS:
        if word in title:
            score += 1.0

    # Bônus temáticos “core”
    if "telemedicina" in title or "atendimento virtual" in title:
        score += 6.0
    if "saúde mental" in title or "saude mental" in title or "bets" in title:
        score += 5.0
    if "inteligência artificial" in title or "inteligencia artificial" in title or " ia " in title:
        score += 4.0

    # (pedido) Estratégico > evento físico
    for term, w in STRATEGIC_TERMS.items():
        if term in title:
            score += w
    for term, w in PHYSICAL_EVENT_TERMS.items():
        if term in title:
            score += w

    # Boost veículos business (quando existirem nas fontes)
    if "bloomberglinea" in url or "bloomberg.com" in url:
        score += 7.0
    if "neofeed" in url:
        score += 6.0
    if "exame.com" in url:
        score += 5.0
    if "valor.globo.com" in url or "valor" in source:
        score += 4.0

    # seção healthtech costuma ter bom sinal
    if article.section == SECTION_HEALTHTECHS:
        score += 2.0

    return score


# ------------------------------
# BLOCKLIST (URL institucionais/hubs)
# ------------------------------

URL_BLACKLIST_SUBSTR = [
    # Saúde Digital News institucional repetido
    "saudedigitalnews.com.br/receba",

    # hubs / tags
    "oglobo.globo.com/tudo-sobre/",
    "/tudo-sobre/",
    "/assunto/",
    "/tag/",
    "/tags/",

    # Medicina S/A branded/evergreen (do seu feedback)
    "medicinasa.com.br/conexa-edi",
    "medicinasa.com.br/unip-longevidade",
    "medicinasa.com.br/conexa-assefaz",
    "medicinasa.com.br/noa-notes",
    "medicinasa.com.br/noa-notes-recursos",
]

URL_BLOCKLIST_KEYWORDS = [
    "receba",
    "assine",
    "newsletter",
    "tudo-sobre",
    "assunto",
    "/tag/",
    "/tags/",
    "/sobre",
]

BLOCKED_DOMAINS_SUBSTR = [
    "folha.uol.com.br/equilibrio",
    "folha.uol.com.br/equilibrioesaude",
]


def is_blacklisted_url(url: str) -> bool:
    u = (url or "").lower()
    if any(d in u for d in BLOCKED_DOMAINS_SUBSTR):
        return True
    if any(p in u for p in URL_BLACKLIST_SUBSTR):
        return True
    if any(k in u for k in URL_BLOCKLIST_KEYWORDS):
        return True
    return False


# ------------------------------
# LINK EXTRACTION
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

    # ✅ Ajuste pedido: Brasil D-2; outras seções D-1
    max_days = 2 if source.section == SECTION_BRASIL else 1

    for link in parser.links:
        if len(articles) >= MAX_ARTICLES_PER_SOURCE:
            break

        href = normalize_amp_url(link["href"])
        text = link["text"]

        if not href.startswith(base_domain):
            continue

        if href in seen_urls:
            continue

        if is_blacklisted_url(href):
            continue

        title = re.sub(r"\s+", " ", (text or "")).strip()
        if len(title) < 25:
            continue

        if not is_relevant(title):
            continue

        if not is_recent_with_article_fetch(title, href, max_days=max_days):
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
