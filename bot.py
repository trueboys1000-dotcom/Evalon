"""
╔══════════════════════════════════════════════════════════════╗
║         EVALON WINNERS — TELEGRAM SUPPORT BOT v6.2          ║
║                                                              ║
║  ✅ Multi-step menu                                          ║
║  ✅ Melt effect (broadcast messages STAY)                    ║
║  ✅ Auto-clean chat every 12 hours + restart button          ║
║  ✅ Support in Services menu only                            ║
║  ✅ Support messages stay until session ends                 ║
║  ✅ End session → delete all chat messages                   ║
║  ✅ Admin messages for active sessions only                  ║
║  ✅ Keywords working                                         ║
║  ✅ Welcome image + new service images                       ║
║  ✅ Referral min 5 + progress bar + fake leaderboard         ║
║  ✅ Welcome video for new users                              ║
║  ✅ Rating after support                                     ║
║  ✅ Comeback message week 2                                  ║
║  ✅ Poll for new users                                       ║
║  ✅ Free Manual Bot section                                  ║
║  ✅ Broadcast button on text only                            ║
║  ✅ Protect content (no forward/save)                        ║
║  ✅ PostgreSQL database                                      ║
║  ✅ 12 languages                                             ║
╚══════════════════════════════════════════════════════════════╝
"""

import logging
import asyncio
import random
import os
import psycopg2
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ChatJoinRequestHandler,
    ContextTypes, filters,
)
from telegram.constants import ChatAction
from telegram.error import TelegramError, BadRequest

# ══════════════════════════════════════════════════════════════
#  CONFIGURATION
# ══════════════════════════════════════════════════════════════

BOT_TOKEN         = os.environ.get("BOT_TOKEN", "")
BUSINESS_NAME     = "EVALON WINNERS"
ADMIN_IDS         = [8535925646]
WEBSITE_URL       = "https://evalon-winners-traders.netlify.app/"
MAIN_CHANNEL_ID   = -1003403743370
MAIN_CHANNEL_LINK = "https://t.me/+mRNfGaNhz3RkZGRk"
INDICATOR_CHANNEL = "https://t.me/+Px5zPQnChsE2OTg0"
DATABASE_URL      = os.environ.get("DATABASE_URL", "")
BOT_USERNAME      = os.environ.get("BOT_USERNAME", "EvalonwinnersBot")
REFERRAL_MIN      = 5
COMEBACK_DAYS     = 14
CLEAN_HOURS       = 12

FREE_BOT_LINKS = {
    "all_brokers": "https://allbrokersbotpro.netlify.app/",
    "evalon":      "https://evalonwinners.netlify.app/",
    "evalon_ai":   "https://evalonai.netlify.app/",
    "quotex":      "https://quotexprobot.netlify.app/",
}

# ══════════════════════════════════════════════════════════════
#  LOGGING
# ══════════════════════════════════════════════════════════════

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════
#  STATE
# ══════════════════════════════════════════════════════════════

pending_requests: dict = {}
reply_map: dict        = {}
active_support: dict   = {}
# Track ALL message ids per chat {chat_id: [msg_id, ...]}
# support_msg_ids tracks messages during support sessions
bot_msg_ids: dict      = {}   # regular bot messages
support_msg_ids: dict  = {}   # support session messages (both sides)

# ══════════════════════════════════════════════════════════════
#  IMAGES
# ══════════════════════════════════════════════════════════════

WELCOME_IMAGE = "AgACAgQAAxkBAAIBd2oImM1v4VXOsEHovz0kYR_VeucQAAJ2D2sbgzNJUBaZvafv1UR1AQADAgADeQADOwQ"
WELCOME_VIDEO = "AgACAgQAAxkBAANxaggFfxWFFyYzo0XSq9_y6KHx4fMAAsEMaxv560FQMZWpi18Og3oBAAMCAAN5AAM7BA"

SERVICE_PHOTOS = [
    "AgACAgQAAxkBAAIBh2oInvA51r1Qv_mxkOz4qBxl3KXxAALkDWsb-etBUAzHrk3a0q_xAQADAgADeAADOwQ",
    "AgACAgQAAxkBAAIBiGoInvA_hAHaJVMi7klgnYsEUEGuAALmDWsb-etBUAs0gjpeqAGGAQADAgADeQADOwQ",
    "AgACAgQAAxkBAAIBiWoInvAkvZ--Fcqj16f55tPVPO3GAALoDWsb-etBUChBiWPZ1OX6AQADAgADeQADOwQ",
    "AgACAgQAAxkBAAIBimoInvDznDq8cWKZINEofhpxH3whAALqDWsb-etBUFMPgupad-jfAQADAgADeQADOwQ",
    "AgACAgQAAxkBAAIBi2oInvD4dhSTnKVpqNDXkBEnEyhsAALtDWsb-etBUEhXwklgWQ82AQADAgADeQADOwQ",
    "AgACAgQAAxkBAAIBjGoInvBkoCz09uVc_3XgD1j0GRWlAALuDWsb-etBUN0rznzdM5sCAQADAgADeQADOwQ",
    "AgACAgQAAxkBAAIBk2oInvuVyGpoJNsae8VSZ5HnpOS7AALiDWsb-etBUJShk0Rr26IUAQADAgADeQADOwQ",
    "AgACAgQAAxkBAAIBlGoInvv26Z5f5z52SppjSoe2XQktAALlDWsb-etBUL864S1h4nn0AQADAgADeQADOwQ",
    "AgACAgQAAxkBAAIBlWoInvtMhQdS83nMudTAVAVU60L6AALnDWsb-etBULjYJVuU9osDAQADAgADeQADOwQ",
    "AgACAgQAAxkBAAIBlmoInvsqyjwqUMi9gTeOQydcWn8gAALpDWsb-etBUBLBIZ5STt12AQADAgADeQADOwQ",
    "AgACAgQAAxkBAAIBl2oInvvMWqtL8S7E4ALWwPMzdFqHAALsDWsb-etBUNy_zowkOI4eAQADAgADeQADOwQ",
    "AgACAgQAAxkBAAIBmGoInvtYiPBTrDY_htbcaTWDRYHgAALjDWsb-etBUAdXqL-_DLb0AQADAgADeQADOwQ",
    "AgACAgQAAxkBAAIBiGoInvA_hAHaJVMi7klgnYsEUEGuAALmDWsb-etBUAs0gjpeqAGGAQADAgADeQADOwQ",
    "AgACAgQAAxkBAAIBmmoInvttk-uihK65lzzVupjjFgUSAALvDWsb-etBUIQxNCKveqfhAQADAgADeQADOwQ",
    "AgACAgQAAxkBAAIBm2oInvvIboauia90Qf_LWc27kA8wAALwDWsb-etBUAv73VfWq-qmAQADAgADeAADOwQ",
    "AgACAgQAAxkBAAIBnGoInvuQ08hV7TQGJeySrRh2nshlAALxDWsb-etBUPLZF1S8gatiAQADAgADeQADOwQ",
    "AgACAgQAAxkBAAIBs2oIxpB_XPo_oWTh_oIyTkoiWPnbAAJ0Dmsb-etJUET8sipLzHoSAQADAgADeAADOwQ",
    "AgACAgQAAxkBAAIBtGoIxpDZj27MD18ezx7dpmAujkSvAAJ1Dmsb-etJUBg33AABYu1Z8QEAAwIAA3gAAzsE",
]

IMGS_SIGNALS   = SERVICE_PHOTOS[:5]
IMGS_SOCIAL    = SERVICE_PHOTOS[5:9]
IMGS_INDICATOR = SERVICE_PHOTOS[9:13]
IMGS_AUTOBOT   = SERVICE_PHOTOS[13:17]
IMGS_FREEBOT   = SERVICE_PHOTOS[:9]

def rand_img(pool, user_data, key):
    last = user_data.get(key)
    available = [x for x in pool if x != last] or pool
    chosen = random.choice(available)
    user_data[key] = chosen
    return chosen

# ══════════════════════════════════════════════════════════════
#  DATABASE
# ══════════════════════════════════════════════════════════════

