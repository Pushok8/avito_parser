import requests
from requests import Response
from bs4 import BeautifulSoup
from typing import List, NewType
from random import choice


HOST: str = 'https://www.avito.ru/'
URL: str = HOST + 'moskva_i_mo/koshki'
USER_AGENTS: List['user_agent'] = [user_agent.strip() for user_agent in open('user-agents.txt').readlines()]

output_xlsx_file: dict = {
    'Ключ': None,
    'Регион': None,
    'Общее количество объявлений': None,
    'Общее количество просмотров всего': None,
    'Общее количество просмотров за сегодня': None,
    'Общее количество просмотров за вчера': None,
    'Дата публикации 10го объявления (сортировка объявлений по дате)': None,
    '20го объявления (сортировка объявлений по дате)': None,
    '50го объявления (сортировка объявлений по дате)': None,
    'Средняя цена всех со всех объявлений': None,
    'Общее количество просмотров первых 50 объявлений (сегодня)': None,
    'Общее количество просмотров первых 50 объявлений (всего)': None
}
# Будет расширен функционал
# ad_name = input('Введите имя объявления: ')
# region = input('Введите регион: ')
# category = input('Введите категорию: ')
avito_response: Response = requests.get(URL, headers={'User-Agent': choice(USER_AGENTS)})
url_type = NewType('url_type', str)


def set_common_amount_of_ad(bs_html: BeautifulSoup) -> None:
    amount_ad = bs_html.find('span', class_='page-title-count-1oJOc')
    output_xlsx_file['Общее количество объявлений'] = amount_ad.string


def run():
    avito_page_content = BeautifulSoup(avito_response.content, 'html.parser')
    set_common_amount_of_ad(avito_page_content)


if __name__ == '__main__':
    run()