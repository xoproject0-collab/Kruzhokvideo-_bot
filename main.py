import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# ▶️ /start
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    username = message.from_user.username

    if username:
        text = f"""👋 @{username} !

Отправь мне видео до 100МБ и я преобразую его в кружок (до 60 секунд, квадрат) с сохранением звука ! ⭕️

Если видео не квадратное — я обрежу его автоматически до квадратного формата."""
    else:
        text = """👋 !

Отправь мне видео до 100МБ и я преобразую его в кружок (до 60 секунд, квадрат) с сохранением звука ! ⭕️"""

    await message.answer(text)

# ▶️ обработка видео
@dp.message_handler(content_types=['video'])
async def handle_video(message: types.Message):
    file = await bot.get_file(message.video.file_id)
    file_path = file.file_path

    input_file = "input.mp4"
    output_file = "output.mp4"

    # скачать видео
    await bot.download_file(file_path, input_file)

    width = message.video.width
    height = message.video.height

    # если не квадрат
    if width != height:
        await message.answer("Видео не имеет квадратного формата, оно будет обрезано.")

    await message.answer("Видео в обработке, немного терпения ⏳")

    # размер квадрата
    size = min(width, height)

    # ffmpeg команда
    command = f"ffmpeg -i {input_file} -vf crop={size}:{size} -t 60 -c:a copy {output_file}"

    os.system(command)

    # отправка как кружок
    with open(output_file, "rb") as video:
        await bot.send_video_note(message.chat.id, video)

    # удаляем файлы
    os.remove(input_file)
    os.remove(output_file)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)