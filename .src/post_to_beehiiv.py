import os
from datetime import date

import requests


def post_to_beehiiv(html_content: str):
    """Cria um post na Beehiiv via API v2.

    Observação: o endpoint exato e os campos podem variar conforme o plano e versão da API.
    Este exemplo usa um payload mínimo. Ajuste conforme a documentação oficial da Beehiiv.
    """
    api_key = os.getenv("BEEHIIV_API_KEY")
    publication_id = os.getenv("BEEHIIV_PUBLICATION_ID")

    if not api_key or not publication_id:
        print("Beehiiv não configurado (BEEHIIV_API_KEY ou BEEHIIV_PUBLICATION_ID ausentes). Pulando envio para Beehiiv.")
        return

    url = f"https://api.beehiiv.com/v2/publications/{publication_id}/posts"

    title = f"Principais notícias de Saúde – {date.today().strftime('%d/%m/%Y')}"

    payload = {
        "title": title,
        # Dependendo da API, pode haver campos separados para email/web.
        # Aqui usamos um campo genérico de conteúdo HTML.
        "web": {
            "body": html_content,
        },
        "email": {
            "body": html_content,
        },
        # Em muitos casos você pode criar como 'draft' e publicar depois no painel
        "status": "draft",
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        print("Post criado na Beehiiv com sucesso. Status:", resp.status_code)
    except Exception as e:
        print("Falha ao criar post na Beehiiv:", e)
