import asyncio
import json
from playwright.async_api import async_playwright
from functions import collect_product_data, make_file_name

driver_args = [
    "--start-maximized", 
    "--disable-blink-features=AutomationControlled",
    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
]

class OzonScraper:
    def __init__(self, max_threads=10):
        self.max_threads = max_threads

    async def async_get_products_links(self, item_name='наушники hyperx', items_count=10):
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True, args=driver_args)
                page = await browser.new_page()

                # Открываем сайт Ozon
                await page.goto('https://ozon.ru')
                await page.wait_for_timeout(2000)
                print('[INFO] Сайт ozon открыт')

                # Ввод запроса в поиск
                await page.fill('input[name="text"]', item_name)
                await page.press('input[name="text"]', 'Enter')

                # Ожидание загрузки результатов
                await page.wait_for_selector('[data-widget="searchResultsV2"]')
                print('[INFO] Запрос поиска на ozon создан')

                # Прокрутка страницы для подгрузки товаров
                if items_count > 25:
                    for _ in range(5):
                        await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                        await page.wait_for_timeout(1000)

                # Получение ссылок на товары
                links = await page.query_selector_all("[data-widget='searchResultsV2'] a[href]")
                products_urls = []

                for link in links:
                    href = await link.get_attribute('href')
                    if href and href.startswith('/product/'):
                        products_urls.append(f'https://ozon.ru{href}')

                # Удаляем дубликаты и ограничиваем количество
                products_urls = list(dict.fromkeys(products_urls))[:items_count]
                print(f'[INFO] Найдено {len(products_urls)} ссылок на товары!')

                # Сбор данных о товарах
                collected_data = []
                tasks = [collect_product_data(browser, url, 'ozon') for url in products_urls]
                for result in await asyncio.gather(*tasks, return_exceptions=True):
                    if isinstance(result, Exception):
                        print(f'[ERROR] Ошибка при обработке товара: {result}')
                    else:
                        collected_data.append(result)

                await browser.close()
                return collected_data

        except Exception as e:
            print(f'[ERROR] Ошибка при сборе ссылок: {e}')
            return []

    @staticmethod
    def save_to_json(data, file_name):
        try:
            with open(file_name, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
            print(f'[INFO] Данные сохранены в файл {file_name}')
        except Exception as e:
            print(f'[ERROR] Ошибка при сохранении данных: {e}')


if __name__ == '__main__':
    request = 'красивая тетрадь'
    scraper = OzonScraper(max_threads=10)

    async def main():
        start_time = asyncio.get_event_loop().time()  # Первая точка замера времени
        print('[INFO] Сбор данных начался...')

        products_data = await scraper.async_get_products_links(item_name=request, items_count=100)

        if products_data:
            file_name = f'{make_file_name(request)}_DATA.json'
            scraper.save_to_json(products_data, file_name)

        end_time = asyncio.get_event_loop().time()  # Точка завершения
        print(f'[INFO] Сбор данных завершён за {end_time - start_time:.2f} секунд.')

    asyncio.run(main())
