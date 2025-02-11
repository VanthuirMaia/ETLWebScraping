import requests, time, pandas as pd, sqlite3
from bs4 import BeautifulSoup

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
        CREATE TABLE IF NOT EXISTS produtos (
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

    

if __name__ == "__main__":

    conn = create_connection()
    setup_database(conn)

    while True:
        page_content = fetch_page()
        produto_info = parse_page(page_content)
        save_to_database(conn, produto_info)
        print("Dados salvos no banco de dados", produto_info)
        time.sleep(10)