# -*- coding: utf-8 -*-
import feedparser
from bs4 import BeautifulSoup

"""
news_fetcher.py

Busca notícias em fontes RSS e aplica filtros por seção:
- brasil_operadoras    → SUS, operadoras, hospitais, laboratórios, planos de saúde
- mundo_saude_global   → sistemas de saúde / health insurance / política de saúde
- healthtechs          → saúde digital, healthtechs, telemedicina, apps de saúde, medtech
- wellness             → bem-estar, saúde mental, estilo de vida

A saída é usada pelo render_news.py para montar a newsletter.
"""

# =========================
#   FONTES POR SEÇÃO
# =========================

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
        # Jornais / negócios – ainda permitidos, mas filtrados por saúde e operadoras
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
        # Inovação, digital health, healthtechs
        "https://techcrunch.com/feed/",
        "https://www.businessinsider.com/sai/rss",
        "https://www.mobihealthnews.com/rss",
        "https://www.digitalhealth.net/feed/",
    ],

    "wellness": [
        "https://rss.nytimes.com/services/xml/rss/nyt/Well.xml",
    ],
}

# =======================================
#   PALAVRAS-CHAVE POR TEMA / SEÇÃO
# =======================================

HEALTH_KEYWORDS_PT = [
    "saúde", "saude",
    "hospital", "hospitais",
    "clínica", "clinica", "clínicas", "clinicas",
    "laboratório", "laboratorio", "laboratórios", "laboratorios",
    "diagnóstico", "diagnostico", "exame", "exames",
    "vacina", "vacinas",
    "tratamento", "doença", "doencas", "doenças",
    "oncologia", "câncer", "cancer",
    "uti", "internação", "internacao",
    "unidade básica de saúde", "ubs", "upa", "upas",
]

HEALTH_KEYWORDS_EN = [
    "health", "healthcare",
    "hospital", "hospitals",
    "clinic", "clinics",
    "diagnostic", "diagnostics",
    "disease", "diseases",
    "vaccine", "vaccines",
    "treatment", "patients", "patient",
]

# Específicas para Brasil & Operadoras
BR_OPERADORAS_KEYWORDS = [
    "plano de saúde", "planos de saúde", "plano de saude", "planos de saude",
    "operadora", "operadoras",
    "seguro saúde", "seguro-saúde", "seguro saude",
    "convênio médico", "convenio médico", "convenio medico",
    "coparticipação", "coparticipacao",
    "ans", "agência nacional de saúde suplementar",
    "sus", "sistema único de saúde", "sistema unico de saude",
    "rede credenciada", "rede própria", "rede propria",
    "hospital filantrópico", "hospitais filantrópicos",
    # principais grupos
    "unimed", "hapvida", "notredame", "amil",
    "bradesco saúde", "bradesco saude",
    "sulamérica saúde", "sulamerica saude", "sulamérica saude",
    "rede d'or", "rede dor",
    "dasa", "fleury", "oncoclínicas", "oncoclinicas",
    "laboratório clínico", "laboratorio clinico",
]

# Healthtech & digital health
HEALTHTECH_TERMS = [
    "healthtech", "health tech",
    "digital health", "saúde digital", "saude digital",
    "telemedicina", "teleconsulta",
    "telehealth", "telemedicine",
    "prontuário eletrônico", "prontuario eletronico",
    "remote patient monitoring", "rpm",
    "app de saúde", "app de saude", "health app",
    "medtech", "e-health", "ehealth",
    "plataforma digital de saúde", "plataforma digital de saude",
    "dados de saúde", "dados de saude",
    "conexa saúde", "conexa saude",
]

HEALTHTECH_INNOVATION = [
    "startup", "startups", "start-up",
    "funding", "fundraise", "raises",
    "rodada", "investimento", "investimentos",
    "seed round", "series a", "series b",
    "venture capital", "vc",
    "parceria", "parcerias",
    "aquisição", "aquisicao", "acquisition",
    "lançamento", "lancamento", "lança", "lanca",
]

# Wellness
WELLNESS_KEYWORDS = [
    "wellness", "bem-estar", "bem estar",
    "saúde mental", "saude mental",
    "ansiedade", "depressão", "depressao",
    "sono", "sleep", "insônia", "insonia",
    "mindfulness", "meditação", "meditacao",
    "burnout", "stress", "estresse",
    "atividade física", "atividade fisica",
    "exercício", "exercicio",
    "lifestyle",
]


# =========================
#   FUNÇÕES DE APOIO
# =========================

def _clean_summary(raw_summary: str) -> str:
    """Limpa HTML básico e corta o tamanho para caber bem no e-mail."""
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

    # ------------------------
    # Brasil – Saúde & Operadoras
    # ------------------------
    if section == "brasil_operadoras":
        # precisa bater em termos de operadoras/SUS/hospitais/labs
        if any(k in text for k in BR_OPERADORAS_KEYWORDS):
            return True
        # fallback: notícia claramente de saúde (hospital, SUS, etc.)
        base = HEALTH_KEYWORDS_PT + HEALTH_KEYWORDS_EN
        return any(k in text for k in base)

    # ------------------------
    # Healthtechs – Brasil e Mundo
    # ------------------------
    if section == "healthtechs":
        # 1) precisa falar de digital health / healthtech / telemedicina / app de saúde etc
        has_digital_health = any(k in text for k in HEALTHTECH_TERMS)

        # 2) idealmente também falar de inovação / startup / funding, mas não é obrigatório
        has_innovation = any(k in text for k in HEALTHTECH_INNOVATION)

        # 3) base de saúde genérica, para garantir que tem contexto de saúde
        base_health = HEALTH_KEYWORDS_PT + HEALTH_KEYWORDS_EN

        # Regra:
        # - sempre aceita quando tem termos de digital health E saúde
        # - OU quando é inovação clara de healthtech (digital health + inovação)
        if has_digital_health and any(b in text for b in base_health):
            return True
        if has_digital_health and has_innovation:
            return True

        # Bloqueia coisas totalmente fora (spotify, iphone, bicicleta etc)
        return False

    # ------------------------
    # Wellness – EUA / Europa
    # ------------------------
    if section == "wellness":
        return any(k in text for k in WELLNESS_KEYWORDS)

    # ------------------------
    # Mundo – Saúde Global
    # ------------------------
    if section == "mundo_saude_global":
        global_keywords = (
            HEALTH_KEYWORDS_EN
            + [
                "health insurance",
                "insurance premiums",
                "medicare",
                "medicaid",
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
        all_news[section_key] = section_items[:20]
    return all_news
