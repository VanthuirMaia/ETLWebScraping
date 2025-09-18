import requests, time, pandas as pd, sqlite3, os, asyncio
from bs4 import BeautifulSoup
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

# Configurações do bot Telegram
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = Bot(token=TOKEN)


def fetch_page():
    url = "https://www.mercadolivre.com.br/combo-teclado-e-mouse-sem-fio-logitech-mk345-layout-abnt2/p/MLB18610873"
    headers = {"User-Agent": "Mozilla/5.0"}  # força o site a retornar HTML completo
    response = requests.get(url, headers=headers, timeout=10)
    return response.text


def parse_page(html):
    soup = BeautifulSoup(html, "html.parser")

    # Nome do produto
    title_tag = soup.find("h1")
    product_name = title_tag.get_text(strip=True) if title_tag else "Título não encontrado"

    # Preços
    price_tags = soup.find_all("span", class_=lambda x: x and "andes-money-amount__fraction" in x)
    prices = [int(tag.get_text().replace(".", "")) for tag in price_tags]

    old_price = prices[0] if len(prices) > 0 else None
    new_price = prices[1] if len(prices) > 1 else None
    installments_price = prices[2] if len(prices) > 2 else None

    if new_price is None:
        print("⚠️ Atenção: não foi possível capturar o preço atual.")

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    return {
        "product_name": product_name,
        "old_price": old_price,
        "new_price": new_price,
        "installments_price": installments_price,
        "timestamp": timestamp
    }


def create_connection(db_name="ETLWebScraping.db"):
    return sqlite3.connect(db_name)


def setup_database(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT,
            old_price INTEGER,
            new_price INTEGER,
            installments_price INTEGER,
            timestamp TEXT
        )
    """)
    conn.commit()


def save_to_database(conn, produto_info):
    new_row = pd.DataFrame([produto_info])
    new_row.to_sql("prices", conn, if_exists="append", index=False)


def get_max_price(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(new_price), timestamp FROM prices")
    result = cursor.fetchone()
    return result[0], result[1]


async def send_telegram_message(text):
    try:
        await bot.send_message(chat_id=CHAT_ID, text=text)
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem para Telegram: {e}")


async def main():
    conn = create_connection()
    setup_database(conn)

    while True:
        page_content = fetch_page()
        produto_info = parse_page(page_content)
        current_price = produto_info["new_price"]

        # Se não conseguiu capturar preço, pula
        if current_price is None:
            print("⚠️ Preço não encontrado. Tentando novamente em 30 segundos...")
            await asyncio.sleep(30)
            continue

        # Preço máximo histórico
        max_price, max_price_timestamp = get_max_price(conn)

        if max_price is None or current_price > max_price:
            msg = f"📈 Novo preço máximo detectado: R$ {current_price},00"
            print(msg)
            await send_telegram_message(msg)
            max_price = current_price
            max_price_timestamp = produto_info["timestamp"]
        else:
            msg = (
                f"ℹ️ Preço não mudou. Máximo registrado: R$ {max_price},00 "
                f"em {max_price_timestamp}"
            )
            print(msg)
            await send_telegram_message(msg)

        # Salva no banco
        save_to_database(conn, produto_info)
        print("✅ Dados salvos:", produto_info)

        await asyncio.sleep(30)  # intervalo entre execuções

    conn.close()


if __name__ == "__main__":
    asyncio.run(main())
