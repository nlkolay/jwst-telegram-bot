import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# Поскольку bot.py и position.py находятся в корне, добавляем корень в путь
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Теперь можно импортировать модули
import bot
import position

@pytest.fixture
def update_mock():
    """Фикстура для создания мока объекта Update."""
    update = AsyncMock()
    update.effective_user = MagicMock()
    update.effective_user.mention_html.return_value = "testuser"
    update.message = AsyncMock()
    update.effective_chat = MagicMock()
    update.effective_chat.id = 12345
    return update

@pytest.fixture
def context_mock():
    """Фикстура для создания мока объекта Context."""
    context = AsyncMock()
    context.bot = AsyncMock()
    # Мокируем get_my_commands, чтобы он возвращал список тестовых команд
    context.bot.get_my_commands.return_value = [
        MagicMock(command="start", description="Запуск"),
        MagicMock(command="help", description="Помощь"),
    ]
    return context

@pytest.mark.asyncio
async def test_start_command(update_mock, context_mock):
    """Тестирует команду /start."""
    await bot.start(update_mock, context_mock)
    update_mock.message.reply_html.assert_called_once()
    call_args = update_mock.message.reply_html.call_args[0][0]
    assert "Привет, testuser" in call_args
    assert "Я бот, который расскажет всё о космическом телескопе «Джеймс Уэбб»" in call_args

@pytest.mark.asyncio
async def test_help_command(update_mock, context_mock):
    """Тестирует команду /help."""
    await bot.help_command(update_mock, context_mock)
    update_mock.message.reply_html.assert_called_once()
    call_args = update_mock.message.reply_html.call_args[0][0]
    assert "<b>Доступные команды:</b>" in call_args
    assert "/start - Запуск" in call_args
    assert "/help - Помощь" in call_args

@pytest.mark.asyncio
async def test_get_fact_command(update_mock, context_mock):
    """Тестирует команду /fact."""
    with patch('random.choice', return_value="Тестовый факт") as mock_choice:
        await bot.get_fact(update_mock, context_mock)
        mock_choice.assert_called_once_with(bot.JWST_FACTS)
        update_mock.message.reply_text.assert_called_once_with(
            "<b>💡 Интересный факт:</b>\n\nТестовый факт",
            parse_mode='HTML'
        )

@pytest.mark.asyncio
@patch('asyncio.to_thread', new_callable=AsyncMock)
@patch('os.path.exists')
@patch('os.remove')
@patch('builtins.open')
async def test_get_position_success(mock_open, mock_remove, mock_exists, mock_to_thread, update_mock, context_mock):
    """Тестирует успешное выполнение команды /position."""
    mock_plot_path = "test_orbit.png"
    mock_to_thread.return_value = mock_plot_path
    mock_exists.return_value = True

    await bot.get_position(update_mock, context_mock)

    # 1. Проверяем, что пользователю отправили сообщение о начале генерации
    context_mock.bot.send_chat_action.assert_called_once_with(chat_id=12345, action="TYPING")
    
    # Проверяем вызов reply_text более гибко, чтобы избежать проблем с кодировкой
    update_mock.message.reply_text.assert_called_once()
    call_text = update_mock.message.reply_text.call_args[0][0]
    assert "Генерирую схему положения" in call_text

    # 2. Проверяем, что была вызвана функция генерации графика в отдельном потоке
    mock_to_thread.assert_called_once()

    # 3. Проверяем, что бот попытался отправить фото
    update_mock.message.reply_photo.assert_called_once()
    call_args = update_mock.message.reply_photo.call_args
    assert call_args.kwargs['caption'] == "Схема орбит JWST и Луны относительно Земли."
    
    # 4. Проверяем, что файл был удален после отправки
    mock_remove.assert_called_once_with(mock_plot_path)

@pytest.mark.asyncio
@patch('asyncio.to_thread', new_callable=AsyncMock)
async def test_get_position_failure(mock_to_thread, update_mock, context_mock):
    """Тестирует команду /position в случае ошибки генерации."""
    mock_to_thread.side_effect = Exception("Test error")

    await bot.get_position(update_mock, context_mock)

    # Проверяем, что пользователю отправили сообщение об ошибке
    update_mock.message.reply_text.assert_called_with("Произошла внутренняя ошибка при создании схемы. Администратор уже уведомлен.")

# ... (предыдущие тесты)

