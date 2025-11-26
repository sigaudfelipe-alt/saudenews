from datetime import datetime
from zoneinfo import ZoneInfo

from news_fetcher import fetch_all_news
from render_news import render_news_html
from send_email import send_newsletter_email
from post_to_beehiiv import post_to_beehiiv


def main():
    # Regra: enviar apenas de segunda a sexta (0=segunda, 6=domingo)
    now_br = datetime.now(ZoneInfo("America/Sao_Paulo"))
    if now_br.weekday() > 4:
        print("Hoje não é dia útil (segunda a sexta). Newsletter não será enviada.")
        return

    news = fetch_all_news()
    html = render_news_html(news)

    # 1) Envia por e-mail
    send_newsletter_email("Principais notícias de Saúde – Brasil e Mundo", html)

    # 2) Cria post na Beehiiv (rascunho)
    post_to_beehiiv(html)


if __name__ == "__main__":
    main()
