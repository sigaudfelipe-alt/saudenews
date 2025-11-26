import feedparser
from bs4 import BeautifulSoup

# Fontes organizadas por seÃ§Ã£o da newsletter
RSS_SOURCES = {
    "brasil_operadoras": [
        # MinistÃ©rio da SaÃºde / SUS / ANS / Governo
        "https://www.gov.br/saude/pt-br/assuntos/noticias/@@rss.xml",
        "https://www.gov.br/ans/pt-br/assuntos/noticias-ans/@@rss.xml",
        # AgÃªncia Brasil â SaÃºde
        "https://agenciabrasil.ebc.com.br/rss/saude.xml",
        # Especializados em saÃºde no Brasil
        "https://medicinasa.com.br/feed/",
        "https://healthcare.grupomidia.com/feed/",
        "https://saudedigitalnews.com.br/feed/",
        # Jornais / negÃ³cios â filtrados por palavras de operadoras/SUS
        "https://valor.globo.com/rss/",
        "https://oglobo.globo.com/rss.xml",
        "https://www.braziljournal.com/feed/",
        "https://neofeed.com.br/feed/",
        "https://pipelinevalor.globo.com/rss/",
    ],
    "mundo_saude_global": [
        "https://rss.nytimes.com/services/xml/rss/nyt/Health.xml",
        "https://www.who.int/feeds/entity/mediacentre/news/en/rss.xml",
    ],
    "healthtechs": [
        "https://techcrunch.com/feed/",
        "https://www.businessinsider.com/sai/rss",
        # Feeds adicionais para notÃ­cias de funding e startups
        "https://www.mobihealthnews.com/rss",
        "https://www.digitalhealth.net/feed/",
    ],
    "wellness": [
        "https://rss.nytimes.com/services/xml/rss/nyt/Well.xml",
    ],
}

# Palavras-chave para saÃºde em geral (portuguÃªs/inglÃªs)
HEALTH_KEYWORDS_PT = [
    "saÃºde", "hospital", "hospitais", "clÃ­nica", "clÃ­nicas",
    "laboratÃ³rio", "laboratÃ³rios", "diagnÃ³stico", "exame",
    "vacina", "vacinas", "tratamento", "doenÃ§a", "doenÃ§as",
    "oncologia", "cÃ¢ncer", "cardiologia", "uti", "internaÃ§Ã£o",
    "unidade bÃ¡sica de saÃºde", "ubs", "upas", "atenÃ§Ã£o primÃ¡ria",
]

HEALTH_KEYWORDS_EN = [
    "health", "healthcare", "hospital", "clinic", "clinics",
    "diagnostic", "diagnostics", "disease", "diseases",
    "vaccine", "vaccines", "treatment",
]

# Palavras especÃ­ficas para operadoras/planos/SUS/hospitais/labs
BR_OPERADORAS_KEYWORDS = [
    "plano de saÃºde", "planos de saÃºde", "plano de saude", "planos de saude",
    "operadora", "operadoras", "seguro saÃºde", "seguro-saÃºde", "seguro saude",
    "convÃªnio mÃ©dico", "convenio mÃ©dico", "convenio medico",
    "coparticipaÃ§Ã£o", "coparticipacao",
    "ans", "agÃªncia nacional de saÃºde suplementar",
    "sus", "sistema Ãºnico de saÃºde",
    "rede credenciada", "rede prÃ³pria", "rede prÃ³pria de hospitais",
    "hospitais filantrÃ³picos", "hospital filantrÃ³pico",
    # nomes de players e grupos de saÃºde
    "unimed", "hapvida", "notredame", "amil", "bradesco saÃºde",
    "sulamÃ©rica saÃºde", "sulamerica saÃºde", "sulamerica saude",
    "rede d'or", "rede dor", "dasa", "fleury", "oncoclÃ­nicas", "oncoclinicas",
    "laboratÃ³rio clÃ­nico", "laboratorio clÃ­nico", "laboratorio clinico",
]

# Palavras para wellness/bem-estar
WELLNESS_KEYWORDS = [
    "wellness", "bem-estar", "bem estar",
    "saÃºde mental", "saude mental",
    "ansiedade", "depressÃ£o", "depressao",
    "sono", "sleep", "insÃ´nia", "insonia",
    "mindfulness", "meditaÃ§Ã£o", "meditacao",
    "burnout", "stress", "estresse",
    "atividade fÃ­sica", "atividade fisica", "exercÃ­cio", "exercicio",
    "lifestyle",
]

def _clean_summary(raw_summary: str) -> str:
    """Remove HTML tags and trims the summary to ~260 chars."""
    if not raw_summary:
        return ""
    text = BeautifulSoup(raw_summary, "html.parser").get_text(separator=" ")
    text = text.replace("\n", " ").strip()
    if len(text) > 260:
        text = text[:257] + "..."
    return text

def is_relevant(section: str, title: str, summary: str) -> bool:
    """Decides whether a news item is relevant to the section."""
    text = f"{title} {summary}".lower()

    if section == "brasil_operadoras":
        return any(k in text for k in BR_OPERADORAS_KEYWORDS)

    if section == "healthtechs":
        # Terms indicating digital health/telehealth/AI
        base_terms = [
            "digital health", "healthtech", "health tech",
            "telemedicina", "teleconsulta", "telehealth", "telemedicine",
            "inteligÃªncia artificial", "ai in healthcare",
            "ia na saÃºde", "machine learning",
            "prontuÃ¡rio eletrÃ´nico", "prontuario eletronico",
            "app de saÃºde", "health app",
        ]
        # Terms indicating innovation/startups/investment
        innovation_terms = [
            "startup", "start-up", "startups",
            "funding", "fundraise", "investimento", "investimentos",
            "investment", "seed round", "series a", "series b",
            "vc", "venture capital",
            "unicÃ³rnio", "unicorn", "avaliado em", "valuation",
        ]
        return any(b in text for b in base_terms) and any(i in text for i in innovation_terms)

    if section == "wellness":
        return any(k in text for k in WELLNESS_KEYWORDS)

    if section == "mundo_saude_global":
        global_keywords = (
            HEALTH_KEYWORDS_EN + [
                "health insurance", "insurance premiums",
                "medicare", "medicaid",
                "universal health coverage", "universal health care",
            ]
        )
        return any(k in text for k in global_keywords)

    return False

def fetch_rss(url: str, section: str, max_items: int = 20):
    """Fetches items from an RSS feed, filters by relevance, and returns a list of dicts."""
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
    Returns a dict with lists of news items per section, already filtered for
    health/operadoras/hospitals/labs/healthtech/wellness.
    """
    all_news = {}
    for section_key, urls in RSS_SOURCES.items():
        section_items = []
        for url in urls:
            section_items.extend(fetch_rss(url, section_key))
        all_news[section_key] = section_items[:20]
    return all_news
