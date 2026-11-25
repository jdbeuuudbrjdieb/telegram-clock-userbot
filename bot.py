import os
import asyncio
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo  # محاسبه دقیق و استاندارد منطقه زمانی
from telethon import TelegramClient
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
logger = logging.getLogger("UserBotClock")

# ══════════════════════════════════════════════════════════════════════════════
# ۲. خواندن اطلاعات امن از Secrets
# ══════════════════════════════════════════════════════════════════════════════
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION_STRING = os.getenv("SESSION_STRING", "")
BASE_NAME = os.getenv("BASE_NAME", "My Name")

if not API_ID or not API_HASH or not SESSION_STRING:
    logger.error("❌ متغیرهای محیطی (API_ID, API_HASH, SESSION_STRING) یافت نشدند.")
    exit(1)

# منطقه زمانی دقیق کابل (افغانستان)
KABUL_TZ = ZoneInfo("Asia/Kabul")

# ══════════════════════════════════════════════════════════════════════════════
# ۳. تابع اصلی
# ══════════════════════════════════════════════════════════════════════════════
async def main():
    logger.info("🚀 در حال اتصال به تلگرام...")
    
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        logger.error("❌ سشن منقضی شده است. لطفاً SESSION_STRING جدید بسازید.")
        return

    logger.info("✅ اتصال برقرار شد. شروع فرآیند به‌روزرسانی...")

    while True:
        try:
            # ۱. محاسبه زمان دقیق کابل (افغانستان)
            now = datetime.now(KABUL_TZ)
            time_str = now.strftime("%H:%M")  # ساعت:دقیقه
            
            # لاگ برای مشاهده دقیق زمان در گیت‌هاب
            logger.info(f"⏰ ساعت کابل: {now.strftime('%H:%M:%S')} | ساعت جهانی (UTC): {datetime.now(timezone.utc).strftime('%H:%M')}")
            
            # ۲. ساخت نام جدید: 🕒 14:35 | Ali
            new_name = f"🕒 {time_str} | {BASE_NAME}"
            
            # ۳. آپدیت نام پروفایل
            await client(UpdateProfileRequest(first_name=new_name[:64]))
            
            # ۴. آپدیت وضعیت به آنلاین (Always Online)
            await client(UpdateStatusRequest(offline=False))
            
            # ۵. قابلیت جدید: همیشه در حال تایپ (Always Typing)
            # ربات وضعیت تایپ را به آخرین چت باز شده شما می‌فرستد
            try:
                dialogs = await client.get_dialogs(limit=1)
                if dialogs:
                    # اگر چتی وجود داشته باشد، در همان چت تایپ می‌کند
                    peer = dialogs[0].entity
                    await client(SetTypingRequest(peer=peer, action=SendMessageTypingAction()))
                    logger.info(f"⌨️ ارسال وضعیت 'در حال تایپ' به چت: {dialogs[0].name}")
                else:
                    # اگر هیچ چتی نبود (اکانت نو)، در چت Saved Messages تایپ می‌کند
                    me = await client.get_me()
                    await client(SetTypingRequest(peer=me, action=SendMessageTypingAction()))
            except Exception as typing_err:
                logger.warning(f"⚠️ خطای تایپ: {typing_err}")
            
            logger.info(f"✅ پروفایل آپدیت شد: '{new_name}' | وضعیت: آنلاین 🟢 | در حال تایپ ⌨️")
            
        except FloodWaitError as e:
            logger.warning(f"⚠️ محدودیت تلگرام. باید {e.seconds} ثانیه صبر کنیم.")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            logger.error(f"❌ خطای غیرمنتظره: {e}")
            
        # صبر ۶۰ ثانیه تا دقیقه بعد
        await asyncio.sleep(60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("👋 خاموش شدن ربات.")
