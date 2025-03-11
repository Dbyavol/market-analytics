from scrapers.ozon_scraper import OzonScraper
from scrapers.wb_scraper import WildberriesScraper
import asyncio


async def main():
    request = 'красивая тетрадь'
    items_count = 5

    scraper = OzonScraper()

    start_time = asyncio.get_event_loop().time()
    print(f'[INFO] Начинаем сбор данных с {scraper.site_name}')

    products_data = await scraper.async_get_products_links(request, items_count)

    if products_data:
        file_name = request.replace(' ', '_') + '_DATA.json'
        scraper.save_to_json(products_data, file_name)

    end_time = asyncio.get_event_loop().time()
    print(f'[INFO] Сбор данных завершён за {end_time - start_time:.2f} секунд.')

if __name__ == '__main__':
    asyncio.run(main())