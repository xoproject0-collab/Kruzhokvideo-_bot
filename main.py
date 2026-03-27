import os
import asyncio
from io import BytesIO
from aiogram import Bot, Dispatcher, types

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    username = message.from_user.username
    if username:
        text = f"👋 Привет @{username}!\n\nОтправь видео, и я сделаю его кружком (до 60 секунд, квадрат) с сохранением звука! ⭕️"
    else:
        text = "👋\n\nОтправь видео, и я сделаю его кружком (до 60 секунд, квадрат) с сохранением звука! ⭕️"
    await message.answer(text)

@dp.message_handler(content_types=['video'])
async def handle_video(message: types.Message):
    file_msg = await message.answer("📥 Видео получено, начинаем обработку...")

    file = await bot.get_file(message.video.file_id)
    input_file = f"{message.video.file_id}.mp4"
    output_file = f"{message.video.file_id}_circle.webm"

    await bot.download_file(file.file_path, input_file)

    width = message.video.width
    height = message.video.height
    size = min(width, height)

    if width != height:
        await message.answer("⚠️ Видео не квадратное, оно будет обрезано.")

    processing_msg = await message.answer("🎬 Видео обрабатывается, немного терпения ⏳")

    ffmpeg_cmd = [
        "ffmpeg",
        "-i", input_file,
        "-t", "60",
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

    try:
        process = await asyncio.create_subprocess_exec(
            *ffmpeg_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _, err = await process.communicate()

        if process.returncode != 0:
            await processing_msg.edit_text("❌ Произошла ошибка при обработке видео. Попробуйте другое видео.")
            return

        await processing_msg.edit_text("✅ Видео успешно обработано! Отправляю кружок...")
        with open(output_file, "rb") as video:
            await bot.send_video_note(message.chat.id, video)

    except Exception as e:
        await processing_msg.edit_text(f"❌ Произошла ошибка: {str(e)}")

    finally:
        if os.path.exists(input_file):
            os.remove(input_file)
        if os.path.exists(output_file):
            os.remove(output_file)

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))