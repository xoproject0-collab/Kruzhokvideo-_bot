import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import exceptions
import subprocess

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    username = message.from_user.username
    if username:
        text = f"👋 Привет @{username}!\n\nОтправь видео, и я быстро сделаю его кружком!"
    else:
        text = "👋\n\nОтправь видео, и я быстро сделаю его кружком!"
    await message.answer(text)

@dp.message_handler(content_types=['video'])
async def handle_video(message: types.Message):
    file = await bot.get_file(message.video.file_id)
    input_file = f"{message.video.file_id}.mp4"
    output_file = f"{message.video.file_id}_circle.webm"

    await bot.download_file(file.file_path, input_file)

    width = message.video.width
    height = message.video.height
    size = min(width, height)

    if width != height:
        await message.answer("⚠️ Видео не квадратное, будет обрезано до квадрата.")

    msg = await message.answer("🎬 Создаём кружок из первого кадра...")

    try:
        cmd = [
            "ffmpeg",
            "-i", input_file,
            "-t", "1",
            "-vf",
            f"crop={size}:{size},format=yuva420p,"
            f"geq=r='if(gt(pow(X-{size}/2,2)+pow(Y-{size}/2,2),pow({size}/2,2)),0,255)':"
            f"g='if(gt(pow(X-{size}/2,2)+pow(Y-{size}/2,2),pow({size}/2,2)),0,255)':"
            f"b='if(gt(pow(X-{size}/2,2)+pow(Y-{size}/2,2),pow({size}/2,2)),0,255)':"
            f"a='if(gt(pow(X-{size}/2,2)+pow(Y-{size}/2,2),pow({size}/2,2)),0,255)'",
            "-c:v", "libvpx",
            "-c:a", "libvorbis",
            "-auto-alt-ref", "0",
            output_file
        ]
        subprocess.run(cmd, check=True)

        await msg.edit_text("✅ Кружок готов! Отправляю...")
        with open(output_file, "rb") as vid:
            try:
                await bot.send_video_note(message.chat.id, vid)
            except exceptions.TelegramAPIError:
                await message.answer("⚠️ Кружок слишком большой, отправляю как обычное видео.")
                await bot.send_video(message.chat.id, vid)

    except Exception as e:
        await msg.edit_text(f"❌ Произошла ошибка при обработке: {str(e)}")

    finally:
        if os.path.exists(input_file):
            os.remove(input_file)
        if os.path.exists(output_file):
            os.remove(output_file)

if __name__ == "__main__":
    asyncio.run(bot.start_polling())