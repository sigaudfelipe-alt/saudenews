import feedparser
from bs4 import BeautifulSoup
import requests


# Fontes organizadas por seção da newsletter
RSS_SOURCES = {
    # Foco: Operadoras, hospitais, laboratórios e negócios de saúde no Brasil
    "brasil_operadoras": [
        # Jornais / negócios – vamos filtrar por palavras de saúde
        "https://www.estadao.com.br/rss",
        "https://feeds.folha.uol.com.br/emcimadahora/rss091.xml",
        "https://valor.globo.com/rss/",
        "https://oglobo.globo.com/rss.xml",
        "https://www.braziljournal.com/feed/",
        "https://neofeed.com.br/feed/",
        "https://pipelinevalor.globo.com/rss/",
        # Especializados em saúde no Brasil
        "https://medicinasa.com.br/feed/",
        "https://healthcare.grupomidia.com/feed/",
        "https://saudedigitalnews.com.br/feed/",
    ],

    # Foco: sistemas de saúde, políticas, saúde global
    "mundo_saude_global": [
        "https://rss.nytimes.com/services/xml/rss/nyt/Health.xml",
        "https://www.who.int/feeds/entity/mediacentre/news/en/rss.xml",
    ],

    # Foco: healthtechs, digital health, inovação em saúde
    "healthtechs": [
        "https://techcrunch.com/feed/",
        "https://www.businessinsider.com/sai/rss",
    ],

    # Foco: wellness, bem-estar, saúde mental, lifestyle (principalmente EUA/Europa)
    "wellness": [
        "https://rss.nytimes.com/services/xml/rss/nyt/Well.xml",
    ],
}


# Palavras-chave principais de SAÚDE (operadoras, hospitais, labs, SUS, etc.)
HEALTH_KEYWORDS_PT = [
    "saúde", "hospital", "hospitais", "clínica", "clínicas",
    "laboratório", "laboratórios", "diagnóstico", "exame",
    "plano de saúde", "planos de saúde", "operadora", "operadoras",
    "beneficiário", "beneficiários", "ans", "sus",
    "pronto-socorro", "urgência", "emergência",
    "oncologia", "cardiologia", "uti", "internação",
    "rede credenciada", "convênio médico",
]

HEALTH_KEYWORDS_EN = [
    "health", "healthcare", "hospital", "clinic", "clinics",
    "insurer", "insurance", "payer", "medicare", "medicaid",
    "pharma", "biotech", "drug", "drugs", "diagnostic",
    "telehealth", "telemedicine",
]

# Palavras extras para filtrar HEALTHTECH
HEALTHTECH_EXTRA = [
    "digital health", "healthtech", "health tech", "e-health",
    "telemedicina", "telemedicina", "teleconsulta",
    "wearable", "fitness app", "remote patient monitoring",
    "ai in healthcare", "ia na saúde",
]

# Palavras para WELLNESS / bem-estar
WELLNESS_KEYWORDS = [
    "wellness", "bem-estar", "saúde mental", "ansiedade",
    "depressão", "sono", "sleep", "mindfulness", "meditação",
    "burnout", "stress", "estresse", "atividade física",
    "exercício", "lifestyle",
]


def _clean_summary(raw_summary: str) -> str:
    """Limpa HTML básico e corta o tamanho."""
    if not raw_summary:
        return ""
    text = BeautifulSoup(raw_summary, "html.parser").get_text(separator=" ")
    text = text.replace("\n", " ").strip()
    if len(text) > 260:
        text = text[:257] + "..."
    return text


def is_relevant(section: str, title: str, summary: str) -> bool:
    """Decide se a notícia é relevante para saúde/healthtech/wellness."""
    text = f"{title} {summary}".lower()

    # Base de saúde geral
    health_keywords = HEALTH_KEYWORDS_PT + HEALTH_KEYWORDS_EN

    if section == "healthtechs":
        keywords = health_keywords + HEALTHTECH_EXTRA
    elif section == "wellness":
        keywords = WELLNESS_KEYWORDS
    else:
        # brasil_operadoras e mundo_saude_global
        keywords = health_keywords

    return any(k in text for k in keywords)


def fetch_rss(url: str, section: str, max_items: int = 15):
    """Busca itens de um feed RSS, filtra por relevância e devolve dicionários básicos."""
    try:
        feed = feedparser.parse(url)
        items = []

        for entry in feed.entries:
            title = getattr(entry, "title", "").strip()
            raw_summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
            summary = _clean_summary(raw_summary)
            link = getattr(entry, "link", "").strip()

            if not title or not link:
                continue

            # Aplica filtro de relevância por seção
            if not is_relevant(section, title, summary):
                continue

            items.append(
                {
                    "title": title,
                    "link": link,
                    "summary": summary,
                    "source": url,
                }
            )

            if len(items) >= max_items:
                break

        return items
    except Exception:
        return []


def fetch_all_news():
    """
    Retorna um dicionário com as listas de notícias por seção da newsletter,
    já filtradas para temas de saúde / operadoras / hospitais / labs / healthtech / wellness.
    """
    all_news = {}
    for section_key, urls in RSS_SOURCES.items():
        section_items = []
        for url in urls:
            section_items.extend(fetch_rss(url, section_key))
        # Deixa cada seção enxuta
        all_news[section_key] = section_items[:20]
    return all_news