@pytest.mark.asyncio
@patch('bot.news.get_latest_image', new_callable=AsyncMock, return_value=None)
async def test_latest_image_failure(mock_get_image, update_mock, context_mock):
    """Тестирует команду /latest_image в случае ошибки получения данных."""
    await bot.latest_image(update_mock, context_mock)
    update_mock.message.reply_text.assert_called_with("Не удалось получить последнее изображение. Попробуйте позже.")

@pytest.mark.asyncio
@patch('bot.news.get_latest_news', new_callable=AsyncMock, return_value=None)
async def test_get_news_failure(mock_get_news, update_mock, context_mock):
    """Тестирует команду /news в случае ошибки получения данных."""
    await bot.get_news(update_mock, context_mock)
    update_mock.message.reply_text.assert_called_with("Не удалось найти последние новости о телескопе Уэбба.")

import numpy as np
from astropy import units as u

# ... (остальные импорты)

# ... (код)

@patch('bot.Application.builder')
@patch('bot.load_config', return_value={"telegram_token": None}) # Симулируем отсутствие токена
@patch('bot.logger.critical') # Мокаем логгер
def test_main_no_token(mock_logger, mock_load_config, mock_app_builder):
    """Тестирует запуск main без токена."""
    bot.main()
    # Проверяем, что было вызвано логирование критической ошибки
    mock_logger.assert_called_with("Токен Telegram не найден в config.json. Пожалуйста, добавьте его.")
    # Проверяем, что приложение не создавалось
    mock_app_builder.return_value.build.assert_not_called()

@patch('bot.Application')
@patch('bot.load_config', return_value={"telegram_token": "fake_token"})
def test_main_with_token(mock_load_config, mock_application):
    """Тестирует успешный запуск main с токеном."""
    # Мокаем всю цепочку Application.builder()...
    mock_builder = MagicMock()
    mock_app = AsyncMock()
    
    mock_application.builder.return_value = mock_builder
    mock_builder.token.return_value = mock_builder
    mock_builder.job_queue.return_value = mock_builder
    mock_builder.post_init.return_value = mock_builder
    mock_builder.build.return_value = mock_app

    bot.main()

    # Проверяем, что builder был вызван
    mock_application.builder.assert_called_once()
    # Проверяем, что build был вызван
    mock_builder.build.assert_called_once()
    # Проверяем, что бот был запущен
    mock_app.run_polling.assert_called_once()
    # Проверяем, что были добавлены обработчики
    assert mock_app.add_handler.call_count > 0


@pytest.mark.asyncio
async def test_post_init(context_mock):
    """Тестирует функцию post_init."""
    application = MagicMock()
    application.bot = context_mock.bot
    await bot.post_init(application)
    context_mock.bot.set_my_commands.assert_called_once()

# ... (остальные тесты)


@patch('position.Horizons')
@patch('position.plt')
def test_create_jwst_orbit_plot_success(mock_plt, mock_horizons):
    """Тестирует успешное создание графика."""
    mock_fig = MagicMock()
    mock_ax = MagicMock()
    mock_plt.subplots.return_value = (mock_fig, mock_ax)

    # Финальная, упрощенная версия мока
    def get_mock_vectors(*args, **kwargs):
        mock_instance = MagicMock()
        
        # .vectors() возвращает объект, который ведет себя как astropy.table.Table
        # и у которого можно получать колонки по ключу
        vectors_result = MagicMock()
        
        # Каждая колонка - это Quantity, у которого есть .value
        # Возвращаем массив с одним элементом, как это делает astroquery
        fake_quantity_x = MagicMock()
        fake_quantity_x.value = np.array([1.0])
        fake_quantity_y = MagicMock()
        fake_quantity_y.value = np.array([2.0])
        
        def getitem(key):
            if key == 'x':
                return fake_quantity_x
            elif key == 'y':
                return fake_quantity_y
            return MagicMock()

        vectors_result.__getitem__.side_effect = getitem
        mock_instance.vectors.return_value = vectors_result
        return mock_instance

    mock_horizons.side_effect = get_mock_vectors

    plot_path = position.create_jwst_orbit_plot()

    assert plot_path is not None
    assert plot_path.endswith('.png')
    mock_plt.savefig.assert_called_once()
    assert plot_path.endswith('.png')
    mock_plt.savefig.assert_called_once()
    assert plot_path.endswith('.png')
    mock_plt.savefig.assert_called_once()

@patch('position.Horizons', side_effect=Exception("JPL Error"))
def test_create_jwst_orbit_plot_failure(mock_horizons):
    """Тестирует ошибку при создании графика."""
    plot_path = position.create_jwst_orbit_plot()
    assert plot_path is None