import os
import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
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
logger = logging.getLogger("MasterClock")

# ══════════════════════════════════════════════════════════════════════════════
# ۲. خواندن اطلاعات امن
# ══════════════════════════════════════════════════════════════════════════════
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION_STRING = os.getenv("SESSION_STRING", "")
BASE_NAME = os.getenv("BASE_NAME", "My Name")

if not API_ID or not API_HASH or not SESSION_STRING:
    logger.critical("❌ متغیرهای محیطی یافت نشدند.")
    exit(1)

KABUL_TZ = ZoneInfo("Asia/Kabul")
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# ══════════════════════════════════════════════════════════════════════════════
# ۳. حلقه اول: آپدیت ساعت و وضعیت آنلاین (هر ۳۰ ثانیه)
# ══════════════════════════════════════════════════════════════════════════════
async def clock_and_online_loop():
    logger.info("⏰ حلقه ساعت و آنلاین بودن فعال شد.")
    while True:
        try:
            # محاسبه زمان دقیق افغانستان
            now = datetime.now(KABUL_TZ)
            time_str = now.strftime("%H:%M")
            new_name = f"🕒 {time_str} | {BASE_NAME}"
            
            # آپدیت نام و آنلاین
            await client(UpdateProfileRequest(first_name=new_name[:64]))
            await client(UpdateStatusRequest(offline=False))
            
            logger.info(f"✅ ساعت و وضعیت آپدیت شد: '{new_name}' | آنلاین 🟢")
            
        except FloodWaitError as e:
            logger.warning(f"⚠️ محدودیت: {e.seconds} ثانیه")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            logger.error(f"❌ خطا در حلقه ساعت: {e}")
            
        # ۳۰ ثانیه صبر می‌کنیم تا ساعت دقیق بماند و وضعیت آنلاین تازه شود
        await asyncio.sleep(30)

# ══════════════════════════════════════════════════════════════════════════════
# ۴. حلقه دوم: تایپ کردن مداوم (هر ۴ ثانیه)
# ══════════════════════════════════════════════════════════════════════════════
async def typing_loop():
    logger.info("⌨️ حلقه تایپ کردن فعال شد.")
    peer = None
    
    while True:
        try:
            # پیدا کردن چت هدف (آخرین چت باز شده یا Saved Messages)
            if peer is None:
                dialogs = await client.get_dialogs(limit=1)
                peer = dialogs[0].entity if dialogs else await client.get_me()
            
            # ارسال سیگنال تایپ
            await client(SetTypingRequest(peer=peer, action=SendMessageTypingAction()))
            
            # تلگرام سیگنال تایپ را بعد از ۵ ثانیه پاک می‌کند،
            # پس هر ۴ ثانیه دوباره می‌فرستیم تا هرگز قطع نشود.
            
        except FloodWaitError as e:
            logger.warning(f"⚠️ محدودیت تایپ: {e.seconds} ثانیه")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            logger.debug(f"⚠️ خطای تایپ (در حال تلاش مجدد): {e}")
            peer = None # اگر خطا داد، چت را دوباره پیدا می‌کنیم
            
        # ۴ ثانیه صبر می‌کنیم
        await asyncio.sleep(4)

# ══════════════════════════════════════════════════════════════════════════════
# ۵. نقطه ورود و اجرای موازی
# ══════════════════════════════════════════════════════════════════════════════
async def main():
    logger.info("🚀 در حال اتصال به تلگرام...")
    await client.connect()
    
    if not await client.is_user_authorized():
        logger.error("❌ سشن نامعتبر است.")
        return

    me = await client.get_me()
    logger.info(f"✅ اتصال برقرار شد: {me.first_name}")
    
    # 🌟 جادوی مهندسی: اجرای همزمان دو حلقه (Parallel Execution)
    asyncio.create_task(clock_and_online_loop())
    asyncio.create_task(typing_loop())
    
    logger.info("🔥 هر دو حلقه فعال شدند. اکانت شما همیشه آنلاین و در حال تایپ است.")
    
    # ربات را روشن نگه می‌داریم
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        client.loop.run_until_complete(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("👋 خاموش شد.")
    finally:
        # قطع امن اتصال برای جلوگیری از باطل شدن سشن
        try:
            client.loop.run_until_complete(client.disconnect())
        except: pass
