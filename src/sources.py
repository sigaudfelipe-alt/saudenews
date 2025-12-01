from dataclasses import dataclass
from typing import List, Dict


@dataclass
class Source:
    """Represents a single news source (site / feed)."""
    name: str
    url: str
    section: str  # brasil | mundo | healthtechs | wellness
    max_articles: int = 3


# ---- Section identifiers ----------------------------------------------------

SECTION_BRASIL = "brasil"
SECTION_MUNDO = "mundo"
SECTION_HEALTHTECHS = "healthtechs"
SECTION_WELLNESS = "wellness"


def _build_sources() -> List[Source]:
    """Return the full list of sources used by the newsletter.

    The idea is to centralize everything here, para ficar fácil ajustar no futuro.
    Se quiser adicionar/remover fontes, basta editar esta função.
    """
    sources: List[Source] = []

    # -------------------------------------------------------------------------
    # BRASIL – Saúde & Operadoras
    # -------------------------------------------------------------------------
    brasil_sites = [
        ("Estadão – Saúde", "https://www.estadao.com.br/saude/"),
        ("Folha – Equilíbrio e Saúde", "https://www1.folha.uol.com.br/equilibrioesaude/"),
        ("O Globo – Saúde", "https://oglobo.globo.com/saude/"),
        ("Valor Econômico – Saúde", "https://valor.globo.com/brasil/saude/"),
        ("Brazil Journal", "https://braziljournal.com/"),  # negócios & saúde
        ("Pipeline – Valor", "https://pipelinevalor.globo.com/"),  # deals
        ("NeoFeed", "https://neofeed.com.br/"),  # negócios & inovação
        ("Medicina S/A", "https://medicinasa.com.br/"),  # já usávamos
        ("Saúde Digital News", "https://saudedigitalnews.com.br/"),  # digital health
        ("Healthcare – Grupo Mídia", "https://healthcare.grupomidia.com/"),  # gestão hospitalar
    ]
    for name, url in brasil_sites:
        sources.append(
            Source(
                name=name,
                url=url,
                section=SECTION_BRASIL,
                max_articles=3,
            )
        )

    # -------------------------------------------------------------------------
    # MUNDO – Sistemas de Saúde, Regulação & Política
    # -------------------------------------------------------------------------
    world_sites = [
        ("New York Times – Health", "https://www.nytimes.com/section/health"),  # já usávamos
        ("Financial Times – Health", "https://www.ft.com/health"),  # health policy & business
        ("Wall Street Journal – Health Industry", "https://www.wsj.com/news/types/health-industry"),
        ("Bloomberg – Health", "https://www.bloomberg.com/topics/health"),
        ("Reuters – Healthcare & Pharma", "https://www.reuters.com/business/healthcare-pharmaceuticals/"),
        ("Modern Healthcare", "https://www.modernhealthcare.com/"),  # pedida por você
        ("STAT News", "https://www.statnews.com/"),  # ciência & health policy
        ("Fierce Healthcare", "https://www.fiercehealthcare.com/"),  # US health system
    ]
    for name, url in world_sites:
        sources.append(
            Source(
                name=name,
                url=url,
                section=SECTION_MUNDO,
                max_articles=2,
            )
        )

    # -------------------------------------------------------------------------
    # HEALTHTECHS – Inovação, Startups, Digital Health
    # -------------------------------------------------------------------------
    healthtech_sites = [
        ("TechCrunch – Healthtech", "https://techcrunch.com/tag/healthtech/"),  # deals & startups
        ("TechCrunch – Digital Health", "https://techcrunch.com/tag/digital-health/"),
        ("MobiHealthNews", "https://mobihealthnews.com/"),  # clássico
        ("Fierce Digital Health", "https://www.fiercehealthcare.com/tech"),  # tech em saúde
        ("Sifted – Healthtech", "https://sifted.eu/sector/healthtech"),  # Europa
        ("CB Insights – Digital Health", "https://www.cbinsights.com/research/category/digital-health/"),  # relatórios
    ]
    for name, url in healthtech_sites:
        sources.append(
            Source(
                name=name,
                url=url,
                section=SECTION_HEALTHTECHS,
                max_articles=2,
            )
        )

    # -------------------------------------------------------------------------
    # WELLNESS – EUA / Europa
    # -------------------------------------------------------------------------
    wellness_sites = [
        ("Fitt Insider", "https://insider.fitt.co/"),  # você pediu explicitamente
        ("Well+Good", "https://www.wellandgood.com/"),  # wellness moderno
        ("MindBodyGreen", "https://www.mindbodygreen.com/"),  # lifestyle saudável
        ("Healthline – Wellness", "https://www.healthline.com/wellness"),  # conteúdo baseado em evidência
        ("WSJ – Wellness", "https://www.wsj.com/lifestyle/wellness"),  # tendência premium
        ("NYTimes – Well", "https://www.nytimes.com/section/well"),  # ainda assim limitamos
    ]
    for name, url in wellness_sites:
        sources.append(
            Source(
                name=name,
                url=url,
                section=SECTION_WELLNESS,
                max_articles=2,
            )
        )

    return sources


SOURCES: List[Source] = _build_sources()


def sources_by_section() -> Dict[str, List[Source]]:
    """Return a mapping section -> list of sources."""
    sections: Dict[str, List[Source]] = {
        SECTION_BRASIL: [],
        SECTION_MUNDO: [],
        SECTION_HEALTHTECHS: [],
        SECTION_WELLNESS: [],
    }
    for src in SOURCES:
        sections[src.section].append(src)
    return sections
