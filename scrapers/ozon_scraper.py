from base_scraper import BaseScraper
import re


class OzonScraper(BaseScraper):
    """Скрапер для парсинга Ozon"""
    
    def __init__(self):
        super().__init__(
            site_name='ozon',
            base_url='https://www.ozon.ru',
            search_input_selector='input[name="text"]',
            results_container_selector='[data-widget="searchResultsV2"]',
            product_link_selector='[data-widget="searchResultsV2"] a[href]',
            product_link_template='/product/'
        )
    
    @staticmethod
    def parse_product(soup):
        # product_id
        try:
            product_id = soup.find('div', string=re.compile(
                'Артикул:')).text.split('Артикул: ')[1].strip()
        except:
            product_id = None

        # product_name
        product_name = soup.find('div', attrs={"data-widget": 'webProductHeading'}).find(
            'h1').text.strip().replace('\t', '').replace('\n', ' ')

        # product statistic
        try:
            product_statistic = soup.find(
                'div', attrs={"data-widget": 'webSingleProductScore'}).text.strip()

            if " • " in product_statistic:
                product_stars = product_statistic.split(' • ')[0].strip()
                product_reviews = product_statistic.split(' • ')[1].strip()
            else:
                product_statistic = product_statistic
        except:
            product_statistic = None
            product_stars = None
            product_reviews = None

        # product price
        try:
            ozon_card_price_element = soup.find(
                'span', string="c Ozon Картой").parent.find('div').find('span')
            product_ozon_card_price = ozon_card_price_element.text.strip(
            ) if ozon_card_price_element else ''

            price_element = soup.find(
                'span', string="без Ozon Карты").parent.parent.find('div').findAll('span')

            product_discount_price = price_element[0].text.strip(
            ) if price_element[0] else ''
            product_base_price = price_element[1].text.strip(
            ) if price_element[1] is not None else ''
        except:
            product_ozon_card_price = None
            product_discount_price = None
            product_base_price = None

        # product price
        try:
            ozon_card_price_element = soup.find(
                'span', string="c Ozon Картой").parent.find('div').find('span')
        except AttributeError:
            card_price_div = soup.find(
                'div', attrs={"data-widget": "webPrice"}).findAll('span')

            product_base_price = card_price_div[0].text.strip()
            product_discount_price = card_price_div[1].text.strip()

        product_data = (
            {
                'Артикул': product_id,
                'Название': product_name,
                'Цена по озон карте': product_ozon_card_price,
                'Цена по скидке': product_discount_price,
                'Цена без скидки': product_base_price,
                'Статистика оценок': product_statistic,
                'Рейтинг': product_stars,
                'Количество отзывов': product_reviews,
            }
        )
        return product_data
    