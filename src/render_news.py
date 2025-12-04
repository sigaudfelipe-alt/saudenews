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


def _render_article_list(articles: List[Article]) -> str:
    if not articles:
        return "<p style='color:#666;font-size:13px'>Sem notícias relevantes nesta seção nas últimas horas.</p>"

    items = []
    for art in articles:
        items.append(
            f"""<li style='margin-bottom:6px;'>
            <a href="{art.url}" style="color:#0052cc;text-decoration:none;font-weight:500;" target="_blank">
                {art.title}
            </a>
            <span style="color:#777;font-size:12px;"> &nbsp;· {art.source_name}</span>
        </li>"""
        )
    return "<ul style='padding-left:18px;margin-top:4px;margin-bottom:12px;'>" + "".join(items) + "</ul>"


def _today_str() -> str:
    return datetime.now().strftime("%d/%m/%Y")


def build_subject() -> str:
    return f"Principais notícias de Saúde – Brasil e Mundo · {_today_str()}"


def render_html(sections: Dict[str, List[Article]]) -> str:
    brasil_html = _render_article_list(sections.get(SECTION_BRASIL, []))
    mundo_html = _render_article_list(sections.get(SECTION_MUNDO, []))
    healthtechs_html = _render_article_list(sections.get(SECTION_HEALTHTECHS, []))
    wellness_html = _render_article_list(sections.get(SECTION_WELLNESS, []))

    # Top 5 baseado em Brasil + Mundo + Healthtechs
    top_candidates: List[Article] = []
    for key in (SECTION_BRASIL, SECTION_MUNDO, SECTION_HEALTHTECHS):
        top_candidates.extend(sections.get(key, []))
    top_candidates.sort(key=lambda a: (a.score, a.title), reverse=True)
    top5 = top_candidates[:5]

    if top5:
        top5_items = []
        for art in top5:
            top5_items.append(
                f"""<li style='margin-bottom:6px;'>
                <a href="{art.url}" style="color:#111827;text-decoration:none;font-weight:600;" target="_blank">
                    {art.title}
                </a>
                <span style="color:#6b7280;font-size:12px;"> &nbsp;· {art.source_name}</span>
            </li>"""
            )
        top5_html = (
            "<ul style='padding-left:18px;margin-top:8px;margin-bottom:16px;'>"
            + "".join(top5_items)
            + "</ul>"
        )
    else:
        top5_html = "<p style='color:#6b7280;font-size:13px'>Sem destaques suficientes para o Top 5 hoje.</p>"

    today = _today_str()

    html = f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="UTF-8" />
  <title>Principais notícias de Saúde – Brasil e Mundo</title>
</head>
<body style="margin:0;padding:0;background-color:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color:#f3f4f6;padding:24px 0;">
    <tr>
      <td align="center">
        <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="max-width:720px;background-color:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 10px 25px rgba(15,23,42,0.12);">
          <!-- Header -->
          <tr>
            <td style="background-color:#2563eb;padding:20px 24px 18px 24px;color:#ecfeff;">
              <div style="font-size:11px;letter-spacing:0.08em;text-transform:uppercase;opacity:0.85;">Curadoria diária · {today}</div>
              <h1 style="margin:4px 0 6px 0;font-size:22px;">Principais notícias de Saúde – Brasil e Mundo</h1>
              <p style="margin:0;font-size:13px;max-width:540px;line-height:1.5;opacity:0.95;">
                Radar rápido de movimentos em operadoras, hospitais, planos de saúde, laboratórios, healthtechs e tendências de bem-estar.
              </p>
            </td>
          </tr>

          <!-- Top 5 -->
          <tr>
            <td style="padding:18px 24px 4px 24px;">
              <h2 style="font-size:15px;margin:0 0 4px 0;color:#111827;">⭐ Top 5 do dia</h2>
              <p style="margin:0 0 8px 0;font-size:12px;color:#6b7280;">
                Use estes destaques como ponto de partida para conversas com operadoras, hospitais, empregadores e parceiros.
              </p>
              {top5_html}
            </td>
          </tr>

          <!-- Brasil -->
          <tr>
            <td style="padding:8px 24px 0 24px;">
              <h2 style="font-size:15px;margin:0 0 4px 0;color:#111827;">🇧🇷 Brasil – Saúde &amp; Operadoras</h2>
              <p style="margin:0 0 6px 0;font-size:12px;color:#6b7280;">
                Movimentos em operadoras, SUS, hospitais, laboratórios e negócios em saúde.
              </p>
              {brasil_html}
            </td>
          </tr>

          <!-- Mundo -->
          <tr>
            <td style="padding:8px 24px 0 24px;">
              <h2 style="font-size:15px;margin:0 0 4px 0;color:#111827;">🌍 Mundo – Saúde Global</h2>
              <p style="margin:0 0 6px 0;font-size:12px;color:#6b7280;">
                Sistemas de saúde, regulação, política pública e tendências em grandes mercados.
              </p>
              {mundo_html}
            </td>
          </tr>

          <!-- Healthtechs -->
          <tr>
            <td style="padding:8px 24px 0 24px;">
              <h2 style="font-size:15px;margin:0 0 4px 0;color:#111827;">🚀 Healthtechs – Brasil &amp; Mundo</h2>
              <p style="margin:0 0 6px 0;font-size:12px;color:#6b7280;">
                Startups, big techs em saúde, IA, investimentos e modelos digitais.
              </p>
              {healthtechs_html}
            </td>
          </tr>

          <!-- Wellness -->
          <tr>
            <td style="padding:8px 24px 4px 24px;">
              <h2 style="font-size:15px;margin:0 0 4px 0;color:#111827;">🧘‍♀️ Wellness – EUA / Europa</h2>
              <p style="margin:0 0 6px 0;font-size:12px;color:#6b7280;">
                Bem-estar, saúde mental, performance, fitness e hábitos de longo prazo.
              </p>
              {wellness_html}
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:14px 24px 18px 24px;border-top:1px solid #e5e7eb;font-size:11px;color:#9ca3af;background-color:#f9fafb;">
              <p style="margin:0 0 4px 0;">
                Curadoria automática com apoio de IA. Sempre que necessário, valide os detalhes diretamente nas fontes originais.
              </p>
              <p style="margin:0;">
                Quer ajustar fontes, seções ou público-alvo desta newsletter? Fale com a equipe responsável pela News Saúde.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
    return html