def get_conn():
    url = DATABASE_URL
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return psycopg2.connect(url, sslmode="require")

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          BIGINT PRIMARY KEY,
            name        TEXT,
            username    TEXT,
            joined      TEXT,
            last_seen   TEXT,
            referred_by BIGINT DEFAULT NULL,
            referrals   INTEGER DEFAULT 0,
            lang        TEXT DEFAULT 'en'
        )
    """)
    c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS lang TEXT DEFAULT 'en'")
    conn.commit()
    conn.close()

def register_user(user, referred_by=None, lang="en"):
    conn = get_conn()
    c = conn.cursor()
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    c.execute("SELECT id FROM users WHERE id=%s", (user.id,))
    exists = c.fetchone()
    if exists:
        c.execute("""
            UPDATE users SET name=%s, username=%s, last_seen=%s, lang=%s WHERE id=%s
        """, (user.full_name, user.username or "", now, lang, user.id))
    else:
        c.execute("""
            INSERT INTO users (id, name, username, joined, last_seen, referred_by, referrals, lang)
            VALUES (%s,%s,%s,%s,%s,%s,0,%s)
        """, (user.id, user.full_name, user.username or "", now, now, referred_by, lang))
        if referred_by:
            c.execute("UPDATE users SET referrals=referrals+1 WHERE id=%s", (referred_by,))
    conn.commit()
    conn.close()

def is_new_user(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE id=%s", (user_id,))
    exists = c.fetchone()
    conn.close()
    return exists is None

def get_all_user_ids():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM users")
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]

def get_user_count():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    count = c.fetchone()[0]
    conn.close()
    return count

def get_active_users(days):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT last_seen FROM users")
    rows = c.fetchall()
    conn.close()
    now = datetime.now()
    count = 0
    for (ls,) in rows:
        try:
            if (now - datetime.strptime(ls, "%d/%m/%Y %H:%M")).days <= days:
                count += 1
        except:
            pass
    return count

def get_user_info(uid):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id,name,username,referrals,lang FROM users WHERE id=%s", (uid,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "name": row[1], "username": row[2], "referrals": row[3], "lang": row[4] or "en"}
    return {"id": uid, "name": str(uid), "username": "", "referrals": 0, "lang": "en"}

def get_referral_count(uid):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT referrals FROM users WHERE id=%s", (uid,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def get_new_users_today():
    conn = get_conn()
    c = conn.cursor()
    today = datetime.now().strftime("%d/%m/%Y")
    c.execute("SELECT COUNT(*) FROM users WHERE joined LIKE %s", (f"{today}%",))
    count = c.fetchone()[0]
    conn.close()
    return count

def get_top_referrers(limit=5):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT name, referrals FROM users ORDER BY referrals DESC LIMIT %s", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

def is_admin(uid):
    return uid in ADMIN_IDS

# ══════════════════════════════════════════════════════════════
#  FAKE LEADERBOARD & PROGRESS BAR
# ══════════════════════════════════════════════════════════════

FAKE_NAMES = [
    "Trader_254", "VIP_Master", "Signals_Pro", "Alpha_Trader",
    "Gold_Winner", "FX_Champion", "Binary_King", "Profit_Hunter",
]

def get_fake_leaderboard(user_real_count):
    fake_scores = sorted(random.sample(range(15, 60), 3), reverse=True)
    names = random.sample(FAKE_NAMES, 3)
    medals = ["👑", "🥈", "🥉"]
    text = "\n🏆 *LEADERBOARD YA WIKI*\n"
    for i, (name, score) in enumerate(zip(names, fake_scores)):
        text += f"{medals[i]} {name} — {score} watu\n"
    text += f"👤 *Wewe — {user_real_count} watu* 🔥"
    if user_real_count < fake_scores[-1]:
        text += f"\n💪 Alika {fake_scores[-1] - user_real_count} zaidi kuingia top 3!"
    return text

def make_progress_bar(count, total):
    filled = int((count / total) * 10)
    bar = "█" * filled + "░" * (10 - filled)
    return f"`[{bar}]` {count}/{total}"

# ══════════════════════════════════════════════════════════════
#  URGENCY
# ══════════════════════════════════════════════════════════════

URGENCY = {
    "en": [
        "⚠️ *LIMITED SLOTS!* Only a few VIP spots left today!",
        "🔥 *HIGH DEMAND!* 12 traders joined in the last hour!",
        "⏰ *TODAY ONLY!* Special offer expires at midnight!",
        "🚨 *ALMOST FULL!* VIP channel closing new members soon!",
        "💥 *LAST CHANCE!* Don't miss today's winning signals!",
    ],
    "sw": [
        "⚠️ *NAFASI CHACHE!* Nafasi chache za VIP zimebaki leo!",
        "🔥 *MAHITAJI MAKUBWA!* Wafanyabiashara 12 walijiunga saa moja iliyopita!",
        "⏰ *LEO TU!* Ofa maalum inaisha usiku wa manane!",
        "🚨 *KARIBU KUJAA!* Channel ya VIP itafunga wanachama wapya hivi karibuni!",
        "💥 *NAFASI YA MWISHO!* Usikose signals za kushinda za leo!",
    ],
}

def get_urgency(lang):
    pool = URGENCY.get(lang, URGENCY["en"])
    return pool[datetime.now().weekday() % len(pool)]

# ══════════════════════════════════════════════════════════════
#  SERVICE REPLIES
# ══════════════════════════════════════════════════════════════

SIGNALS_REPLIES = {
    "en": [
        "📊 *VIP SIGNALS — EVALON WINNERS* 🎯\n\n✅ 80–95% Win Rate\n✅ 3–10 signals daily\n✅ Real Forex pairs (EUR/USD, GBP/USD, USD/JPY, XAU/USD & more)\n✅ Entry, TP & SL included\n✅ Works on Quotex & Pocket Option\n✅ 24/7 active team\n\n👇 Visit our website:",
        "🎯 *PRECISION SIGNALS* ⚡\n\n🔑 Each signal:\n• Real Forex pair\n• Direction (BUY/SELL)\n• Entry price, TP & SL\n\n📊 Quotex | Pocket Option | All brokers\n\n👇 Get access now:",
        "💎 *EVALON VIP SIGNALS* 🚀\n\n📈 Real price action\n📊 EUR/USD | GBP/USD | USD/JPY | XAU/USD & more\n⚡ Instant delivery\n\n👇 Start winning:",
    ],
    "sw": [
        "📊 *VIP SIGNALS — EVALON WINNERS* 🎯\n\n✅ Usahihi 80–95%\n✅ Signals 3–10 kila siku\n✅ Forex ya kweli (EUR/USD, GBP/USD, XAU/USD & zaidi)\n✅ Entry, TP & SL\n✅ Quotex & Pocket Option\n\n👇 Tembelea website:",
        "🎯 *SIGNALS ZA USAHIHI* ⚡\n\n🔑 Kila signal:\n• Pair ya forex ya kweli\n• Mwelekeo (BUY/SELL)\n• Bei ya kuingia, TP & SL\n\n👇 Pata ufikiaji:",
    ],
    "ar": ["📊 *إشارات VIP — EVALON* 🎯\n\n✅ دقة 80–95%\n✅ فوركس حقيقي\n\n👇 زر موقعنا:"],
    "zh": ["📊 *VIP信号 — EVALON* 🎯\n\n✅ 80–95%胜率\n✅ 真实外汇\n\n👇 访问网站:"],
    "hi": ["📊 *VIP सिग्नल — EVALON* 🎯\n\n✅ 80–95% जीत दर\n✅ असली फॉरेक्स\n\n👇 वेबसाइट:"],
    "ru": ["📊 *VIP СИГНАЛЫ — EVALON* 🎯\n\n✅ Точность 80–95%\n✅ Реальный форекс\n\n👇 Сайт:"],
    "es": ["📊 *SEÑALES VIP — EVALON* 🎯\n\n✅ 80–95% precisión\n✅ Forex real\n\n👇 Web:"],
    "fr": ["📊 *SIGNAUX VIP — EVALON* 🎯\n\n✅ Précision 80–95%\n✅ Forex réel\n\n👇 Site:"],
    "pt": ["📊 *SINAIS VIP — EVALON* 🎯\n\n✅ 80–95% precisão\n✅ Forex real\n\n👇 Site:"],
    "de": ["📊 *VIP-SIGNALE — EVALON* 🎯\n\n✅ 80–95% Genauigkeit\n✅ Echter Forex\n\n👇 Website:"],
    "ur": ["📊 *VIP سگنلز — EVALON* 🎯\n\n✅ 80–95% درستگی\n✅ حقیقی فاریکس\n\n👇 ویب سائٹ:"],
    "ja": ["📊 *VIPシグナル — EVALON* 🎯\n\n✅ 80–95%勝率\n✅ リアルFX\n\n👇 ウェブサイト:"],
}

SOCIAL_REPLIES = {
    "en": [
        "👥 *POCKET SOCIAL TRADING — EVALON* 🔄\n\nCopy the best traders automatically!\n\n✅ Auto-copy top performers\n✅ Works on Pocket Option\n✅ No experience needed\n✅ Start & stop anytime\n\n👇 Learn more:",
        "🔄 *COPY TRADING — EARN PASSIVELY* 💰\n\n1️⃣ Connect Pocket Option\n2️⃣ Choose top trader\n3️⃣ Trades copy automatically\n4️⃣ You earn when they earn!\n\n👇 Get started:",
    ],
    "sw": [
        "👥 *POCKET SOCIAL TRADING* 🔄\n\nNakili wafanyabiashara bora!\n\n✅ Nakili otomatiki\n✅ Pocket Option\n✅ Huhitaji uzoefu\n\n👇 Jifunze zaidi:",
        "🔄 *NAKILI & PATA FAIDA* 💰\n\n1️⃣ Unganisha Pocket Option\n2️⃣ Chagua trader bora\n3️⃣ Biashara zinakiliwa\n4️⃣ Pata faida!\n\n👇 Anza:",
    ],
    "ar": ["👥 *التداول الاجتماعي* 🔄\n\n✅ نسخ تلقائي\n✅ Pocket Option\n\n👇 زر موقعنا:"],
    "zh": ["👥 *社交交易* 🔄\n\n✅ 自动复制\n✅ Pocket Option\n\n👇 访问网站:"],
    "hi": ["👥 *सोशल ट्रेडिंग* 🔄\n\n✅ ऑटो-कॉपी\n✅ Pocket Option\n\n👇 वेबसाइट:"],
    "ru": ["👥 *СОЦИАЛЬНЫЙ ТРЕЙДИНГ* 🔄\n\n✅ Авто-копирование\n✅ Pocket Option\n\n👇 Сайт:"],
    "es": ["👥 *TRADING SOCIAL* 🔄\n\n✅ Auto-copia\n✅ Pocket Option\n\n👇 Web:"],
    "fr": ["👥 *TRADING SOCIAL* 🔄\n\n✅ Auto-copie\n✅ Pocket Option\n\n👇 Site:"],
    "pt": ["👥 *TRADING SOCIAL* 🔄\n\n✅ Auto-cópia\n✅ Pocket Option\n\n👇 Site:"],
    "de": ["👥 *SOCIAL TRADING* 🔄\n\n✅ Auto-Kopie\n✅ Pocket Option\n\n👇 Website:"],
    "ur": ["👥 *سوشل ٹریڈنگ* 🔄\n\n✅ آٹو کاپی\n✅ Pocket Option\n\n👇 ویب سائٹ:"],
    "ja": ["👥 *ソーシャルトレード* 🔄\n\n✅ 自動コピー\n✅ Pocket Option\n\n👇 ウェブサイト:"],
}

INDICATOR_REPLIES = {
    "en": [
        "📈 *FREE INDICATOR — EVALON WINNERS* 🎁\n\n100% FREE!\n\n✅ Buy/sell arrows on chart\n✅ All timeframes (1m–1h)\n✅ No repaint\n✅ MT4, MT5 & web\n✅ Easy install + guide\n\n📲 Join FREE channel:",
        "🆓 *FREE INDICATOR — NO PAYMENT* 💎\n\n🔧 Non-repainting\n📊 20+ pairs\n⚡ OTC weekend trading\n\n👇 Get FREE:",
    ],
    "sw": [
        "📈 *INDICATOR YA BURE* 🎁\n\nBURE KABISA!\n\n✅ Mishale ya BUY/SELL\n✅ Vipindi vyote\n✅ Rahisi kusakinisha\n\n📲 Jiunge na channel ya BURE:",
        "🆓 *INDICATOR BURE* 💎\n\n🔧 Haibadilishi\n📊 Jozi 20+\n\n👇 Ipate BURE:",
    ],
    "ar": ["📈 *مؤشر مجاني* 🎁\n\n✅ 100% مجاني\n\n📲 القناة المجانية:"],
    "zh": ["📈 *免费指标* 🎁\n\n✅ 100%免费\n\n📲 免费频道:"],
    "hi": ["📈 *मुफ्त इंडिकेटर* 🎁\n\n✅ 100% मुफ्त\n\n📲 मुफ्त चैनल:"],
    "ru": ["📈 *БЕСПЛАТНЫЙ ИНДИКАТОР* 🎁\n\n✅ 100% бесплатно\n\n📲 Бесплатный канал:"],
    "es": ["📈 *INDICADOR GRATIS* 🎁\n\n✅ 100% gratis\n\n📲 Canal gratuito:"],
    "fr": ["📈 *INDICATEUR GRATUIT* 🎁\n\n✅ 100% gratuit\n\n📲 Canal gratuit:"],
    "pt": ["📈 *INDICADOR GRÁTIS* 🎁\n\n✅ 100% grátis\n\n📲 Canal gratuito:"],
    "de": ["📈 *KOSTENLOSER INDIKATOR* 🎁\n\n✅ 100% kostenlos\n\n📲 Kostenloser Kanal:"],
    "ur": ["📈 *مفت انڈیکیٹر* 🎁\n\n✅ 100% مفت\n\n📲 مفت چینل:"],
    "ja": ["📈 *無料インジケーター* 🎁\n\n✅ 100%無料\n\n📲 無料チャンネル:"],
}

AUTOBOT_REPLIES = {
    "en": [
        "🤖 *AUTO TRADING BOT — EVALON* 💎\n\nTrade automatically 24/7!\n\n✅ All brokers supported\n✅ Runs 24/7\n✅ No experience needed\n\n🏦 Quotex | Pocket Option | IQ Option | Deriv & more\n\n👇 Get it now:",
        "⚡ *EVALON AUTO BOT — 24/7* 🚀\n\nYou focus on life — bot focuses on profits!\n\n🔧 AI entry detection\n📱 Mobile notifications\n🔐 Funds stay in YOUR account\n\n👇 Website:",
    ],
    "sw": [
        "🤖 *AUTO TRADING BOT — EVALON* 💎\n\nBiashara otomatiki 24/7!\n\n✅ Mawakala WOTE\n✅ Inafanya kazi 24/7\n\n🏦 Quotex | Pocket Option | IQ Option | Deriv\n\n👇 Ipate sasa:",
        "⚡ *EVALON AUTO BOT — 24/7* 🚀\n\nWewe zingatia maisha — bot izingatie faida!\n\n👇 Website:",
    ],
    "ar": ["🤖 *بوت التداول* 💎\n\n✅ جميع الوسطاء\n✅ 24/7\n\n👇 احصل عليه:"],
    "zh": ["🤖 *自动机器人* 💎\n\n✅ 所有经纪商\n✅ 24/7\n\n👇 立即获取:"],
    "hi": ["🤖 *ऑटो बॉट* 💎\n\n✅ सभी ब्रोकर\n✅ 24/7\n\n👇 अभी पाएं:"],
    "ru": ["🤖 *АВТО БОТ* 💎\n\n✅ Все брокеры\n✅ 24/7\n\n👇 Получить:"],
    "es": ["🤖 *BOT AUTO* 💎\n\n✅ Todos los brokers\n✅ 24/7\n\n👇 Obtener:"],
    "fr": ["🤖 *BOT AUTO* 💎\n\n✅ Tous les brokers\n✅ 24/7\n\n👇 Obtenir:"],
    "pt": ["🤖 *BOT AUTO* 💎\n\n✅ Todos os brokers\n✅ 24/7\n\n👇 Obter:"],
    "de": ["🤖 *AUTO-BOT* 💎\n\n✅ Alle Broker\n✅ 24/7\n\n👇 Holen:"],
    "ur": ["🤖 *آٹو بوٹ* 💎\n\n✅ تمام بروکرز\n✅ 24/7\n\n👇 حاصل کریں:"],
    "ja": ["🤖 *自動ボット* 💎\n\n✅ 全ブローカー\n✅ 24/7\n\n👇 入手:"],
}

FREEBOT_REPLIES = {
    "en": ["🆓 *FREE MANUAL BOT — EVALON* 🤖\n\nGet our FREE trading bot!\n\n✅ Works on ALL brokers\n✅ Easy to use\n✅ Step-by-step guide\n\nChoose your broker 👇"],
    "sw": ["🆓 *FREE MANUAL BOT — EVALON* 🤖\n\nPata bot yetu ya BURE!\n\n✅ Mawakala WOTE\n✅ Rahisi kutumia\n✅ Mwongozo wa hatua kwa hatua\n\nChagua broker yako 👇"],
}

# ══════════════════════════════════════════════════════════════
#  UI TRANSLATIONS
# ══════════════════════════════════════════════════════════════

UI = {
    "en": {
        "welcome": "👋 Welcome, *{name}!*\n\n{urgency}\n\n🏆 *{business}* — Where winners trade!\n\nWhat would you like to explore? 👇",
        "btn_services": "🏆 Our Services",
        "btn_referral": "🎁 Invite & Earn",
        "btn_stories": "⭐ Success Stories",
        "btn_language": "🌍 Language",
        "btn_signals": "📊 VIP Signals",
        "btn_social": "👥 Social Trading",
        "btn_indicator": "📈 Free Indicator",
        "btn_autobot": "🤖 Auto Bot",
        "btn_freebot": "🆓 Free Manual Bot",
        "btn_website": "🌐 Website & Pricing",
        "btn_support": "💬 Contact Support",
        "btn_back": "⬅️ Back",
        "btn_restart": "🚀 Tap to Start",
        "btn_free_indicator": "📲 Get FREE Indicator",
        "btn_join": "📢 Join Our Channel",
        "btn_poll_quotex": "📊 Quotex",
        "btn_poll_pocket": "💰 Pocket Option",
        "btn_poll_both": "✅ Both",
        "join_msg": "⚠️ *Please join our channel first!*\n\nJoin now and come back! 👇",
        "support_msg": "💬 *Support Request Received!* ✅\n\nOur team will contact you *within 5 hours.* ⏳\n\nPlease keep the bot open! 🙏",
        "fallback_msg": "🤔 I didn't find an answer for that.\n\nWould you like to speak with our support team?",
        "msg_received": "📨 Message received! Our team will reply shortly. 🙏",
        "referral_msg": "🎁 *YOUR REFERRAL LINK*\n\n🔗 `https://t.me/{bot}?start=ref{uid}`\n\n📊 Your referrals: *{count}/{min}*\n{bar}\n\n🎯 Refer *{needed}* more to unlock your reward!\n{leaderboard}",
        "comeback_msg": "👋 Hey *{name}!* We missed you! 😊\n\n🔥 New signals & opportunities waiting!\n\n💎 *EVALON WINNERS* has exciting updates for you!\n\n👇 Come back and explore:",
        "rating_msg": "⭐ *How was your support experience?*\n\nPlease rate our service:",
        "rating_thanks": "🙏 Thank you for your rating, *{name}!* ⭐",
        "poll_msg": "📊 *Quick Question!*\n\nWhich platform do you mainly use?",
        "welcome_video": "🎬 *Welcome to EVALON WINNERS!*\n\nWatch this intro to see how we help traders win! 🏆",
        "services_msg": "🏆 *OUR SERVICES*\n\nChoose a service to learn more 👇",
        "price_msg": "💰 *Pricing & Plans*\n\nVisit our website for latest pricing 👇",
        "join_pending": "⏳ *Request received!*\n\nAdmin will approve shortly. 🙏",
        "auto_clean_msg": "🔄 *Chat refreshed!*\n\nTap below to continue 👇",
        "session_ended": "👋 *Support chat has ended.*\n\nThank you! Tap below if you need more help.",
    },
    "sw": {
        "welcome": "👋 Karibu, *{name}!*\n\n{urgency}\n\n🏆 *{business}* — Mahali pa washindi!\n\nUnataka kuchunguza nini? 👇",
        "btn_services": "🏆 Huduma Zetu",
        "btn_referral": "🎁 Alika & Pata",
        "btn_stories": "⭐ Hadithi za Mafanikio",
        "btn_language": "🌍 Lugha",
        "btn_signals": "📊 VIP Signals",
        "btn_social": "👥 Social Trading",
        "btn_indicator": "📈 Indicator ya Bure",
        "btn_autobot": "🤖 Auto Bot",
        "btn_freebot": "🆓 Free Manual Bot",
        "btn_website": "🌐 Website & Bei",
        "btn_support": "💬 Wasiliana na Support",
        "btn_back": "⬅️ Rudi",
        "btn_restart": "🚀 Bonyeza Kuanza",
        "btn_free_indicator": "📲 Pata Indicator BURE",
        "btn_join": "📢 Jiunge na Channel",
        "btn_poll_quotex": "📊 Quotex",
        "btn_poll_pocket": "💰 Pocket Option",
        "btn_poll_both": "✅ Zote Mbili",
        "join_msg": "⚠️ *Tafadhali jiunge na channel yetu kwanza!*\n\nJiunge sasa na urudi! 👇",
        "support_msg": "💬 *Ombi la Msaada Limepokelewa!* ✅\n\nTimu yetu itawasiliana nawe *ndani ya masaa 5.* ⏳\n\nKaa na bot wazi! 🙏",
        "fallback_msg": "🤔 Sikupata jibu la hilo.\n\nUnataka kuzungumza na timu yetu ya msaada?",
        "msg_received": "📨 Ujumbe umepokelewa! Timu yetu itajibu hivi karibuni. 🙏",
        "referral_msg": "🎁 *KIUNGO CHAKO CHA RUFAA*\n\n🔗 `https://t.me/{bot}?start=ref{uid}`\n\n📊 Rufaa zako: *{count}/{min}*\n{bar}\n\n🎯 Alika *{needed}* zaidi kufungua zawadi!\n{leaderboard}",
        "comeback_msg": "👋 Habari *{name}!* Tulikusahau! 😊\n\n🔥 Signals mpya, fursa mpya!\n\n💎 *EVALON WINNERS* ina mambo mapya!\n\n👇 Rudi na uchunguze:",
        "rating_msg": "⭐ *Huduma ya support ilikuwaje?*\n\nTupa alama:",
        "rating_thanks": "🙏 Asante kwa alama yako, *{name}!* ⭐",
        "poll_msg": "📊 *Swali Moja!*\n\nUnatumia platform ipi zaidi?",
        "welcome_video": "🎬 *Karibu EVALON WINNERS!*\n\nAngalia video hii fupi! 🏆",
        "services_msg": "🏆 *HUDUMA ZETU*\n\nChagua huduma kujifunza zaidi 👇",
        "price_msg": "💰 *Bei na Mipango*\n\nTembelea website 👇",
        "join_pending": "⏳ *Ombi limepokelewa!*\n\nAdmin atakuidhibitisha. 🙏",
        "auto_clean_msg": "🔄 *Chat imesafishwa!*\n\nBonyeza hapa chini kuendelea 👇",
        "session_ended": "👋 *Mazungumzo ya msaada yamekwisha.*\n\nAsante! Bonyeza hapa chini ukihitaji msaada zaidi.",
    },
}

for _lc in ["ar","zh","hi","ru","es","fr","pt","de","ur","ja"]:
    UI[_lc] = {k: UI["en"][k] for k in UI["en"]}

def ui(key, lang):
    return UI.get(lang, UI["en"]).get(key, UI["en"].get(key, key))

def get_lang(context):
    return context.user_data.get("lang", "en")

def get_replies(pool, lang):
    return pool.get(lang) or pool.get("en", ["Coming soon!"])

# ══════════════════════════════════════════════════════════════
#  MESSAGE TRACKING
# ══════════════════════════════════════════════════════════════

def track_msg(chat_id, msg_id):
    """Track regular bot message for melt effect"""
    if chat_id not in bot_msg_ids:
        bot_msg_ids[chat_id] = []
    bot_msg_ids[chat_id].append(msg_id)
    if len(bot_msg_ids[chat_id]) > 100:
        bot_msg_ids[chat_id] = bot_msg_ids[chat_id][-100:]

def track_support_msg(chat_id, msg_id):
    """Track support session message — stays until session ends"""
    if chat_id not in support_msg_ids:
        support_msg_ids[chat_id] = []
    support_msg_ids[chat_id].append(msg_id)

# ══════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════

async def safe_delete(context, chat_id, message_id):
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except:
        pass

async def delete_user_msg(message):
    try:
        await message.delete()
    except:
        pass

async def delete_all_bot_msgs(context, chat_id):
    """Delete all tracked regular bot messages"""
    if chat_id in bot_msg_ids:
        for msg_id in bot_msg_ids[chat_id]:
            await safe_delete(context, chat_id, msg_id)
        bot_msg_ids[chat_id] = []

async def delete_support_msgs(context, chat_id):
    """Delete all support session messages"""
    if chat_id in support_msg_ids:
        for msg_id in support_msg_ids[chat_id]:
            await safe_delete(context, chat_id, msg_id)
        support_msg_ids[chat_id] = []

async def typing_action(chat_id, context, seconds=1.5):
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    await asyncio.sleep(seconds)

async def is_member(context, user_id):
    try:
        member = await context.bot.get_chat_member(
            chat_id=MAIN_CHANNEL_ID, user_id=user_id)
        if member.status in ("member", "administrator", "creator", "restricted"):
            return True
        if member.status == "left" and user_id in pending_requests:
            return True
    except:
        if user_id in pending_requests:
            return True
    return user_id in pending_requests

async def notify_new_user(context, user):
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    text = f"🆕 *New User!*\n\n👤 {user.full_name}\n🔗 @{user.username or 'N/A'}\n🆔 `{user.id}`\n🕐 {now}"
    for aid in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=aid, text=text, parse_mode="Markdown")
        except Exception as e:
            logger.warning(f"Notify failed: {e}")

async def notify_support_request(context, user, lang):
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    text = (
        f"🆘 *Support Request*\n\n"
        f"👤 {user.full_name}\n🔗 @{user.username or 'N/A'}\n"
        f"🆔 `{user.id}`\n🕐 {now}\n🌍 Lang: {lang}"
    )
    btns = InlineKeyboardMarkup([[
        InlineKeyboardButton("🟢 Connect", callback_data=f"con:{user.id}:{lang}"),
        InlineKeyboardButton("🔴 End Chat", callback_data=f"dis:{user.id}:{lang}"),
    ]])
    for aid in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=aid, text=text,
                parse_mode="Markdown", reply_markup=btns)
        except Exception as e:
            logger.warning(f"Support notify failed: {e}")

# ══════════════════════════════════════════════════════════════
#  AUTO CLEAN JOB (every 12 hours)
# ══════════════════════════════════════════════════════════════

async def auto_clean_chat(context: ContextTypes.DEFAULT_TYPE):
    job_data = context.job.data
    chat_id = job_data["chat_id"]
    lang    = job_data.get("lang", "en")
    name    = job_data.get("name", "")

    # Skip if in active support session
    uid = job_data.get("uid")
    if uid and active_support.get(uid):
        schedule_auto_clean(context, chat_id, lang, name, uid)
        return

    await delete_all_bot_msgs(context, chat_id)

    try:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        await asyncio.sleep(1.0)
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text=ui("auto_clean_msg", lang),
            parse_mode="Markdown",
            protect_content=True,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(ui("btn_restart", lang), callback_data="main_menu")
            ]]))
        track_msg(chat_id, msg.message_id)
    except Exception as e:
        logger.warning(f"Auto clean failed for {chat_id}: {e}")

    schedule_auto_clean(context, chat_id, lang, name, uid)

def schedule_auto_clean(context, chat_id, lang, name, uid=None):
    if not context.job_queue:
        return
    job_name = f"clean_{chat_id}"
    for job in context.job_queue.get_jobs_by_name(job_name):
        job.schedule_removal()
    context.job_queue.run_once(
        auto_clean_chat,
        when=CLEAN_HOURS * 3600,
        data={"chat_id": chat_id, "lang": lang, "name": name, "uid": uid},
        name=job_name)

# ══════════════════════════════════════════════════════════════
#  COMEBACK JOB
# ══════════════════════════════════════════════════════════════

async def send_comeback_reminder(context: ContextTypes.DEFAULT_TYPE):
    job_data = context.job.data
    chat_id = job_data["chat_id"]
    name    = job_data["name"]
    lang    = job_data.get("lang", "en")
    try:
        img = random.choice(SERVICE_PHOTOS)
        text = ui("comeback_msg", lang).format(name=name)
        try:
            msg = await context.bot.send_photo(
                chat_id=chat_id, photo=img, caption=text,
                parse_mode="Markdown",
                protect_content=True,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(ui("btn_services", lang), callback_data="menu_services")],
                    [InlineKeyboardButton(ui("btn_support", lang), callback_data="do_support")],
                ]))
        except:
            msg = await context.bot.send_message(
                chat_id=chat_id, text=text,
                parse_mode="Markdown",
                protect_content=True,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(ui("btn_services", lang), callback_data="menu_services")],
                ]))
        track_msg(chat_id, msg.message_id)
    except Exception as e:
        logger.warning(f"Comeback failed: {e}")

def schedule_comeback(context, chat_id, name, lang):
    if not context.job_queue:
        return
    job_name = f"comeback_{chat_id}"
    for job in context.job_queue.get_jobs_by_name(job_name):
        job.schedule_removal()
    context.job_queue.run_once(
        send_comeback_reminder,
        when=COMEBACK_DAYS * 24 * 3600,
        data={"chat_id": chat_id, "name": name, "lang": lang},
        name=job_name)

# ══════════════════════════════════════════════════════════════
#  KEYBOARDS
# ══════════════════════════════════════════════════════════════

def lang_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
         InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh"),
         InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es")],
        [InlineKeyboardButton("🇫🇷 Français", callback_data="lang_fr"),
         InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar"),
         InlineKeyboardButton("🇮🇳 हिन्दी", callback_data="lang_hi")],
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
         InlineKeyboardButton("🇹🇿 Swahili", callback_data="lang_sw"),
         InlineKeyboardButton("🇧🇷 Português", callback_data="lang_pt")],
        [InlineKeyboardButton("🇩🇪 Deutsch", callback_data="lang_de"),
         InlineKeyboardButton("🇵🇰 اردو", callback_data="lang_ur"),
         InlineKeyboardButton("🇯🇵 日本語", callback_data="lang_ja")],
    ])

def main_menu(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(ui("btn_services", lang), callback_data="menu_services")],
        [InlineKeyboardButton(ui("btn_referral", lang), callback_data="do_referral"),
         InlineKeyboardButton(ui("btn_stories", lang), callback_data="do_stories")],
        [InlineKeyboardButton(ui("btn_language", lang), callback_data="change_lang")],
    ])

def services_menu(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(ui("btn_signals", lang), callback_data="svc_signals"),
         InlineKeyboardButton(ui("btn_social", lang), callback_data="svc_social")],
        [InlineKeyboardButton(ui("btn_indicator", lang), callback_data="svc_indicator"),
         InlineKeyboardButton(ui("btn_autobot", lang), callback_data="svc_autobot")],
        [InlineKeyboardButton(ui("btn_freebot", lang), callback_data="svc_freebot")],
        [InlineKeyboardButton(ui("btn_website", lang), url=WEBSITE_URL)],
        [InlineKeyboardButton(ui("btn_support", lang), callback_data="do_support")],
        [InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")],
    ])

def freebot_menu(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 All Brokers Bot", url=FREE_BOT_LINKS["all_brokers"])],
        [InlineKeyboardButton("💎 Evalon Winners Bot", url=FREE_BOT_LINKS["evalon"])],
        [InlineKeyboardButton("🤖 Evalon AI Bot", url=FREE_BOT_LINKS["evalon_ai"])],
        [InlineKeyboardButton("📊 Quotex Pro Bot", url=FREE_BOT_LINKS["quotex"])],
        [InlineKeyboardButton(ui("btn_back", lang), callback_data="menu_services")],
    ])

def svc_keyboard(lang, indicator=False):
    rows = [
        [InlineKeyboardButton(ui("btn_website", lang), url=WEBSITE_URL)],
        [InlineKeyboardButton(ui("btn_support", lang), callback_data="do_support")],
        [InlineKeyboardButton(ui("btn_back", lang), callback_data="menu_services")],
    ]
    if indicator:
        rows.insert(1, [InlineKeyboardButton(
            ui("btn_free_indicator", lang), url=INDICATOR_CHANNEL)])
    return InlineKeyboardMarkup(rows)

def join_keyboard(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(ui("btn_join", lang), url=MAIN_CHANNEL_LINK)],
        [InlineKeyboardButton("✅ I've Joined!", callback_data="check_join")],
    ])

def support_keyboard(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(ui("btn_support", lang), callback_data="do_support")],
        [InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")],
    ])

def broadcast_keyboard(lang):
    """Button for broadcast TEXT messages only"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(ui("btn_services", lang), callback_data="menu_services")],
    ])

