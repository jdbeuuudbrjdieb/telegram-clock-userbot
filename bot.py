import os
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from telethon import TelegramClient
from telethon.sessions import StringSession
# اضافه شدن UpdateStatusRequest برای قابلیت آنلاین ماندن
from telethon.tl.functions.account import UpdateProfileRequest, UpdateStatusRequest
from telethon.errors import FloodWaitError

# ══════════════════════════════════════════════════════════════════════════════
# ۱. تنظیمات لاگ
# ══════════════════════════════════════════════════════════════════════════════
logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("UserBotClock")

# ══════════════════════════════════════════════════════════════════════════════
# ۲. خواندن اطلاعات امن از Secrets (بدون تغییر)
# ══════════════════════════════════════════════════════════════════════════════
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION_STRING = os.getenv("SESSION_STRING", "")
BASE_NAME = os.getenv("BASE_NAME", "My Name")

if not API_ID or not API_HASH or not SESSION_STRING:
    logger.error("❌ متغیرهای محیطی (API_ID, API_HASH, SESSION_STRING) یافت نشدند.")
    exit(1)

# ساعت افغانستان (UTC + 4:30)
AFGHAN_TZ = timezone(timedelta(hours=4, minutes=30))

# ══════════════════════════════════════════════════════════════════════════════
# ۳. تابع اصلی
# ══════════════════════════════════════════════════════════════════════════════
async def main():
    logger.info("🚀 در حال اتصال به تلگرام...")
    
    # ساخت کلاینت
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        logger.error("❌ سشن منقضی شده است. لطفاً SESSION_STRING جدید بسازید.")
        return

    logger.info("✅ اتصال برقرار شد. شروع فرآیند به‌روزرسانی ساعت و وضعیت آنلاین...")

    while True:
        try:
            # ۱. محاسبه زمان دقیق افغانستان
            now = datetime.now(AFGHAN_TZ)
            time_str = now.strftime("%H:%M")  # فرمت ساعت:دقیقه
            
            # ۲. ساخت نام جدید
            # فرمت: 🕒 14:35 | Ali
            new_name = f"🕒 {time_str} | {BASE_NAME}"
            
            # ۳. آپدیت نام پروفایل
            await client(UpdateProfileRequest(first_name=new_name[:64]))
            
            # ۴. آپدیت وضعیت به آنلاین (Always Online)
            # پارامتر offline=False باعث می‌شود تلگرام شما را آنلاین نشان دهد
            await client(UpdateStatusRequest(offline=False))
            
            logger.info(f"✅ پروفایل آپدیت شد: '{new_name}' | وضعیت: آنلاین 🟢")
            
        except FloodWaitError as e:
            logger.warning(f"⚠️ محدودیت تلگرام. باید {e.seconds} ثانیه صبر کنیم.")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            logger.error(f"❌ خطای غیرمنتظره: {e}")
            
        # صبر تا دقیقه بعد
        await asyncio.sleep(60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("👋 خاموش شدن ربات.")
