import requests, time
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

    return {
        "product_name": product_name,
        "old_price": old_price,
        "new_price": new_price,
        "installments_price": installments_price
    }
    

if __name__ == "__main__":
    while True:
        page_content = fetch_page()
        produto_info = parse_page(page_content)
        print(produto_info)
        time.sleep(10)