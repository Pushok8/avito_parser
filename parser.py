import requests
from requests import Response
from bs4 import BeautifulSoup
from typing import List, NewType
from random import choice, random, randint
from sys import exit
import time

# CONSTANTS
HOST: str = 'https://www.avito.ru'
URL: str = HOST + '/elektrogorsk/odezhda_obuv_aksessuary/kupit-aksessuary-ASgBAgICAUTeAtoL'
USER_AGENTS: List['user_agent'] = [user_agent.strip() for user_agent in open('user-agents.txt').readlines()]
# ANNOTATIONS
url_type = NewType('url_type', str)
int_price = NewType('int_price', int)
# To read the first fifty ads
counter_first_fifty_ads: int = 50
# Будет расширен функционал
# ad_name = input('Введите имя объявления: ')
# region = input('Введите регион: ')
# category = input('Введите категорию: ')
output_xlsx_file: dict = {
    'Ключ': None,
    'Регион': None,
    'Общее количество объявлений': 0,
    'Общее количество просмотров всего': 0,
    'Общее количество просмотров за сегодня': 0,
    'Общее количество просмотров за вчера': '???',
    'Дата публикации 10го объявления (сортировка объявлений по дате)': None,
    '20го объявления (сортировка объявлений по дате)': None,
    '50го объявления (сортировка объявлений по дате)': None,
    'Средняя цена всех со всех объявлений': 0,
    'Общее количество просмотров первых 50 объявлений (сегодня)': 0,
    'Общее количество просмотров первых 50 объявлений (всего)': 0
}


def set_common_amount_of_ad(bs_html: BeautifulSoup) -> None:
    amount_ad = bs_html.find('span', class_='page-title-count-1oJOc')
    try:
        output_xlsx_file['Общее количество объявлений'] = int(amount_ad.string)
    except AttributeError:
        if bs_html.find('h2', class_='firewall-title') is None:
            print('По вашим параметрам ничего не найдено.')
        else:
            print('Ваш IP адрес заблокировал Avito на время. Следуйте указаниям файла help.txt.')
        exit()


def set_total_amount_views(views_on_ad_page: list) -> None:
    global counter_first_fifty_ads

    if counter_first_fifty_ads != 0:
        output_xlsx_file['Общее количество просмотров первых 50 объявлений (всего)'] += int(
            views_on_ad_page[0])
        output_xlsx_file['Общее количество просмотров первых 50 объявлений (сегодня)'] += int(
            views_on_ad_page[1][2:-1])
        counter_first_fifty_ads -= 1
    output_xlsx_file['Общее количество просмотров всего'] += int(views_on_ad_page[0])
    output_xlsx_file['Общее количество просмотров за сегодня'] += int(views_on_ad_page[1][2:-1])


def add_price_to_price_from_all_ads(price_of_product: int_price) -> None:
    output_xlsx_file['Средняя цена всех со всех объявлений'] += price_of_product


def set_date_of_publication_of_ad(bs_ad_html: BeautifulSoup) -> None:
    pass


def set_average_price_of_all_ads() -> None:
    output_xlsx_file['Средняя цена всех со всех объявлений'] = \
        (output_xlsx_file['Средняя цена всех со всех объявлений']
         / output_xlsx_file['Общее количество объявлений'])


