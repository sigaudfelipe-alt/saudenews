import os
from datetime import date
import requests


def post_to_beehiiv(html_content: str):
    """Cria um post na Beehiiv via API v2 e registra a resposta no log."""
    api_key = os.getenv("BEEHIIV_API_KEY")
    publication_id = os.getenv("BEEHIIV_PUBLICATION_ID")

    if not api_key or not publication_id:
        print("Beehiiv não configurado (BEEHIIV_API_KEY ou BEEHIIV_PUBLICATION_ID ausentes).")
        return

    url = f"https://api.beehiiv.com/v2/publications/{publication_id}/posts"
    title = f"Principais notícias de Saúde – {date.today().strftime('%d/%m/%Y')}"

    # Payload mínimo para contas que só aceitam web posts (sem bloco 'email')
    payload = {
        "title": title,
        "web": {
            "body": html_content,
        },
        "status": "draft",
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        # Se a resposta não for ok, imprime status e texto para debug
        if not resp.ok:
            print(f"Beehiiv API retornou status {resp.status_code}: {resp.text}")
            return
        data = resp.json()
        print(f"Post criado na Beehiiv. ID: {data.get('id', 'desconhecido')}")
    except Exception as e:
        print("Falha ao criar post na Beehiiv:", e)