def rating_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("⭐", callback_data="rate_1"),
        InlineKeyboardButton("⭐⭐", callback_data="rate_2"),
        InlineKeyboardButton("⭐⭐⭐", callback_data="rate_3"),
        InlineKeyboardButton("⭐⭐⭐⭐", callback_data="rate_4"),
        InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data="rate_5"),
    ]])

def poll_keyboard(lang):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(ui("btn_poll_quotex", lang), callback_data="poll_quotex"),
        InlineKeyboardButton(ui("btn_poll_pocket", lang), callback_data="poll_pocket"),
        InlineKeyboardButton(ui("btn_poll_both", lang), callback_data="poll_both"),
    ]])

# ══════════════════════════════════════════════════════════════
#  SEND WITH PROTECT CONTENT
# ══════════════════════════════════════════════════════════════

async def send_protected_photo(context, chat_id, photo, caption, keyboard):
    try:
        return await context.bot.send_photo(
            chat_id=chat_id, photo=photo, caption=caption,
            parse_mode="Markdown", reply_markup=keyboard,
            protect_content=True)
    except:
        return await context.bot.send_message(
            chat_id=chat_id, text=caption,
            parse_mode="Markdown", reply_markup=keyboard,
            protect_content=True)

async def send_protected_text(context, chat_id, text, keyboard):
    return await context.bot.send_message(
        chat_id=chat_id, text=text,
        parse_mode="Markdown", reply_markup=keyboard,
        protect_content=True)

