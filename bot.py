import logging
import json
import os
import random
import datetime
import asyncio
import html
from io import BytesIO
import requests
from PIL import Image
from telegram import Update, BotCommand, InputMediaPhoto
from telegram.ext import Application, CommandHandler, ContextTypes, JobQueue

from logger_config import setup_logging
from position import create_jwst_orbit_plot
import news
from news import get_latest_news

setup_logging()
logger = logging.getLogger(__name__)

CAPTION_LIMIT = 1024

def load_config():
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.critical("Файл config.json не найден!")
        exit()
    except json.JSONDecodeError:
        logger.critical("Ошибка в синтаксисе файла config.json.")
        exit()

async def post_init(application: Application) -> None:
    commands = [
        BotCommand("start", "🚀 Перезапустить бота"),
        BotCommand("latest_image", "🖼️ Последнее изображение"),
        BotCommand("news", "📰 Последние новости"),
        BotCommand("position", "🛰️ Схема положения в космосе"),
        BotCommand("fact", "💡 Случайный факт о телескопе"),
        BotCommand("help", "ℹ️ Помощь по командам"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("Команды бота успешно установлены.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(
        f"Привет, {user.mention_html()}\n\n"
        "Я бот, который расскажет всё о космическом телескопе «Джеймс Уэбб».\n"
        "Используйте /help, чтобы увидеть список всех команд."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    commands = await context.bot.get_my_commands()
    help_text = "<b>Доступные команды:</b>\n\n"
    help_text += "\n".join(f"/{command.command} - {command.description}" for command in commands)
    await update.message.reply_html(help_text, disable_web_page_preview=True)

async def latest_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="TYPING")
    try:
        image_info = await asyncio.to_thread(news.get_latest_image)
        if image_info and image_info.get('image_url'):
            caption = f"<b>{html.escape(image_info['title'])}</b>\n\n" \
                      f"{html.escape(image_info['description'])}\n\n" \
                      f"<i>Дата: {image_info['date']}</i>\n" \
                      f"<a href=\"{image_info['link']}\">Источник</a>"

            if len(caption) > CAPTION_LIMIT:
                caption = caption[:CAPTION_LIMIT - 3] + "..."

            await update.message.reply_photo(
                photo=image_info['image_url'],
                caption=caption,
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text("Не удалось получить последнее изображение. Попробуйте позже.")
    except Exception as e:
        logger.error(f"Ошибка при получении изображения: {e}", exc_info=True)
        await update.message.reply_text("Произошла внутренняя ошибка при получении изображения. Администратор уже уведомлен.")

async def get_news(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="TYPING")
    try:
        latest_news = await asyncio.to_thread(get_latest_news, limit=5)
        if latest_news:
            for news_item in latest_news:
                text_caption = (f"<b>{html.escape(news_item['title'])}</b>\n\n"
                                f"{html.escape(news_item['description'])} \n\n"
                                f"<i>Дата: {news_item['date']}</i>\n"
                                f"<a href=\"{news_item['link']}\">Читать далее</a>")

                if news_item.get('image_urls'):
                    media_group = []
                    for i, image_url in enumerate(news_item['image_urls'][:10]):
                        try:
                            response = await asyncio.to_thread(requests.get, image_url, {'timeout': 15})
                            response.raise_for_status()
                            content_type = response.headers.get('Content-Type', '')

                            if 'image' not in content_type:
                                logger.warning(f"Skipping non-image URL: {image_url} (Content-Type: {content_type})")
                                continue

                            image_content = BytesIO(response.content)

                            # --- Image Resizing Logic ---
                            image_content.seek(0)
                            img = Image.open(image_content)
                            
                            # Resize if the image is large to save memory
                            if img.width > 1280 or img.height > 1280:
                                img.thumbnail((1280, 1280))
                                resized_content = BytesIO()
                                img.save(resized_content, format='JPEG')
                                resized_content.seek(0)
                                image_content = resized_content
                            else:
                                image_content.seek(0)
                            # --- End Resizing Logic ---

                            caption = text_caption if i == 0 else None
                            if caption and len(caption) > CAPTION_LIMIT:
                                caption = caption[:CAPTION_LIMIT - 3] + "..."
                            
                            media_group.append(InputMediaPhoto(media=image_content, caption=caption, parse_mode='HTML'))

                        except requests.exceptions.RequestException as e:
                            logger.warning(f"Failed to download image {image_url}: {e}")
                        except Exception as e:
                            logger.error(f"An unexpected error occurred while processing image {image_url}: {e}")

                    if media_group:
                        await update.message.reply_media_group(media=media_group)
                    else:
                        await update.message.reply_text(text=text_caption, parse_mode='HTML', disable_web_page_preview=True)
                else:
                    await update.message.reply_text(text=text_caption, parse_mode='HTML', disable_web_page_preview=True)
        else:
            await update.message.reply_text("Не удалось найти последние новости о телескопе Уэбба.")
    except Exception as e:
        logger.error(f"Ошибка при получении новостей: {e}", exc_info=True)
        await update.message.reply_text("Произошла внутренняя ошибка при получении новостей. Администратор уже уведомлен.")

async def get_position(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="TYPING")
    await update.message.reply_text("🛰️ Генерирую схему положения в космосе. Это может занять до одной минуты...")
    try:
        plot_path = await asyncio.to_thread(create_jwst_orbit_plot)
        
        if plot_path == "JPL_ERROR":
            await update.message.reply_text("Не удалось связаться с серверами NASA (JPL Horizons) для получения данных. Попробуйте позже.")
        elif plot_path and os.path.exists(plot_path):
            await update.message.reply_photo(
                photo=open(plot_path, 'rb'),
                caption="Схема орбит JWST и Луны относительно Земли."
            )
            os.remove(plot_path) # Удаляем файл после отправки
        else:
            await update.message.reply_text("Не удалось создать схему из-за внутренней ошибки. Попробуйте позже.")
    except Exception as e:
        logger.error(f"Ошибка при вызове команды /position: {e}", exc_info=True)
        await update.message.reply_text("Произошла внутренняя ошибка при создании схемы. Администратор уже уведомлен.")

JWST_FACTS = [
    "Главное зеркало телескопа «Джеймс Уэбб» состоит из 18 шестиугольных сегментов, покрытых тонким слоем золота для оптимального отражения инфракрасного света.",
    "Телескоп находится в точке Лагранжа L2 на расстоянии около 1,5 миллиона километров от Земли, что позволяет ему оставаться холодным и защищенным от солнечного света.",
]

async def get_fact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    fact = random.choice(JWST_FACTS)
    await update.message.reply_text(f"<b>💡 Интересный факт:</b>\n\n{fact}", parse_mode='HTML')

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log Errors caused by Updates."""
    logger.error("Exception while handling an update:", exc_info=context.error)


# ... (остальной код)

def main() -> None:
    """Start the bot."""
    config = load_config()
    token = config.get("telegram_token")

    if not token or token == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        logger.critical("Токен Telegram не найден в config.json. Пожалуйста, добавьте его.")
        return

    logger.info("Creating JobQueue...")
    job_queue = JobQueue()
    logger.info("Building Application...")
    application = (
        Application.builder()
        .token(token)
        .job_queue(job_queue)
        .post_init(post_init)
        .build()
    )
    logger.info("Application built successfully.")

    # on different commands - add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("latest_image", latest_image))
    application.add_handler(CommandHandler("news", get_news))
    application.add_handler(CommandHandler("position", get_position))
    application.add_handler(CommandHandler("fact", get_fact))

    # log all errors
    application.add_error_handler(error_handler)

    # Run the bot until the user presses Ctrl-C
    logger.info("Бот запускается...")
    application.run_polling()


if __name__ == '__main__':
    main()