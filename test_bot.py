import pytest
from unittest.mock import AsyncMock, MagicMock
from bot import start, fetch_nasa_news, fetch_nasa_iotd

# Mock the GoogleTranslator to avoid actual API calls during testing
class MockGoogleTranslator:
    def __init__(self, source, target):
        pass

    def translate(self, text):
        return f"Translated_{text}"

# Replace the actual GoogleTranslator with the mock one for testing
# This needs to be done carefully, usually by patching the module where it's imported
# For simplicity in this example, we'll assume a direct replacement for demonstration
# In a real scenario, consider pytest-mock or unittest.mock.patch

# Mock feedparser to avoid actual network requests
class MockFeedParser:
    def __init__(self, entries):
        self.entries = entries

    def parse(self, url):
        mock_feed = MagicMock()
        mock_feed.entries = self.entries
        return mock_feed

@pytest.mark.asyncio
async def test_start_command():
    update = AsyncMock()
    context = AsyncMock()
    await start(update, context)
    update.message.reply_html.assert_called_once_with(
        f"Hi {update.effective_user.mention_html()}! Welcome to the JWST Bot. I can provide you with the latest news, images, and telemetry from the James Webb Space Telescope.",
    )

# You would add more tests here for fetch_nasa_news, fetch_nasa_iotd, etc.
# For example, to test fetch_nasa_news, you would need to mock feedparser.parse
# and GoogleTranslator.translate to control their return values.

# Example of how you might structure a test for fetch_nasa_news (conceptual)
# This would require more sophisticated mocking than shown above for simplicity
@pytest.mark.asyncio
async def test_fetch_nasa_news_success():
    update = AsyncMock()
    context = AsyncMock()

    # Mock feedparser.parse to return a controlled feed
    mock_entry = MagicMock()
    mock_entry.title = "Original Title"
    mock_entry.summary = "Original Summary"
    mock_feed = MagicMock()
    mock_feed.entries = [mock_entry]

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("feedparser.parse", lambda url: mock_feed)
        mp.setattr("bot.GoogleTranslator", MockGoogleTranslator) # Patch the imported GoogleTranslator

        await fetch_nasa_news(update, context)
        update.message.reply_text.assert_called_with("Fetching NASA news...")
        update.message.reply_html.assert_called_once_with(
            "<b>Translated_Original Title</b>\nTranslated_Original Summary\n"
        )

@pytest.mark.asyncio
async def test_fetch_nasa_iotd_success():
    update = AsyncMock()
    context = AsyncMock()

    mock_entry = MagicMock()
    mock_entry.title = "IOTD Title"
    mock_entry.summary = "First sentence. Second sentence. Third sentence."
    mock_entry.media_content = [{'url': 'http://example.com/image.jpg', 'type': 'image/jpeg'}]
    mock_feed = MagicMock()
    mock_feed.entries = [mock_entry]

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("feedparser.parse", lambda url: mock_feed)
        mp.setattr("bot.GoogleTranslator", MockGoogleTranslator)

        await fetch_nasa_iotd(update, context)
        update.message.reply_text.assert_called_with("Fetching NASA Image of the Day...")
        update.message.reply_photo.assert_called_once_with(
            photo='http://example.com/image.jpg',
            caption='<b>Translated_IOTD Title</b>\n\nTranslated_First sentence. Translated_Second sentence.',
            parse_mode='HTML'
        )
