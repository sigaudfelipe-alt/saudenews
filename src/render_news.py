from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from news_fetcher import Article
from sources import (
    SECTION_BRASIL,
    SECTION_MUNDO,
    SECTION_HEALTHTECHS,
    SECTION_WELLNESS,
)


def build_subject() -> str:
    """
    Assunto do e-mail da newsletter.
    Ex.: "Principais notícias de Saúde – Brasil e Mundo · 05/12/2025"
    """
    today = datetime.now()
    date_str = today.strftime("%d/%m/%Y")
    return f"Principais notícias de Saúde – Brasil e Mundo · {date_str}"


def _flatten(sections: Dict[str, List[Article]]) -> List[Article]:
    flat: List[Article] = []
    for lst in sections.values():
        flat.extend(lst)
    return flat


def render_html(sections: Dict[str, List[Article]]) -> str:
    """
    Gera o HTML final a partir do dicionário de seções retornado
    por fetch_all_news().
    """
    all_articles = _flatten(sections)
    # Garantir que temos score (definido em news_fetcher)
    all_articles = sorted(all_articles, key=lambda a: a.score, reverse=True)
    top5 = all_articles[:5]

    brasil = sections.get(SECTION_BRASIL, [])
    mundo = sections.get(SECTION_MUNDO, [])
    healthtechs = sections.get(SECTION_HEALTHTECHS, [])
    wellness = sections.get(SECTION_WELLNESS, [])

    # HTML simples, compatível com Brevo
    html_parts: List[str] = []

    html_parts.append('<html><head><meta charset="utf-8" /></head><body>')
    html_parts.append(
        '<h1 style="font-family: Arial, sans-serif; font-size: 22px; margin-bottom: 4px;">'
        "Principais notícias de Saúde – Brasil e Mundo"
        "</h1>"
    )

    # Top 5
    html_parts.append(
        '<p style="font-family: Arial, sans-serif; font-size: 14px; margin-top: 0;">'
        "⭐ <strong>Top 5 do dia</strong><br/>"
        "Use estes destaques como ponto de partida para conversas com operadoras, hospitais, empregadores e parceiros."
        "</p>"
    )
    html_parts.append('<ul style="font-family: Arial, sans-serif; font-size: 14px;">')
    for art in top5:
        html_parts.append(
            f'<li><a href="{art.url}" target="_blank">{art.title}</a> · {art.source_name}</li>'
        )
    html_parts.append("</ul>")

    # Separador
    html_parts.append('<hr style="margin: 16px 0;" />')

    # 🇧🇷 Brasil – Saúde & Operadoras
    if brasil:
        html_parts.append(
            '<h2 style="font-family: Arial, sans-serif; font-size: 18px;">'
            "🇧🇷 Brasil – Saúde &amp; Operadoras"
            "</h2>"
        )
        html_parts.append(
            '<p style="font-family: Arial, sans-serif; font-size: 13px;">'
            "Movimentos em operadoras, hospitais privados, laboratórios, planos de saúde e negócios em saúde."
            "</p>"
        )
        html_parts.append(
            '<ul style="font-family: Arial, sans-serif; font-size: 14px;">'
        )
        for art in brasil:
            html_parts.append(
                f'<li><a href="{art.url}" target="_blank">{art.title}</a> · {art.source_name}</li>'
            )
        html_parts.append("</ul>")
        html_parts.append('<hr style="margin: 16px 0;" />')

    # 🌍 Mundo – Saúde Global
    if mundo:
        html_parts.append(
            '<h2 style="font-family: Arial, sans-serif; font-size: 18px;">'
            "🌍 Mundo – Saúde Global"
            "</h2>"
        )
        html_parts.append(
            '<p style="font-family: Arial, sans-serif; font-size: 13px;">'
            "Sistemas de saúde, regulação, política de saúde e tendências digitais em grandes mercados."
            "</p>"
        )
        html_parts.append(
            '<ul style="font-family: Arial, sans-serif; font-size: 14px;">'
        )
        for art in mundo:
            html_parts.append(
                f'<li><a href="{art.url}" target="_blank">{art.title}</a> · {art.source_name}</li>'
            )
        html_parts.append("</ul>")
        html_parts.append('<hr style="margin: 16px 0;" />')

    # 🚀 Healthtechs – Brasil & Mundo
    if healthtechs:
        html_parts.append(
            '<h2 style="font-family: Arial, sans-serif; font-size: 18px;">'
            "🚀 Healthtechs – Brasil &amp; Mundo"
            "</h2>"
        )
        html_parts.append(
            '<p style="font-family: Arial, sans-serif; font-size: 13px;">'
            "Startups, big techs em saúde, IA, investimentos e modelos digitais."
            "</p>"
        )
        html_parts.append(
            '<ul style="font-family: Arial, sans-serif; font-size: 14px;">'
        )
        for art in healthtechs:
            html_parts.append(
                f'<li><a href="{art.url}" target="_blank">{art.title}</a> · {art.source_name}</li>'
            )
        html_parts.append("</ul>")
        html_parts.append('<hr style="margin: 16px 0;" />')

    # 🧘‍♀️ Wellness – EUA / Europa
    if wellness:
        html_parts.append(
            '<h2 style="font-family: Arial, sans-serif; font-size: 18px;">'
            "🧘‍♀️ Wellness – EUA / Europa"
            "</h2>"
        )
        html_parts.append(
            '<p style="font-family: Arial, sans-serif; font-size: 13px;">'
            "Bem-estar, saúde mental, performance, fitness e hábitos de longo prazo."
            "</p>"
        )
        html_parts.append(
            '<ul style="font-family: Arial, sans-serif; font-size: 14px;">'
        )
        for art in wellness:
            html_parts.append(
                f'<li><a href="{art.url}" target="_blank">{art.title}</a> · {art.source_name}</li>'
            )
        html_parts.append("</ul>")
        html_parts.append('<hr style="margin: 16px 0;" />')

    # Rodapé
    html_parts.append(
        '<p style="font-family: Arial, sans-serif; font-size: 12px; color: #666;">'
        "Curadoria automática com apoio de IA. Sempre que necessário, valide os detalhes diretamente nas fontes originais."
        "</p>"
    )

    html_parts.append("</body></html>")

    return "".join(html_parts)
