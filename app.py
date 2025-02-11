import requests

def fetch_page(url):
    response = requests.get(url)
    return response.text

if __name__ == "__main__":
    url = "https://www.mercadolivre.com.br/combo-teclado-e-mouse-sem-fio-logitech-mk345-layout-abnt2/p/MLB18610873#polycard_client=search-nordic&searchVariation=MLB18610873&wid=MLB2759289419&position=6&search_layout=grid&type=product&tracking_id=4530e096-b8fd-4ac0-9f3b-e0489a0e5de4&sid=search"
    page_content = fetch_page(url)
    print(fetch_page)