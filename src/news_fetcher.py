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

    # Prescrição eletrônica / Memed / e-prescription
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
    # SUS / política pública generalista (mais específicos, sem bloquear "sus" inteiro)
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

    # Vacina / política de imunização genérica e polarizada
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

    # Nutrição generalista / culinária
    "veja quais alimentos",
    "alimentos que ajudam",
    "receita de",
    "como preparar",
    "cozinhar",
    "cozinha",
    "salada",
    "tomate, melancia e goiaba",
    "tomate, melancia, goiaba",

    # Lifestyle muito genérico
    "my therapist",
    "thicker, healthier hair",
    "best products for thicker, healthier hair",
    "melhores produtos para cabelo",

    # Conteúdo policial / tragédia
    "morte de criança",
    "morre criança",
    "morre paciente",
    "crime",
    "assassinato",
    "violência",
    "violencia",

    # Doenças específicas que não queremos (prostata)
    "câncer de próstata",
    "cancer de prostata",
    "próstata",
    "prostata",

    # Farmacêutica corporativa que não é foco
    "indústria farmacêutica",
    "industria farmaceutica",
    " farmacêutica",
    " farmaceutica",
    " ems ",
]


def is_relevant(text: str) -> bool:
    if not text:
        return False

    t = text.lower()

    # 1) filtro negativo
    for word in NEGATIVE_KEYWORDS:
        if word in t:
            return False

    # 2) exige ao menos um termo positivo
    for word in POSITIVE_KEYWORDS:
        if word in t:
            return True

    return False


# ------------------------------
# FILTRO DE DATA (D-1)
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
    t = text.lower()

    # Formato PT: 2.dez.2025
    m = re.search(r"(\d{1,2})\.(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)\.(\d{4})", t)
    if m:
        day = int(m.group(1))
        month = MONTHS_PT[m.group(2)]
        year = int(m.group(3))
        return date(year, month, day)

    # Formato numérico: 02.12.2025
    m = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", t)
    if m:
        day = int(m.group(1))
        month = int(m.group(2))
        year = int(m.group(3))
        return date(year, month, day)

    # Inglês: December 4, 2025 / Dec. 4, 2025
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
    Captura datas no formato /YYYY/MM/DD/ em URLs (ex: Valor, O Globo etc.).
    """
    m = re.search(r"/(20\d{2})/(\d{1,2})/(\d{1,2})/", url)
    if not m:
        return None
    year = int(m.group(1))
    month = int(m.group(2))
    day = int(m.group(3))
    return date(year, month, day)


def is_recent_from_any(text: str, url: str, max_days: int = 1) -> bool:
    """
    Tenta achar a data no texto OU na URL.
    Se achar, aplica D-1.
    Se não achar nada, assume recente (para não matar fontes que não expõem data no anchor).
    """
    d = _parse_date_from_text(text) or _parse_date_from_url(url)
    if not d:
        return True

    today = datetime.now().date()
    delta = (today - d).days
    return 0 <= delta <= max_days


def compute_score(article: Article) -> float:
    title = article.title.lower()
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

    # Prescrição eletrônica / digital – dar um bônus
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
            self.current_text_parts.append(data.strip())

    def handle_endtag(self, tag):
        if tag == "a" and self.current_href:
            text = " ".join([t for t in self.current_text_parts if t]).strip()
            if text:
                self.links.append({"href": self.current_href, "text": text})
            self.current_href = None
            self.current_text_parts = []


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


def extract_domain(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


# URLs que não queremos NUNCA (conteúdo antigo / branded que já se repetiu)
URL_BLACKLIST_SUBSTR = [
    "medicinasa.com.br/conexa-assefaz",
    "medicinasa.com.br/noa-notes",
    "medicinasa.com.br/noa-notes-recursos",
]


def is_blacklisted_url(url: str) -> bool:
    u = url.lower()
    return any(pattern in u for pattern in URL_BLACKLIST_SUBSTR)


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

        href = link["href"]
        text = link["text"]

        if not href.startswith(base_domain):
            continue

        if href in seen_urls:
            continue

        if is_blacklisted_url(href):
            continue

        title = re.sub(r"\s+", " ", text).strip()
        if len(title) < 25:
            continue

        if not is_relevant(title):
            continue

        # Filtro D-1 considerando também a data na URL
        if not is_recent_from_any(title, href, max_days=1):
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
    """
    Agrupa por seção com trava global de URL:
    - mesma matéria NUNCA aparece em duas seções (evita repetição Mundo/Healthtechs).
    """
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
            # já colocamos essa URL em alguma seção, não repetir
            continue
        seen_urls.add(art.url)

        if art.section not in grouped:
            grouped[art.section] = []
        grouped[art.section].append(art)

    # Limite de segurança por seção
    for sec in grouped:
        grouped[sec] = grouped[sec][:20]

    return grouped


def get_top_n(articles: List[Article], n: int = 5) -> List[Article]:
    return sorted(articles, key=lambda a: a.score, reverse=True)[:n]


def fetch_all_news() -> Dict[str, List[Article]]:
    articles = fetch_all_articles()
    sections = group_articles_by_section(articles)
    return sections


if __name__ == "__main__":
    arts = fetch_all_articles()
    print(f"Total de artigos relevantes: {len(arts)}")
    for a in get_top_n(arts, 10):
        print(f"- ({a.section}) [{a.score:.1f}] {a.title} -> {a.url}")