# ══════════════════════════════════════════════════════════════
#  JOIN REQUEST
# ══════════════════════════════════════════════════════════════

async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    req  = update.chat_join_request
    user = req.from_user
    chat = req.chat
    now  = datetime.now().strftime("%d/%m/%Y %H:%M")

    pending_requests[user.id] = {
        "chat_id": chat.id, "chat_title": chat.title,
        "user": user, "time": now,
    }

    btns = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user.id}"),
        InlineKeyboardButton("❌ Decline", callback_data=f"decline_{user.id}"),
    ]])
    for aid in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=aid,
                text=f"📨 *New Join Request*\n\n👤 {user.full_name}\n🔗 @{user.username or 'N/A'}\n🆔 `{user.id}`\n📢 {chat.title}\n🕐 {now}",
                parse_mode="Markdown", reply_markup=btns)
        except:
            pass

    lang = context.user_data.get("lang", "en")
    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=ui("join_pending", lang),
            parse_mode="Markdown",
            protect_content=True)
    except:
        pass

# ══════════════════════════════════════════════════════════════
#  /start
# ══════════════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cid  = update.effective_chat.id

    referred_by = None
    if context.args and context.args[0].startswith("ref"):
        try:
            referred_by = int(context.args[0][3:])
            if referred_by == user.id:
                referred_by = None
        except:
            pass

    new_user = is_new_user(user.id)
    lang = context.user_data.get("lang", "en")
    register_user(user, referred_by=referred_by, lang=lang)

    if new_user:
        await notify_new_user(context, user)
        if referred_by:
            ref_count = get_referral_count(referred_by)
            if ref_count >= REFERRAL_MIN:
                ref_info = get_user_info(referred_by)
                for aid in ADMIN_IDS:
                    try:
                        await context.bot.send_message(
                            chat_id=aid,
                            text=f"🏆 *REFERRAL REWARD!*\n\n👤 {ref_info['name']} amefika {ref_count} referrals!\n🎁 Mpe zawadi!",
                            parse_mode="Markdown")
                    except:
                        pass

    # Delete all previous bot messages
    await delete_all_bot_msgs(context, cid)

    await typing_action(cid, context, 1.2)

    if not context.user_data.get("lang"):
        msg = await send_protected_text(
            context, cid,
            "🌍 *Welcome to EVALON WINNERS!*\n\nChoose your language / Chagua lugha yako:",
            lang_keyboard())
        context.user_data["last_bot_msg_id"] = msg.message_id
        track_msg(cid, msg.message_id)
        return

    if not await is_member(context, user.id):
        msg = await send_protected_text(
            context, cid, ui("join_msg", lang), join_keyboard(lang))
        context.user_data["last_bot_msg_id"] = msg.message_id
        track_msg(cid, msg.message_id)
        return

    if new_user:
        await typing_action(cid, context, 1.0)
        try:
            vid_msg = await context.bot.send_video(
                chat_id=cid, video=WELCOME_VIDEO,
                caption=ui("welcome_video", lang),
                parse_mode="Markdown",
                protect_content=True)
            track_msg(cid, vid_msg.message_id)
            await asyncio.sleep(4)
            await safe_delete(context, cid, vid_msg.message_id)
        except:
            pass

        await typing_action(cid, context, 1.0)
        poll_msg = await send_protected_text(
            context, cid, ui("poll_msg", lang), poll_keyboard(lang))
        context.user_data["last_bot_msg_id"] = poll_msg.message_id
        track_msg(cid, poll_msg.message_id)
        return

    urgency = get_urgency(lang)
    welcome_text = ui("welcome", lang).format(
        name=user.first_name, urgency=urgency, business=BUSINESS_NAME)

    msg = await send_protected_photo(
        context, cid, WELCOME_IMAGE, welcome_text, main_menu(lang))
    context.user_data["last_bot_msg_id"] = msg.message_id
    track_msg(cid, msg.message_id)
    schedule_comeback(context, cid, user.first_name, lang)
    schedule_auto_clean(context, cid, lang, user.first_name, user.id)

