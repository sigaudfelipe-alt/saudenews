from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, List

from news_fetcher import Article
from sources import (
    SECTION_BRASIL,
    SECTION_MUNDO,
    SECTION_HEALTHTECHS,
    SECTION_WELLNESS,
)

# URL do formulário de inscrição na News Saúde (Brevo, Substack etc.)
# Defina em GitHub Secrets/Actions como NEWS_CTA_URL
CTA_URL = os.getenv("NEWS_CTA_URL", "").strip()


def build_subject() -> str:
    today = datetime.now()
    date_str = today.strftime("%d/%m/%Y")
    return f"Principais notícias de Saúde – Brasil e Mundo · {date_str}"


def _flatten(sections: Dict[str, List[Article]]) -> List[Article]:
    flat: List[Article] = []
    for lst in sections.values():
        flat.extend(lst)
    return flat


def render_html(sections: Dict[str, List[Article]]) -> str:
    all_articles = _flatten(sections)
    all_articles = sorted(all_articles, key=lambda a: a.score, reverse=True)
    top5 = all_articles[:5]

    brasil = sections.get(SECTION_BRASIL, [])
    mundo = sections.get(SECTION_MUNDO, [])
    healthtechs = sections.get(SECTION_HEALTHTECHS, [])
    wellness = sections.get(SECTION_WELLNESS, [])

    today = datetime.now()
    date_str = today.strftime("%d/%m/%Y")

    html_parts: List[str] = []

    html_parts.append('<html><head><meta charset="utf-8" /></head><body>')
    # Título principal
    html_parts.append(
        '<h1 style="font-family: Arial, sans-serif; font-size: 22px; margin-bottom: 4px;">'
        "Principais notícias de Saúde – Brasil e Mundo"
        "</h1>"
    )

    # Linha CURADORIA DIÁRIA similar ao layout antigo
    html_parts.append(
        f'<p style="font-family: Arial, sans-serif; font-size: 12px; color: #666; margin-top: 0;">'
        f"CURADORIA DIÁRIA · {date_str}<br/>"
        "Radar rápido de movimentos em operadoras, hospitais, planos de saúde, laboratórios, "
        "healthtechs e tendências de bem-estar."
        "</p>"
    )

    # Top 5
    html_parts.append(
        '<p style="font-family: Arial, sans-serif; font-size: 14px; margin-top: 12px; margin-bottom: 4px;">'
        "⭐ <strong>Top 5 do dia</strong><br/>"
        "Use estes destaques como ponto de partida para conversas com operadoras, hospitais, empregadores e parceiros."
        "</p>"
    )
    html_parts.append('<ul style="font-family: Arial, sans-serif; font-size: 14px; margin-top: 4px;">')
    for art in top5:
        html_parts.append(
            f'<li><a href="{art.url}" target="_blank">{art.title}</a> · {art.source_name}</li>'
        )
    html_parts.append("</ul>")

    html_parts.append('<hr style="margin: 16px 0;" />')

    # 🇧🇷 Brasil – Saúde & Operadoras
    if brasil:
        html_parts.append(
            '<h2 style="font-family: Arial, sans-serif; font-size: 18px; margin-bottom: 4px;">'
            "🇧🇷 Brasil – Saúde &amp; Operadoras"
            "</h2>"
        )
        html_parts.append(
            '<p style="font-family: Arial, sans-serif; font-size: 13px; margin-top: 0;">'
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
            '<h2 style="font-family: Arial, sans-serif; font-size: 18px; margin-bottom: 4px;">'
            "🌍 Mundo – Saúde Global"
            "</h2>"
        )
        html_parts.append(
            '<p style="font-family: Arial, sans-serif; font-size: 13px; margin-top: 0;">'
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
            '<h2 style="font-family: Arial, sans-serif; font-size: 18px; margin-bottom: 4px;">'
            "🚀 Healthtechs – Brasil &amp; Mundo"
            "</h2>"
        )
        html_parts.append(
            '<p style="font-family: Arial, sans-serif; font-size: 13px; margin-top: 0;">'
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
            '<h2 style="font-family: Arial, sans-serif; font-size: 18px; margin-bottom: 4px;">'
            "🧘‍♀️ Wellness – EUA / Europa"
            "</h2>"
        )
        html_parts.append(
            '<p style="font-family: Arial, sans-serif; font-size: 13px; margin-top: 0;">'
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

    # CTA de inscrição - sempre mostra algum CTA
    if CTA_URL:
        html_parts.append(
            f'<p style="font-family: Arial, sans-serif; font-size: 13px; margin-top: 24px;">'
            'Quer receber esta curadoria diariamente por e-mail?<br/>'
            f'<a href="{CTA_URL}" target="_blank"><strong>👉 Clique aqui para se inscrever na News Saúde</strong></a>.'
            "</p>"
        )
    else:
        # CTA sem link (caso NEWS_CTA_URL não esteja configurada)
        html_parts.append(
            '<p style="font-family: Arial, sans-serif; font-size: 13px; margin-top: 24px;">'
            'Quer receber esta curadoria diariamente por e-mail?<br/>'
            '<strong>👉 Responda este e-mail pedindo sua inclusão na lista da News Saúde.</strong>'
            "</p>"
        )

    # Rodapé
    html_parts.append(
        '<p style="font-family: Arial, sans-serif; font-size: 12px; color: #666;">'
        "Curadoria automática com apoio de IA. Sempre que necessário, valide os detalhes diretamente nas fontes originais."
        "</p>"
    )

    html_parts.append("</body></html>")

    return "".join(html_parts)
