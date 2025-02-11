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
    url = "https://www.mercadolivre.com.br/combo-teclado-e-mouse-sem-fio-logitech-mk345-layout-abnt2/p/MLB18610873#polycard_client=search-nordic&searchVariation=MLB18610873&wid=MLB2759289419&position=6&search_layout=grid&type=product&tracking_id=4530e096-b8fd-4ac0-9f3b-e0489a0e5de4&sid=search"
    response = requests.get(url)
    return response.text

def parse_page(html):
    soup = BeautifulSoup(html, "html.parser")
    product_name = soup.find("h1", class_="ui-pdp-title").get_text()
    prices: list = soup.find_all("span", class_="andes-money-amount__fraction")
    old_price: int = int(prices[0].get_text().replace(".", ""))
    new_price: int = int(prices[1].get_text().replace(".", ""))
    installments_price: int = int(prices[2].get_text().replace(".", ""))

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    return {
        "product_name": product_name,
        "old_price": old_price,
        "new_price": new_price,
        "installments_price": installments_price,
        "timestamp": timestamp
    }

def create_connection(db_name="ETLWebScraping.db"):
    # Cria a conexão com o banco de dados
    conn = sqlite3.connect(db_name)
    return conn

def setup_database(conn):
    # Cria a tabela no banco de dados
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
    # Conectar com meu DB
    cursor = conn.cursor()
    # Preço maximo historico
    cursor.execute("SELECT MAX(new_price), timestamp FROM prices")
    # Retornar o valor
    result = cursor.fetchone()
    return result[0], result[1]

async def send_telegram_message(text):
    await bot.send_message(chat_id=CHAT_ID, text=text)

async def main():
    conn = create_connection()
    setup_database(conn)

    while True:
        # Faz a requisição e parseia a página
        page_content = fetch_page()
        produto_info = parse_page(page_content)
        current_price = produto_info["new_price"]

        # Obtem o maior preço ja salvo
        max_price, max_price_timestamp = get_max_price(conn)

        if max_price is None or current_price > max_price:
            print(f"Preço maior detectado: {current_price}")
            await send_telegram_message(f"Preço maior detectado: {current_price}")
            max_price = current_price
            max_price_timestamp = produto_info["timestamp"]
        else:
            print(f"O preço máximo registrado é {max_price} em {max_price_timestamp}")
            await send_telegram_message(f"Olá usuário, o preço não alterou, espere mais um pouco!!! R$ {max_price},00 esse preço foi em {max_price_timestamp}")

        save_to_database(conn, produto_info)
        print("Dados salvos no banco de dados", produto_info)
        
        await asyncio.sleep(10)
    
    conn.close()

asyncio.run(main())