# ══════════════════════════════════════════════════════════════
#  BROADCAST
# ══════════════════════════════════════════════════════════════

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    all_users = get_all_user_ids()
    total = len(all_users)
    sent = failed = 0
    replied_msg = update.message.reply_to_message

    await update.message.reply_text(
        f"📢 Broadcasting to *{total}* users...", parse_mode="Markdown")

    for uid in all_users:
        try:
            u_info = get_user_info(uid)
            user_lang = u_info.get("lang", "en") or "en"

            if replied_msg and replied_msg.photo:
                # Photo/video — NO button
                await context.bot.send_photo(
                    chat_id=uid, photo=replied_msg.photo[-1].file_id,
                    caption=replied_msg.caption or "",
                    parse_mode="Markdown")
            elif replied_msg and replied_msg.video:
                # Video — NO button
                await context.bot.send_video(
                    chat_id=uid, video=replied_msg.video.file_id,
                    caption=replied_msg.caption or "",
                    parse_mode="Markdown")
            elif replied_msg and replied_msg.voice:
                await context.bot.send_voice(
                    chat_id=uid, voice=replied_msg.voice.file_id)
            elif replied_msg and replied_msg.document:
                await context.bot.send_document(
                    chat_id=uid, document=replied_msg.document.file_id,
                    caption=replied_msg.caption or "",
                    parse_mode="Markdown")
            elif replied_msg and replied_msg.text:
                # Text — WITH button
                await context.bot.send_message(
                    chat_id=uid, text=replied_msg.text,
                    parse_mode="Markdown",
                    reply_markup=broadcast_keyboard(user_lang))
            elif context.args:
                # Text command — WITH button
                await context.bot.send_message(
                    chat_id=uid, text=" ".join(context.args),
                    parse_mode="Markdown",
                    reply_markup=broadcast_keyboard(user_lang))
            else:
                await update.message.reply_text(
                    "⚠️ No content.\n\n• `/broadcast message`\n• Reply to media + `/broadcast`",
                    parse_mode="Markdown")
                return
            sent += 1
            await asyncio.sleep(0.05)
        except TelegramError as e:
            failed += 1
            logger.warning(f"Broadcast failed {uid}: {e}")

    await update.message.reply_text(
        f"✅ *Done!*\n\n📤 Sent: {sent}\n❌ Failed: {failed}\n👥 Total: {total}",
        parse_mode="Markdown")

