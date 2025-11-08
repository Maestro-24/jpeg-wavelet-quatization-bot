import asyncio
import logging
from io import BytesIO

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup
from PIL import Image

from compression import (
    color_quantization_simple,
    jpeg_compression,
    wavelet_compression,
)
from config_reader import config

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.bot_token.get_secret_value())

dp = Dispatcher()

keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="JPEG сжатие"), KeyboardButton(text="Вейвлет сжатие")],
        [
            KeyboardButton(text="Квантовое сжатие"),
            KeyboardButton(text="Информация"),
        ],
    ],
    resize_keyboard=True,
)

user_states = {}


@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer(
        "👋 Добро пожаловать в бот для сжатия изображений!\n\n"
        "Выберите метод сжатия после чего просто отправьте изображение:\n"
        "• JPEG сжатие - классический метод\n"
        "• Вейвлет сжатие - современный метод\n"
        "• Квантовое сжатие - уменьшение количества различных цветов\n\n",
        reply_markup=keyboard,
    )


# Обработчик команды /help
@dp.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(
        "📖 Помощь по использованию бота:\n\n"
        "1. Отправьте изображение\n"
        "2. Выберите метод сжатия из меню\n"
        "3. Бот обработает изображение и вернет результат\n\n"
        "Доступные методы:\n"
        "• JPEG - быстрое сжатие с настраиваемым качеством\n"
        "• Вейвлет - лучше сохраняет детали\n"
        "• Квантование - повышение резкости границ",
        reply_markup=keyboard,
    )


# Обработчик изображений
@dp.message(lambda message: message.photo or message.document)
async def image_handler(message: Message):
    user_id = message.from_user.id

    # Отладочная информация
    logging.info(f"User {user_id} state: {user_states.get(user_id, 'NOT SET')}")

    if user_id not in user_states:
        await message.answer("❌ Пожалуйста, сначала выберите метод сжатия из меню!")
        return

    method = user_states[user_id]

    try:
        await message.answer("⏳ Обрабатываю изображение...")

        # Скачиваем изображение
        if message.photo:
            file_id = message.photo[-1].file_id
        else:
            file_id = message.document.file_id

        file = await bot.get_file(file_id)
        file_path = file.file_path

        # Скачиваем файл
        downloaded_file = await bot.download_file(file_path)
        file_data = downloaded_file.read()
        original_size = len(file_data)

        # Открываем изображение из данных
        original_image = Image.open(BytesIO(file_data))

        # Получаем информацию об исходном изображении
        original_format = original_image.format

        # Применяем выбранный метод сжатия
        if method == "jpeg":
            compressed_image = jpeg_compression(original_image, quality=50)
            method_name = "JPEG"

        elif method == "wavelet":
            compressed_image = wavelet_compression(
                original_image, compression_ratio=0.2
            )
            method_name = "Вейвлет"

        elif method == "quantization":
            compressed_image = color_quantization_simple(original_image, n_colors=32)
            method_name = "Квантование"

        else:
            await message.answer("❌ Неизвестный метод сжатия!")
            return

        # Сохраняем сжатое изображение в буфер
        compressed_buffer = BytesIO()
        compressed_image.save(compressed_buffer, format="JPEG", quality=85)
        compressed_buffer.seek(0)
        compressed_size = len(compressed_buffer.getvalue())

        # Вычисляем степень сжатия
        compression_ratio = (1 - compressed_size / original_size) * 100

        # Отправляем результат
        await message.answer_photo(
            types.BufferedInputFile(
                compressed_buffer.getvalue(), filename=f"compressed_{method_name}.jpg"
            ),
            caption=(
                f"✅ Сжатие завершено!\n"
                f"📊 Метод: {method_name}\n"
                f"📁 Исходный размер: {original_size // 1024} КБ\n"
                f"📁 Сжатый размер: {compressed_size // 1024} КБ\n"
                f"📈 Степень сжатия: {compression_ratio:.1f}%\n\n"
                f"Выберите следующий метод сжатия:"
            ),
            reply_markup=keyboard,
        )

        # del user_states[user_id]

    except Exception as e:
        logging.error(f"Error processing image: {str(e)}")
        await message.answer(f"❌ Произошла ошибка при обработке: {str(e)}")


@dp.message()
async def text_handler(message: Message):
    user_id = message.from_user.id
    text = message.text

    if text == "JPEG сжатие":
        user_states[user_id] = "jpeg"
        await message.answer(
            "✅ Выбран метод JPEG сжатия. Теперь отправьте изображение!"
        )

    elif text == "Вейвлет сжатие":
        user_states[user_id] = "wavelet"
        await message.answer(
            "🌀 Выбран метод вейвлет сжатия. Теперь отправьте изображение!"
        )

    elif text == "Квантовое сжатие":
        user_states[user_id] = "quantization"
        await message.answer(
            "🔷 Выбран метод квантования. Теперь отправьте изображение!"
        )

    elif text == "Информация":
        await message.answer(
            "📊 Информация о методах сжатия:\n\n"
            "🔸 JPEG:\n"
            "• Быстрое сжатие\n"
            "• Хорошее качество при средних настройках\n"
            "• Подходит для фотографий\n\n"
            "🔸 Вейвлет:\n"
            "• Современный метод\n"
            "• Лучше сохраняет детали\n"
            "• Меньше артефактов\n\n"
            "🔸 Квантование цветов:\n"
            "• Уменьшает количество цветов в изображении\n"
            "• Эффективно для графики и логотипов\n"
            "• Может создавать стилизованный вид\n"
            "• Подходит для изображений с ограниченной палитрой",
            reply_markup=keyboard,
        )

    else:
        # Проверяем, есть ли состояние у пользователя
        if user_id in user_states:
            await message.answer(
                "Пожалуйста, отправьте изображение для сжатия или выберите другой метод из меню."
            )
        else:
            await message.answer(
                "Пожалуйста, используйте кнопки меню для выбора метода сжатия."
            )


# Запуск процесса поллинга новых апдейтов
async def main():
    logging.info("Start")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
