from datetime import datetime
from zoneinfo import ZoneInfo

from news_fetcher import fetch_all_news
from render_news import render_news_html
from send_email import send_newsletter_email


def main():
    # Regra: enviar apenas de segunda a sexta (0=segunda, 6=domingo)
    now_br = datetime.now(ZoneInfo("America/Sao_Paulo"))
    if now_br.weekday() > 4:
        print("Hoje não é dia útil (segunda a sexta). Newsletter não será enviada.")
        return

    # Busca notícias e monta HTML
    news = fetch_all_news()
    html = render_news_html(news)

    # Envia via Brevo (implementado em send_email.py)
    send_newsletter_email("Principais notícias de Saúde – Brasil e Mundo", html)


if __name__ == "__main__":
    main()
