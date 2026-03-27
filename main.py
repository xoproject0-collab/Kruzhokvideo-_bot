import os
import asyncio
import subprocess
from aiogram import Bot, Dispatcher, types
from aiogram.exceptions import TelegramAPIError

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(commands=["start"])
async def start(message: types.Message):
    username = message.from_user.username

    if username:
        text = f"👋 Привет @{username}!\n\nОтправь видео и я превращу его в кружок ⭕️"
    else:
        text = "👋 Привет!\n\nОтправь видео и я превращу его в кружок ⭕️"

    await message.answer(text)

@dp.message(lambda message: message.video)
async def handle_video(message: types.Message):

    file = await bot.get_file(message.video.file_id)

    input_file = "input.mp4"
    output_file = "circle.webm"

    await bot.download_file(file.file_path, input_file)

    width = message.video.width
    height = message.video.height
    size = min(width, height)

    if width != height:
        await message.answer("⚠️ Видео не квадратное, будет автоматически обрезано.")

    msg = await message.answer("🎬 Создаю кружок...")

    try:

        cmd = [
            "ffmpeg",
            "-y",
            "-i", input_file,
            "-t", "1",
            "-vf",
            f"crop={size}:{size}",
            "-c:v", "libvpx",
            "-c:a", "libvorbis",
            output_file
        ]

        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        await msg.edit_text("✅ Кружок готов!")

        with open(output_file, "rb") as video:

            try:
                await bot.send_video_note(message.chat.id, video)

            except TelegramAPIError:
                await message.answer("⚠️ Не удалось отправить как кружок, отправляю видео.")
                await bot.send_video(message.chat.id, video)

    except Exception:
        await msg.edit_text("❌ Ошибка обработки видео.")

    finally:

        if os.path.exists(input_file):
            os.remove(input_file)

        if os.path.exists(output_file):
            os.remove(output_file)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())