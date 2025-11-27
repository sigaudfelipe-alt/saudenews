from datetime import date


SECTION_META = {
    "brasil_operadoras": {
        "title": "Brasil – Saúde & Operadoras",
        "subtitle": "Operadoras • SUS • Hospitais • Laboratórios",
        "tag": "BRASIL",
        "emoji": "",
    },
    "mundo_saude_global": {
        "title": "🌍 Mundo – Saúde Global",
        "subtitle": "Sistemas de Saúde • Regulação & Política",
        "tag": "🌍 MUNDO",
        "emoji": "🌍",
    },
    "healthtechs": {
        "title": "🚀 Healthtechs – Brasil e Mundo",
        "subtitle": "Inovação • Startups & Digital Health",
        "tag": "🚀 HEALTHTECHS",
        "emoji": "🚀",
    },
    "wellness": {
        "title": "🧘‍♀️ Wellness – EUA / Europa",
        "subtitle": "Bem-estar • Saúde Mental • Lifestyle",
        "tag": "🧘 WELLNESS",
        "emoji": "🧘‍♀️",
    },
}


def build_top_5(news):
    ordered_keys = ["brasil_operadoras", "mundo_saude_global", "healthtechs", "wellness"]
    top_items = []

    for key in ordered_keys:
        items = news.get(key, [])
        for item in items:
            meta = SECTION_META.get(key, {})
            tagged_item = {
                **item,
                "tag": meta.get("tag", ""),
            }
            top_items.append(tagged_item)
            if len(top_items) >= 5:
                return top_items
    return top_items


def render_news_html(news):
    today_str = date.today().strftime("%d/%m/%Y")
    top_5 = build_top_5(news)

    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background:#f5f5f5; padding:20px;">
      <div style="max-width:800px; margin:0 auto; background:white; padding:24px; border-radius:12px;">

        <h1 style="margin-top:0; color:#111111; font-size:26px;">
          Principais notícias de Saúde – Brasil e Mundo
        </h1>
        <p style="color:#555555; font-size:14px; margin-top:-10px;">
          Curadoria diária • {today_str}
        </p>

        <p style="color:#333333; line-height:1.5; font-size:14px;">
          Nas últimas 24 horas, o setor de saúde ganhou tração com movimentos em operadoras,
          hospitais, planos de saúde, laboratórios e healthtechs — além de temas de
          sustentabilidade dos sistemas públicos e tendências de bem-estar e saúde mental.
        </p>

        <h2 style="margin-top:24px; font-size:18px;">🧠 RESUMO DO DIA (IA)</h2>
        <p style="color:#333333; line-height:1.6; font-size:14px;">
          Brasil & Operadoras • Saúde Global • Healthtechs & IA • Wellness EUA/Europa.
          Use esta newsletter como radar rápido para captar movimentos que podem impactar
          operadoras, hospitais, empregadores e todo o ecossistema de saúde.
        </p>

        <h2 style="margin-top:28px; font-size:18px;">⭐ TOP 5 DO DIA</h2>
    """

    if not top_5:
        html += '<p style="font-size:14px; color:#777777;"><i>Sem destaques encontrados hoje.</i></p>'
    else:
        html += "<ul style='padding-left:18px; font-size:14px; color:#333333;'>"
        for item in top_5:
            tag = item.get("tag", "").strip()
            prefix = f"<b>{tag}</b> " if tag else ""
            title = item["title"]
            link = item["link"]
            html += f"""
            <li style="margin-bottom:6px;">
              {prefix}<a href="{link}" style="color:#1a73e8; text-decoration:none;">{title}</a>
            </li>
            """
        html += "</ul>"

    for key, meta in SECTION_META.items():
        items = news.get(key, [])
        title = meta["title"]
        subtitle = meta.get("subtitle")

        html += f"""
        <h2 style="margin-top:28px; font-size:18px;">{title}</h2>
        """

        if subtitle:
            html += f"""
            <p style="margin-top:-4px; margin-bottom:10px; font-size:13px; color:#777777;">
              {subtitle}
            </p>
            """

        if not items:
            html += '<p style="font-size:14px; color:#777777;"><i>Sem notícias listadas nesta seção hoje.</i></p>'
            continue

        html += "<ul style='padding-left:18px; font-size:14px; color:#333333; list-style-type:disc;'>"
        for item in items[:12]:
            title = item["title"]
            link = item["link"]
            summary = item.get("summary", "")
            html += f"""
            <li style="margin-bottom:10px;">
              <a href="{link}" style="color:#1a73e8; text-decoration:none; font-weight:bold;">
                {title}
              </a>
            """
            if summary:
                html += f"""
                  <br>
                  <span style="font-size:13px; color:#555555;">{summary}</span>
                """
            html += "</li>"
        html += "</ul>"

    # -------------------------------
    # CTA para inscrição na newsletter
    # -------------------------------

    html += """
        <hr style="margin-top:32px; border:none; border-top:1px solid #e0e0e0;">
        <p style="font-size:11px; color:#888888; line-height:1.4;">
          Curadoria automática com apoio de IA. Use esta newsletter como insumo estratégico, validando
          detalhes diretamente nas fontes originais quando necessário.
        </p>

        <hr style="margin-top:24px; border:none; border-top:1px solid #e0e0e0;">

        <p style="font-size:13px; color:#555555; margin-top:16px; margin-bottom:4px;">
          💌 <b>Quer receber esta newsletter todos os dias às 9h?</b>
        </p>
        <p style="margin-top:0; margin-bottom:20px;">
          <a href="https://0ce811e1.sibforms.com/serve/MUIFABmrR-vKsTfK8hyop_0K5PbZE6WYC3KqpaX_RjLAQbutDR5nNcfk0KtxQHGvCDp4QD26EWx-bjlypjL1gp5LDl-T0hKA-Unc6kd0igomqwe10xFyKMxoaHoO9-xI1dP1M_0Y24VRHRxEoY-cy9XX4Lg2qPnrR52kFuAolB_Ii2CLeYumVVSCjg_SkEUEPkx_hwFvk6YkTbFkZg=="
             style="display:inline-block; background:#1a73e8; color:#ffffff; padding:10px 18px; border-radius:6px;
                    text-decoration:none; font-size:13px; font-weight:bold;">
            Inscreva-se na Newsletter de Saúde
          </a>
        </p>

      </div>
    </body>
    </html>
    """

    return html