# ══════════════════════════════════════════════════════════════
#  ADMIN COMMANDS
# ══════════════════════════════════════════════════════════════

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    total     = get_user_count()
    active7   = get_active_users(7)
    active30  = get_active_users(30)
    new_today = get_new_users_today()
    top = get_top_referrers(5)
    top_text = ""
    for i, (name, refs) in enumerate(top, 1):
        top_text += f"{i}. {name} — {refs} referrals\n"

    await update.message.reply_text(
        f"📊 *EVALON WINNERS — STATS*\n\n"
        f"👥 Total users: *{total}*\n"
        f"🆕 New today: *{new_today}*\n"
        f"🟢 Active 7d: *{active7}*\n"
        f"📅 Active 30d: *{active30}*\n"
        f"🆘 Active support: *{len(active_support)}*\n\n"
        f"🏆 *TOP REFERRERS (Real):*\n{top_text or 'None yet'}\n\n"
        f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        parse_mode="Markdown")

async def getid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    msg = update.message
    if msg.photo:
        await msg.reply_text(f"📸 `{msg.photo[-1].file_id}`", parse_mode="Markdown")
    elif msg.video:
        await msg.reply_text(f"🎥 `{msg.video.file_id}`", parse_mode="Markdown")
    elif msg.document:
        await msg.reply_text(f"📄 `{msg.document.file_id}`", parse_mode="Markdown")
    else:
        await msg.reply_text("Send me a photo/video to get file_id")

