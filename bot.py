import logging
import feedparser
from deep_translator import GoogleTranslator
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import numpy as np
from astropy.coordinates import get_body_barycentric_posvel, solar_system_ephemeris
from astropy.time import Time
import matplotlib.pyplot as plt
from astroquery.jplhorizons import Horizons
import astropy.units as u
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import init_db, subscribe_user, unsubscribe_user, get_subscribed_users

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO,
    filename='bot.log', filemode='a'
)
logger = logging.getLogger(__name__)

# Replace with your bot token
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}! Welcome to the JWST Bot. I can provide you with the latest news, images, and telemetry from the James Webb Space Telescope.",
    )

async def fetch_nasa_news(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetches and displays the latest NASA news."""
    await update.message.reply_text("Fetching NASA news...")
    try:
        feed = feedparser.parse("https://www.nasa.gov/feed/")
        news_items = []
        for entry in feed.entries[:5]:  # Get top 5 news items
            title = GoogleTranslator(source='auto', target='ru').translate(entry.title)
            summary = GoogleTranslator(source='auto', target='ru').translate(entry.summary)
            news_items.append(f"<b>{title}</b>\n{summary}\n")
        
        if news_items:
            await update.message.reply_html("\n".join(news_items))
        else:
            await update.message.reply_text("Could not fetch NASA news at this time.")
    except Exception as e:
        logger.error(f"Error fetching NASA news: {e}")
        await update.message.reply_text("An error occurred while fetching NASA news.")

async def fetch_nasa_iotd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetches and displays the NASA Image of the Day."""
    await update.message.reply_text("Fetching NASA Image of the Day...")
    try:
        feed = feedparser.parse("https://www.nasa.gov/feeds/iotd-feed/")
        if feed.entries:
            entry = feed.entries[0]  # Get the latest image
            title = GoogleTranslator(source='auto', target='ru').translate(entry.title)
            
            # Extract image URL from media_content or summary
            image_url = None
            if 'media_content' in entry and entry.media_content:
                for media in entry.media_content:
                    if media.get('type', '').startswith('image'):
                        image_url = media.get('url')
                        break
            
            if not image_url and 'summary' in entry:
                # Try to extract image from summary HTML
                import re
                match = re.search(r'<img src="(.*?)"', entry.summary)
                if match:
                    image_url = match.group(1)

            description = entry.summary
            # Extract first two sentences for description
            sentences = re.split(r'(?<=[.!?])\s+', description)
            short_description = " ".join(sentences[:2])
            translated_description = GoogleTranslator(source='auto', target='ru').translate(short_description)

            message = f"<b>{title}</b>\n\n{translated_description}"
            if image_url:
                await update.message.reply_photo(photo=image_url, caption=message, parse_mode='HTML')
            else:
                await update.message.reply_html(message)
        else:
            await update.message.reply_text("Could not fetch NASA Image of the Day at this time.")
    except Exception as e:
        logger.error(f"Error fetching NASA Image of the Day: {e}")
        await update.message.reply_text("An error occurred while fetching NASA Image of the Day.")

async def jwst_orbit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetches and displays the JWST orbit relative to Earth and Moon."""
    await update.message.reply_text("Fetching JWST orbital data and generating plot. This may take a moment...")
    try:
        # Define time range (e.g., 30 days around current date)
        t_now = Time.now()
        t_start = t_now - 15 * u.day
        t_end = t_now + 15 * u.day
        times = Time(np.linspace(t_start.jd, t_end.jd, 100), format='jd')

        # Query JPL Horizons for Earth, Moon, and JWST
        # Earth (body ID 399)
        earth = Horizons(id='399', location='@ssb', epochs=times.jd).vectors()
        earth_pos = earth['x', 'y', 'z'].quantity

        # Moon (body ID 301)
        moon = Horizons(id='301', location='@ssb', epochs=times.jd).vectors()
        moon_pos = moon['x', 'y', 'z'].quantity

        # JWST (body ID -170)
        jwst = Horizons(id='-170', location='@ssb', epochs=times.jd).vectors()
        jwst_pos = jwst['x', 'y', 'z'].quantity

        # Convert to Earth-centered coordinates
        jwst_rel_earth = jwst_pos - earth_pos
        moon_rel_earth = moon_pos - earth_pos

        # Plotting
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.set_aspect('equal')

        # Plot Earth (at origin)
        ax.plot(0, 0, 'o', color='blue', markersize=10, label='Earth')

        # Plot Moon orbit
        ax.plot(moon_rel_earth.x.to(u.km).value, moon_rel_earth.y.to(u.km).value, '--', color='gray', label='Moon Orbit')
        ax.plot(moon_rel_earth.x[-1].to(u.km).value, moon_rel_earth.y[-1].to(u.km).value, 'o', color='lightgray', markersize=5, label='Moon')

        # Plot JWST orbit
        ax.plot(jwst_rel_earth.x.to(u.km).value, jwst_rel_earth.y.to(u.km).value, '-', color='red', label='JWST Orbit')
        ax.plot(jwst_rel_earth.x[-1].to(u.km).value, jwst_rel_earth.y[-1].to(u.km).value, 'x', color='orange', markersize=8, label='JWST')

        # Set limits and labels
        max_range = max(np.max(np.abs(jwst_rel_earth.x.to(u.km).value)), np.max(np.abs(jwst_rel_earth.y.to(u.km).value)))
        max_range = max(max_range, np.max(np.abs(moon_rel_earth.x.to(u.km).value)), np.max(np.abs(moon_rel_earth.y.to(u.km).value)))
        
        # Add some padding
        padding = max_range * 0.1
        ax.set_xlim(-max_range - padding, max_range + padding)
        ax.set_ylim(-max_range - padding, max_range + padding)

        ax.set_xlabel('X (km)')
        ax.set_ylabel('Y (km)')
        ax.set_title('JWST and Moon Orbit Relative to Earth')
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.6)

        # Add grid in thousands of km
        # Calculate appropriate tick interval based on max_range
        tick_interval = 10**(np.floor(np.log10(max_range / 5)) + 3) # Roughly 5 ticks
        if tick_interval < 1000: # Ensure at least 1000 km interval
            tick_interval = 1000

        x_ticks = np.arange(ax.get_xlim()[0], ax.get_xlim()[1], tick_interval)
        y_ticks = np.arange(ax.get_ylim()[0], ax.get_ylim()[1], tick_interval)
        ax.set_xticks(x_ticks)
        ax.set_yticks(y_ticks)
        ax.ticklabel_format(style='plain', axis='both', useOffset=False)

        # Save plot to a temporary file
        plot_path = "jwst_orbit.png"
        plt.savefig(plot_path)
        plt.close(fig)

        # Send the plot to the user
        await update.message.reply_photo(photo=open(plot_path, 'rb'))

    except Exception as e:
        logger.error(f"Error generating JWST orbit plot: {e}")
        await update.message.reply_text("An error occurred while generating the JWST orbit plot. This feature requires `astropy` and `astroquery` to be correctly installed and configured, and may also be affected by network issues when querying JPL Horizons.")

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    subscribe_user(user_id)
    await update.message.reply_text("You have been subscribed to daily updates!")

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    unsubscribe_user(user_id)
    await update.message.reply_text("You have been unsubscribed from updates.")

async def set_frequency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    args = context.args
    if not args or len(args) != 1:
        await update.message.reply_text("Usage: /set_frequency <daily|weekly>")
        return
    
    frequency = args[0].lower()
    if frequency not in ['daily', 'weekly']:
        await update.message.reply_text("Invalid frequency. Please choose 'daily' or 'weekly'.")
        return
    
    subscribe_user(user_id, frequency) # Update frequency for existing subscription or create new one
    await update.message.reply_text(f"Your update frequency has been set to {frequency}.")

async def send_daily_update(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a daily update to all subscribed users."""
    users = get_subscribed_users()
    for user_id, frequency in users:
        if frequency == 'daily':
            try:
                # For now, just send a placeholder message. Later, integrate news/iotd/telemetry.
                await context.bot.send_message(chat_id=user_id, text="Daily update: More exciting JWST content coming soon!")
            except Exception as e:
                logger.error(f"Could not send daily update to user {user_id}: {e}")

def main() -> None:
    """Start the bot."""
    init_db()
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(BOT_TOKEN).build()

    # Initialize scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_daily_update, 'cron', hour=10, minute=0, args=[application.bot]) # Run daily at 10:00 AM UTC
    scheduler.start()

    # on different commands - add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("news", fetch_nasa_news))
    application.add_handler(CommandHandler("iotd", fetch_nasa_iotd))
    application.add_handler(CommandHandler("jwst_orbit", jwst_orbit))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))
    application.add_handler(CommandHandler("set_frequency", set_frequency))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
