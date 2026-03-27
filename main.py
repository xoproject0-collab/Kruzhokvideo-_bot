import os
import subprocess
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    username = message.from_user.username

    if username:
        text = f"""👋 Привет @{username} !

Отправь мне видео и я преобразую его в кружок (до 60 секунд, квадрат) с сохранением звука ⭕️

Если видео не квадратное — я обрежу его автоматически."""
    else:
        text = """👋 !

Отправь мне видео и я преобразую его в кружок (до 60 секунд, квадрат) с сохранением звука ⭕️"""

    await message.answer(text)

@dp.message_handler(content_types=['video'])
async def handle_video(message: types.Message):

    await message.answer("📥 Видео получено.")

    file = await bot.get_file(message.video.file_id)

    input_file = "input.mp4"
    output_file = "output.mp4"

    await bot.download_file(file.file_path, input_file)

    width = message.video.width
    height = message.video.height
    size = min(width, height)

    if width != height:
        await message.answer("⚠️ Видео не квадратное, оно будет обрезано.")

    process_msg = await message.answer("🎬 Видео обрабатывается, немного терпения ⏳")

    try:

        command = f"ffmpeg -y -i {input_file} -t 60 -vf crop={size}:{size} -c:a copy {output_file}"
        subprocess.run(command, shell=True)

        await process_msg.edit_text("✅ Видео готово! Отправляю кружок...")

        with open(output_file, "rb") as video:
            await bot.send_video_note(message.chat.id, video)

    except Exception:
        await process_msg.edit_text("❌ Произошла ошибка при обработке видео.")

    finally:

        if os.path.exists(input_file):
            os.remove(input_file)

        if os.path.exists(output_file):
            os.remove(output_file)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)