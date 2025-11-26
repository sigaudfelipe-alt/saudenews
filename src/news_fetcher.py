import feedparser
from bs4 import BeautifulSoup


# Fontes organizadas por seção da newsletter
# Deixei Brasil & Operadoras bem mais focado em saúde / SUS / operadoras
RSS_SOURCES = {
    "brasil_operadoras": [
        # Ministério da Saúde / SUS / ANS / Governo
        "https://www.gov.br/saude/pt-br/assuntos/noticias/@@rss.xml",
        "https://www.gov.br/ans/pt-br/assuntos/noticias-ans/@@rss.xml",
        # Agência Brasil – Saúde
        "https://agenciabrasil.ebc.com.br/rss/saude.xml",
        # Especializados em saúde no Brasil
        "https://medicinasa.com.br/feed/",
        "https://healthcare.grupomidia.com/feed/",
        "https://saudedigitalnews.com.br/feed/",
        # Jornais / negócios – ainda permitidos, mas filtrados por palavras de operadoras/SUS
        "https://valor.globo.com/rss/",
        "https://oglobo.globo.com/rss.xml",
        "https://www.braziljournal.com/feed/",
        "https://neofeed.com.br/feed/",
        "https://pipelinevalor.globo.com/rss/",
    ],

    "mundo_saude_global": [
        # Saúde global / sistemas de saúde / política pública
        "https://rss.nytimes.com/services/xml/rss/nyt/Health.xml",
        "https://www.who.int/feeds/entity/mediacentre/news/en/rss.xml",
    ],

    "healthtechs": [
        # Inovação, digital health, healthtechs
        "https://techcrunch.com/feed/",
        "https://www.businessinsider.com/sai/rss",
    ],

    "wellness": [
        # Bem-estar, saúde mental, hábitos de vida
        "https://rss.nytimes.com/services/xml/rss/nyt/Well.xml",
    ],
}


# Palavras-chave para SAÚDE em geral (português/inglês)
HEALTH_KEYWORDS_PT = [
    "saúde", "hospital", "hospitais", "clínica", "clínicas",
    "laboratório", "laboratórios", "diagnóstico", "exame",
    "vacina", "vacinas", "tratamento", "doença", "doenças",
    "oncologia", "câncer", "cardiologia", "uti", "internação",
    "unidade básica de saúde", "ubs", "upas", "atenção primária",
]

HEALTH_KEYWORDS_EN = [
    "health", "healthcare", "hospital", "clinic", "clinics",
    "diagnostic", "diagnostics", "disease", "diseases",
    "vaccine", "vaccines", "treatment",
]

# Palavras específicas pra OPERADORAS / PLANOS / SUS / HOSPITAIS / LABS
BR_OPERADORAS_KEYWORDS = [
    "plano de saúde", "planos de saúde", "plano de saude", "planos de saude",
    "operadora", "operadoras", "seguro saúde", "seguro-saúde", "seguro saude",
    "convênio médico", "convenio médico", "convenio medico",
    "coparticipação", "coparticipacao",
    "ans", "agência nacional de saúde suplementar",
    "sus", "sistema único de saúde",
    "rede credenciada", "rede própria", "rede própria de hospitais",
    "hospitais filantrópicos", "hospital filantrópico",
    # nomes de players e grupos de saúde (pode ir afinando)
    "unimed", "hapvida", "notredame", "amil", "bradesco saúde",
    "sulamérica saúde", "sulamerica saúde", "sulamerica saude",
    "rede d'or", "rede dor", "dasa", "fleury", "oncoclínicas", "oncoclinicas",
    "laboratório clínico", "laboratorio clínico", "laboratorio clinico",
]

# Palavras extras para HEALTHTECH
HEALTHTECH_EXTRA = [
    "digital health", "healthtech", "health tech", "e-health",
    "telemedicina", "teleconsulta", "teleconsulta", "telehealth", "telemedicine",
    "prontuário eletrônico", "prontuario eletronico", "rpm", "remote patient monitoring",
    "ai in healthcare", "ia na saúde", "inteligência artificial na saúde",
]

# Palavras pra WELLNESS / bem-estar
WELLNESS_KEYWORDS = [
    "wellness", "bem-estar", "bem estar",
    "saúde mental", "saude mental",
    "ansiedade", "depressão", "depressao",
    "sono", "sleep", "insônia", "insonia",
    "mindfulness", "meditação", "meditacao",
    "burnout", "stress", "estresse",
    "atividade física", "atividade fisica", "exercício", "exercicio",
    "lifestyle",
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
    """Decide se a notícia é relevante para cada seção."""
    text = f"{title} {summary}".lower()

    # Seção Brasil – Saúde & Operadoras:
    # bem mais restrita: precisa bater em SUS/operadoras/hospitais/labs
    if section == "brasil_operadoras":
        return any(k in text for k in BR_OPERADORAS_KEYWORDS)

    # Healthtechs: base de saúde + termos de tech
    if section == "healthtechs":
        base = HEALTH_KEYWORDS_EN + HEALTH_KEYWORDS_PT + HEALTHTECH_EXTRA
        return any(k in text for k in base)

    # Wellness: bem-estar/saúde mental
    if section == "wellness":
        return any(k in text for k in WELLNESS_KEYWORDS)

    # Mundo – Saúde Global: sistemas de saúde / seguro / políticas
    if section == "mundo_saude_global":
        global_keywords = (
            HEALTH_KEYWORDS_EN
            + [
                "health insurance",
                "insurance premiums",
                "medicare", "medicaid",
                "universal health coverage",
                "universal health care",
            ]
        )
        return any(k in text for k in global_keywords)

    return False


def fetch_rss(url: str, section: str, max_items: int = 20):
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
        # Mantém cada seção enxuta, com itens relevantes
        all_news[section_key] = section_items[:20]
    return all_news
