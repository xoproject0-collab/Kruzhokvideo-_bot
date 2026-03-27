import os
import asyncio
from io import BytesIO
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
        text = f"👋 Привет @{username}!\n\nОтправь видео до 100МБ, и я сделаю его кружком (до 60 секунд, квадрат) с сохранением звука! ⭕️"
    else:
        text = "👋\n\nОтправь видео до 100МБ, и я сделаю его кружком (до 60 секунд, квадрат) с сохранением звука! ⭕️"
    await message.answer(text)

# ▶️ асинхронная обработка видео
@dp.message_handler(content_types=['video'])
async def handle_video(message: types.Message):
    file = await bot.get_file(message.video.file_id)
    file_bytes = BytesIO()
    await bot.download_file(file.file_path, file_bytes)
    file_bytes.seek(0)

    await message.answer("Видео обрабатывается, немного терпения ⏳")

    width = message.video.width
    height = message.video.height
    size = min(width, height)

    if width != height:
        await message.answer("Видео не квадратное, оно будет обрезано.")

    ffmpeg_cmd = [
        "ffmpeg",
        "-i", "pipe:0",
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
        "-f", "webm",
        "pipe:1"
    ]

    # асинхронное выполнение ffmpeg через asyncio
    process = await asyncio.create_subprocess_exec(
        *ffmpeg_cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    output_bytes, err = await process.communicate(input=file_bytes.read())

    output_video = BytesIO(output_bytes)
    output_video.seek(0)

    await bot.send_video_note(message.chat.id, output_video)