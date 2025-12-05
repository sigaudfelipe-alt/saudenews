from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

SECTION_BRASIL = "brasil"
SECTION_MUNDO = "mundo"
SECTION_HEALTHTECHS = "healthtechs"
SECTION_WELLNESS = "wellness"


@dataclass
class Source:
    name: str
    base_url: str
    section: str


BRASIL_SOURCES: List[Source] = [
    Source(
        name="Medicina S/A",
        base_url="https://medicinasa.com.br/",
        section=SECTION_BRASIL,
    ),
    Source(
        name="Saúde Digital News",
        base_url="https://saudedigitalnews.com.br/",
        section=SECTION_BRASIL,
    ),
    Source(
        name="Healthcare – Grupo Mídia",
        base_url="https://grupomidia.com/healthcare/",
        section=SECTION_BRASIL,
    ),
    Source(
        name="Folha – Equilíbrio e Saúde",
        base_url="https://www1.folha.uol.com.br/equilibrioesaude/",
        section=SECTION_BRASIL,
    ),
    Source(
        name="O Globo – Saúde",
        base_url="https://oglobo.globo.com/saude/",
        section=SECTION_BRASIL,
    ),
    Source(
        name="Valor Econômico – Saúde",
        base_url="https://valor.globo.com/empresas/saude/",
        section=SECTION_BRASIL,
    ),
]


MUNDO_SOURCES: List[Source] = [
    Source(
        name="STAT News",
        base_url="https://www.statnews.com/",
        section=SECTION_MUNDO,
    ),
    Source(
        name="Modern Healthcare",
        base_url="https://www.modernhealthcare.com/",
        section=SECTION_MUNDO,
    ),
    Source(
        name="New York Times – Health",
        base_url="https://www.nytimes.com/section/health",
        section=SECTION_MUNDO,
    ),
    Source(
        name="Fierce Healthcare",
        base_url="https://www.fiercehealthcare.com/",
        section=SECTION_MUNDO,
    ),
    Source(
        name="Financial Times – Health",
        base_url="https://www.ft.com/health",
        section=SECTION_MUNDO,
    ),
    Source(
        name="Healthbrew",
        base_url="https://healthbrew.com/",
        section=SECTION_MUNDO,
    ),
]


HEALTHTECH_SOURCES: List[Source] = [
    Source(
        name="MobiHealthNews",
        base_url="https://www.mobihealthnews.com/",
        section=SECTION_HEALTHTECHS,
    ),
    Source(
        name="Rock Health – Insights",
        base_url="https://rockhealth.com/insights/",
        section=SECTION_HEALTHTECHS,
    ),
    Source(
        name="Startup Health – News",
        base_url="https://www.startuphealth.com/news",
        section=SECTION_HEALTHTECHS,
    ),
    Source(
        name="Fierce Healthcare – Payers",
        base_url="https://www.fiercehealthcare.com/payers",
        section=SECTION_HEALTHTECHS,
    ),
    Source(
        name="STAT News – AI/Digital",
        base_url="https://www.statnews.com/",
        section=SECTION_HEALTHTECHS,
    ),
]


WELLNESS_SOURCES: List[Source] = [
    Source(
        name="Fitt Insider",
        base_url="https://insider.fitt.co/",
        section=SECTION_WELLNESS,
    ),
    Source(
        name="NYTimes – Well",
        base_url="https://www.nytimes.com/section/well",
        section=SECTION_WELLNESS,
    ),
    Source(
        name="WHOOP – The Locker",
        base_url="https://www.whoop.com/thelocker/",
        section=SECTION_WELLNESS,
    ),
    Source(
        name="Oura – Blog",
        base_url="https://ouraring.com/blog",
        section=SECTION_WELLNESS,
    ),
]


sources_by_section: Dict[str, List[Source]] = {
    SECTION_BRASIL: BRASIL_SOURCES,
    SECTION_MUNDO: MUNDO_SOURCES,
    SECTION_HEALTHTECHS: HEALTHTECH_SOURCES,
    SECTION_WELLNESS: WELLNESS_SOURCES,
}
