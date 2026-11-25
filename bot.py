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
# ۳. هسته اصلی
# ══════════════════════════════════════════════════════════════════════════════
async def master_loop():
    logger.info("🌟 هسته اصلی فعال شد...")
    
    while True:
        try:
            now = datetime.now(KABUL_TZ)
            time_str = now.strftime("%H:%M")
            new_name = f"🕒 {time_str} | {BASE_NAME}"
            
            await client(UpdateProfileRequest(first_name=new_name[:64]))
            await client(UpdateStatusRequest(offline=False))
            
            try:
                dialogs = await client.get_dialogs(limit=1)
                peer = dialogs[0].entity if dialogs else await client.get_me()
                await client(SetTypingRequest(peer=peer, action=SendMessageTypingAction()))
            except: pass
            
            logger.info(f"✅ نام: '{new_name}' | آنلاین 🟢 | تایپ ⌨️")
            
        except FloodWaitError as e:
            logger.warning(f"⚠️ محدودیت: {e.seconds} ثانیه")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            logger.error(f"❌ خطا: {e}")
            await asyncio.sleep(10)
            
        await asyncio.sleep(60)

# ══════════════════════════════════════════════════════════════════════════════
# ۴. نقطه ورود
# ══════════════════════════════════════════════════════════════════════════════
async def main():
    logger.info("🚀 اتصال به تلگرام...")
    await client.connect()
    
    if not await client.is_user_authorized():
        logger.error("❌ سشن نامعتبر است.")
        return

    me = await client.get_me()
    logger.info(f"✅ متصل شد: {me.first_name}")
    await master_loop()

if __name__ == "__main__":
    try:
        client.loop.run_until_complete(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("👋 خاموش شد.")
    finally:
        # 🛡️ خاموشی امن: اتصال را قبل از بسته شدن سرور قطع می‌کنیم
        try:
            client.loop.run_until_complete(client.disconnect())
            logger.info("🔌 اتصال به تلگرام به درستی قطع شد.")
        except: pass