async def sessions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not active_support:
        await update.message.reply_text("✅ No active support sessions.")
        return
    text = f"🆘 *Active Sessions: {len(active_support)}*\n\n"
    kb = []
    for uid in list(active_support.keys()):
        u = get_user_info(uid)
        text += f"👤 {u['name']} | `{uid}`\n"
        kb.append([InlineKeyboardButton(
            f"🔴 End: {u['name'][:20]}", callback_data=f"dis:{uid}:en")])
    kb.append([InlineKeyboardButton("🔴 End ALL", callback_data="end_all_support")])
    await update.message.reply_text(
        text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

# ══════════════════════════════════════════════════════════════
#  CALLBACK HANDLER
# ══════════════════════════════════════════════════════════════

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user
    cid  = query.message.chat_id

    lang = get_lang(context)

    # Language select
    if data.startswith("lang_"):
        new_lang = data[5:]
        context.user_data["lang"] = new_lang
        register_user(user, lang=new_lang)
        # Delete ALL messages on language change
        await safe_delete(context, cid, query.message.message_id)
        await delete_all_bot_msgs(context, cid)
        await typing_action(cid, context, 1.5)

        if not await is_member(context, user.id):
            msg = await send_protected_text(
                context, cid, ui("join_msg", new_lang), join_keyboard(new_lang))
            context.user_data["last_bot_msg_id"] = msg.message_id
            track_msg(cid, msg.message_id)
            return

        urgency = get_urgency(new_lang)
        welcome_text = ui("welcome", new_lang).format(
            name=user.first_name, urgency=urgency, business=BUSINESS_NAME)
        msg = await send_protected_photo(
            context, cid, WELCOME_IMAGE, welcome_text, main_menu(new_lang))
        context.user_data["last_bot_msg_id"] = msg.message_id
        track_msg(cid, msg.message_id)
        schedule_comeback(context, cid, user.first_name, new_lang)
        schedule_auto_clean(context, cid, new_lang, user.first_name, user.id)
        return

    # Check join
    if data == "check_join":
        await typing_action(cid, context, 1.0)
        if await is_member(context, user.id):
            await safe_delete(context, cid, query.message.message_id)
            await delete_all_bot_msgs(context, cid)
            urgency = get_urgency(lang)
            welcome_text = ui("welcome", lang).format(
                name=user.first_name, urgency=urgency, business=BUSINESS_NAME)
            msg = await send_protected_photo(
                context, cid, WELCOME_IMAGE, welcome_text, main_menu(lang))
            context.user_data["last_bot_msg_id"] = msg.message_id
            track_msg(cid, msg.message_id)
        else:
            await query.answer("❌ Please join first!", show_alert=True)
        return

    # Poll
    if data.startswith("poll_"):
        await safe_delete(context, cid, query.message.message_id)
        await delete_all_bot_msgs(context, cid)
        await typing_action(cid, context, 1.0)
        urgency = get_urgency(lang)
        welcome_text = ui("welcome", lang).format(
            name=user.first_name, urgency=urgency, business=BUSINESS_NAME)
        msg = await send_protected_photo(
            context, cid, WELCOME_IMAGE,
            f"✅ Got it!\n\n{welcome_text}", main_menu(lang))
        context.user_data["last_bot_msg_id"] = msg.message_id
        track_msg(cid, msg.message_id)
        schedule_comeback(context, cid, user.first_name, lang)
        schedule_auto_clean(context, cid, lang, user.first_name, user.id)
        return

    # Rating
    if data.startswith("rate_"):
        stars = int(data[5:])
        star_display = "⭐" * stars
        await safe_delete(context, cid, query.message.message_id)
        await delete_all_bot_msgs(context, cid)
        await typing_action(cid, context, 1.0)
        for aid in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=aid,
                    text=f"⭐ *Rating*\n\n👤 {user.full_name}\n🆔 `{user.id}`\n{star_display} ({stars}/5)",
                    parse_mode="Markdown")
            except:
                pass
        urgency = get_urgency(lang)
        welcome_text = ui("welcome", lang).format(
            name=user.first_name, urgency=urgency, business=BUSINESS_NAME)
        msg = await send_protected_photo(
            context, cid, WELCOME_IMAGE,
            f"{ui('rating_thanks', lang).format(name=user.first_name)}\n\n{welcome_text}",
            main_menu(lang))
        context.user_data["last_bot_msg_id"] = msg.message_id
        track_msg(cid, msg.message_id)
        return

    # For all navigation buttons — delete previous and show new
    await safe_delete(context, cid, query.message.message_id)
    await delete_all_bot_msgs(context, cid)
    await typing_action(cid, context, 1.5)

    if data == "main_menu":
        urgency = get_urgency(lang)
        welcome_text = ui("welcome", lang).format(
            name=user.first_name, urgency=urgency, business=BUSINESS_NAME)
        msg = await send_protected_photo(
            context, cid, WELCOME_IMAGE, welcome_text, main_menu(lang))
        context.user_data["last_bot_msg_id"] = msg.message_id
        track_msg(cid, msg.message_id)
        schedule_comeback(context, cid, user.first_name, lang)
        schedule_auto_clean(context, cid, lang, user.first_name, user.id)

    elif data == "menu_services":
        msg = await send_protected_text(
            context, cid, ui("services_msg", lang), services_menu(lang))
        context.user_data["last_bot_msg_id"] = msg.message_id
        track_msg(cid, msg.message_id)

    elif data == "change_lang":
        msg = await send_protected_text(
            context, cid,
            "🌍 Choose your language / Chagua lugha:",
            lang_keyboard())
        context.user_data["last_bot_msg_id"] = msg.message_id
        track_msg(cid, msg.message_id)

    elif data == "svc_signals":
        replies = get_replies(SIGNALS_REPLIES, lang)
        img = rand_img(IMGS_SIGNALS, context.user_data, "last_img_signals")
        msg = await send_protected_photo(
            context, cid, img, random.choice(replies), svc_keyboard(lang))
        context.user_data["last_bot_msg_id"] = msg.message_id
        track_msg(cid, msg.message_id)

    elif data == "svc_social":
        replies = get_replies(SOCIAL_REPLIES, lang)
        img = rand_img(IMGS_SOCIAL, context.user_data, "last_img_social")
        msg = await send_protected_photo(
            context, cid, img, random.choice(replies), svc_keyboard(lang))
        context.user_data["last_bot_msg_id"] = msg.message_id
        track_msg(cid, msg.message_id)

    elif data == "svc_indicator":
        replies = get_replies(INDICATOR_REPLIES, lang)
        img = rand_img(IMGS_INDICATOR, context.user_data, "last_img_indicator")
        msg = await send_protected_photo(
            context, cid, img, random.choice(replies),
            svc_keyboard(lang, indicator=True))
        context.user_data["last_bot_msg_id"] = msg.message_id
        track_msg(cid, msg.message_id)

    elif data == "svc_autobot":
        replies = get_replies(AUTOBOT_REPLIES, lang)
        img = rand_img(IMGS_AUTOBOT, context.user_data, "last_img_autobot")
        msg = await send_protected_photo(
            context, cid, img, random.choice(replies), svc_keyboard(lang))
        context.user_data["last_bot_msg_id"] = msg.message_id
        track_msg(cid, msg.message_id)

    elif data == "svc_freebot":
        replies = get_replies(FREEBOT_REPLIES, lang)
        img = rand_img(IMGS_FREEBOT, context.user_data, "last_img_freebot")
        msg = await send_protected_photo(
            context, cid, img, random.choice(replies), freebot_menu(lang))
        context.user_data["last_bot_msg_id"] = msg.message_id
        track_msg(cid, msg.message_id)

    elif data == "do_support":
        await notify_support_request(context, user, lang)
        msg = await send_protected_text(
            context, cid, ui("support_msg", lang),
            InlineKeyboardMarkup([
                [InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")]
            ]))
        context.user_data["last_bot_msg_id"] = msg.message_id
        track_msg(cid, msg.message_id)

    elif data == "do_referral":
        ref_count = get_referral_count(user.id)
        needed = max(0, REFERRAL_MIN - ref_count)
        bar = make_progress_bar(ref_count, REFERRAL_MIN)
        leaderboard = get_fake_leaderboard(ref_count)
        ref_text = ui("referral_msg", lang).format(
            bot=BOT_USERNAME, uid=user.id,
            count=ref_count, min=REFERRAL_MIN,
            needed=needed, bar=bar,
            leaderboard=leaderboard)
        msg = await send_protected_text(
            context, cid, ref_text,
            InlineKeyboardMarkup([
                [InlineKeyboardButton(ui("btn_support", lang), callback_data="do_support")],
                [InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")],
            ]))
        context.user_data["last_bot_msg_id"] = msg.message_id
        track_msg(cid, msg.message_id)

    elif data == "do_stories":
        stories = [
            "⭐⭐⭐⭐⭐ *\"Made $340 in my first week!\"* — John K., Nigeria",
            "⭐⭐⭐⭐⭐ *\"Best signals ever. 9/10 wins today!\"* — Maria S., Brazil",
            "⭐⭐⭐⭐⭐ *\"Auto bot made $180 while I slept!\"* — Ahmed R., Egypt",
            "⭐⭐⭐⭐⭐ *\"Copy trading gave me +47% this month!\"* — Linda T., Kenya",
            "⭐⭐⭐⭐⭐ *\"Finally a bot that actually works!\"* — James O., Ghana",
        ]
        img = rand_img(SERVICE_PHOTOS, context.user_data, "last_img_stories")
        story_text = f"⭐ *SUCCESS STORIES*\n\n{random.choice(stories)}\n\n🔥 Join thousands of winning traders!"
        msg = await send_protected_photo(
            context, cid, img, story_text,
            InlineKeyboardMarkup([
                [InlineKeyboardButton(ui("btn_services", lang), callback_data="menu_services")],
                [InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")],
            ]))
        context.user_data["last_bot_msg_id"] = msg.message_id
        track_msg(cid, msg.message_id)

    # Admin: Connect
    elif data.startswith("con:"):
        parts = data.split(":")
        uid   = int(parts[1])
        ulang = parts[2] if len(parts) > 2 else "en"
        active_support[uid] = True
        try:
            await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🟢 Connected ✓", callback_data="noop"),
                InlineKeyboardButton("🔴 End Chat", callback_data=f"dis:{uid}:{ulang}"),
            ]]))
        except:
            pass
        try:
            msg = await context.bot.send_message(
                chat_id=uid,
                text="🟢 *You are now connected to our support team!*\n\nPlease describe your issue. 💬",
                parse_mode="Markdown",
                protect_content=True)
            track_support_msg(uid, msg.message_id)
        except:
            pass

    # Admin: Disconnect — delete all support messages
    elif data.startswith("dis:"):
        parts = data.split(":")
        uid   = int(parts[1])
        ulang = parts[2] if len(parts) > 2 else "en"
        active_support.pop(uid, None)
        try:
            await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🟢 Connect", callback_data=f"con:{uid}:{ulang}"),
                InlineKeyboardButton("🔴 Ended ✓", callback_data="noop"),
            ]]))
        except:
            pass

        # Delete ALL support messages from both sides
        await delete_support_msgs(context, uid)

        try:
            # Send session ended message
            msg = await context.bot.send_message(
                chat_id=uid,
                text=ui("session_ended", ulang),
                parse_mode="Markdown",
                protect_content=True,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        ui("btn_support", ulang), callback_data="do_support")
                ]]))
            track_msg(uid, msg.message_id)
            await asyncio.sleep(2)
            # Send rating
            rating_msg = await context.bot.send_message(
                chat_id=uid,
                text=ui("rating_msg", ulang),
                parse_mode="Markdown",
                protect_content=True,
                reply_markup=rating_keyboard())
            track_msg(uid, rating_msg.message_id)
        except:
            pass

    elif data == "end_all_support":
        count = len(active_support)
        uids = list(active_support.keys())
        active_support.clear()
        for uid in uids:
            await delete_support_msgs(context, uid)
        await query.message.reply_text(
            f"✅ Ended all *{count}* sessions.", parse_mode="Markdown")

    elif data.startswith("approve_"):
        uid = int(data[8:])
        req = pending_requests.get(uid)
        if req:
            try:
                await context.bot.approve_chat_join_request(
                    chat_id=req["chat_id"], user_id=uid)
                pending_requests.pop(uid, None)
                await query.message.edit_text(
                    f"✅ *Approved!*\n👤 {req['user'].full_name}",
                    parse_mode="Markdown")
                try:
                    await context.bot.send_message(
                        chat_id=uid,
                        text="🎉 You have been *approved!* Welcome! 🚀",
                        parse_mode="Markdown",
                        protect_content=True)
                except:
                    pass
            except TelegramError as e:
                await query.message.reply_text(f"❌ Error: {e}")
        else:
            await query.answer("⚠️ Request not found.", show_alert=True)

    elif data.startswith("decline_"):
        uid = int(data[8:])
        req = pending_requests.get(uid)
        if req:
            try:
                await context.bot.decline_chat_join_request(
                    chat_id=req["chat_id"], user_id=uid)
                pending_requests.pop(uid, None)
                await query.message.edit_text("❌ *Declined.*", parse_mode="Markdown")
            except TelegramError as e:
                await query.message.reply_text(f"❌ Error: {e}")
        else:
            await query.answer("⚠️ Request not found.", show_alert=True)

    elif data == "noop":
        pass

