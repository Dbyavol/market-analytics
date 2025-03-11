from base_scraper import BaseScraper
import re


class WildberriesScraper(BaseScraper):
    """Скрапер для парсинга Wildberries"""
    
    def __init__(self):
        super().__init__(
            site_name='wildberries',
            base_url='https://www.wildberries.ru',
            search_input_selector='input.search-catalog__input',
            results_container_selector='div.product-card-list',
            product_link_selector='a.product-card__link',
            product_link_template='/catalog/'
        )
    
    async def _extract_product_links(self, page, items_count: int) -> list:
        """
        Извлечение ссылок на найденные товары

        Args:
            page: Страница в браузере
            items_count (int): Количество объектов для сбора
        
        Returns:
            product_urls (list): Список собранных ссылок на товары
        """
        links = await page.query_selector_all(self.product_link_selector)
        products_urls = []

        for link in links:
            href = await link.get_attribute('href')
            if href:
                products_urls.append(href)

        # Удаляем дубликаты и ограничиваем количество
        products_urls = list(dict.fromkeys(products_urls))[:items_count]
        print(f'[INFO] Найдено {len(products_urls)} ссылок на товары!')
        return products_urls

    @staticmethod
    def parse_product(soup):
        # Артикул товара
        try:
            product_id = soup.find('span', string=re.compile('Артикул')).text.split(':')[1].strip()
        except:
            product_id = None

        # Название товара
        try:
            product_name = soup.find('h1', class_='product-page__header').text.strip()
        except:
            product_name = None

        # Статистика оценок, рейтинг и отзывы
        try:
            product_statistic = soup.find('span', class_='user-feedback__rating').text.strip()
            if "из" in product_statistic:
                product_stars = product_statistic.split(' из')[0].strip()
                product_reviews = soup.find('span', class_='user-feedback__count').text.strip()
            else:
                product_statistic = None
                product_stars = None
                product_reviews = None
        except:
            product_statistic = None
            product_stars = None
            product_reviews = None

        # Цена товара
        try:
            price_block = soup.find('div', class_='product-price__price-block')
            product_discount_price = price_block.find('span', class_='price-block__final-price').text.strip()

            product_base_price = price_block.find('span', class_='price-block__old-price').text.strip() if price_block.find(
                'span', class_='price-block__old-price') else product_discount_price

        except:
            product_discount_price = None
            product_base_price = None

        # Создание словаря данных
        product_data = {
            'Артикул': product_id,
            'Название': product_name,
            'Цена по скидке': product_discount_price,
            'Цена без скидки': product_base_price,
            'Статистика оценок': product_statistic if product_stars is None else None,
            'Рейтинг': product_stars,
            'Количество отзывов': product_reviews,
        }

        return product_data
    