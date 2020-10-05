import requests
from requests import Response
from bs4 import BeautifulSoup
from typing import List, NewType
from random import choice, random, randint, shuffle
import time

HOST: str = 'https://www.avito.ru/'
URL: str = HOST + 'elektrogorsk/bytovaya_tehnika/dlya_kuhni-ASgBAgICAURglk8?q=микроволновая+печь'
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
    output_xlsx_file['Общее количество объявлений'] = int(amount_ad.string)


def set_total_amount_views(bs_ad_html: BeautifulSoup) -> None:
    try:
        views_on_ad_page: str = bs_ad_html.find(class_='title-info-metadata-item').get_text()[1:].split()
    except AttributeError:
        print('''
              Скорее всего ваш IP адресс забанил Avito из-за частых запросов. Это можно решить 
              путём захода на сайт через браузер через тот же IP, через который запускали парсер
              (в 99% случаев просто нужно открыть авито в браузере). Либо сменить IP или же просто
              подождать какое то время(примерно 10 минут). Так же попробуйте перезапустить программу.

              Если программа работает нормально, необращайте внимания.
              ''')
    output_xlsx_file['Общее количество просмотров всего'] += int(views_on_ad_page[0])
    output_xlsx_file['Общее количество просмотров за сегодня'] += int(views_on_ad_page[1][2:-1])


def set_common_amount_of_total_views_and_today(max_pages: int) -> None:
    maximum_amount_of_open_links_without_pause: int = randint(1, 5)
    next_page: int = 1
    ad_limit: int = output_xlsx_file['Общее количество объявлений']

    while next_page != max_pages:

        page_with_ad: Response = requests.get(URL, headers={'User-Agent': choice(USER_AGENTS)}, params={'p': next_page,
                                                                                                        's': 104})
        #                                                                                               'q': То что напишет заказчик
        content_of_ad_page: BeautifulSoup = BeautifulSoup(page_with_ad.content, 'html.parser')
        links_on_ads: List[url_type] = [HOST[:-1] + element.get('href') for element in
                                        content_of_ad_page.find_all('a', class_='snippet-link')]
        time.sleep(3)
        if ad_limit > 50:
            shuffle(links_on_ads)

        for link in links_on_ads:

            ad_limit -= 1
            if ad_limit == 0: break
            if link[21:].find('/') == -1: continue
            if maximum_amount_of_open_links_without_pause == 0:
                time.sleep(round(randint(6, 8) + random(), 1))
                maximum_amount_of_open_links_without_pause = randint(1, 5)
            maximum_amount_of_open_links_without_pause -= 1

            # Get respone page of all pages with ads
            ad_page: Response = requests.get(link, headers={'User-Agent': choice(USER_AGENTS)})
            ad_content: BeautifulSoup = BeautifulSoup(ad_page.content, 'html.parser')
            set_total_amount_views(ad_content)
            next_page += 1

        if ad_limit < 50:
            break


def run():
    avito_page_content: BeautifulSoup = BeautifulSoup(avito_response.content, 'html.parser')
    set_common_amount_of_ad(avito_page_content)
    time.sleep(5)
    set_common_amount_of_total_views_and_today(2)
    print(output_xlsx_file)


if __name__ == '__main__':
    run()