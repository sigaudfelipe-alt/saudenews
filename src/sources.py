from dataclasses import dataclass
from typing import List, Dict


@dataclass
class Source:
    """Represents a single news source (site / feed)."""
    name: str
    url: str
    section: str  # brasil | mundo | healthtechs | wellness
    max_articles: int = 3
    health_focus: bool = True  # se False, exige palavra de saúde no título


# ---- Section identifiers ----------------------------------------------------

SECTION_BRASIL = "brasil"
SECTION_MUNDO = "mundo"
SECTION_HEALTHTECHS = "healthtechs"
SECTION_WELLNESS = "wellness"


def _build_sources() -> List[Source]:
    """Return the full list of sources used by the newsletter."""
    sources: List[Source] = []

    # -------------------------------------------------------------------------
    # BRASIL – Saúde & Operadoras
    # -------------------------------------------------------------------------
    brasil_sites = [
        ("Estadão – Saúde", "https://www.estadao.com.br/saude/", True),
        ("Folha – Equilíbrio e Saúde", "https://www1.folha.uol.com.br/equilibrioesaude/", True),
        ("O Globo – Saúde", "https://oglobo.globo.com/saude/", True),
        ("Valor Econômico – Saúde", "https://valor.globo.com/brasil/saude/", True),
        ("Brazil Journal", "https://braziljournal.com/", False),
        ("Pipeline – Valor", "https://pipelinevalor.globo.com/", False),
        ("NeoFeed", "https://neofeed.com.br/", False),
        ("Medicina S/A", "https://medicinasa.com.br/", True),
        ("Saúde Digital News", "https://saudedigitalnews.com.br/", True),
        ("Healthcare – Grupo Mídia", "https://healthcare.grupomidia.com/", True),
    ]
    for name, url, health_focus in brasil_sites:
        sources.append(
            Source(
                name=name,
                url=url,
                section=SECTION_BRASIL,
                max_articles=3,
                health_focus=health_focus,
            )
        )

    # -------------------------------------------------------------------------
    # MUNDO – Sistemas de Saúde, Regulação & Política
    # -------------------------------------------------------------------------
    world_sites = [
        ("New York Times – Health", "https://www.nytimes.com/section/health", True),
        ("Financial Times – Health", "https://www.ft.com/health", False),
        ("Wall Street Journal – Health Industry", "https://www.wsj.com/news/types/health-industry", True),
        ("Bloomberg – Health", "https://www.bloomberg.com/topics/health", True),
        ("Reuters – Healthcare & Pharma", "https://www.reuters.com/business/healthcare-pharmaceuticals/", True),
        ("Modern Healthcare", "https://www.modernhealthcare.com/", True),
        ("STAT News", "https://www.statnews.com/", True),
        ("Fierce Healthcare", "https://www.fiercehealthcare.com/", True),
    ]
    for name, url, health_focus in world_sites:
        sources.append(
            Source(
                name=name,
                url=url,
                section=SECTION_MUNDO,
                max_articles=2,
                health_focus=health_focus,
            )
        )

    # -------------------------------------------------------------------------
    # HEALTHTECHS – Inovação, Startups, Digital Health
    # -------------------------------------------------------------------------
    healthtech_sites = [
        ("TechCrunch – Healthtech", "https://techcrunch.com/tag/healthtech/", False),
        ("TechCrunch – Digital Health", "https://techcrunch.com/tag/digital-health/", False),
        ("MobiHealthNews", "https://mobihealthnews.com/", True),
        ("Fierce Digital Health", "https://www.fiercehealthcare.com/tech", True),
        ("Sifted – Healthtech", "https://sifted.eu/sector/healthtech", True),
        ("CB Insights – Digital Health", "https://www.cbinsights.com/research/category/digital-health/", True),
    ]
    for name, url, health_focus in healthtech_sites:
        sources.append(
            Source(
                name=name,
                url=url,
                section=SECTION_HEALTHTECHS,
                max_articles=2,
                health_focus=health_focus,
            )
        )

    # -------------------------------------------------------------------------
    # WELLNESS – EUA / Europa
    # -------------------------------------------------------------------------
    wellness_sites = [
        ("Fitt Insider", "https://insider.fitt.co/", True),
        ("Well+Good", "https://www.wellandgood.com/", True),
        ("MindBodyGreen", "https://www.mindbodygreen.com/", True),
        ("Healthline – Wellness", "https://www.healthline.com/wellness", True),
        ("WSJ – Wellness", "https://www.wsj.com/lifestyle/wellness", True),
        ("NYTimes – Well", "https://www.nytimes.com/section/well", True),
    ]
    for name, url, health_focus in wellness_sites:
        sources.append(
            Source(
                name=name,
                url=url,
                section=SECTION_WELLNESS,
                max_articles=2,
                health_focus=health_focus,
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
