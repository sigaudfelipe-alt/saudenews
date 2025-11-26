import feedparser
import requests
from bs4 import BeautifulSoup


# Fontes organizadas por seção da newsletter
RSS_SOURCES = {
    "brasil_operadoras": [
        # Jornais e negócios no Brasil
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
    "mundo_saude_global": [
        # Saúde global / sistemas de saúde
        "https://rss.nytimes.com/services/xml/rss/nyt/Health.xml",
        "https://www.who.int/feeds/entity/mediacentre/news/en/rss.xml",
    ],
    "healthtechs": [
        # Inovação, healthtechs e digital health
        "https://techcrunch.com/feed/",
        "https://www.businessinsider.com/sai/rss",
    ],
    "wellness": [
        # Bem-estar, saúde mental, lifestyle (EUA/Europa)
        "https://rss.nytimes.com/services/xml/rss/nyt/Well.xml",
    ],
}


def fetch_rss(url, max_items=7):
    """Busca itens de um feed RSS e devolve uma lista de dicionários básicos."""
    try:
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:max_items]:
            summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
            summary = summary.replace("\n", " ").strip()
            if len(summary) > 260:
                summary = summary[:257] + "..."

            items.append(
                {
                    "title": entry.title,
                    "link": entry.link,
                    "summary": summary,
                    "source": url,
                }
            )
        return items
    except Exception:
        return []


def fetch_all_news():
    """Retorna um dicionário com as listas de notícias por seção da newsletter."""
    all_news = {}
    for section_key, urls in RSS_SOURCES.items():
        section_items = []
        for url in urls:
            section_items.extend(fetch_rss(url))
        all_news[section_key] = section_items[:20]
    return all_news
