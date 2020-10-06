import requests
from requests import Response
from bs4 import BeautifulSoup
from typing import List, NewType
from random import choice, random, randint
from termcolor2 import c
from urllib import parse
from sys import exit
import time
import transliterate
import openpyxl


# input data for scrapping ads

ad_name = input('Введите что нужно найти: ')
region = input('Введите регион*: ').lower()
category = input('Введите категорию*: ').lower()
subcategory = input('Введите подкатегорию: ')

ad_name_for_url = parse.urlencode({'q': ad_name})
region_for_url = transliterate.translit(region, reversed=True).replace(' ', '_')
category_for_url = transliterate.translit(category, reversed=True).replace(' ', '_')
try:
    subcategory_for_url = transliterate.translit(subcategory, reversed=True).replace(' ', '_')
except transliterate.exceptions.LanguageDetectionError:
    subcategory_for_url = ''
# CONSTANTS
HOST: str = 'https://www.avito.ru'
URL: str = f'{HOST}/{region_for_url}/{category_for_url}/{subcategory}?{ad_name_for_url}'
USER_AGENTS: List['user_agent'] = [user_agent.strip() for user_agent in open('user-agents.txt').readlines()]
MONTH_IN_NUMBER = {
    'января': '01',
    'февраля': '02',
    'марта': '03',
    'апреля': '04',
    'мая': '05',
    'июня': '06',
    'июля': '07',
    'августа': '08',
    'сентября': '09',
    'октября': '10',
    'ноября': '11',
    'декабря': '12'
}
# ANNOTATIONS
url_type = NewType('url_type', str)
int_price = NewType('int_price', int)
# To read the first fifty ads
counter_first_fifty_ads: int = 50
output_xlsx_file: dict = {
    'Ключ': ad_name,
    'Регион': region,
    'Общее количество объявлений': 0,
    'Общее количество просмотров всего': 0,
    'Общее количество просмотров за сегодня': 0,
    'Дата публикации 10-ого объявления (сортировка по дате)': 'Нету',
    '20-ого объявления (сортировка по дате)': 'Нету',
    '50-ого объявления (сортировка по дате)': 'Нету',
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
            print(c('По вашим параметрам ничего не найдено.').red)
        else:
            print(c('Ваш IP адрес заблокировал Avito на время. Следуйте указаниям файла help.txt.').red)
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


def set_date_of_publication_of_ad() -> None:

    list_of_ad_publication_dates = []
    max_number_of_attempts = 10

    while not list_of_ad_publication_dates:
        time.sleep(3)

        ads_sorted_by_date = requests.get(URL, headers={'User-Agent': choice(USER_AGENTS)}, params={'s': 104})
        bs_page_ads = BeautifulSoup(ads_sorted_by_date.content, 'html.parser')
        ads_publication_dates = bs_page_ads.find_all('div', class_='snippet-date-info')

        if max_number_of_attempts == 0:
            print(c('Повторите попытку.').white)
            exit()
        max_number_of_attempts -= 1
        for date_tag in ads_publication_dates[:output_xlsx_file['Общее количество объявлений']]:
            try:
                day_publication, month_publication = date_tag['data-tooltip'].split()[:2]
            except ValueError:
                continue
            month_publication = MONTH_IN_NUMBER[month_publication]
            list_of_ad_publication_dates.append(f'{day_publication}.{month_publication}.2020')

    # If there are fewer ads, the script tries to install what it can.
    try:
        output_xlsx_file['Дата публикации 10-ого объявления (сортировка по дате)'] = list_of_ad_publication_dates[10]
    except IndexError:
        return

    try:
        output_xlsx_file['20-ого объявления (сортировка по дате)'] = list_of_ad_publication_dates[20]
    except IndexError:
        return

    try:
        output_xlsx_file['50-ого объявления (сортировка по дате)'] = list_of_ad_publication_dates[-1]
    except IndexError:
        return


def set_average_price_of_all_ads() -> None:
    output_xlsx_file['Средняя цена всех со всех объявлений'] = \
        (output_xlsx_file['Средняя цена всех со всех объявлений']
         / output_xlsx_file['Общее количество объявлений'])


def bypass_traps_avito(bs_ad_html: BeautifulSoup, ad_page: Response, link: str) -> int_price:
    try:

        views_on_ad_page: str = bs_ad_html.find(class_='title-info-metadata-item').get_text()[1:].split()
        try:
            price_of_product: int_price = int(
                str(bs_ad_html.find('span', class_='js-item-price').text).replace(' ', ''))
        except AttributeError:
            price_of_product: int_price = 0

    except AttributeError:

        if ad_page.status_code == 404:

            try:
                ad_page: Response = requests.get(link, headers={'User-Agent': choice(USER_AGENTS)})
                bs_ad_html: BeautifulSoup = BeautifulSoup(ad_page.content, 'html.parser')
                views_on_ad_page: list = bs_ad_html.find(class_='title-info-metadata-item').get_text()[1:].split()
                try:
                    price_of_product: int_price = int(str(bs_ad_html.find('span', class_='js-item-price').text).replace(' ', ''))
                except AttributeError:
                    price_of_product: int_price = 0
            except AttributeError:
                print(c('''
                      Это исключение возможно лишь при том, если Avito отвечает не тем сайтом, который пар-
                      сер ожидал увидеть. За остальной информацией обращайтесь к файлу help.txt.

                      Если программа продолжает парсить, необращайте внимания.
                      ''').yellow)
            else:
                try:
                    set_total_amount_views(views_on_ad_page)
                except IndexError:
                    pass
                add_price_to_price_from_all_ads(price_of_product)

        elif ad_page.status_code == 429:

            print(c('''
                  Ваш IP был заблокирован на время. Нужно подождать некоторое время, либо зайти на
                  на сайт через браузер и ввести капчу. Если ничто из этого не помогло, следуйте указа-
                  ниям в файле help.txt.
                  ''').red)
            exit()

    else:

        try:
            set_total_amount_views(views_on_ad_page)
        except IndexError:
            pass
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
                continue

            # It is done to imitate a person, so that Avito does not consider the parser a bot.
            # If delete this code, Avito can give block by IP for a while.
            if maximum_amount_of_open_links_without_pause == 0:
                time.sleep(round(randint(6, 8) + random(), 2))
                maximum_amount_of_open_links_without_pause = randint(1, 4)
            maximum_amount_of_open_links_without_pause -= 1

            ad_page: Response = requests.get(link, headers={'User-Agent': choice(USER_AGENTS)})
            bs_ad_content: BeautifulSoup = BeautifulSoup(ad_page.content, 'html.parser')

            bypass_traps_avito(bs_ad_content, ad_page, link)
            print(c(f'{link[12:]: ^} спарсено удачно.').magenta)
        print(f'{next_page} из {max_pages} спарсено.')
        next_page += 1
        if isinstance(ad_limit, int): break
    set_average_price_of_all_ads()
    print(c('Парсинг завершен успешно!').green)


def input_data_in_xlsx_file() -> None:
    row: int = 2
    xlsx_file_name: str = 'avito_statistic.xlsx'
    try:
        workbook = openpyxl.load_workbook(xlsx_file_name)
    except FileNotFoundError:
        new_workbook = openpyxl.Workbook()
        for sheet_name in new_workbook.sheetnames:
            sheet = new_workbook[sheet_name]
            new_workbook.remove(sheet)
        new_workbook_list = new_workbook.create_sheet('avito_statistic')
        for column in range(1, 11 + 1):

            new_workbook_list.cell(row=1, column=column).value = list(output_xlsx_file.keys())[column - 1]
        new_workbook.save(xlsx_file_name)
        new_workbook.close()
        workbook = openpyxl.load_workbook(xlsx_file_name)

    workbook_list = workbook['avito_statistic']
    while True:
        if workbook_list['C' + str(row)].value is None:
            for column in range(1, 11 + 1):
                workbook_list.cell(row=row, column=column).value = list(output_xlsx_file.values())[column - 1]
            break
        else:
            row += 1
    workbook.save(xlsx_file_name)
    workbook.close()


def run():
    avito_response: Response = requests.get(URL, headers={'User-Agent': choice(USER_AGENTS)})
    avito_page_content: BeautifulSoup = BeautifulSoup(avito_response.content, 'html.parser')

    set_common_amount_of_ad(avito_page_content)
    time.sleep(3)

    set_date_of_publication_of_ad()
    time.sleep(5)

    max_pages = int(avito_page_content.find_all('span', class_='pagination-item-1WyVp')[-2].text)
    send_ad_data_to_functions(max_pages)
    print('Записываем данные...')
    input_data_in_xlsx_file()
    print(c('Данные успешно записаны!').green)


if __name__ == '__main__':
    run()