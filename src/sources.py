from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

# Constantes de seção usadas em todo o pipeline
SECTION_BRASIL = "brasil"
SECTION_MUNDO = "mundo"
SECTION_HEALTHTECHS = "healthtechs"
SECTION_WELLNESS = "wellness"


@dataclass
class Source:
    name: str
    base_url: str
    section: str


# --------------------------------
# BRASIL – SAÚDE & OPERADORAS
# (foco: operadoras, hospitais privados, planos, gestão)
# --------------------------------
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
    # Adicione aqui páginas específicas de operadoras / ANS caso deseje
]


# --------------------------------
# MUNDO – SAÚDE GLOBAL
# (foco: sistemas de saúde, digital health, regulação, payers)
# --------------------------------
MUNDO_SOURCES: List[Source] = [
    Source(
        name="STAT News – Health / AI / Policy",
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
    # Healthbrew é mais “healthtech/insights”, mas como não tem seção separada,
    # podemos tratar como global (ou mover para healthtechs se preferir)
    Source(
        name="Healthbrew",
        base_url="https://healthbrew.com/",
        section=SECTION_MUNDO,
    ),
]


# --------------------------------
# HEALTHTECHS – BRASIL & MUNDO
# (startups, big techs, IA, investimentos, modelos digitais)
# --------------------------------
HEALTHTECH_SOURCES: List[Source] = [
    Source(
        name="MobiHealthNews",
        base_url="https://www.mobihealthnews.com/",
        section=SECTION_HEALTHTECHS,
    ),
    Source(
        name="Rock Health – News",
        base_url="https://rockhealth.com/insights/",
        section=SECTION_HEALTHTECHS,
    ),
    Source(
        name="Startup Health",
        base_url="https://www.startuphealth.com/news",
        section=SECTION_HEALTHTECHS,
    ),
    Source(
        name="Fierce Healthcare – Payers/Tech",
        base_url="https://www.fiercehealthcare.com/payers",
        section=SECTION_HEALTHTECHS,
    ),
    Source(
        name="STAT Plus – Digital / AI",
        base_url="https://www.statnews.com/",
        section=SECTION_HEALTHTECHS,
    ),
]


# --------------------------------
# WELLNESS – EUA / EUROPA
# (bem-estar, saúde mental, performance, hábitos, longevity)
# --------------------------------
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


# Dicionário principal usado pelo news_fetcher
sources_by_section: Dict[str, List[Source]] = {
    SECTION_BRASIL: BRASIL_SOURCES,
    SECTION_MUNDO: MUNDO_SOURCES,
    SECTION_HEALTHTECHS: HEALTHTECH_SOURCES,
    SECTION_WELLNESS: WELLNESS_SOURCES,
}
