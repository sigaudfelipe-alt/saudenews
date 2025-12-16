from __future__ import annotations

"""
sources.py — catálogo de fontes para o pipeline Saúde News.

Melhorias aplicadas (16/12):
- Inclusão do Valor Econômico (RSS Empresas) para capturar movimentos relevantes (ex: operadoras/hospitais).
- Estrutura simples e explícita para manutenção.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

# -------------------------
# Seções
# -------------------------
SECTION_BRASIL = "Brasil – Saúde & Operadoras"
SECTION_MUNDO = "Mundo – Saúde Global"
SECTION_HEALTHTECHS = "Healthtechs – Brasil & Mundo"
SECTION_WELLNESS = "Wellness – EUA / Europa"


@dataclass(frozen=True)
class Source:
    name: str
    section: str
    base_url: str
    rss_url: Optional[str] = None


# -------------------------
# Fontes por seção
# -------------------------

sources_by_section: Dict[str, List[Source]] = {
    SECTION_BRASIL: [
        # Saúde Digital News
        Source(
            name="Saúde Digital News",
            section=SECTION_BRASIL,
            base_url="https://saudedigitalnews.com.br",
            # Ajuste se o RSS mudar — exemplo comum:
            rss_url="https://saudedigitalnews.com.br/feed/",
        ),
        # Medicina S/A (atenção: possui áreas tipo revista/panorama; o fetcher bloqueia por URL keyword e data)
        Source(
            name="Medicina S/A",
            section=SECTION_BRASIL,
            base_url="https://medicinasa.com.br",
            rss_url="https://medicinasa.com.br/feed/",
        ),
        # O Globo – Saúde (se o RSS estiver instável, você pode remover)
        Source(
            name="O Globo – Saúde",
            section=SECTION_BRASIL,
            base_url="https://oglobo.globo.com/saude",
            rss_url="https://oglobo.globo.com/rss/saude/",
        ),
        # Valor Econômico – Empresas (muito útil para operadoras/hospitais e movimentações)
        Source(
            name="Valor Econômico – Empresas",
            section=SECTION_BRASIL,
            base_url="https://valor.globo.com/empresas",
            rss_url="https://valor.globo.com/rss/empresas/",
        ),
    ],
    SECTION_MUNDO: [
        Source(
            name="STAT News",
            section=SECTION_MUNDO,
            base_url="https://www.statnews.com",
            rss_url="https://www.statnews.com/feed/",
        ),
        Source(
            name="Modern Healthcare",
            section=SECTION_MUNDO,
            base_url="https://www.modernhealthcare.com",
            rss_url="https://www.modernhealthcare.com/section/rss",
        ),
        Source(
            name="Fierce Healthcare",
            section=SECTION_MUNDO,
            base_url="https://www.fiercehealthcare.com",
            rss_url="https://www.fiercehealthcare.com/rss/xml",
        ),
    ],
    SECTION_HEALTHTECHS: [
        Source(
            name="MobiHealthNews",
            section=SECTION_HEALTHTECHS,
            base_url="https://www.mobihealthnews.com",
            rss_url="https://www.mobihealthnews.com/feed",
        ),
        # Future Health (você pediu antes para incluir futurehealth.cc)
        Source(
            name="Future Health",
            section=SECTION_HEALTHTECHS,
            base_url="https://futurehealth.cc",
            rss_url="https://futurehealth.cc/feed/",
        ),
    ],
    SECTION_WELLNESS: [
        Source(
            name="Fitt Insider",
            section=SECTION_WELLNESS,
            base_url="https://fittinsider.com",
            rss_url="https://fittinsider.com/feed/",
        ),
    ],
}
