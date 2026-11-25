import os
import asyncio
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.account import UpdateProfileRequest, UpdateStatusRequest
from telethon.tl.functions.messages import SetTypingRequest
from telethon.tl.types import SendMessageTypingAction
from telethon.errors import FloodWaitError, RPCError

# ══════════════════════════════════════════════════════════════════════════════
# ۱. تنظیمات حرفه‌ای لاگ (برای رصد دقیق در گیت‌هاب)
# ══════════════════════════════════════════════════════════════════════════════
logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("MasterClock")

# ══════════════════════════════════════════════════════════════════════════════
# ۲. خواندن اطلاعات امن (از Secrets گیت‌هاب)
# ══════════════════════════════════════════════════════════════════════════════
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION_STRING = os.getenv("SESSION_STRING", "")
BASE_NAME = os.getenv("BASE_NAME", "My Name")

if not API_ID or not API_HASH or not SESSION_STRING:
    logger.critical("❌ متغیرهای محیطی (API_ID, API_HASH, SESSION_STRING) یافت نشدند.")
    exit(1)

# منطقه زمانی دقیق افغانستان (کابل - UTC+4:30)
KABUL_TZ = ZoneInfo("Asia/Kabul")

# ساخت کلاینت تلگرام
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# ══════════════════════════════════════════════════════════════════════════════
# ۳. هسته اصلی ربات (ساعت + آنلاین + تایپ)
# ══════════════════════════════════════════════════════════════════════════════
async def master_loop():
    """حلقه بی‌نقص برای مدیریت پروفایل، وضعیت و تایپ"""
    logger.info("🌟 هسته اصلی فعال شد. شروع چرخه به‌روزرسانی...")
    
    while True:
        try:
            # ۱. محاسبه دقیق زمان افغانستان
            now = datetime.now(KABUL_TZ)
            time_str = now.strftime("%H:%M")
            
            # ۲. ساخت نام جدید (با محدودیت ۶۴ کاراکتری تلگرام)
            new_name = f"🕒 {time_str} | {BASE_NAME}"
            
            # ۳. آپدیت نام پروفایل
            await client(UpdateProfileRequest(first_name=new_name[:64]))
            
            # ۴. آپدیت وضعیت به آنلاین همیشگی
            await client(UpdateStatusRequest(offline=False))
            
            # ۵. ارسال سیگنال تایپ کردن
            try:
                # دریافت آخرین چت باز شده
                dialogs = await client.get_dialogs(limit=1)
                if dialogs:
                    peer = dialogs[0].entity
                else:
                    # اگر هیچ چتی نبود، در Saved Messages تایپ کن
                    peer = await client.get_me()
                
                await client(SetTypingRequest(peer=peer, action=SendMessageTypingAction()))
            except Exception as typing_err:
                logger.debug(f"⚠️ خطای جزئی در تایپ: {typing_err}")
            
            # لاگ موفقیت‌آمیز
            logger.info(f"✅ نام: '{new_name}' | وضعیت: آنلاین 🟢 | تایپ: فعال ⌨️ | زمان کابل: {now.strftime('%Y-%m-%d %H:%M:%S')}")
            
        except FloodWaitError as e:
            # مدیریت هوشمند محدودیت تلگرام
            logger.warning(f"⚠️ محدودیت تلگرام! باید {e.seconds} ثانیه صبر کنیم.")
            await asyncio.sleep(e.seconds)
        except RPCError as e:
            logger.error(f"❌ خطای RPC تلگرام: {e}")
            await asyncio.sleep(10)
        except Exception as e:
            logger.error(f"❌ خطای غیرمنتظره: {e}")
            await asyncio.sleep(10)
            
        # صبر تا دقیقه بعد
        await asyncio.sleep(60)

# ══════════════════════════════════════════════════════════════════════════════
# ۴. نقطه ورود
# ══════════════════════════════════════════════════════════════════════════════
async def main():
    logger.info("🚀 در حال اتصال به سرورهای تلگرام...")
    await client.connect()
    
    if not await client.is_user_authorized():
        logger.error("❌ سشن منقضی شده یا نامعتبر است. لطفاً SESSION_STRING جدید بسازید.")
        return

    me = await client.get_me()
    logger.info(f"✅ اتصال برقرار شد. حساب متصل: {me.first_name} (ID: {me.id})")
    logger.info("🎯 سه قابلیت خارق‌العاده (ساعت کابل، آنلاین همیشگی، تایپ مداوم) فعال شدند.")
    
    # اجرای حلقه اصلی
    await master_loop()

if __name__ == "__main__":
    try:
        client.loop.run_until_complete(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("👋 ربات به درخواست شما خاموش شد.")
    except Exception as e:
        logger.critical(f"💥 خطای بحرانی در اجرا: {e}")