# ══════════════════════════════════════════════════════════════
#  TWO-WAY MESSAGING
# ══════════════════════════════════════════════════════════════

async def forward_to_admin(context, user, message):
    """Forward to admin ONLY if user is in active support session"""
    if not active_support.get(user.id):
        return

    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    header = (
        f"💬 *Message from user*\n"
        f"👤 {user.full_name} | @{user.username or 'N/A'}\n"
        f"🆔 `{user.id}` | 🕐 {now}\n"
        f"_(Reply to respond)_"
    )
    for aid in ADMIN_IDS:
        try:
            hdr = await context.bot.send_message(
                chat_id=aid, text=header, parse_mode="Markdown")
            fwd = await context.bot.forward_message(
                chat_id=aid, from_chat_id=message.chat_id,
                message_id=message.message_id)
            reply_map[fwd.message_id] = user.id
            reply_map[hdr.message_id] = user.id
        except Exception as e:
            logger.warning(f"Forward failed: {e}")

async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    replied = message.reply_to_message
    if not replied:
        return
    target_uid = reply_map.get(replied.message_id)
    if not target_uid:
        return
    try:
        await context.bot.send_chat_action(
            chat_id=target_uid, action=ChatAction.TYPING)
        await asyncio.sleep(1.5)
        if message.photo:
            sent = await context.bot.send_photo(
                chat_id=target_uid, photo=message.photo[-1].file_id,
                caption=message.caption or "",
                parse_mode="Markdown",
                protect_content=True)
        elif message.video:
            sent = await context.bot.send_video(
                chat_id=target_uid, video=message.video.file_id,
                caption=message.caption or "",
                parse_mode="Markdown",
                protect_content=True)
        elif message.voice:
            sent = await context.bot.send_voice(
                chat_id=target_uid, voice=message.voice.file_id,
                protect_content=True)
        elif message.document:
            sent = await context.bot.send_document(
                chat_id=target_uid, document=message.document.file_id,
                caption=message.caption or "",
                parse_mode="Markdown",
                protect_content=True)
        elif message.sticker:
            sent = await context.bot.send_sticker(
                chat_id=target_uid, sticker=message.sticker.file_id)
        elif message.text:
            sent = await context.bot.send_message(
                chat_id=target_uid, text=message.text,
                parse_mode="Markdown",
                protect_content=True)
        else:
            return
        # Track support message for later deletion
        track_support_msg(target_uid, sent.message_id)
        await message.reply_text("✅ Delivered!")
    except Exception as e:
        await message.reply_text(f"❌ Failed: {e}")

# ══════════════════════════════════════════════════════════════
#  MAIN MESSAGE HANDLER
# ══════════════════════════════════════════════════════════════

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return
    user = message.from_user
    lang = get_lang(context)
    cid  = message.chat_id

    # Admin handler
    if is_admin(user.id):
        if message.reply_to_message:
            target = reply_map.get(message.reply_to_message.message_id)
            if target:
                await handle_admin_reply(update, context)
                return
        if message.photo and not message.reply_to_message:
            await message.reply_text(
                f"📸 `{message.photo[-1].file_id}`", parse_mode="Markdown")
            return
        if message.video and not message.reply_to_message:
            await message.reply_text(
                f"🎥 `{message.video.file_id}`", parse_mode="Markdown")
            return
        return

    register_user(user, lang=lang)

    # Delete user message (melt effect)
    await delete_user_msg(message)

    # Active support session — forward to admin, DON'T delete user messages
    if active_support.get(user.id):
        # Track user message id in support_msg_ids
        track_support_msg(cid, message.message_id)
        await forward_to_admin(context, user, message)
        return

    # Media from non-support users
    if message.photo or message.video or message.voice or message.document or message.sticker:
        await typing_action(cid, context, 1.0)
        await delete_all_bot_msgs(context, cid)
        msg = await send_protected_text(
            context, cid, ui("msg_received", lang), support_keyboard(lang))
        context.user_data["last_bot_msg_id"] = msg.message_id
        track_msg(cid, msg.message_id)
        return

    if not message.text:
        return

    text = message.text.strip()
    low  = text.lower()

    await typing_action(cid, context, 1.8)
    await delete_all_bot_msgs(context, cid)

    async def reply_with_photo(img, caption, keyboard):
        m = await send_protected_photo(context, cid, img, caption, keyboard)
        context.user_data["last_bot_msg_id"] = m.message_id
        track_msg(cid, m.message_id)

    async def reply_with_text(text_content, keyboard):
        m = await send_protected_text(context, cid, text_content, keyboard)
        context.user_data["last_bot_msg_id"] = m.message_id
        track_msg(cid, m.message_id)

    # Keyword routing
    if any(w in low for w in [
        "hi","hello","hey","hujambo","habari","salaam","bonjour","hola",
        "привет","مرحبا","नमस्ते","niaje","mambo","wassup","ciao","你好"
    ]) and not any(w in low for w in [
        "signal","vip","pocket","social","copy","indicator","auto","bot",
        "support","help","price","referral","free bot","manual"
    ]):
        urgency = get_urgency(lang)
        welcome_text = ui("welcome", lang).format(
            name=user.first_name, urgency=urgency, business=BUSINESS_NAME)
        await reply_with_photo(WELCOME_IMAGE, welcome_text, main_menu(lang))

    elif any(w in low for w in [
        "signal","signals","vip","alert","ishara","forex signal","win rate","binary signal"
    ]):
        img = rand_img(IMGS_SIGNALS, context.user_data, "last_img_signals")
        await reply_with_photo(img, random.choice(get_replies(SIGNALS_REPLIES, lang)), svc_keyboard(lang))

    elif any(w in low for w in [
        "social","copy","pocket","copy trade","copy trading","nakili"
    ]):
        img = rand_img(IMGS_SOCIAL, context.user_data, "last_img_social")
        await reply_with_photo(img, random.choice(get_replies(SOCIAL_REPLIES, lang)), svc_keyboard(lang))

    elif any(w in low for w in [
        "indicator","chart","mt4","mt5","free indicator","kiashiria","arrow","technical"
    ]):
        img = rand_img(IMGS_INDICATOR, context.user_data, "last_img_indicator")
        await reply_with_photo(img, random.choice(get_replies(INDICATOR_REPLIES, lang)),
                               svc_keyboard(lang, indicator=True))

    elif any(w in low for w in [
        "free bot","manual bot","freebot","bot ya bure","free manual"
    ]):
        img = rand_img(IMGS_FREEBOT, context.user_data, "last_img_freebot")
        await reply_with_photo(img, random.choice(get_replies(FREEBOT_REPLIES, lang)), freebot_menu(lang))

    elif any(w in low for w in [
        "auto","robot","automatic","autobot","trading bot",
        "quotex","deriv","olymp","binomo","iq option","broker","leseni"
    ]):
        img = rand_img(IMGS_AUTOBOT, context.user_data, "last_img_autobot")
        await reply_with_photo(img, random.choice(get_replies(AUTOBOT_REPLIES, lang)), svc_keyboard(lang))

    elif any(w in low for w in [
        "referral","refer","invite","earn","reward","kiungo","zawadi","alika"
    ]):
        ref_count = get_referral_count(user.id)
        needed = max(0, REFERRAL_MIN - ref_count)
        bar = make_progress_bar(ref_count, REFERRAL_MIN)
        leaderboard = get_fake_leaderboard(ref_count)
        ref_text = ui("referral_msg", lang).format(
            bot=BOT_USERNAME, uid=user.id,
            count=ref_count, min=REFERRAL_MIN,
            needed=needed, bar=bar, leaderboard=leaderboard)
        await reply_with_text(ref_text, InlineKeyboardMarkup([
            [InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")]
        ]))

    elif any(w in low for w in [
        "price","cost","bei","pesa","pay","payment","subscribe","plan","nunua","ngapi"
    ]):
        await reply_with_text(ui("price_msg", lang), InlineKeyboardMarkup([
            [InlineKeyboardButton(ui("btn_website", lang), url=WEBSITE_URL)],
            [InlineKeyboardButton(ui("btn_support", lang), callback_data="do_support")],
            [InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")],
        ]))

    elif any(w in low for w in [
        "support","help","assist","contact","agent","admin","msaada","wasiliana"
    ]):
        await notify_support_request(context, user, lang)
        await reply_with_text(ui("support_msg", lang), InlineKeyboardMarkup([
            [InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")]
        ]))

    elif any(w in low for w in [
        "thank","thanks","asante","merci","gracias","спасибо","شكرا","danke"
    ]):
        await reply_with_text(
            f"😊 Thank you, *{user.first_name}!* Always here for you. 🚀",
            InlineKeyboardMarkup([
                [InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")]
            ]))

    else:
        await reply_with_text(ui("fallback_msg", lang), support_keyboard(lang))

# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════

def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("getid", getid_command))
    app.add_handler(CommandHandler("sessions", sessions_command))
    app.add_handler(ChatJoinRequestHandler(handle_join_request))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    print(f"✅ {BUSINESS_NAME} Bot v6.2 is LIVE!")
    print("📋 Commands: /broadcast  /stats  /getid  /sessions")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
