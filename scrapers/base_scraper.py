import asyncio
import json
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

driver_args = [
    "--start-maximized",
    "--disable-blink-features=AutomationControlled",
    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
]

class BaseScraper:
    """Базовый класс для парсинга интернет-магазинов"""
    
    def __init__(self, site_name, base_url, search_input_selector, results_container_selector,
                 product_link_selector, product_link_template):
        self.site_name = site_name
        self.base_url = base_url
        self.search_input_selector = search_input_selector
        self.results_container_selector = results_container_selector
        self.product_link_selector = product_link_selector
        self.product_link_template = product_link_template

    async def async_get_products_links(self, item_name: str, items_count: int) -> list:
        """
        Главный метод получения данных, который вызывает подфункции

        Args:
            item_name (str): Текст запроса
            items_count (int): Количество объектов для сбора

        Returns:
            collected_data: Собранные данные по запросу
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False, args=driver_args)
                page = await browser.new_page()

                # 1. Открываем сайт
                await self._open_site(page)

                # 2. Ввод запроса
                await self._search_product(page, item_name)

                # 3. Скроллим страницу для подгрузки результатов
                if items_count > 8:
                    await self._scroll_and_load_results(page)

                # 4. Извлекаем ссылки на товары
                products_urls = await self._extract_product_links(page, items_count)

                # 5. Собираем данные о товарах
                collected_data = await self._collect_product_data(browser, products_urls)

                await browser.close()
                return collected_data

        except Exception as e:
            print(f'[ERROR] Ошибка при сборе ссылок: {e}')
            return []

    async def _open_site(self, page):
        """
        Открытие сайта в браузере

        Args:
            page: Страница в браузере
        """
        await page.goto(self.base_url)
        await page.wait_for_timeout(2000)
        print(f'[INFO] {self.site_name} открыт')

    async def _search_product(self, page, item_name: str):
        """
        Ввод поискового запроса и запуск поиска

        Args:
            page: Страница в браузере
            item_name (str): Текст запроса
        """
        await page.fill(self.search_input_selector, item_name)
        await page.press(self.search_input_selector, 'Enter')
        print('[INFO] Поиск начат')

        await page.wait_for_selector(self.results_container_selector, timeout=10000)
        print('[INFO] Поиск завершен')

    async def _scroll_and_load_results(self, page):
        """
        Прокрутка страницы для загрузки товаров

        Args:
            page: Страница в браузере
        """
        for _ in range(5):
            await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)

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
            print(href)
            if href and href.startswith(self.product_link_template):
                products_urls.append(f'{self.base_url}{href}')

        # Удаляем дубликаты и ограничиваем количество
        products_urls = list(dict.fromkeys(products_urls))[:items_count]
        print(f'[INFO] Найдено {len(products_urls)} ссылок на товары!')
        return products_urls

    async def _collect_product_data(self, browser, products_urls: list) -> list:
        """
        Сбор данных по ссылка

        Args:
            browser: Браузер
            product_urls (list): Список собранных ссылок на товары

        Returns:
            collected_data (list): Собранные данные
        """
        collected_data = []
        tasks = [self.collect_product_data(browser, url) for url in products_urls]
        for result in await asyncio.gather(*tasks, return_exceptions=True):
            if isinstance(result, Exception):
                print(f'[ERROR] Ошибка при обработке товара: {result}')
            else:
                collected_data.append(result)
        return collected_data
    
    def parse_product(soup):
        pass

    async def collect_product_data(self, browser, url):
        """Собирает данные о товарах по ссылке."""
        page = await browser.new_page()
        await page.goto(url)
        await asyncio.sleep(5)  # Ожидание полной загрузки страницы

        content = await page.content()
        soup = BeautifulSoup(content, 'lxml')

        product_data = self.parse_product(soup)

        await page.close()

        return product_data

    @staticmethod
    def save_to_json(data: list, file_name: str):
        """
        Сохранение данных в JSON-файл

        Args:
            data (list): Данные
            file_name (str): Название JSON-файла
        """
        try:
            with open(file_name, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
            print(f'[INFO] Данные сохранены в файл {file_name}')
        except Exception as e:
            print(f'[ERROR] Ошибка при сохранении данных: {e}')
            