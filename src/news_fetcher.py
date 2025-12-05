from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
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
# NOVA LÓGICA DE CURADORIA
# ------------------------------

# Palavras que indicam que a notícia é RELEVANTE para:
# - Saúde Digital
# - Operadoras / Planos
# - Saúde mental
# - Wellness de performance / longevity
POSITIVE_KEYWORDS = [
    # Digital health / tecnologia
    "telemedicina",
    "teleatendimento",
    "saúde digital",
    "healthtech",
    "prontuário eletrônico",
    "prontuario eletrônico",
    "prontuario eletronico",
    "inteligência artificial",
    "inteligencia artificial",
    "ia",
    "machine learning",
    "algoritmo",
    "dados de saúde",
    "dados em saúde",
    "analytics",
    "big data",
    "plataforma digital",
    "app de saúde",
    "aplicativo de saúde",
    "monitoramento remoto",
    "monitorização remota",
    "atendimento virtual",
    "consulta virtual",
    "gestão de crônicos",
    "gestão de cronicos",

    # Operadoras / mercado privado
    "operadora",
    "plano de saúde",
    "planos de saúde",
    "plano de saude",
    "planos de saude",
    "ans ",
    "ans:",
    "sinistralidade",
    "autogestão",
    "autogestao",
    "coparticipação",
    "coparticipacao",
    "seguros saúde",
    "seguro saúde",
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
]

# Palavras que indicam que a notícia NÃO é adequada ao recorte
# mesmo sendo “de saúde”.
NEGATIVE_KEYWORDS = [
    # SUS / política pública generalista
    " sus ",
    "prefeitura",
    "prefeito",
    "governo de",
    "governo do ",
    "governo da ",
    "governador",
    "secretaria de saúde",
    "secretaria da saúde",
    "hospital municipal",
    "unidade básica de saúde",
    "ubs ",
    "inaugura novas instalações",
    "inaugura novas instalacoes",
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

    # Lifestyle muito genérico (NYTimes Well etc.)
    "my therapist",
    "melhor produto para cabelo",
    "thicker, healthier hair",
    "best products for thicker, healthier hair",
    "pergunta ao colunista",
    "pergunte ao colunista",

    # Conteúdo policial / tragédia
    "morte de criança",
    "morre criança",
    "morre paciente",
    "crime",
    "assassinato",
    "violência",
    "violencia",
]


def is_relevant(text: str) -> bool:
    """
    Decide se uma notícia é ou não relevante para o recorte da News.
    1) Se bater em qualquer NEGATIVE_KEYWORD => exclui.
    2) Só entra se tiver ao menos 1 POSITIVE_KEYWORD.
    """
    if not text:
        return False

    t = text.lower()

    # Regra 1 – filtro negativo
    for word in NEGATIVE_KEYWORDS:
        if word in t:
            return False

    # Regra 2 – exige pelo menos 1 termo positivo
    for word in POSITIVE_KEYWORDS:
        if word in t:
            return True

    return False


def compute_score(article: Article) -> float:
    """
    Score maior para temas centrais da Conexa:
      - Telemedicina
      - Saúde mental
      - Operadoras / planos
      - IA / dados
    """
    title = article.title.lower()
    score = 0.0

    # peso base por quantidade de positivos encontrados
    for word in POSITIVE_KEYWORDS:
        if word in title:
            score += 1.0

    # boosts específicos
    if "telemedicina" in title or "atendimento virtual" in title:
        score += 6.0

    if "saúde mental" in title or "saude mental" in title or "bets" in title:
        score += 5.0

    if "operadora" in title or "plano de saúde" in title or "plano de saude" in title:
        score += 5.0

    if "inteligência artificial" in title or "inteligencia artificial" in title or " ia " in title:
        score += 4.0

    if article.section == SECTION_HEALTHTECHS:
        score += 2.0

    return score


# ------------------------------
# FETCH BÁSICO DE LINKS
# ------------------------------

class LinkExtractor(HTMLParser):
    """
    Parser HTML simples para extrair <a href="">
    """

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


def fetch_articles_from_source(source: Source) -> List[Article]:
    """
    Estratégia simples:
      - Buscar a URL principal da fonte (source.base_url)
      - Extrair todos os links (anchor)
      - Filtrar por relevância de título
    """
    html = fetch_html(source.base_url)
    if not html:
        return []

    parser = LinkExtractor(source.base_url)
    parser.feed(html)

    articles: List[Article] = []
    seen_urls = set()

    base_domain = extract_domain(source.base_url)

    for link in parser.links:
        href = link["href"]
        text = link["text"]

        # manter apenas links internos do site
        if not href.startswith(base_domain):
            continue

        # ignorar anchors repetidos / vazios
        if href in seen_urls:
            continue

        # limpeza básica do título
        title = re.sub(r"\s+", " ", text).strip()
        if len(title) < 25:  # evita títulos muito curtos tipo "Saiba mais"
            continue

        if not is_relevant(title):
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


# ------------------------------
# FUNÇÕES PÚBLICAS DO MÓDULO
# ------------------------------

def fetch_all_articles() -> List[Article]:
    """
    Busca artigos em todas as fontes configuradas em sources.py
    e aplica score de relevância.
    """
    all_articles: List[Article] = []

    for section, sources in sources_by_section.items():
        for src in sources:
            logger.info(f"Buscando notícias em {src.name} ({section})")
            try:
                src_articles = fetch_articles_from_source(src)
            except Exception as e:  # proteção extra para não quebrar o pipeline
                logger.exception(f"Erro ao processar fonte {src.name}: {e}")
                continue

            for art in src_articles:
                art.score = compute_score(art)
                all_articles.append(art)

    # ordena por score decrescente
    all_articles.sort(key=lambda a: a.score, reverse=True)
    return all_articles


def group_articles_by_section(articles: List[Article]) -> Dict[str, List[Article]]:
    """
    Agrupa por seção, já assumindo que tudo aqui já passou por is_relevant().
    Podemos fazer pequenos ajustes adicionais se necessário.
    """
    grouped: Dict[str, List[Article]] = {
        SECTION_BRASIL: [],
        SECTION_MUNDO: [],
        SECTION_HEALTHTECHS: [],
        SECTION_WELLNESS: [],
    }

    for art in articles:
        # segurança: se por acaso apareceu algo com vacina infantil / SUS,
        # ainda excluímos aqui (não deveria, mas é um "double check").
        if not is_relevant(art.title):
            continue

        if art.section not in grouped:
            grouped[art.section] = []
        grouped[art.section].append(art)

    # mantém cada bloco limitado, para não ficar gigante
    for sec in grouped:
        grouped[sec] = grouped[sec][:20]

    return grouped


def get_top_n(articles: List[Article], n: int = 5) -> List[Article]:
    """
    Top N do dia, independente da seção, ordenado por score.
    """
    return sorted(articles, key=lambda a: a.score, reverse=True)[:n]


if __name__ == "__main__":
    # para debug local rápido
    arts = fetch_all_articles()
    print(f"Total de artigos relevantes: {len(arts)}")
    for a in get_top_n(arts, 10):
        print(f"- ({a.section}) [{a.score:.1f}] {a.title} -> {a.url}")
