from __future__ import annotations

from typing import Dict, List

from news_fetcher import Article, (
    fetch_all_articles,
    get_top_n,
    group_articles_by_section,
)
from sources import (
    SECTION_BRASIL,
    SECTION_MUNDO,
    SECTION_HEALTHTECHS,
    SECTION_WELLNESS,
)


def format_article_line(article: Article) -> str:
    return f"{article.title}  · {article.source_name}"


def render_markdown(articles: List[Article]) -> str:
    """
    Gera o conteúdo em Markdown (que depois você converte para HTML no e-mail).
    Estrutura:
      - Título / data
      - Top 5 do dia
      - Brasil – Saúde & Operadoras
      - Mundo – Saúde Global
      - Healthtechs – Brasil & Mundo
      - Wellness – EUA / Europa
    """
    grouped = group_articles_by_section(articles)
    top5 = get_top_n(articles, n=5)

    lines: List[str] = []

    # Cabeçalho
    lines.append("# Principais notícias de Saúde – Brasil e Mundo")
    lines.append("")
    lines.append("⭐ **Top 5 do dia**")
    lines.append("Use estes destaques como ponto de partida para conversas com operadoras, hospitais, empregadores e parceiros.")
    lines.append("")

    for art in top5:
        lines.append(f"- [{art.title}]({art.url})  · {art.source_name}")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Brasil
    brasil = grouped.get(SECTION_BRASIL, [])
    if brasil:
        lines.append("## 🇧🇷 Brasil – Saúde & Operadoras")
        lines.append("Movimentos em operadoras, hospitais privados, laboratórios, planos de saúde e negócios em saúde.")
        lines.append("")
        for art in brasil:
            lines.append(f"- [{art.title}]({art.url})  · {art.source_name}")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Mundo
    mundo = grouped.get(SECTION_MUNDO, [])
    if mundo:
        lines.append("## 🌍 Mundo – Saúde Global")
        lines.append("Sistemas de saúde, regulação, política de saúde e tendências digitais em grandes mercados.")
        lines.append("")
        for art in mundo:
            lines.append(f"- [{art.title}]({art.url})  · {art.source_name}")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Healthtechs
    healthtechs = grouped.get(SECTION_HEALTHTECHS, [])
    if healthtechs:
        lines.append("## 🚀 Healthtechs – Brasil & Mundo")
        lines.append("Startups, big techs em saúde, IA, investimentos e modelos digitais.")
        lines.append("")
        for art in healthtechs:
            lines.append(f"- [{art.title}]({art.url})  · {art.source_name}")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Wellness
    wellness = grouped.get(SECTION_WELLNESS, [])
    if wellness:
        lines.append("## 🧘‍♀️ Wellness – EUA / Europa")
        lines.append("Bem-estar, saúde mental, performance, fitness e hábitos de longo prazo.")
        lines.append("")
        for art in wellness:
            lines.append(f"- [{art.title}]({art.url})  · {art.source_name}")
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append(
        "Curadoria automática com apoio de IA. Sempre que necessário, valide os detalhes diretamente nas fontes originais."
    )

    return "\n".join(lines)


def main() -> str:
    """
    Função principal usada pelo main.py ou pelo workflow.
    Retorna uma string em Markdown (ou HTML, se você converter aqui).
    """
    articles = fetch_all_articles()
    md = render_markdown(articles)
    return md


if __name__ == "__main__":
    # debug local
    print(main())
