import os
import asyncio
import logging
import re
import yt_dlp
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.account import UpdateProfileRequest, UpdateStatusRequest
from telethon.tl.functions.messages import SetTypingRequest
from telethon.tl.types import SendMessageTypingAction
from telethon.errors import FloodWaitError

# ══════════════════════════════════════════════════════════════════════════════
# ۱. تنظیمات لاگ
# ══════════════════════════════════════════════════════════════════════════════
logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("SuperUserBot")

# ══════════════════════════════════════════════════════════════════════════════
# ۲. خواندن اطلاعات امن
# ══════════════════════════════════════════════════════════════════════════════
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION_STRING = os.getenv("SESSION_STRING", "")
BASE_NAME = os.getenv("BASE_NAME", "My Name")

if not API_ID or not API_HASH or not SESSION_STRING:
    logger.error("❌ متغیرهای محیطی یافت نشدند.")
    exit(1)

KABUL_TZ = ZoneInfo("Asia/Kabul")
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# ══════════════════════════════════════════════════════════════════════════════
# ۳. قابلیت دانلود خودکار رسانه
# ══════════════════════════════════════════════════════════════════════════════
URL_REGEX = re.compile(r'(https?://[^\s]+)')

YDL_OPTS = {
    'outtmpl': 'downloads/%(id)s.%(ext)s',
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    'quiet': True,
    'no_warnings': True,
    'noplaylist': True,
    'max_filesize': 50000000,
}

@client.on(events.NewMessage(outgoing=True, pattern=URL_REGEX))
async def auto_download_handler(event):
    logger.info("🔔 سیگنال پیام دریافتی...")
    
    me = await client.get_me()
    if event.chat_id != me.id:
        logger.info(f"⏭️ پیام در Saved Messages نیست (Chat ID: {event.chat_id}). نادیده گرفته شد.")
        return

    url = event.raw_text.strip()
    logger.info(f"🔗 لینک در Saved Messages: {url}")
    
    status_msg = await event.reply("⏳ **در حال پردازش لینک...** لطفاً صبر کنید.")
    
    try:
        os.makedirs('downloads', exist_ok=True)
        loop = asyncio.get_event_loop()
        
        def download_media():
            logger.info("📥 شروع دانلود با yt-dlp...")
            with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                if not os.path.exists(filename):
                    base = os.path.splitext(filename)[0]
                    for ext in ['.mp4', '.mkv', '.webm', '.mp3']:
                        if os.path.exists(base + ext):
                            filename = base + ext
                            break
                return filename, info
        
        filename, info = await loop.run_in_executor(None, download_media)
        logger.info(f"✅ دانلود کامل شد: {filename}")
        
        await status_msg.edit("📤 **در حال آپلود به تلگرام...**")
        
        caption = f"✅ **دانلود شد:**\n{info.get('title', 'بدون عنوان')}"
        await client.send_file(
            me.id,
            filename,
            caption=caption,
            reply_to=event.message.id
        )
        logger.info("✅ فایل با موفقیت به تلگرام ارسال شد.")
        
        if os.path.exists(filename):
            os.remove(filename)
            logger.info("🗑 فایل موقت پاک شد.")
            
        await status_msg.delete()
        
    except Exception as e:
        logger.error(f"❌ خطا در دانلود: {e}")
        await status_msg.edit(f"❌ **خطا در دانلود:**\n`{str(e)[:200]}`")

# ══════════════════════════════════════════════════════════════════════════════
# ۴. حلقه آپدیت پروفایل (ساعت، آنلاین، تایپ)
# ══════════════════════════════════════════════════════════════════════════════
async def update_profile_loop():
    while True:
        try:
            now = datetime.now(KABUL_TZ)
            time_str = now.strftime("%H:%M")
            new_name = f"🕒 {time_str} | {BASE_NAME}"
            
            await client(UpdateProfileRequest(first_name=new_name[:64]))
            await client(UpdateStatusRequest(offline=False))
            
            try:
                dialogs = await client.get_dialogs(limit=1)
                if dialogs:
                    await client(SetTypingRequest(peer=dialogs[0].entity, action=SendMessageTypingAction()))
            except: 
                pass
            
            logger.info(f"✅ پروفایل: '{new_name}' | آنلاین 🟢 | تایپ ⌨️")
            
        except FloodWaitError as e:
            logger.warning(f"⚠️ محدودیت: {e.seconds} ثانیه")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            logger.error(f"❌ خطا در آپدیت: {e}")
            
        await asyncio.sleep(60)

# ══════════════════════════════════════════════════════════════════════════════
# ۵. نقطه ورود (Main)
# ══════════════════════════════════════════════════════════════════════════════
async def main():
    logger.info("🚀 اتصال به تلگرام...")
    await client.connect()
    
    if not await client.is_user_authorized():
        logger.error("❌ سشن منقضی شده.")
        return

    me = await client.get_me()
    logger.info(f"✅ متصل شد به: {me.first_name} (ID: {me.id})")
    logger.info("💡 دانلودر فعال است. لینک را به Saved Messages بفرستید.")
    
    asyncio.create_task(update_profile_loop())
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        client.loop.run_until_complete(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("👋 خاموش شد.")