def bypass_traps_avito(bs_ad_html: BeautifulSoup, ad_page: Response, link: str) -> int_price:

    try:
        views_on_ad_page: str = bs_ad_html.find(class_='title-info-metadata-item').get_text()[1:].split()
        price_of_product = int(str(bs_ad_html.find('span', class_='js-item-price').text).replace(' ', ''))
        date_of_publication_of_ad = bs_ad_html.find('div', class_='title-info-metadata-item-redesign')
    except AttributeError:
        if ad_page.status_code == 404:
            try:
                ad_page: Response = requests.get(link, headers={'User-Agent': choice(USER_AGENTS)})
                bs_ad_html: BeautifulSoup = BeautifulSoup(ad_page.content, 'html.parser')
                views_on_ad_page: list = bs_ad_html.find(class_='title-info-metadata-item').get_text()[1:].split()
                price_of_product: int_price = int(str(bs_ad_html.find('span', class_='js-item-price').text).replace(' ', ''))
            except AttributeError:
                print('''
                      Это исключение возможно лишь при том, если Avito отвечает не тем сайтом, который пар-
                      сер ожидал увидеть. За остальной информацией обращайтесь к файлу help.txt.

                      Если программа продолжает парсить, необращайте внимания.
                      ''')
            else:
                print('Good')
                set_total_amount_views(views_on_ad_page)
                add_price_to_price_from_all_ads(price_of_product)
        elif ad_page.status_code == 429:
            print('''
                  Ваш IP был заблокирован на время. Нужно подождать некоторое время, либо зайти на
                  на сайт через браузер и ввести капчу. Если ничто из этого не помогло, следуйте указа-
                  ниям в файле help.txt.
                  ''')
            exit()
    else:
        set_total_amount_views(views_on_ad_page)
        add_price_to_price_from_all_ads(price_of_product)


def send_ad_data_to_functions(max_pages: int) -> None:

    maximum_amount_of_open_links_without_pause: int = randint(1, 5)
    next_page: int = 1
    # Sometimes ads are not enough for one page and Avito fills it with similar ads.
    if output_xlsx_file['Общее количество объявлений'] <= 50:
        ad_limit = output_xlsx_file['Общее количество объявлений']
    else:
        ad_limit = 'More than 50'

    while next_page != max_pages + 1:

        page_with_ad: Response = requests.get(URL, headers={'User-Agent': choice(USER_AGENTS)}, params={'p': next_page})
        content_of_ad_page: BeautifulSoup = BeautifulSoup(page_with_ad.content, 'html.parser')
        links_on_ads: List[url_type] = [HOST + element.get('href') for element in
                                        content_of_ad_page.find_all('a', class_='snippet-link')]
        while not links_on_ads:
            # Avito sometimes gives out the wrong data that it usually gives out (we are talking about classes).
            links_on_ads = [HOST + element.get('href') for element in
                            content_of_ad_page.find_all('a', class_='title-root-395AQ')]
        time.sleep(3)

        for link in links_on_ads:

            if isinstance(ad_limit, int):
                ad_limit -= 1
            if ad_limit == 0: break
            if link[21:link[21:].find('/') + 21] != URL[21:URL[21:].find('/') + 21]:
                print(link, 'is fake link')
                continue

            # It is done to imitate a person, so that Avito does not consider the parser a bot.
            # If delete this code, Avito can give block by IP for a while.
            if maximum_amount_of_open_links_without_pause == 0:
                time.sleep(round(randint(6, 8) + random(), 2))
                maximum_amount_of_open_links_without_pause = randint(1, 4)
            maximum_amount_of_open_links_without_pause -= 1

            print(link, end=' ')
            ad_page: Response = requests.get(link, headers={'User-Agent': choice(USER_AGENTS)})
            bs_ad_content: BeautifulSoup = BeautifulSoup(ad_page.content, 'html.parser')
            print(ad_page.status_code)
            bypass_traps_avito(bs_ad_content, ad_page, link)

        next_page += 1
        print(next_page, 'is next page')
        if isinstance(ad_limit, int):
            break
    set_average_price_of_all_ads()


def run():
    avito_response: Response = requests.get(URL, headers={'User-Agent': choice(USER_AGENTS)})
    avito_page_content: BeautifulSoup = BeautifulSoup(avito_response.content, 'html.parser')
    set_common_amount_of_ad(avito_page_content)
    time.sleep(5)
    send_ad_data_to_functions(2)
    print(output_xlsx_file)


if __name__ == '__main__':
    run()