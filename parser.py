import requests
from requests import Response
from bs4 import BeautifulSoup
from typing import List, NewType, NamedTuple, Tuple
from random import choice, random, randint, shuffle
from collections import namedtuple
import time


HOST: str = 'https://www.avito.ru'
URL: str = HOST + '/moskovskaya_oblast/avtomobili?q=range+rover'
USER_AGENTS: List['user_agent'] = [user_agent.strip() for user_agent in open('user-agents.txt').readlines()]
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
avito_response: Response = requests.get(URL, headers={'User-Agent': choice(USER_AGENTS)})
url_type = NewType('url_type', str)
int_price = NewType('int_price', int)


def set_common_amount_of_ad(bs_html: BeautifulSoup) -> None:
    amount_ad = bs_html.find('span', class_='page-title-count-1oJOc')
    try:
        output_xlsx_file['Общее количество объявлений'] = int(amount_ad.string)
    except AttributeError:
        print('Если вы видите эту ошибку, то скорее всего Avito заблокировал ваш IP на время.'
              '\nСледуйте рекомендация, описанные в файле help.txt.')
        raise AttributeError("'NoneType' object has no attribute 'string'")

    
def set_total_amount_views(bs_ad_html: BeautifulSoup) -> None:
    global counter_first_fifty_ads

    try:
        views_on_ad_page: str = bs_ad_html.find(class_='title-info-metadata-item').get_text()[1:].split()
    except AttributeError:
        print('''
              Это исключение возможно лишь при том, если Avito отвечает не тем сайтом, который парсер 
              ожидал увидеть. За остальной информацией обращайтесь к файлу help.txt.
              
              Если программа продолжает парсить, необращайте внимания.
              ''')
    else:
        print(views_on_ad_page)
        if counter_first_fifty_ads != 0:
            output_xlsx_file['Общее количество просмотров первых 50 объявлений (всего)'] += int(views_on_ad_page[0])
            output_xlsx_file['Общее количество просмотров первых 50 объявлений (сегодня)'] += int(views_on_ad_page[1][2:-1])
        output_xlsx_file['Общее количество просмотров всего'] += int(views_on_ad_page[0])
        output_xlsx_file['Общее количество просмотров за сегодня'] += int(views_on_ad_page[1][2:-1])
    counter_first_fifty_ads -= 1


def get_price_of_product(bs_ad_html: BeautifulSoup) -> int_price:
    try:
        price_of_product = int(str(bs_ad_html.find('span', class_='js-item-price').text).replace(' ', ''))
    except AttributeError:
        pass
    else:
        return price_of_product
    return 0


def set_average_price_of_all_ads(price_of_all_product: int_price) -> None:
    output_xlsx_file['Средняя цена всех со всех объявлений'] = \
        price_of_all_product / output_xlsx_file['Общее количество объявлений']


def set_date_of_publication_of_ad(bs_ad_html: BeautifulSoup) -> None:
    pass


def send_ad_data_to_functions(max_pages: int) -> None:

    maximum_amount_of_open_links_without_pause: int = randint(1, 5)
    price_all_product: int = 0
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
        if isinstance(ad_limit, int):
            shuffle(links_on_ads)

        for link in links_on_ads:
            print(link)
            if isinstance(ad_limit, int):
                ad_limit -= 1
            if ad_limit == 0: break
            if link[21:link.find(21)] != URL[21:link.find(21)]:
                continue

            # It is done to imitate a person, so that Avito does not consider the parser a bot.
            if maximum_amount_of_open_links_without_pause == 0:
                time.sleep(round(randint(6, 8) + random(), 1))
                maximum_amount_of_open_links_without_pause = randint(1, 5)
            maximum_amount_of_open_links_without_pause -= 1

            ad_page: Response = requests.get(link, headers={'User-Agent': choice(USER_AGENTS)})
            ad_content: BeautifulSoup = BeautifulSoup(ad_page.content, 'html.parser')

            set_total_amount_views(ad_content)
            price_all_product += get_price_of_product(ad_content)
        next_page += 1
        print('One page is scrapped')
        if isinstance(ad_limit, int):
            break
    set_average_price_of_all_ads(price_all_product)


def run():
    avito_page_content: BeautifulSoup = BeautifulSoup(avito_response.content, 'html.parser')
    set_common_amount_of_ad(avito_page_content)
    time.sleep(5)
    send_ad_data_to_functions(2)
    print(output_xlsx_file)


if __name__ == '__main__':
    run()