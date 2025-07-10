import logging
import feedparser
import requests
from deep_translator import GoogleTranslator
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 10 # seconds

def _translate_text(text: str) -> str:
    """Translates text to Russian using GoogleTranslator."""
    if not text:
        return ""
    try:
        return GoogleTranslator(source='auto', target='ru').translate(text)
    except Exception as e:
        logger.error(f"Ошибка при переводе текста: {e}", exc_info=True)
        return text # Return original text on error

def get_latest_image() -> dict | None:
    """
    Fetches the latest Image of the Day from NASA, extracts relevant info, and translates it.
    """
    feed_url = "https://www.nasa.gov/feeds/iotd-feed/"
    try:
        response = requests.get(feed_url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        feed = feedparser.parse(response.content)

        if not feed.entries:
            logger.warning("NASA IOTD feed is empty.")
            return None

        logger.info(f"Получено {len(feed.entries)} записей из фида IOTD.")
        latest_entry = feed.entries[0]

        title = latest_entry.get('title', 'No Title')
        logger.info(f"Заголовок последней записи IOTD: {title}")
        description_html = latest_entry.get('summary', latest_entry.get('description', ''))
        link = latest_entry.get('link', '')

        # Extract image URL from the linked page
        image_url = None
        if link:
            try:
                page_response = requests.get(link, timeout=REQUEST_TIMEOUT)
                page_response.raise_for_status()
                soup = BeautifulSoup(page_response.content, 'html.parser')
                # Find the og:image meta tag
                og_image_tag = soup.find('meta', property='og:image')
                if og_image_tag and og_image_tag.get('content'):
                    image_url = og_image_tag['content']
            except requests.exceptions.RequestException as e:
                logger.error(f"Ошибка при загрузке страницы с изображением: {e}", exc_info=True)

        # Fallback to media_content if page parsing fails
        if not image_url and 'media_content' in latest_entry and latest_entry.media_content:
            for media in latest_entry.media_content:
                if media.get('type', '').startswith('image/'):
                    image_url = media.get('url')
                    break
        logger.info(f"Найден URL изображения для IOTD: {image_url}")

        # Extract first two sentences from description
        sentences = re.split(r'(?<=[.!?])\s+', BeautifulSoup(description_html, 'html.parser').get_text())
        short_description = " ".join(sentences[:2]) if sentences else ""

        translated_title = _translate_text(title)
        translated_description = _translate_text(short_description)

        logger.info(f"Получено последнее изображение: {translated_title}")
        return {
            'title': translated_title,
            'description': translated_description,
            'date': latest_entry.get('published', 'N/A'),
            'link': link,
            'image_url': image_url
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка сети при получении изображения дня NASA: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Неизвестная ошибка при обработке изображения дня NASA: {e}", exc_info=True)
        return None

def get_latest_news(limit: int = 5) -> list[dict]:
    """
    Fetches the latest news from NASA, filters for JWST, extracts relevant info, and translates it.
    """
    feed_url = "https://www.nasa.gov/feed/"
    news_items = []
    try:
        response = requests.get(feed_url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        feed = feedparser.parse(response.content)

        if not feed.entries:
            logger.warning("NASA news feed is empty.")
            return []

        logger.info(f"Получено {len(feed.entries)} записей из новостного фида NASA.")
        for entry in feed.entries[:50]:
            title = entry.get('title', 'No Title')
            logger.debug(f"Проверка новости: {title}")
            summary = entry.get('summary', '')
            content = ''
            if hasattr(entry, 'content'):
                content = entry.content[0].value
            
            if "webb" in title.lower() or "jwst" in title.lower() or "webb" in summary.lower() or "jwst" in summary.lower() or "james webb" in title.lower() or "james webb" in summary.lower() or "webb" in content.lower() or "jwst" in content.lower() or "james webb" in content.lower():
                description_html = entry.get('summary', entry.get('description', ''))
                link = entry.get('link', '')

                # Clean description from HTML tags
                clean_description = BeautifulSoup(description_html, 'html.parser').get_text()

                # Extract all unique image URLs
                image_urls = set()
                
                # From media_content
                if 'media_content' in entry and entry.media_content:
                    for media in entry.media_content:
                        if media.get('type', '').startswith('image/') and media.get('url'):
                            image_urls.add(media.get('url'))
                
                # From HTML in summary
                soup_summary = BeautifulSoup(description_html, 'html.parser')
                for img_tag in soup_summary.find_all('img'):
                    if img_tag.get('src'):
                        image_urls.add(img_tag['src'])

                # From HTML in full content
                if hasattr(entry, 'content'):
                    full_content_html = entry.content[0].value
                    soup_content = BeautifulSoup(full_content_html, 'html.parser')
                    for img_tag in soup_content.find_all('img'):
                        if img_tag.get('src'):
                            image_urls.add(img_tag['src'])
                
                logger.info(f"Найдено {len(image_urls)} уникальных изображений для новости: {title}")

                translated_title = _translate_text(title)
                translated_description = _translate_text(clean_description)

                news_items.append({
                    'title': translated_title,
                    'description': translated_description,
                    'date': entry.get('published', 'N/A'),
                    'link': link,
                    'image_urls': list(image_urls)
                })
                if len(news_items) >= limit:
                    break
        
        logger.info(f"Найдено {len(news_items)} новостей по теме JWST.")
        return news_items

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка сети при получении новостей NASA: {e}. URL: {feed_url}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"Неизвестная ошибка при обработке новостей NASA: {e}. URL: {feed_url}", exc_info=True)
        return []
