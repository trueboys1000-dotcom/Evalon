"""
╔══════════════════════════════════════════════════════════════╗
║         EVALON WINNERS — TELEGRAM SUPPORT BOT v7.0          ║
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
║  ✅ Rating after support + free text opinion                 ║
║  ✅ Comeback message week 2                                  ║
║  ✅ Poll for new users                                       ║
║  ✅ Free Manual Bot section                                  ║
║  ✅ Broadcast button on text only                            ║
║  ✅ Protect content (no forward/save)                        ║
║  ✅ PostgreSQL database                                      ║
║  ✅ 12 languages (ALL translated properly)                   ║
║  ✅ FIXED: Markdown parse errors (escape_md everywhere)      ║
║  ✅ FIXED: Forward → Copy (no more "message not found")      ║
║  ✅ FIXED: Conflict error (drop_pending_updates)             ║
║  ✅ FIXED: Support messages arrive correctly                 ║
║  ✅ FIXED: Lang loaded from DB on restart                    ║
║  ✅ FIXED: Referral progress bar backtick crash              ║
║  ✅ FIXED: Referral message markdown crash                   ║
║  ✅ FIXED: Session ended — no Contact Support button         ║
║  ✅ FIXED: Rating collects text opinion from user            ║
║  ✅ FIXED: All 12 languages reply in correct language        ║
║  ✅ FIXED: MarkdownV2 vs Markdown inconsistency              ║
║  ✅ FIXED: editMessageReplyMarkup on deleted messages        ║
║  ✅ NEW: Spin Wheel — 1x/day, 5% win chance, admin notify   ║
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
VIP_BOT_LINK      = "https://t.me/Kentehsharevvipbot"
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
    "pocket":      "BAACAgQAAxkBAAIEaGoK58L-fS3J05qVoD12215hKSpsAAKoHwAC-y5RUMiA8M6DOMlkOwQ",
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
bot_msg_ids: dict      = {}
support_msg_ids: dict  = {}
# FIX: Track users waiting to give rating text opinion
awaiting_rating_opinion: dict = {}  # uid -> star_count

# SPIN WHEEL: last spin date stored in DB (see spin_db functions below)

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
#  MARKDOWN ESCAPE — FIXED: handles all special chars
# ══════════════════════════════════════════════════════════════

def escape_md(text):
    """Escape ALL Markdown special characters to prevent parse errors"""
    if not text:
        return ""
    # Order matters — escape backslash first
    chars = ['\\', '_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for c in chars:
        text = text.replace(c, f'\\{c}')
    return text

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
    c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS onboarding_done BOOLEAN DEFAULT FALSE")
    c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS badges TEXT DEFAULT ''")
    c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS streak INTEGER DEFAULT 0")
    c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS quiz_score INTEGER DEFAULT 0")
    c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS goal TEXT DEFAULT NULL")
    c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS goal_date TEXT DEFAULT NULL")
    c.execute("""
        CREATE TABLE IF NOT EXISTS results_history (
            id          SERIAL PRIMARY KEY,
            caption     TEXT DEFAULT NULL,
            media_id    TEXT DEFAULT NULL,
            media_type  TEXT DEFAULT NULL,
            saved_at    TEXT DEFAULT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS stories (
            id         SERIAL PRIMARY KEY,
            caption    TEXT DEFAULT NULL,
            media_id   TEXT DEFAULT NULL,
            media_type TEXT DEFAULT 'text',
            created_at TEXT DEFAULT NULL
        )
    """)
    conn.commit()
    conn.close()
    init_spin_db()
    init_dynamic_db()
    init_feedback_db()
    init_media_db()
    # Load admin-added photos into runtime pool
    try:
        admin_photos = get_admin_photos()
        for fid in admin_photos:
            if fid not in SERVICE_PHOTOS:
                SERVICE_PHOTOS.append(fid)
        if admin_photos:
            logger.info(f"Loaded {len(admin_photos)} admin photos into pool")
    except Exception as e:
        logger.warning(f"Could not load admin photos: {e}")

def has_done_onboarding(uid):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT onboarding_done FROM users WHERE id=%s", (uid,))
    row = c.fetchone()
    conn.close()
    return row and row[0]

def mark_onboarding_done(uid):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET onboarding_done=TRUE WHERE id=%s", (uid,))
    conn.commit()
    conn.close()

def get_referred_users(uid):
    """Get list of users referred by this uid"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT name, joined FROM users WHERE referred_by=%s ORDER BY joined DESC", (uid,))
    rows = c.fetchall()
    conn.close()
    return rows

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
#  DYNAMIC CONTENT — Admin sets news/VIP content via commands
# ══════════════════════════════════════════════════════════════

def init_dynamic_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS dynamic_content (
            key         TEXT PRIMARY KEY,
            text_value  TEXT DEFAULT NULL,
            file_id     TEXT DEFAULT NULL,
            file_type   TEXT DEFAULT NULL,
            updated_at  TEXT DEFAULT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS streak_log (
            user_id     BIGINT PRIMARY KEY,
            last_visit  TEXT DEFAULT NULL,
            streak      INTEGER DEFAULT 1,
            max_streak  INTEGER DEFAULT 1
        )
    """)
    conn.commit()
    conn.close()

def set_dynamic_content(key, text_value=None, file_id=None, file_type=None):
    conn = get_conn()
    c = conn.cursor()
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    c.execute("""
        INSERT INTO dynamic_content (key, text_value, file_id, file_type, updated_at)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (key) DO UPDATE
        SET text_value=EXCLUDED.text_value,
            file_id=EXCLUDED.file_id,
            file_type=EXCLUDED.file_type,
            updated_at=EXCLUDED.updated_at
    """, (key, text_value, file_id, file_type, now))
    conn.commit()
    conn.close()

def get_dynamic_content(key):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT text_value, file_id, file_type, updated_at FROM dynamic_content WHERE key=%s", (key,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"text": row[0], "file_id": row[1], "file_type": row[2], "updated_at": row[3]}
    return None

def update_streak(uid):
    """Update daily streak for user — returns (streak, is_new_record)"""
    from datetime import timedelta
    conn = get_conn()
    c = conn.cursor()
    today = datetime.now().strftime("%d/%m/%Y")
    c.execute("SELECT last_visit, streak, max_streak FROM streak_log WHERE user_id=%s", (uid,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO streak_log (user_id, last_visit, streak, max_streak) VALUES (%s,%s,1,1)",
                  (uid, today))
        conn.commit()
        conn.close()
        return 1, True
    last_visit, streak, max_streak = row
    try:
        last_dt = datetime.strptime(last_visit, "%d/%m/%Y")
        today_dt = datetime.strptime(today, "%d/%m/%Y")
        diff = (today_dt - last_dt).days
        if diff == 0:
            conn.close()
            return streak, False  # Already visited today
        elif diff == 1:
            streak += 1  # Consecutive day
        else:
            streak = 1  # Streak broken
    except:
        streak = 1
    new_max = max(streak, max_streak)
    is_new_record = streak > max_streak
    c.execute("""
        UPDATE streak_log SET last_visit=%s, streak=%s, max_streak=%s WHERE user_id=%s
    """, (today, streak, new_max, uid))
    conn.commit()
    conn.close()
    return streak, is_new_record

def get_streak(uid):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT streak, max_streak FROM streak_log WHERE user_id=%s", (uid,))
    row = c.fetchone()
    conn.close()
    return (row[0], row[1]) if row else (0, 0)

# ── FAKE WINNERS DATA ──────────────────────────────────────────
# Majina yanabadilika kila wiki — hayarudii nafasi 1 mara mbili

# (name, flag, base_invites, weekly_growth)  — 120 names, no repeats for 3+ months
REFERRAL_LEADER_POOL = [
    ("James K.", "🇳🇬", 23, 8), ("Maria S.", "🇧🇷", 31, 6), ("Ahmed R.", "🇪🇬", 18, 9),
    ("Linda T.", "🇰🇪", 27, 7), ("Carlos M.", "🇲🇽", 34, 5), ("Priya K.", "🇮🇳", 19, 10),
    ("Ivan P.", "🇷🇺", 41, 4), ("Fatima A.", "🇲🇦", 16, 11), ("David L.", "🇬🇭", 29, 7),
    ("Sarah W.", "🇿🇦", 22, 8), ("Omar H.", "🇸🇦", 37, 6), ("Ana C.", "🇨🇴", 14, 12),
    ("Michael B.", "🇺🇬", 26, 7), ("Yuki T.", "🇯🇵", 33, 5), ("Hassan M.", "🇹🇿", 20, 9),
    ("Elena V.", "🇺🇦", 28, 8), ("John K.", "🇳🇬", 15, 11), ("Amina D.", "🇸🇳", 39, 5),
    ("Peter N.", "🇿🇼", 24, 8), ("Sofia R.", "🇦🇷", 17, 10), ("Ali H.", "🇵🇰", 32, 6),
    ("Grace A.", "🇨🇲", 21, 9), ("Lucas F.", "🇵🇹", 43, 4), ("Zara M.", "🇲🇾", 25, 8),
    ("Emmanuel O.", "🇨🇮", 30, 7), ("Natalia K.", "🇵🇱", 13, 12), ("Kwame A.", "🇬🇭", 38, 5),
    ("Isabella L.", "🇧🇷", 22, 9), ("Tariq B.", "🇯🇴", 35, 6), ("Mercy W.", "🇰🇪", 19, 10),
    ("Paulo S.", "🇧🇷", 44, 4), ("Nadia F.", "🇩🇿", 28, 7), ("Kevin O.", "🇳🇬", 16, 11),
    ("Yara M.", "🇱🇧", 33, 6), ("Felix K.", "🇩🇪", 21, 9), ("Aisha B.", "🇹🇳", 40, 5),
    ("Marco R.", "🇮🇹", 17, 10), ("Chloe D.", "🇫🇷", 26, 8), ("Ravi S.", "🇮🇳", 36, 6),
    ("Oluwaseun A.", "🇳🇬", 23, 8), ("Mia C.", "🇵🇭", 14, 12), ("Pedro A.", "🇲🇿", 31, 7),
    ("Leila N.", "🇮🇷", 20, 9), ("Victor T.", "🇷🇴", 42, 4), ("Jasmine O.", "🇯🇲", 18, 10),
    ("Hamid R.", "🇦🇫", 29, 7), ("Bianca M.", "🇧🇷", 37, 5), ("Daniel K.", "🇰🇷", 24, 8),
    ("Amara D.", "🇬🇳", 15, 11), ("Theo V.", "🇧🇪", 34, 6), ("Sana M.", "🇧🇩", 22, 9),
    ("Emeka C.", "🇳🇬", 41, 4), ("Layla H.", "🇸🇾", 27, 8), ("Ricardo F.", "🇵🇪", 19, 10),
    ("Adaeze N.", "🇳🇬", 33, 6), ("Sergei L.", "🇷🇺", 25, 8), ("Fatou D.", "🇸🇳", 16, 11),
    ("Hiroshi T.", "🇯🇵", 38, 5), ("Chisom E.", "🇳🇬", 21, 9), ("Ana M.", "🇵🇹", 30, 7),
    ("Bongani D.", "🇿🇦", 44, 4), ("Nour A.", "🇪🇬", 17, 10), ("Max S.", "🇩🇪", 28, 8),
    ("Precious U.", "🇳🇬", 35, 6), ("Clara B.", "🇫🇷", 23, 8), ("Amir H.", "🇮🇷", 13, 12),
    ("Tunde A.", "🇳🇬", 39, 5), ("Valentina R.", "🇨🇴", 26, 7), ("Yusuf M.", "🇸🇴", 32, 6),
    ("Blessing C.", "🇳🇬", 20, 9), ("Nikolai V.", "🇷🇺", 43, 4), ("Siti R.", "🇮🇩", 18, 10),
    ("Gabriel S.", "🇦🇴", 29, 7), ("Mariam K.", "🇲🇱", 36, 6), ("Diego L.", "🇻🇪", 24, 8),
    ("Patience A.", "🇬🇭", 15, 11), ("Reza M.", "🇮🇷", 40, 5), ("Lucia F.", "🇪🇸", 22, 9),
    ("Chukwu N.", "🇳🇬", 33, 6), ("Oksana P.", "🇺🇦", 27, 8), ("Omar S.", "🇸🇩", 19, 10),
    ("Miriam A.", "🇹🇿", 37, 5), ("Julian M.", "🇦🇷", 25, 8), ("Habiba M.", "🇩🇿", 14, 12),
    ("Samuel O.", "🇨🇲", 41, 4), ("Wanjiru G.", "🇰🇪", 28, 7), ("Andre P.", "🇧🇷", 35, 6),
    ("Nkechi E.", "🇳🇬", 21, 9), ("Tamar K.", "🇮🇱", 30, 7), ("Dawit T.", "🇪🇹", 16, 11),
    ("Rosa M.", "🇲🇽", 44, 4), ("Femi O.", "🇳🇬", 23, 8), ("Kiri W.", "🇳🇿", 38, 5),
    ("Bashir A.", "🇸🇴", 17, 10), ("Camille D.", "🇫🇷", 26, 8), ("Obinna C.", "🇳🇬", 34, 6),
    ("Tsega H.", "🇪🇹", 20, 9), ("Arjun P.", "🇮🇳", 42, 4), ("Salma B.", "🇲🇦", 29, 7),
    ("Festus A.", "🇳🇬", 15, 11), ("Elena M.", "🇬🇷", 36, 6), ("Ifeoma N.", "🇳🇬", 24, 8),
    ("Sergey K.", "🇰🇿", 33, 6), ("Zainab M.", "🇵🇰", 18, 10), ("Rodrigo F.", "🇧🇷", 40, 5),
    ("Chidinma O.", "🇳🇬", 22, 9), ("Mateus S.", "🇧🇷", 27, 7), ("Karim B.", "🇩🇿", 13, 12),
    ("Ngozi A.", "🇳🇬", 39, 5), ("Tomas H.", "🇨🇿", 25, 8), ("Ama O.", "🇬🇭", 31, 6),
    ("Yosef A.", "🇪🇹", 19, 10), ("Beatriz C.", "🇵🇹", 43, 4), ("Ifeanyi N.", "🇳🇬", 28, 7),
]

def get_referral_leaderboard_daily():
    """Weekly referral leaderboard — changes every Monday, counts grow week by week"""
    now = datetime.now()
    week_num = now.isocalendar()[1]   # 1-52
    year = now.year
    seed = year * 100 + week_num
    rng = random.Random(seed)

    pool = list(enumerate(REFERRAL_LEADER_POOL))
    rng.shuffle(pool)
    top5 = pool[:5]

    # Counts grow week by week — same name always higher than previous appearance
    result = []
    for orig_idx, (name, flag, base, growth) in top5:
        count = base + (week_num * growth) + rng.randint(0, 3)
        result.append((name, flag, count))

    result.sort(key=lambda x: x[2], reverse=True)
    return result

# Keep old names for backward compat
FAKE_WINNER_NAMES = [(n, f) for n, f, *_ in REFERRAL_LEADER_POOL]
FAKE_AMOUNTS = [173000, 142500, 98750, 215300, 87600, 164200, 119800, 203400,
                91200, 178900, 134600, 256100, 76400, 189300, 112700, 147800]

def get_fake_weekly_winners():
    """Generate consistent weekly winners — changes every Monday, no repeat at #1"""
    from datetime import timedelta
    # Get current week number for consistency
    week_num = datetime.now().isocalendar()[1]
    year = datetime.now().year
    seed = year * 100 + week_num

    rng = random.Random(seed)
    # Shuffle names with this week's seed
    names = FAKE_WINNER_NAMES.copy()
    rng.shuffle(names)
    amounts = FAKE_AMOUNTS.copy()
    rng.shuffle(amounts)

    winners = []
    for i in range(5):
        name, country = names[i]
        amount = sorted(amounts[:5], reverse=True)[i]
        winners.append((name, country, amount))
    return winners

# Streak badge levels
STREAK_BADGES = [
    (1,   "🌱", "Newcomer"),
    (3,   "🔥", "On Fire"),
    (7,   "⚡", "Weekly Warrior"),
    (14,  "💎", "Diamond Trader"),
    (30,  "👑", "VIP Legend"),
    (60,  "🏆", "Trading Champion"),
    (100, "🌟", "Elite Master"),
]

def get_streak_badge(streak):
    badge_emoji = "🌱"
    badge_name  = "Newcomer"
    for days, emoji, name in STREAK_BADGES:
        if streak >= days:
            badge_emoji = emoji
            badge_name  = name
    return badge_emoji, badge_name

def get_next_badge(streak):
    for days, emoji, name in STREAK_BADGES:
        if streak < days:
            return days, emoji, name
    return None, "🌟", "Elite Master"

def init_spin_db():
    """Create spin_log table if not exists"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS spin_log (
            user_id     BIGINT PRIMARY KEY,
            last_spin   TEXT DEFAULT NULL,
            total_spins INTEGER DEFAULT 0,
            user_name   TEXT DEFAULT NULL,
            username    TEXT DEFAULT NULL
        )
    """)
    c.execute("ALTER TABLE spin_log ADD COLUMN IF NOT EXISTS user_name TEXT DEFAULT NULL")
    c.execute("ALTER TABLE spin_log ADD COLUMN IF NOT EXISTS username TEXT DEFAULT NULL")
    conn.commit()
    conn.close()

def get_top_spinners(limit=10):
    """Get users who spin most often — for admin to pick winners"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT user_id, user_name, username, total_spins, last_spin
        FROM spin_log
        ORDER BY total_spins DESC
        LIMIT %s
    """, (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

def can_spin_today(uid):
    """Returns True if user has not spun in the last 20 hours"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT last_spin FROM spin_log WHERE user_id=%s", (uid,))
    row = c.fetchone()
    conn.close()
    if not row or not row[0]:
        return True
    try:
        last = datetime.strptime(row[0], "%d/%m/%Y %H:%M")
        from datetime import timedelta
        return (datetime.now() - last) >= timedelta(hours=20)
    except:
        return True

def record_spin(uid, user_name="", username=""):
    """Record spin timestamp for user"""
    conn = get_conn()
    c = conn.cursor()
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    c.execute("""
        INSERT INTO spin_log (user_id, last_spin, total_spins, user_name, username)
        VALUES (%s, %s, 1, %s, %s)
        ON CONFLICT (user_id) DO UPDATE
        SET last_spin=EXCLUDED.last_spin,
            total_spins=spin_log.total_spins+1,
            user_name=EXCLUDED.user_name,
            username=EXCLUDED.username
    """, (uid, now, user_name, username))
    conn.commit()
    conn.close()

def get_next_spin_time(uid):
    """Returns hours and minutes until user can spin again (20h cooldown)"""
    from datetime import timedelta
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT last_spin FROM spin_log WHERE user_id=%s", (uid,))
    row = c.fetchone()
    conn.close()
    if not row or not row[0]:
        return 0, 0
    try:
        last = datetime.strptime(row[0], "%d/%m/%Y %H:%M")
        next_spin = last + timedelta(hours=20)
        diff = next_spin - datetime.now()
        if diff.total_seconds() <= 0:
            return 0, 0
        total_secs = int(diff.total_seconds())
        hours = total_secs // 3600
        mins  = (total_secs % 3600) // 60
        return hours, mins
    except:
        return 0, 0

# ── SPIN WHEEL PRIZES ──────────────────────────────────────────
# NO automatic wins — admin picks winners manually via /spinners
# All results look exciting to keep users engaged and coming back
#
# Result types (all is_win=False):
#   almost_won  = 35% — "So close! Almost!"
#   try_again   = 35% — "Not this time!"
#   better_luck = 30% — "Better luck tomorrow!"

SPIN_PRIZES = [
    # (weight, prize_key, emoji, is_win)
    (35, "almost_won",   "🎯", False),
    (35, "try_again",    "🔄", False),
    (30, "better_luck",  "💪", False),
]

def do_spin():
    """Run weighted random spin — always returns lose result.
    Admin manually selects winners via /spinners command."""
    weights = [p[0] for p in SPIN_PRIZES]
    chosen  = random.choices(SPIN_PRIZES, weights=weights, k=1)[0]
    return chosen[1], chosen[2], chosen[3]

def get_prize_text(prize_key, lang):
    """Exciting encouraging messages — no wins, keeps users coming back"""
    lose_texts = {
        "almost_won": {
            "en": "🎯 *HONGERA! You almost won!* 🎉\n\nYour chance to win a *FREE service* is very close!\n\n🔥 Keep coming back every day — active daily players get personally selected by our team for FREE access!\n\n💎 Don't give up — your winning spin could be tomorrow!",
            "sw": "🎯 *HONGERA! Ulikaribia kushinda!* 🎉\n\nNafasi yako ya kupata *huduma BURE* ipo karibu sana!\n\n🔥 Endelea kurudi kila siku — wachezaji wanaoshiriki kila siku huchaguliwa kibinafsi na timu yetu kupata ufikiaji BURE!\n\n💎 Usichoke — spin yako ya kushinda inaweza kuwa kesho!",
            "ar": "🎯 *تهانينا! كدت تفوز!* 🎉\n\nفرصتك للفوز بـ *خدمة مجانية* قريبة جداً!\n\n🔥 استمر في العودة كل يوم — يتم اختيار اللاعبين النشطين شخصياً من قِبل فريقنا للحصول على وصول مجاني!\n\n💎 لا تستسلم — دورتك الفائزة قد تكون غداً!",
            "zh": "🎯 *恭喜！差点赢了！* 🎉\n\n您赢得*免费服务*的机会非常接近！\n\n🔥 每天继续回来——每天活跃的玩家由我们的团队亲自选择获得免费访问！\n\n💎 不要放弃——您的获奖旋转可能就是明天！",
            "hi": "🎯 *बधाई हो! लगभग जीत गए!* 🎉\n\n*मुफ्त सेवा* जीतने का आपका मौका बहुत करीब है!\n\n🔥 हर दिन वापस आते रहें — रोज सक्रिय खिलाड़ियों को हमारी टीम द्वारा व्यक्तिगत रूप से मुफ्त एक्सेस के लिए चुना जाता है!\n\n💎 हार मत मानिए — आपकी विजयी स्पिन कल हो सकती है!",
            "ru": "🎯 *ПОЗДРАВЛЯЕМ! Почти выиграли!* 🎉\n\nВаш шанс выиграть *БЕСПЛАТНУЮ услугу* очень близок!\n\n🔥 Возвращайтесь каждый день — активных игроков лично выбирает наша команда для бесплатного доступа!\n\n💎 Не сдавайтесь — ваш выигрышный спин может быть завтра!",
            "es": "🎯 *¡FELICITACIONES! ¡Casi ganaste!* 🎉\n\n¡Tu oportunidad de ganar un *servicio GRATIS* está muy cerca!\n\n🔥 ¡Sigue volviendo cada día — los jugadores activos diariamente son seleccionados personalmente por nuestro equipo para acceso GRATUITO!\n\n💎 ¡No te rindas — tu giro ganador podría ser mañana!",
            "fr": "🎯 *FÉLICITATIONS! Presque gagné!* 🎉\n\nVotre chance de gagner un *service GRATUIT* est très proche!\n\n🔥 Continuez à revenir chaque jour — les joueurs actifs quotidiens sont sélectionnés personnellement par notre équipe pour un accès GRATUIT!\n\n💎 Ne lâchez pas — votre spin gagnant pourrait être demain!",
            "pt": "🎯 *PARABÉNS! Quase ganhou!* 🎉\n\nSua chance de ganhar um *serviço GRÁTIS* está muito próxima!\n\n🔥 Continue voltando todos os dias — jogadores ativos diariamente são selecionados pessoalmente pela nossa equipe para acesso GRATUITO!\n\n💎 Não desista — seu giro vencedor pode ser amanhã!",
            "de": "🎯 *GLÜCKWUNSCH! Fast gewonnen!* 🎉\n\nIhre Chance, einen *KOSTENLOSEN Service* zu gewinnen, ist sehr nah!\n\n🔥 Kommen Sie täglich zurück — täglich aktive Spieler werden persönlich von unserem Team für kostenlosen Zugang ausgewählt!\n\n💎 Geben Sie nicht auf — Ihr Gewinn-Spin könnte morgen sein!",
            "ur": "🎯 *مبارک! تقریباً جیت گئے!* 🎉\n\n*مفت سروس* جیتنے کا آپ کا موقع بہت قریب ہے!\n\n🔥 ہر روز واپس آتے رہیں — روزانہ فعال کھلاڑیوں کو ہماری ٹیم ذاتی طور پر مفت رسائی کے لیے منتخب کرتی ہے!\n\n💎 ہمت نہ ہاریں — آپ کی جیت والی spin کل ہو سکتی ہے!",
            "ja": "🎯 *おめでとう！もう少しで当選！* 🎉\n\n*無料サービス*を獲得するチャンスがとても近いです！\n\n🔥 毎日戻ってきてください — 毎日アクティブなプレイヤーはチームが個人的に無料アクセスのために選びます！\n\n💎 諦めないで — 当選スピンは明日かもしれません！",
        },
        "try_again": {
            "en": "🔄 *Not today — but you're SO close!* 💪\n\n🎁 Your FREE service access is just around the corner!\n\nActive daily spinners get noticed by our team — the more you spin, the higher your chances of being personally selected! 🏆\n\n⏰ Come back tomorrow — don't break your streak!",
            "sw": "🔄 *Si leo — lakini uko KARIBU SANA!* 💪\n\n🎁 Ufikiaji wako wa huduma BURE uko karibu tu!\n\nWanaospin kila siku wanaonekana na timu yetu — unavyospin zaidi, ndivyo nafasi yako ya kuchaguliwa kibinafsi inavyoongezeka! 🏆\n\n⏰ Rudi kesho — usivunje streak yako!",
            "ar": "🔄 *ليس اليوم — لكنك قريب جداً!* 💪\n\n🎁 وصولك إلى الخدمة المجانية على وشك!\n\nيلاحظ فريقنا من يدور يومياً — كلما دورت أكثر، زادت فرصتك في الاختيار شخصياً! 🏆\n\n⏰ عد غداً — لا تكسر سلسلتك!",
            "zh": "🔄 *今天不行——但你非常接近！* 💪\n\n🎁 您的免费服务访问就在眼前！\n\n我们的团队注意到每天旋转的人——您旋转越多，被亲自选中的机会就越大！ 🏆\n\n⏰ 明天回来——不要打破您的连胜！",
            "ru": "🔄 *Не сегодня — но вы SO CLOSE!* 💪\n\n🎁 Ваш БЕСПЛАТНЫЙ доступ к услуге уже рядом!\n\nНаша команда замечает тех, кто крутит каждый день — чем больше крутите, тем выше шанс личного выбора! 🏆\n\n⏰ Возвращайтесь завтра — не прерывайте серию!",
            "es": "🔄 *¡Hoy no — pero estás muy cerca!* 💪\n\n🎁 ¡Tu acceso GRATUITO al servicio está a la vuelta de la esquina!\n\n¡Nuestro equipo nota a los que giran diariamente — cuanto más gires, mayores son tus posibilidades de ser seleccionado personalmente! 🏆\n\n⏰ ¡Vuelve mañana — no rompas tu racha!",
            "fr": "🔄 *Pas aujourd'hui — mais vous êtes si proche!* 💪\n\n🎁 Votre accès GRATUIT au service est juste au coin!\n\nNotre équipe remarque ceux qui tournent quotidiennement — plus vous tournez, plus vos chances d'être sélectionné sont grandes! 🏆\n\n⏰ Revenez demain — ne brisez pas votre série!",
            "pt": "🔄 *Hoje não — mas você está tão perto!* 💪\n\n🎁 Seu acesso GRÁTIS ao serviço está logo ali!\n\nNossa equipe nota quem gira diariamente — quanto mais você girar, maiores suas chances de ser selecionado pessoalmente! 🏆\n\n⏰ Volte amanhã — não quebre sua sequência!",
            "de": "🔄 *Heute nicht — aber Sie sind SO NAH!* 💪\n\n🎁 Ihr KOSTENLOSER Service-Zugang ist gleich um die Ecke!\n\nUnser Team bemerkt tägliche Dreher — je mehr Sie drehen, desto größer Ihre Chancen, persönlich ausgewählt zu werden! 🏆\n\n⏰ Kommen Sie morgen zurück — brechen Sie Ihre Serie nicht!",
            "ur": "🔄 *آج نہیں — لیکن آپ بہت قریب ہیں!* 💪\n\n🎁 آپ کی مفت سروس تک رسائی بس قریب ہے!\n\nہماری ٹیم روزانہ spin کرنے والوں کو نوٹ کرتی ہے — جتنا زیادہ spin کریں، ذاتی طور پر منتخب ہونے کے اتنے زیادہ امکانات! 🏆\n\n⏰ کل واپس آئیں — اپنی streak نہ توڑیں!",
            "ja": "🔄 *今日は残念——でもとても近いです！* 💪\n\n🎁 あなたの無料サービスアクセスはすぐそこです！\n\nチームは毎日スピンする人を注目しています——スピンすればするほど、個人的に選ばれる可能性が高まります！ 🏆\n\n⏰ 明日戻ってきてください——ストリークを途切れさせないで！",
        },
        "better_luck": {
            "en": "💪 *Keep going — you're building momentum!* 🌟\n\n🎰 Every spin brings you closer to being noticed by our team!\n\nWe reward our most loyal daily spinners with *FREE service access* — this could be YOU!\n\n🔥 Come back tomorrow and keep your winning spirit alive!",
            "sw": "💪 *Endelea — unajengea nguvu!* 🌟\n\n🎰 Kila spin inakukaribishia kuonekana na timu yetu!\n\nTunawatuza wanaospin kwa uaminifu kila siku na *ufikiaji wa huduma BURE* — huyu anaweza kuwa WEWE!\n\n🔥 Rudi kesho na uendelee na roho yako ya ushindi!",
            "ar": "💪 *استمر — أنت تبني الزخم!* 🌟\n\n🎰 كل دورة تقربك من أن يلاحظك فريقنا!\n\nنكافئ من يدورون بأمانة كل يوم بـ *وصول مجاني للخدمة* — قد تكون أنت!\n\n🔥 عد غداً وحافظ على روح الفوز لديك!",
            "zh": "💪 *继续——您正在积蓄动力！* 🌟\n\n🎰 每次旋转都让您更接近被我们团队注意！\n\n我们用*免费服务访问*奖励每天忠实旋转的人——这可能是您！\n\n🔥 明天回来，保持您的胜利精神！",
            "ru": "💪 *Продолжайте — вы набираете обороты!* 🌟\n\n🎰 Каждый спин приближает вас к тому, чтобы наша команда вас заметила!\n\nМы награждаем самых верных ежедневных игроков *БЕСПЛАТНЫМ доступом* — это можете быть вы!\n\n🔥 Возвращайтесь завтра и сохраняйте дух победителя!",
            "es": "💪 *¡Sigue adelante — estás ganando impulso!* 🌟\n\n🎰 ¡Cada giro te acerca a ser notado por nuestro equipo!\n\n¡Recompensamos a nuestros jugadores diarios más leales con *acceso GRATUITO* — podrías ser TÚ!\n\n🔥 ¡Vuelve mañana y mantén vivo tu espíritu ganador!",
            "fr": "💪 *Continuez — vous gagnez de l'élan!* 🌟\n\n🎰 Chaque tour vous rapproche d'être remarqué par notre équipe!\n\nNous récompensons nos joueurs quotidiens les plus fidèles avec un *accès GRATUIT* — cela pourrait être VOUS!\n\n🔥 Revenez demain et gardez votre esprit gagnant vivant!",
            "pt": "💪 *Continue — você está ganhando momentum!* 🌟\n\n🎰 Cada giro te aproxima de ser notado pela nossa equipe!\n\nRecompensamos nossos jogadores diários mais leais com *acesso GRÁTIS* — pode ser VOCÊ!\n\n🔥 Volte amanhã e mantenha seu espírito vencedor vivo!",
            "de": "💪 *Weiter so — Sie bauen Schwung auf!* 🌟\n\n🎰 Jedes Drehen bringt Sie näher daran, von unserem Team bemerkt zu werden!\n\nWir belohnen unsere treuesten täglichen Dreher mit *KOSTENLOSEM Zugang* — das könnten SIE sein!\n\n🔥 Kommen Sie morgen zurück und halten Sie Ihren Siegergeist am Leben!",
            "ur": "💪 *جاری رکھیں — آپ رفتار بنا رہے ہیں!* 🌟\n\n🎰 ہر spin آپ کو ہماری ٹیم کی نظر میں آنے کے قریب لاتی ہے!\n\nہم اپنے سب سے وفادار روزانہ spinners کو *مفت سروس تک رسائی* سے نوازتے ہیں — یہ آپ ہو سکتے ہیں!\n\n🔥 کل واپس آئیں اور اپنی جیتنے والی روح کو زندہ رکھیں!",
            "ja": "💪 *続けてください——勢いをつけています！* 🌟\n\n🎰 スピンするたびにチームに気づいてもらえる可能性が高まります！\n\n最も忠実な毎日のスピナーを*無料サービスアクセス*で報酬します——あなたがそうかもしれません！\n\n🔥 明日戻ってきて、勝利の精神を生かし続けてください！",
        },
    }
    lang_texts = lose_texts.get(prize_key, lose_texts["try_again"])
    return lang_texts.get(lang) or lang_texts.get("en", "Better luck next time!")
# Spinning animation frames
SPIN_FRAMES = [
    "🎰 ▶️ 🎯 🤖 📊 💎 🔄 🎁 🏆 ⚡ 🌟",
    "🎰 ▶️ 🤖 📊 💎 🔄 🎁 🏆 ⚡ 🌟 🎯",
    "🎰 ▶️ 📊 💎 🔄 🎁 🏆 ⚡ 🌟 🎯 🤖",
    "🎰 ▶️ 💎 🔄 🎁 🏆 ⚡ 🌟 🎯 🤖 📊",
    "🎰 ▶️ 🔄 🎁 🏆 ⚡ 🌟 🎯 🤖 📊 💎",
    "🎰 ▶️ 🎁 🏆 ⚡ 🌟 🎯 🤖 📊 💎 🔄",
    "🎰 ▶️ 🏆 ⚡ 🌟 🎯 🤖 📊 💎 🔄 🎁",
    "🎰 ▶️ ⚡ 🌟 🎯 🤖 📊 💎 🔄 🎁 🏆",
    "🎰 ▶️ 🌟 🎯 🤖 📊 💎 🔄 🎁 🏆 ⚡",
    "🎰 ▶️ 🎯 🏆 💎 🔄 🤖 📊 🎁 ⚡ 🌟",
    "🎰 ▶️ 🤖 🎯 🏆 💎 🔄 📊 🎁 ⚡ 🌟",
    "🎰 ▶️ 📊 🎯 🤖 🏆 💎 🔄 🎁 ⚡ 🌟",
    "🎰 ▶️ 💎 📊 🎯 🤖 🏆 🔄 🎁 ⚡ 🌟",
    "🎰 ▶️ 🔄 💎 📊 🎯 🤖 🏆 🎁 ⚡ 🌟",
    "🎰 ▶️ 🎁 🔄 💎 📊 🎯 🤖 🏆 ⚡ 🌟",
    "🎰 ▶️ 🏆 🎁 🔄 💎 📊 🎯 🤖 ⚡ 🌟",
    "🎰 ▶️ ⚡ 🏆 🎁 🔄 💎 📊 🎯 🤖 🌟",
    "🎰 ▶️ 🌟 ⚡ 🏆 🎁 🔄 💎 📊 🎯 🤖",
    "🎰 ▶️ 🎯 🌟 ⚡ 🏆 🎁 🔄 💎 📊 🤖",
    "🎰 ▶️ 🤖 🎯 🌟 ⚡ 🏆 🎁 🔄 💎 📊",
]

def do_spin():
    """Run weighted random spin — returns (prize_key, emoji, is_win)"""
    weights = [p[0] for p in SPIN_PRIZES]
    chosen  = random.choices(SPIN_PRIZES, weights=weights, k=1)[0]
    return chosen[1], chosen[2], chosen[3]

def get_prize_text(prize_key, lang):
    texts = SPIN_PRIZE_TEXT.get(prize_key, {})
    return texts.get(lang) or texts.get("en", "🎁 Prize!")

SPIN_WHEEL_VISUAL = (
    "✨ ━━━━━━━━━━━━━━━━━━━━━━ ✨\n"
    "   🎰 EVALON LUCKY SPIN 🎰\n"
    "✨ ━━━━━━━━━━━━━━━━━━━━━━ ✨\n\n"
    "⭐  🎯 ➤ 🤖 ➤ 📊 ➤ 💎  ⭐\n"
    "⭐  🎁 ➤ 🏆 ➤ ⚡ ➤ 🌟  ⭐\n"
    "⭐       🔄 ➤ 🎊        ⭐\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
)

# ══════════════════════════════════════════════════════════════
#  AUTO CLEAN PERSUASIVE MESSAGES — changes daily
# ══════════════════════════════════════════════════════════════

AUTO_CLEAN_MESSAGES = {
    "en": [
        "💎 *{name}*, want VIP access or a free bot?\n\n🎰 Tap below — *spin your free access now!*\nNew signals dropping today! Don't miss out! 🔥",
        "👋 *{name}!* Still here? Great!\n\n📊 Today's VIP signals are live!\n🎯 Tap Start — your next win is one click away! 💪",
        "🚀 *{name}*, the market is moving!\n\n⚡ Active traders are winning right now.\n🏆 Join them — tap Start and explore! 🔥",
        "🔥 *{name}!* Don't let the market pass you by!\n\n🎁 Spin your free access & discover what's waiting for you!\n💰 Winners are made daily here at EVALON! 🏆",
        "💡 *{name}*, smart traders don't wait!\n\n📈 Our auto bot is running 24/7 — are you?\n🎰 Tap Start and spin to unlock your free access! ⚡",
        "🌟 *{name}!* Your trading journey continues!\n\n🏆 New winners announced this week!\n🔥 Tap Start — could YOU be next? 💎",
        "⚡ *{name}*, the VIP channel is buzzing!\n\n📊 Signals are being sent right now!\n🚀 Tap Start to catch today's opportunities! 🎯",
    ],
    "sw": [
        "💎 *{name}*, unataka VIP au bot ya bure?\n\n🎰 Bonyeza hapa chini — *spin ufikiaji wako wa bure sasa!*\nSignals mpya zinatoka leo! Usikose! 🔥",
        "👋 *{name}!* Bado uko? Vizuri!\n\n📊 Signals za VIP za leo ziko live!\n🎯 Bonyeza Start — ushindi wako upo tap moja mbele! 💪",
        "🚀 *{name}*, soko linasogea!\n\n⚡ Wafanyabiashara wanaoshinda sasa hivi.\n🏆 Jiunge nao — bonyeza Start na uchunguze! 🔥",
        "🔥 *{name}!* Usikubali soko lipite!\n\n🎁 Spin ufikiaji wako wa bure na ugundua kinachokungoja!\n💰 Washindi hufanywa kila siku hapa EVALON! 🏆",
        "💡 *{name}*, wafanyabiashara hodari hawasubiri!\n\n📈 Auto bot yetu inafanya kazi 24/7 — wewe je?\n🎰 Bonyeza Start na spin kufungua ufikiaji wako wa bure! ⚡",
    ],
    "ar": [
        "💎 *{name}*، هل تريد VIP أو بوت مجاني؟\n\n🎰 اضغط أدناه — *أدر عجلتك المجانية الآن!*\nإشارات جديدة اليوم! لا تفوت الفرصة! 🔥",
        "👋 *{name}!* لا تدع السوق يمر!\n\n📊 إشارات VIP اليوم متاحة الآن!\n🎯 اضغط Start — فوزك بنقرة واحدة! 💪",
    ],
    "ru": [
        "💎 *{name}*, хотите VIP или бесплатного бота?\n\n🎰 Нажмите — *крутите бесплатный доступ сейчас!*\nСегодня новые сигналы! Не пропустите! 🔥",
        "🚀 *{name}*, рынок движется!\n\n⚡ Активные трейдеры побеждают прямо сейчас.\n🏆 Присоединяйтесь — нажмите Start! 🔥",
    ],
    "zh": [
        "💎 *{name}*，想要VIP还是免费机器人？\n\n🎰 点击下方 — *立即旋转您的免费访问！*\n今天有新信号！不要错过！ 🔥",
        "🚀 *{name}*，市场在移动！\n\n⚡ 活跃的交易者现在正在获胜。\n🏆 加入他们 — 点击Start！ 🔥",
    ],
}
# Use English for other languages
for _lc in ["hi","es","fr","pt","de","ur","ja","it","ko","tr","fa","pl","uk","kk","cs"]:
    AUTO_CLEAN_MESSAGES[_lc] = AUTO_CLEAN_MESSAGES["en"]

def get_auto_clean_msg(lang, name):
    pool = AUTO_CLEAN_MESSAGES.get(lang, AUTO_CLEAN_MESSAGES["en"])
    # Rotate daily
    idx = datetime.now().timetuple().tm_yday % len(pool)
    return pool[idx].format(name=escape_md(name))

# ══════════════════════════════════════════════════════════════
#  FAKE FEEDBACK DATA — EN:90, SW:23, UR:12 — changes daily
# ══════════════════════════════════════════════════════════════

FAKE_FEEDBACK = {
    "en": [
        ("James O.", "🇳🇬", "This bot changed my trading completely! Made $340 in my first week with the VIP signals. Best decision ever! 🔥"),
        ("Maria S.", "🇧🇷", "I was skeptical at first but WOW — 9 out of 10 signals hit today! Evalon Winners is the real deal 💎"),
        ("David L.", "🇬🇭", "The auto bot made $180 while I was sleeping. Woke up to profits! This is incredible 🚀"),
        ("Sarah W.", "🇿🇦", "Copy trading feature is amazing. Copied the top trader and got +47% return this month alone!"),
        ("Ahmed R.", "🇪🇬", "Finally found a reliable signal service. 85% win rate is no joke. Highly recommend Evalon Winners!"),
        ("Linda T.", "🇰🇪", "The free indicator is unbelievable — I can see BUY/SELL signals clearly now. Trading has never been easier!"),
        ("Carlos M.", "🇲🇽", "I've tried many signal providers but Evalon is different. Real forex pairs, real results. $520 this week! 💰"),
        ("Priya K.", "🇮🇳", "The support team is super responsive. Got my questions answered in minutes. Amazing service!"),
        ("Michael B.", "🇺🇬", "Started with $50 and now at $340 in 3 weeks. The signals are incredibly accurate! Thank you Evalon!"),
        ("Grace A.", "🇨🇲", "The free bot actually works! Was surprised by the results. Going VIP next month for sure 🏆"),
        ("Peter N.", "🇿🇼", "Never thought I could trade profitably until I found Evalon Winners. Life changing! 🌟"),
        ("Emmanuel O.", "🇨🇮", "Best investment I made this year — joining Evalon. The signals come at perfect times!"),
        ("Sophie R.", "🇫🇷", "The auto bot ran all night and I woke up to $220 profit. Dreams do come true with Evalon! ✨"),
        ("Kwame A.", "🇬🇭", "10/10 signals won yesterday! I literally screamed with joy. This service is phenomenal!"),
        ("Ali H.", "🇵🇰", "The indicator alone is worth everything. No repaint, super accurate. Been trading profitably for 2 months!"),
        ("Mercy W.", "🇰🇪", "Was losing money before Evalon. Now consistently profitable. The VIP signals are golden! 💛"),
        ("Lucas F.", "🇵🇹", "Pocket social trading is genius! Just copy the best and earn. Made €180 this week without much effort!"),
        ("Zara M.", "🇲🇾", "The referral system is great too! Earned discounts by inviting friends. Win-win! 🎁"),
        ("Oliver T.", "🇦🇺", "Three months with Evalon and I've never looked back. Consistent profits every single week!"),
        ("Aisha D.", "🇸🇳", "The team genuinely cares about traders' success. Quick support, accurate signals — 5 stars! ⭐⭐⭐⭐⭐"),
        ("Hassan M.", "🇹🇿", "Auto bot + VIP signals = unstoppable! Made $890 last month. Evalon is the best!"),
        ("Elena V.", "🇺🇦", "I recommend Evalon to everyone I know. The free indicator is better than paid ones I've used before!"),
        ("John K.", "🇳🇬", "From zero to hero! 8 weeks with Evalon signals and my account grew 300%. Not exaggerating! 🚀"),
        ("Fatima A.", "🇲🇦", "The daily signals are so consistent. Morning, afternoon, evening — always winning! Thank you team!"),
        ("Ivan P.", "🇷🇺", "Best bot I've ever used. Set it up once and it runs automatically. Profits while I sleep! 💤💰"),
        ("Natalia K.", "🇵🇱", "Joined 2 months ago. Already made back my subscription cost 20x over. Pure gold! ✨"),
        ("Tariq B.", "🇯🇴", "The XAU/USD signals are incredible! Gold trading has been my biggest earner thanks to Evalon!"),
        ("Isabella L.", "🇧🇷", "Social trading feature literally pays me while I do nothing. Copied top trader — up 63% this month!"),
        ("Kevin O.", "🇳🇬", "Tried free first, went VIP immediately. The difference in signal quality is unreal. Worth every cent!"),
        ("Amina D.", "🇸🇳", "5 stars isn't enough! Evalon deserves 10 stars! The team is always available and signals are on point! 🌟"),
        ("Chen W.", "🇨🇳", "The bot works 24/7 — even on weekends with OTC markets. Never miss a trading opportunity!"),
        ("Rebecca M.", "🇰🇪", "I've referred 8 friends already because I believe in this service. Real profits, real results! 💯"),
        ("Samuel T.", "🇬🇭", "From $100 to $780 in one month with Evalon auto bot. I'm speechless honestly. God bless this team!"),
        ("Vera K.", "🇿🇦", "The indicator helped me understand market movements. Now I trade with confidence every day!"),
        ("Omar H.", "🇸🇦", "Evalon VIP signals are the best in the game. Consistent, accurate, and the team explains every signal!"),
        ("Diana R.", "🇲🇽", "Made my first $1000 profit last week with Evalon! Was only dreaming about this before. Thank you! 🙏"),
        ("Felix A.", "🇨🇲", "The pocket social trading is revolutionary! Copy pros and earn passive income. Brilliant concept!"),
        ("Lena B.", "🇩🇪", "German here! Found Evalon randomly and it's the best trading discovery I've made. Danke Evalon! 🙏"),
        ("Victor M.", "🇨🇮", "6 months with Evalon. My trading account grew from $200 to $3,400. These signals are golden! 🏆"),
        ("Joyce W.", "🇺🇬", "The support team replied at 2am when I had a question. That dedication is why I'll never leave Evalon!"),
        ("Patrick N.", "🇿🇼", "Was losing $50/week before. Now winning $200+/week with Evalon. The transformation is real!"),
        ("Aiko T.", "🇯🇵", "Joined from Japan! The signals work perfectly on Quotex. Very impressed with the accuracy rate!"),
        ("Marcus L.", "🇧🇷", "Free indicator + auto bot combo is unstoppable! Trading both manually and automatically now. Love it!"),
        ("Nadia O.", "🇪🇬", "The VIP channel has signals that actually work. Not fake screenshots — REAL live results every day!"),
        ("Bright K.", "🇬🇭", "From struggling trader to profitable one in 6 weeks. All thanks to Evalon Winners. Highly recommended!"),
        ("Yuki T.", "🇯🇵", "The free indicator is phenomenal! Works on all timeframes. My accuracy went from 40% to 82%! 📈"),
        ("Chidi E.", "🇳🇬", "This is not just a signal service — it's a full trading education. I understand markets better now!"),
        ("Sofia R.", "🇦🇷", "Argentine trader here! The EUR/USD signals are incredibly precise. $450 profit this week alone! 💰"),
        ("Moses A.", "🇰🇪", "Evalon is the GOAT of trading bots! My account doubled in 3 weeks. Sharing with everyone I know!"),
        ("Cynthia M.", "🇹🇿", "The comeback messages keep me motivated when I haven't traded for a while. Great community feel!"),
        ("Ibrahim H.", "🇸🇩", "Started skeptical, now a believer! The signals are too accurate to be chance. Science behind trading! 🧠"),
        ("Rosa P.", "🇨🇴", "Made $280 this week with the auto bot running overnight. This is truly passive income! 😍"),
        ("Frank O.", "🇳🇬", "The team is transparent about wins AND losses. That honesty is why I trust Evalon 100%!"),
        ("Amara S.", "🇸🇳", "Pocket Option social trading through Evalon gave me 55% ROI in one month. Simply amazing!"),
        ("Lucas V.", "🇧🇷", "I'm a student and was looking for extra income. Evalon signals gave me financial freedom at 22! 🎓💰"),
        ("Hannah K.", "🇰🇪", "The daily routine of checking Evalon signals has replaced my morning coffee. Can't start day without it!"),
        ("Anthony N.", "🇿🇲", "From Zambia! Was worried no one served my region but Evalon works perfectly here. $340 this month!"),
        ("Miriam J.", "🇹🇿", "3 months of consistent profits. My family has noticed the change. Evalon Winners changed my life! 🙌"),
        ("Christopher A.", "🇨🇮", "The referral program is genius! Got my friend in, we both earn, both win! Best team ever! 🤝"),
        ("Bridget M.", "🇳🇬", "I was almost giving up on trading. Evalon gave me hope and PROFITS! Never looking back! 🔥"),
        ("Daniel O.", "🇬🇭", "Signal accuracy is insane! 91% win rate this month. The team really knows what they're doing!"),
        ("Cecilia R.", "🇲🇿", "From Mozambique! The bot works even with my small account. Growing steadily every week! 🌱"),
        ("Raymond T.", "🇬🇭", "The auto bot + VIP signals combination is pure gold. My portfolio is up 180% in 2 months!"),
        ("Blessing O.", "🇳🇬", "Words can't express my gratitude! Started with $30, now at $340. Evalon is truly a blessing!"),
        ("Fatou D.", "🇸🇳", "The indicator shows clear buy and sell points. No more guessing. Trading is fun now! 🎯"),
        ("Eric K.", "🇰🇪", "Got my first $100 profit in week 1. Then $280 in week 2. The growth is real with Evalon!"),
        ("Josephine A.", "🇨🇲", "The VIP signals come with explanations. I'm learning to trade properly while making money! Perfect!"),
        ("Thomas M.", "🇿🇦", "South African trader here. Evalon signals work across all time zones. No more missed opportunities!"),
        ("Mary N.", "🇳🇬", "5 stars! The customer support alone is worth joining. Responsive, helpful, always there! ❤️"),
        ("Kenneth B.", "🇬🇭", "From $50 to $620 in 7 weeks with signals and auto bot. This is not luck — it's strategy! 🎯"),
        ("Patience A.", "🇳🇬", "The free indicator helped me spot a 10/10 winning streak! Downloaded it and never looked back! 📈"),
        ("Arnold M.", "🇺🇬", "The team manually selects signals — that human touch makes the difference. Trust Evalon! 🤝"),
        ("Abigail T.", "🇿🇼", "Never thought a bot could make me money while I sleep. Evalon proved me wrong. Amazing! 😱💰"),
        ("Theodore O.", "🇨🇮", "The social trading feature let me copy a master trader. Up 78% this month! Passive income achieved!"),
        ("Sandra K.", "🇰🇪", "Join Evalon Winners. Period. Best thing I did for my financial future. Don't hesitate! 💯"),
        ("Philip A.", "🇸🇳", "Evalon signals are so accurate I sometimes think they know the future! Professional level! 🌟"),
        ("Irene M.", "🇹🇿", "The Lucky Spin feature is fun! Got selected by the team for a discount — felt so special! 🎰"),
        ("George N.", "🇳🇬", "Trading education + live signals + auto bot = the complete package. Evalon has everything!"),
        ("Comfort B.", "🇨🇲", "Started last month. Already profitable. Wish I found Evalon earlier! Sharing everywhere I go!"),
        ("Kweku A.", "🇬🇭", "The XAU/USD and EUR/USD signals are my favorites. Consistent winners every single session!"),
        ("Esther M.", "🇳🇬", "Evalon changed my financial story. From debt to savings in 2 months! Real talk! 💪"),
        ("Frederick O.", "🇨🇮", "The bot doesn't just give signals — it teaches you HOW to trade. Educational and profitable!"),
        ("Agnes K.", "🇰🇪", "Recommended to 5 friends. All 5 are now profitable traders. Evalon Winners is the way! 🏆"),
        ("Solomon T.", "🇬🇭", "The auto bot consistency is remarkable. Same reliable performance every single day! 💎"),
        ("Catherine A.", "🇳🇬", "I literally cried when I hit $500 profit for the first time. Thank you Evalon from the bottom of my heart! 🙏"),
        ("Dominic M.", "🇺🇬", "VIP signals + social trading = my new financial strategy. Up $680 in 6 weeks! Join Evalon NOW!"),
    ],
    "sw": [
        ("James O.", "🇳🇬", "Bot hii imebadilisha biashara yangu kabisa! Nilipata $340 wiki yangu ya kwanza na signals za VIP. Uamuzi bora kabisa! 🔥"),
        ("Maria S.", "🇧🇷", "Nilikuwa na shaka mwanzoni lakini WOW — signals 9 kati ya 10 zilishinda leo! Evalon Winners ni ya kweli 💎"),
        ("David L.", "🇬🇭", "Auto bot ilipata $180 nilipokuwa nikilala. Nikaamka na faida! Hii ni ya ajabu sana 🚀"),
        ("Sarah W.", "🇿🇦", "Kipengele cha copy trading ni cha ajabu. Niliiga trader bora na kupata +47% mapato wiki moja tu!"),
        ("Ahmed R.", "🇪🇬", "Mwishowe nimepata huduma ya signals inayoaminika. Kiwango cha ushindi wa 85% si mchezo. Napendekeza Evalon Winners!"),
        ("Linda T.", "🇰🇪", "Indicator ya bure ni ya kushangaza — ninaweza kuona signals za BUY/SELL wazi sasa. Biashara imekuwa rahisi zaidi!"),
        ("Carlos M.", "🇲🇽", "Nimejaribu watoa signals wengi lakini Evalon ni tofauti. Forex halisi, matokeo halisi. $520 wiki hii! 💰"),
        ("Michael B.", "🇺🇬", "Nilianza na $50 na sasa niko $340 katika wiki 3. Signals ni sahihi sana! Asante Evalon!"),
        ("Grace A.", "🇨🇲", "Bot ya bure inafanya kazi kweli! Nilishangazwa na matokeo. Nakwenda VIP mwezi ujao kwa hakika 🏆"),
        ("Peter N.", "🇿🇼", "Sikuwahi fikiria ningeweza kufanya biashara kwa faida mpaka nilipata Evalon Winners. Inabadilisha maisha! 🌟"),
        ("Emmanuel O.", "🇨🇮", "Uwekezaji bora niliofanya mwaka huu — kujiunga na Evalon. Signals zinakuja wakati sahihi!"),
        ("Hassan M.", "🇹🇿", "Auto bot + Signals za VIP = isiyozuiwa! Nilipata $890 mwezi uliopita. Evalon ni bora!"),
        ("John K.", "🇳🇬", "Kutoka sifuri hadi shujaa! Wiki 8 na signals za Evalon na akaunti yangu ilikua 300%. Si kutia chumvi! 🚀"),
        ("Fatima A.", "🇲🇦", "Signals za kila siku ni thabiti sana. Asubuhi, mchana, jioni — ushindi daima! Asante timu!"),
        ("Kevin O.", "🇳🇬", "Nilijaribu bure kwanza, nikakwenda VIP mara moja. Tofauti ya ubora wa signal ni ya kushangaza. Inastahili kila senti!"),
        ("Samuel T.", "🇬🇭", "Kutoka $100 hadi $780 katika mwezi mmoja na Evalon auto bot. Sina maneno. Mungu awabariki timu hii!"),
        ("Moses A.", "🇰🇪", "Evalon ni GOAT wa trading bots! Akaunti yangu iliongezeka mara mbili katika wiki 3. Ninashiriki na kila mtu!"),
        ("Cynthia M.", "🇹🇿", "Ujumbe wa kurudi unanipa motisha ninapokaa bila kufanya biashara kwa muda. Hisia nzuri ya jumuiya!"),
        ("Miriam J.", "🇹🇿", "Miezi 3 ya faida thabiti. Familia yangu imeona mabadiliko. Evalon Winners imebadilisha maisha yangu! 🙌"),
        ("Eric K.", "🇰🇪", "Nilipata faida yangu ya kwanza ya $100 wiki ya 1. Kisha $280 wiki ya 2. Ukuaji ni wa kweli na Evalon!"),
        ("Agnes K.", "🇰🇪", "Nilipendekeza marafiki 5. Wote 5 ni wafanyabiashara wenye faida sasa. Evalon Winners ndiyo njia! 🏆"),
        ("Sandra K.", "🇰🇪", "Jiunge na Evalon Winners. Kipindi. Kitu bora nilichofanya kwa mustakabali wangu wa kifedha. Usisita! 💯"),
        ("Irene M.", "🇹🇿", "Kipengele cha Lucky Spin ni cha kufurahisha! Timu ilinichagua kupata punguzo — nilihisi maalum sana! 🎰"),
    ],
    "ur": [
        ("Ali H.", "🇵🇰", "اس بوٹ نے میری ٹریڈنگ مکمل طور پر بدل دی! VIP سگنلز سے پہلے ہفتے میں $340 کمائے۔ بہترین فیصلہ! 🔥"),
        ("Tariq B.", "🇯🇴", "XAU/USD سگنلز ناقابل یقین ہیں! گولڈ ٹریڈنگ Evalon کی وجہ سے میری سب سے بڑی کمائی بن گئی!"),
        ("Zara M.", "🇲🇾", "ریفرل سسٹم بھی زبردست ہے! دوستوں کو مدعو کرکے رعایتیں کمائیں۔ سب کے لیے فائدہ! 🎁"),
        ("Nadia O.", "🇪🇬", "VIP چینل میں ایسے سگنلز ہیں جو واقعی کام کرتے ہیں۔ جھوٹے اسکرین شاٹس نہیں — ہر روز حقیقی نتائج!"),
        ("Ibrahim H.", "🇸🇩", "شکاک تھا، اب یقین آ گیا! سگنلز اتنے درست ہیں کہ اتفاق نہیں لگتا۔ ٹریڈنگ میں سائنس ہے! 🧠"),
        ("Rosa P.", "🇨🇴", "رات کو آٹو بوٹ چلا کر $280 کمائے۔ یہ واقعی غیر فعال آمدنی ہے! 😍"),
        ("Marcus L.", "🇧🇷", "مفت انڈیکیٹر + آٹو بوٹ کا امتزاج ناقابل روک ہے! دستی اور خودکار دونوں طریقوں سے ٹریڈنگ کر رہا ہوں!"),
        ("Aiko T.", "🇯🇵", "جاپان سے شامل ہوا! Quotex پر سگنلز بالکل کام کرتے ہیں۔ درستگی کی شرح سے بہت متاثر ہوں!"),
        ("Yuki T.", "🇯🇵", "مفت انڈیکیٹر شاندار ہے! تمام ٹائم فریمز پر کام کرتا ہے۔ میری درستگی 40% سے 82% ہو گئی! 📈"),
        ("Sofia R.", "🇦🇷", "EUR/USD سگنلز ناقابل یقین حد تک درست ہیں۔ اس ہفتے اکیلے $450 منافع! 💰"),
        ("Lucas V.", "🇧🇷", "میں ایک طالب علم ہوں اور اضافی آمدنی ڈھونڈ رہا تھا۔ Evalon سگنلز نے 22 سال کی عمر میں مالی آزادی دی! 🎓💰"),
        ("Chen W.", "🇨🇳", "بوٹ 24/7 کام کرتا ہے — ویک اینڈ پر OTC مارکیٹس کے ساتھ بھی۔ کوئی موقع نہیں چھوٹتا!"),
    ],
}


# ══════════════════════════════════════════════════════════════
#  FAKE LEADERBOARD & PROGRESS BAR
# ══════════════════════════════════════════════════════════════

FAKE_NAMES = [
    "Trader_254", "VIP_Master", "Signals_Pro", "Alpha_Trader",
    "Gold_Winner", "FX_Champion", "Binary_King", "Profit_Hunter",
]

def get_fake_leaderboard(user_real_count):
    """FIX: Returns plain text without markdown stars/backticks"""
    fake_scores = sorted(random.sample(range(15, 60), 3), reverse=True)
    names = random.sample(FAKE_NAMES, 3)
    medals = ["👑", "🥈", "🥉"]
    lines = ["\n🏆 LEADERBOARD YA WIKI"]
    for i, (name, score) in enumerate(zip(names, fake_scores)):
        lines.append(f"{medals[i]} {name} — {score} watu")
    lines.append(f"👤 Wewe — {user_real_count} watu 🔥")
    if user_real_count < fake_scores[-1]:
        lines.append(f"💪 Alika {fake_scores[-1] - user_real_count} zaidi kuingia top 3!")
    return "\n".join(lines)

def make_progress_bar(count, total):
    """FIX: No backticks, no markdown, plain text only"""
    filled = int((count / total) * 10)
    bar = "█" * filled + "░" * (10 - filled)
    return f"[{bar}] {count}/{total}"

# ══════════════════════════════════════════════════════════════
#  URGENCY
# ══════════════════════════════════════════════════════════════

URGENCY = {
    "en": [
        "⚠️ LIMITED SLOTS! Only a few VIP spots left today!",
        "🔥 HIGH DEMAND! Many traders have joined recently — do not miss out!",
        "⏰ TODAY ONLY! Special offer expires at midnight!",
        "🚨 ALMOST FULL! VIP channel closing new members soon!",
        "💥 LAST CHANCE! Don't miss today's winning signals!",
    ],
    "sw": [
        "⚠️ NAFASI CHACHE! Nafasi chache za VIP zimebaki leo!",
        "🔥 MAHITAJI MAKUBWA! Wafanyabiashara wengi wamejiunga hivi karibuni!",
        "⏰ LEO TU! Ofa maalum inaisha usiku wa manane!",
        "🚨 KARIBU KUJAA! Channel ya VIP itafunga wanachama wapya hivi karibuni!",
        "💥 NAFASI YA MWISHO! Usikose signals za kushinda za leo!",
    ],
    "ar": [
        "⚠️ مقاعد محدودة! بقيت مقاعد VIP قليلة فقط اليوم!",
        "🔥 طلب عالٍ! انضم كثير من المتداولين مؤخراً!",
        "⏰ اليوم فقط! ينتهي العرض الخاص عند منتصف الليل!",
    ],
    "zh": [
        "⚠️ 名额有限！今天只剩几个VIP名额！",
        "🔥 需求旺盛！最近很多交易者加入了！",
        "⏰ 仅限今天！特别优惠将于午夜到期！",
    ],
    "hi": [
        "⚠️ सीमित स्लॉट! आज केवल कुछ VIP स्पॉट बचे हैं!",
        "🔥 उच्च मांग! हाल ही में कई ट्रेडर्स जुड़े हैं!",
        "⏰ आज ही! विशेष ऑफर आधी रात को समाप्त होता है!",
    ],
    "ru": [
        "⚠️ ОГРАНИЧЕННЫЕ МЕСТА! Осталось несколько VIP мест!",
        "🔥 ВЫСОКИЙ СПРОС! Недавно присоединились многие трейдеры!",
        "⏰ ТОЛЬКО СЕГОДНЯ! Специальное предложение истекает в полночь!",
    ],
    "es": [
        "⚠️ PLAZAS LIMITADAS! Solo quedan pocas plazas VIP hoy!",
        "🔥 ALTA DEMANDA! Muchos traders se han unido recientemente!",
        "⏰ SOLO HOY! La oferta especial expira a medianoche!",
    ],
    "fr": [
        "⚠️ PLACES LIMITÉES! Il ne reste que quelques places VIP aujourd'hui!",
        "🔥 FORTE DEMANDE! De nombreux traders ont rejoint récemment!",
        "⏰ AUJOURD'HUI SEULEMENT! L'offre spéciale expire à minuit!",
    ],
    "pt": [
        "⚠️ VAGAS LIMITADAS! Apenas algumas vagas VIP restam hoje!",
        "🔥 ALTA DEMANDA! Muitos traders entraram recentemente!",
        "⏰ SOMENTE HOJE! Oferta especial expira à meia-noite!",
    ],
    "de": [
        "⚠️ BEGRENZTE PLÄTZE! Nur noch wenige VIP-Plätze heute!",
        "🔥 HOHE NACHFRAGE! Viele Trader sind kürzlich beigetreten!",
        "⏰ NUR HEUTE! Sonderangebot läuft um Mitternacht ab!",
    ],
    "ur": [
        "⚠️ محدود نشستیں! آج صرف چند VIP نشستیں باقی ہیں!",
        "🔥 زیادہ مانگ! حال ہی میں بہت سے ٹریڈرز شامل ہوئے ہیں!",
        "⏰ صرف آج! خصوصی پیشکش آدھی رات کو ختم ہوتی ہے!",
    ],
    "ja": [
        "⚠️ 限定スロット！今日のVIPスポットはわずかです！",
        "🔥 高需要！最近多くのトレーダーが参加しました！",
        "⏰ 本日限り！特別オファーは真夜中に終了します！",
    ],
}

def get_urgency(lang):
    pool = URGENCY.get(lang, URGENCY["en"])
    return pool[datetime.now().weekday() % len(pool)]

# ══════════════════════════════════════════════════════════════
#  SMART GREETING — changes by time of day
# ══════════════════════════════════════════════════════════════

def get_smart_greeting(lang):
    hour = datetime.now().hour
    greetings = {
        "en": {
            "morning":   "🌅 Good morning! Today is a great day to WIN!",
            "afternoon": "☀️ Good afternoon! Markets are moving — are you ready?",
            "evening":   "🌆 Good evening! Evening sessions can be very profitable!",
            "night":     "🌙 Still awake? Smart traders never miss an opportunity!",
        },
        "sw": {
            "morning":   "🌅 Habari za asubuhi! Leo ni siku nzuri ya KUSHINDA!",
            "afternoon": "☀️ Habari za mchana! Masoko yanasogea — uko tayari?",
            "evening":   "🌆 Habari za jioni! Vikao vya jioni vinaweza kuwa na faida sana!",
            "night":     "🌙 Bado macho? Wafanyabiashara werevu hawakosi fursa!",
        },
    }
    period = "morning" if 5 <= hour < 12 else "afternoon" if 12 <= hour < 17 else "evening" if 17 <= hour < 21 else "night"
    lang_g = greetings.get(lang, greetings["en"])
    return lang_g[period]

# ══════════════════════════════════════════════════════════════
#  DAILY MARKET QUOTES
# ══════════════════════════════════════════════════════════════

DAILY_QUOTES = [
    ("The stock market is a device for transferring money from the impatient to the patient.", "Warren Buffett"),
    ("Risk comes from not knowing what you are doing.", "Warren Buffett"),
    ("The goal of a successful trader is to make the best trades, not to be right.", "Mark Douglas"),
    ("Every trader has a story. The winners just write better endings.", "Unknown"),
    ("In trading, the most important thing is not to make money, but not to lose it.", "George Soros"),
    ("The market is a pendulum that forever swings between optimism and pessimism.", "Benjamin Graham"),
    ("Trade what you see, not what you think.", "Unknown"),
    ("Successful trading is about managing risk, not avoiding it.", "Unknown"),
    ("The biggest risk of all is not taking one.", "Mellody Hobson"),
    ("Plan your trade and trade your plan.", "Unknown"),
    ("Cut your losses short and let your profits run.", "Unknown"),
    ("Be fearful when others are greedy, be greedy when others are fearful.", "Warren Buffett"),
    ("Trading is not about being right — it is about being profitable.", "Unknown"),
    ("Discipline is the bridge between goals and accomplishment.", "Jim Rohn"),
    ("Every expert was once a beginner. Keep going!", "Unknown"),
    ("Consistency beats perfection every single time.", "Unknown"),
    ("Your biggest enemy in trading is your own emotions.", "Unknown"),
    ("Small consistent profits beat big risky wins.", "Unknown"),
    ("The trend is your friend — until the end.", "Unknown"),
    ("Patience and discipline separate winners from losers.", "Unknown"),
    ("Know your risk before you know your reward.", "Unknown"),
    ("The market rewards those who respect it.", "Unknown"),
    ("One good trade is worth a hundred rushed ones.", "Unknown"),
    ("Winning traders think in probabilities, not certainties.", "Mark Douglas"),
    ("The best investment you can make is in yourself.", "Warren Buffett"),
    ("Success in trading comes from preparation, not luck.", "Unknown"),
    ("A good trader is always learning, always adapting.", "Unknown"),
    ("Small consistent profits compound into life-changing wealth.", "Unknown"),
    ("The market will always be there. Your capital might not. Protect it.", "Unknown"),
    ("Discipline today, financial freedom tomorrow.", "Unknown"),
]

def get_daily_quote():
    idx = datetime.now().timetuple().tm_yday % len(DAILY_QUOTES)
    quote, author = DAILY_QUOTES[idx]
    return f'💡 *"{quote}"*\n\n— _{author}_'

# ══════════════════════════════════════════════════════════════
#  BINARY TRADING TIPS
# ══════════════════════════════════════════════════════════════

BINARY_TIPS = [
    "💡 *TIP:* Always trade with the trend — if the market is going UP, look for BUY signals only!",
    "💡 *TIP:* Never risk more than 2-5% of your account on a single trade. Protect your capital first!",
    "💡 *TIP:* The best sessions overlap London (8AM-12PM GMT) and New York (1PM-5PM GMT)!",
    "💡 *TIP:* After 3 consecutive losses, STOP trading. Take a break and come back fresh.",
    "💡 *TIP:* Wait for a clear signal before entering. Patience is the most profitable skill!",
    "💡 *TIP:* Strong support and resistance levels give the highest probability trades.",
    "💡 *TIP:* Use 1-5 minute candles for binary options — clearer entry signals!",
    "💡 *TIP:* Always check the economic calendar before trading! News events can break any pattern.",
    "💡 *TIP:* Avoid trading the first 5 minutes of a new session — markets are too volatile!",
    "💡 *TIP:* Best binary trades happen when indicator AND price action agree on direction.",
    "💡 *TIP:* Set a daily profit target. When you reach it, STOP. Don't let greed destroy your gains!",
    "💡 *TIP:* OTC weekend markets follow patterns — great practice time for beginners!",
    "💡 *TIP:* Screenshot your trades. Review what worked and what didn't every week.",
    "💡 *TIP:* For 1-minute candles, use 1-2 minute expiry for best results.",
    "💡 *TIP:* When in doubt, stay OUT. No trade is always better than a bad trade!",
    "💡 *TIP:* Master one asset before trading many — consistency beats variety.",
    "💡 *TIP:* Wednesday-Thursday often give the best signals — Monday/Friday can be unpredictable.",
    "💡 *TIP:* Your mindset determines your results. Trade calm, trade smart!",
    "💡 *TIP:* Keep a trading journal — this separates professionals from gamblers.",
    "💡 *TIP:* Practice on demo accounts before using real money!",
    "💡 *TIP:* Consecutive wins cause overconfidence. Treat every trade as your first!",
    "💡 *TIP:* Check H1 timeframe for trend direction, then M5 for entry timing.",
    "💡 *TIP:* The best binary traders win 60-70% of trades — consistency beats perfection!",
    "💡 *TIP:* Avoid major news: NFP, CPI, Fed announcements can move markets wildly!",
    "💡 *TIP:* Start small and grow — 5% daily compounded beats 50% gambles every time.",
    "💡 *TIP:* Emotional trading kills accounts. Step away when angry or overexcited.",
    "💡 *TIP:* The indicator is a tool, not a guarantee. Always confirm with price action!",
    "💡 *TIP:* Two indicators confirming same direction = high probability trade!",
    "💡 *TIP:* Asian session (midnight-8AM GMT) is quieter — good for OTC assets.",
    "💡 *TIP:* Higher payout percentage = less trades needed to profit. Choose wisely!",
]

def get_daily_binary_tip():
    idx = (datetime.now().timetuple().tm_yday + 7) % len(BINARY_TIPS)
    return BINARY_TIPS[idx]

# ══════════════════════════════════════════════════════════════
#  SCARCITY MESSAGES (shown to returning users visit >= 3)
# ══════════════════════════════════════════════════════════════

SCARCITY_MSGS = {
    "en": [
        "💥 *VIP is filling up fast!*\n\nSpots available — but not for long.\n\nTraders are joining as you read this... 👇",
        "🔥 *Our community is growing FAST!*\n\nTraders worldwide have found EVALON.\n\nDon't be the last one to discover it. 👇",
        "⚡ *Limited VIP access available!*\n\nWe keep our VIP small for quality.\n\nOnce it's full — it's full. 👇",
    ],
    "sw": [
        "💥 *VIP inajaa haraka!*\n\nNafasi zinapatikana — lakini sio kwa muda mrefu.\n\nWafanyabiashara wanajiunga unaposoma hii... 👇",
        "🔥 *Jumuiya yetu inakua HARAKA!*\n\nWafanyabiashara duniani kote wamepata EVALON.\n\nUsiwe wa mwisho kuigundua. 👇",
        "⚡ *Ufikiaji wa VIP mdogo unapatikana!*\n\nTunaweka VIP yetu ndogo kwa ubora.\n\nIkijaa — imejaa. 👇",
    ],
}

def get_scarcity_msg(lang):
    pool = SCARCITY_MSGS.get(lang, SCARCITY_MSGS["en"])
    return random.choice(pool)

# ══════════════════════════════════════════════════════════════
#  TRUST TAGS
# ══════════════════════════════════════════════════════════════

TRUST_TAGS = {
    "en": [
        "\n\n✅ *Verified by 1,200+ traders worldwide*",
        "\n\n🔒 *Your funds always stay in YOUR account*",
        "\n\n⭐ *Rated 4.9/5 by our community*",
        "\n\n🌍 *Trusted by traders in 50+ countries*",
    ],
    "sw": [
        "\n\n✅ *Imethibitishwa na wafanyabiashara 1,200+ duniani*",
        "\n\n🔒 *Fedha zako zinabaki daima kwenye AKAUNTI YAKO*",
        "\n\n⭐ *Imepewa alama ya 4.9/5 na jumuiya yetu*",
        "\n\n🌍 *Inaaminiwa na wafanyabiashara katika nchi 50+*",
    ],
}

def get_trust_tag(lang):
    pool = TRUST_TAGS.get(lang, TRUST_TAGS["en"])
    idx = datetime.now().day % len(pool)
    return pool[idx]

# ══════════════════════════════════════════════════════════════
#  ACHIEVEMENT SYSTEM
# ══════════════════════════════════════════════════════════════

ACHIEVEMENTS = {
    "first_look":    ("🌟", "First Step",    "Viewed your first service"),
    "explorer":      ("💎", "Explorer",      "Viewed all services"),
    "loyal":         ("🏆", "Loyal Member",  "Member for 14+ days"),
    "top_referrer":  ("👑", "Top Referrer",  "Referred 5+ friends"),
    "quiz_master":   ("🎓", "Quiz Master",   "Completed the weekly quiz"),
    "goal_setter":   ("🎯", "Goal Setter",   "Set a trading goal"),
    "streak_3":      ("🔥", "On Fire",       "3-day streak"),
    "streak_7":      ("⚡", "Unstoppable",   "7-day streak"),
}

def get_user_badges(uid):
    import json
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT badges FROM users WHERE id=%s", (uid,))
        row = c.fetchone()
        conn.close()
        if row and row[0]:
            return json.loads(row[0])
        return []
    except:
        return []

def add_badge(uid, badge_key):
    import json
    try:
        badges = get_user_badges(uid)
        if badge_key not in badges:
            badges.append(badge_key)
            conn = get_conn()
            c = conn.cursor()
            c.execute("UPDATE users SET badges=%s WHERE id=%s", (json.dumps(badges), uid))
            conn.commit()
            conn.close()
            return True
        return False
    except:
        return False

# ══════════════════════════════════════════════════════════════
#  QUIZ SYSTEM
# ══════════════════════════════════════════════════════════════

QUIZ_QUESTIONS = [
    {
        "q": "📊 *QUIZ Q1:* In binary options, what does it mean when you place a CALL trade?",
        "options": ["🔴 You expect price to go DOWN", "🟢 You expect price to go UP", "⚪ You expect price to stay the same"],
        "answer": 1,
        "explanation": "A CALL trade means you believe the price will be HIGHER at expiry."
    },
    {
        "q": "💰 *QUIZ Q2:* What is the SAFEST rule for trade size in binary options?",
        "options": ["💸 50% of your account", "✅ 2-5% of your account", "🎲 As much as possible"],
        "answer": 1,
        "explanation": "Never risk more than 2-5% per trade — this protects your capital."
    },
    {
        "q": "⏰ *QUIZ Q3:* When is usually the BEST time to trade binary options?",
        "options": ["🌙 Late night (2AM-6AM)", "✅ London-NY overlap (1PM-5PM GMT)", "🌅 Early morning (5AM-7AM)"],
        "answer": 1,
        "explanation": "The London-New York overlap has the most liquidity and clearest signals."
    },
]

def get_quiz_score(uid):
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT quiz_score FROM users WHERE id=%s", (uid,))
        row = c.fetchone()
        conn.close()
        return row[0] or 0 if row else 0
    except:
        return 0

def save_quiz_score(uid, score):
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("UPDATE users SET quiz_score=%s WHERE id=%s", (score, uid))
        conn.commit()
        conn.close()
    except:
        pass

# ══════════════════════════════════════════════════════════════
#  RESULTS HISTORY DB FUNCTIONS
# ══════════════════════════════════════════════════════════════

def save_result(result_date, content_text, media_id=None, media_type=None):
    try:
        conn = get_conn()
        c = conn.cursor()
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        c.execute("""
            INSERT INTO results_history (caption, media_id, media_type, saved_at)
            VALUES (%s, %s, %s, %s)
        """, (content_text[:2000] if content_text else result_date, media_id, media_type, now))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.warning(f"save_result failed: {e}")
        return False

def get_results_history(limit=10):
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("""
            SELECT id, caption, media_id, media_type, saved_at
            FROM results_history
            ORDER BY id DESC LIMIT %s
        """, (limit,))
        rows = c.fetchall()
        conn.close()
        return rows
    except:
        return []

def get_result_by_id(rid):
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("""
            SELECT id, caption, media_id, media_type, saved_at
            FROM results_history WHERE id=%s
        """, (rid,))
        row = c.fetchone()
        conn.close()
        return row
    except:
        return None

# ══════════════════════════════════════════════════════════════
#  PROFILE BUILDER
# ══════════════════════════════════════════════════════════════

def get_member_days(uid):
    """Return how many days the user has been a member"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT joined FROM users WHERE id=%s", (uid,))
    row = c.fetchone()
    conn.close()
    if not row or not row[0]:
        return 0
    try:
        joined_dt = datetime.strptime(row[0][:16], "%d/%m/%Y %H:%M")
        return max(0, (datetime.now() - joined_dt).days)
    except:
        return 0

# ══════════════════════════════════════════════════════════════
#  FEATURE 7: SUCCESS STORIES — DB helpers
# ══════════════════════════════════════════════════════════════
def add_story(caption, media_id=None, media_type="text"):
    conn = get_conn()
    c = conn.cursor()
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    c.execute(
        "INSERT INTO stories (caption, media_id, media_type, created_at) VALUES (%s,%s,%s,%s) RETURNING id",
        (caption, media_id, media_type, now))
    new_id = c.fetchone()[0]
    conn.commit()
    conn.close()
    return new_id

def get_all_stories():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, caption, media_id, media_type, created_at FROM stories ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "caption": r[1], "media_id": r[2], "media_type": r[3], "created_at": r[4]} for r in rows]

def delete_story(story_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM stories WHERE id=%s RETURNING id", (story_id,))
    deleted = c.fetchone()
    conn.commit()
    conn.close()
    return bool(deleted)

def has_stories():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT 1 FROM stories LIMIT 1")
    row = c.fetchone()
    conn.close()
    return bool(row)

def get_user_vip_progress(uid):
    """Calculate VIP progress 0-100% from activity points"""
    try:
        streak, _ = get_streak(uid)
        referrals = get_referral_count(uid)
        quiz = get_quiz_score(uid)
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT total_spins FROM spin_log WHERE user_id=%s", (uid,))
        row = c.fetchone()
        spins = row[0] if row else 0
        conn.close()
        streak_pts = min(streak * 3, 30)   # max 30
        ref_pts    = min(referrals * 8, 32) # max 32
        spin_pts   = min(spins * 5, 20)    # max 20
        quiz_pts   = min(quiz * 4, 18)     # max 18
        total = streak_pts + ref_pts + spin_pts + quiz_pts
        return min(total, 100)
    except:
        return 0

def render_vip_progress_bar(pct):
    filled = int(pct / 5)   # 20 segments
    bar = "█" * filled + "░" * (20 - filled)
    if pct >= 100:
        label = "🔥 MAX — VIP Ready!"
    elif pct >= 75:
        label = "Almost there! 💎"
    elif pct >= 50:
        label = "Good progress! 🚀"
    elif pct >= 25:
        label = "Keep going! 💪"
    else:
        label = "Just started 🌱"
    return f"[{bar}]\n    {pct}% \u2014 {label}"

def has_early_bird_badge(uid):
    """~30% of users get this fake badge based on uid seed"""
    return (uid % 10) < 3

def build_profile_text(uid, lang):
    days = get_member_days(uid)
    streak_val, _ = update_streak(uid)
    badges = get_user_badges(uid)
    ref_count = get_referral_count(uid)
    quiz_score = get_quiz_score(uid)
    progress = get_user_vip_progress(uid)
    bar = render_vip_progress_bar(progress)

    # Real badges
    badge_list = [ACHIEVEMENTS[b][0] for b in badges if b in ACHIEVEMENTS]
    # Fake Early Bird badge (seed-based)
    if has_early_bird_badge(uid):
        badge_list = ["🌅 Early Bird"] + badge_list
    badge_display = "  ".join(badge_list) if badge_list else "None yet 🌱"

    profile = (
        "👤 *YOUR PROFILE*\n\n"
        f"📅 Member for: *{days} days*\n"
        f"🔥 Daily streak: *{streak_val} days*\n"
        f"👥 People invited: *{ref_count}*\n"
        f"🧠 Quiz score: *{quiz_score}/3*\n\n"
        f"🏅 *Badges:*\n{badge_display}\n\n"
        f"🎯 *VIP Progress:*\n{bar}\n\n"
        "💎 Keep active to unlock VIP access!"
    )
    return profile

# ══════════════════════════════════════════════════════════════
#  CELEBRATION MESSAGES
# ══════════════════════════════════════════════════════════════

def get_celebration_message(days, lang):
    if days == 7:
        msgs = {
            "en": "🎉 *ONE WEEK!* You've been with EVALON for 7 days!\n\n⭐ You're already ahead of 80% of new traders!\n\n💪 Keep going — the best is yet to come!",
            "sw": "🎉 *WIKI MOJA!* Umekuwa na EVALON kwa siku 7!\n\n⭐ Tayari uko mbele ya 80% ya wafanyabiashara wapya!\n\n💪 Endelea — bora zaidi bado inakuja!",
        }
        return msgs.get(lang, msgs["en"])
    elif days == 30:
        msgs = {
            "en": "🏆 *ONE MONTH!* You're a real trader now!\n\n💎 30 days with EVALON — you're in the top tier!\n\n🚀 This is where the magic happens. Stay consistent!",
            "sw": "🏆 *MWEZI MMOJA!* Wewe ni mfanyabiashara wa kweli sasa!\n\n💎 Siku 30 na EVALON — uko kwenye kiwango cha juu!\n\n🚀 Hapa ndipo uchawi unatokea. Endelea kuwa thabiti!",
        }
        return msgs.get(lang, msgs["en"])
    elif days == 90:
        msgs = {
            "en": "👑 *THREE MONTHS!* You're a LEGEND!\n\n🌟 90 days of consistent trading — most people quit after week 1!\n\n💪 You've proven you have what it takes. The sky is the limit!",
            "sw": "👑 *MIEZI MITATU!* Wewe ni HADITHI!\n\n🌟 Siku 90 za biashara thabiti — watu wengi wanakata tamaa baada ya wiki ya kwanza!\n\n💪 Umethibitisha una uwezo. Mbingu ni kikomo!",
        }
        return msgs.get(lang, msgs["en"])
    return None

# ══════════════════════════════════════════════════════════════
#  SMART COMEBACK — week 1, 2, 3
# ══════════════════════════════════════════════════════════════

COMEBACK_MSGS = {
    1: {
        "en": "👋 *Hey {name}! It's been a week!*\n\n🔥 The market has been WILD this week!\n\nTraders who stayed consistent saw amazing results.\n\nDon't miss week 2 — it's usually even BETTER! 💎",
        "sw": "👋 *Habari {name}! Imekuwa wiki!*\n\n🔥 Soko limekuwa LA MSISIMKO wiki hii!\n\nWafanyabiashara waliobaki thabiti walipata matokeo ya ajabu.\n\nUsikose wiki ya 2 — kawaida ni BORA zaidi! 💎",
    },
    2: {
        "en": "🌟 *{name}, you're 2 weeks in!*\n\n💎 This is where real traders are MADE.\n\nThe ones who push through week 2 are the ones who change their lives.\n\nYou've got this. Come back and WIN! 🏆",
        "sw": "🌟 *{name}, uko wiki 2!*\n\n💎 Hapa ndipo wafanyabiashara wa kweli WANAUNDWA.\n\nWale wanaopita wiki ya 2 ndio wanaobadilisha maisha yao.\n\nUnaweza. Rudi na USHINDE! 🏆",
    },
    3: {
        "en": "🚀 *{name} — 3 weeks strong!*\n\n👑 You're in the top 10% of traders just by STAYING.\n\nMost quit in week 1. You're still here.\n\nThat's the trader's mindset. Don't stop now — your breakthrough is CLOSE! ⚡",
        "sw": "🚀 *{name} — Wiki 3 imara!*\n\n👑 Uko kwenye asilimia 10 ya juu ya wafanyabiashara kwa KUBAKI tu.\n\nWengi walikata tamaa wiki ya 1. Bado uko hapa.\n\nHiyo ndiyo akili ya mfanyabiashara. Usiacha sasa — mafanikio yako YAKO KARIBU! ⚡",
    },
}

async def send_smart_comeback(context):
    job_data = context.job.data
    chat_id = job_data["chat_id"]
    name    = job_data["name"]
    lang    = job_data.get("lang", "en")
    week    = job_data.get("week", 1)
    week_msgs = COMEBACK_MSGS.get(week, COMEBACK_MSGS[1])
    text = week_msgs.get(lang, week_msgs["en"]).format(name=name)
    try:
        img = random.choice(SERVICE_PHOTOS)
        await context.bot.send_photo(
            chat_id=chat_id, photo=img, caption=text,
            parse_mode="Markdown", protect_content=True,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🚀 Let's Go!", callback_data="menu_services"),
                InlineKeyboardButton("💬 Support", callback_data="do_support"),
            ]]))
    except:
        try:
            await context.bot.send_message(
                chat_id=chat_id, text=text,
                parse_mode="Markdown", protect_content=True,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🚀 Let's Go!", callback_data="menu_services"),
                ]]))
        except:
            pass

def schedule_smart_comebacks(context, chat_id, name, lang):
    if not context.job_queue:
        return
    for week in [1, 2, 3]:
        job_name = f"comeback_{chat_id}_w{week}"
        for job in context.job_queue.get_jobs_by_name(job_name):
            job.schedule_removal()
        context.job_queue.run_once(
            send_smart_comeback,
            when=week * 7 * 24 * 3600,
            data={"chat_id": chat_id, "name": name, "lang": lang, "week": week},
            name=job_name)

# ══════════════════════════════════════════════════════════════
#  FOMO ENGINE — 30 min after viewing service
# ══════════════════════════════════════════════════════════════

async def send_fomo_message(context):
    job_data = context.job.data
    chat_id = job_data["chat_id"]
    lang    = job_data.get("lang", "en")
    service = job_data.get("service", "our services")
    fomo_msgs = {
        "en": f"👀 *Still thinking about {service}?*\n\nWhile you're deciding, others are already winning...\n\nDon't let hesitation cost you profits. 💰\n\n👇 Take action now:",
        "sw": f"👀 *Bado unafikiri kuhusu {service}?*\n\nUnapoamua, wengine wanashinda tayari...\n\nUsiache kusita kukugharimu faida. 💰\n\n👇 Chukua hatua sasa:",
    }
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=fomo_msgs.get(lang, fomo_msgs["en"]),
            parse_mode="Markdown", protect_content=True,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🚀 Explore Now", callback_data="menu_services")
            ]]))
    except:
        pass

def schedule_fomo(context, chat_id, lang, service_name):
    if not context.job_queue:
        return
    job_name = f"fomo_{chat_id}"
    for job in context.job_queue.get_jobs_by_name(job_name):
        job.schedule_removal()
    context.job_queue.run_once(
        send_fomo_message,
        when=1800,
        data={"chat_id": chat_id, "lang": lang, "service": service_name},
        name=job_name)

# ══════════════════════════════════════════════════════════════
#  ANTI-GHOST SYSTEM — 7 days inactive
# ══════════════════════════════════════════════════════════════

async def send_anti_ghost(context):
    job_data = context.job.data
    chat_id = job_data["chat_id"]
    name    = job_data.get("name", "friend")
    lang    = job_data.get("lang", "en")
    msgs = {
        "en": f"👻 *Hey {name}! Everything okay?*\n\nWe haven't seen you in a while...\n\n🔥 While you were away, traders in our community made serious moves.\n\n💎 Your spot is still here — don't let it go to waste!\n\n👇 Come back:",
        "sw": f"👻 *Hee {name}! Kila kitu sawa?*\n\nHatujakuona kwa muda...\n\n🔥 Ulipokuwa mbali, wafanyabiashara katika jumuiya yetu walifanya vizuri sana.\n\n💎 Nafasi yako bado ipo hapa — usiiacha ipotee!\n\n👇 Rudi:",
    }
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=msgs.get(lang, msgs["en"]),
            parse_mode="Markdown", protect_content=True,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🚀 I'm Back!", callback_data="main_menu")
            ]]))
    except:
        pass

# ══════════════════════════════════════════════════════════════
#  WIN NOTIFICATION
# ══════════════════════════════════════════════════════════════

WIN_NOTIFICATIONS = {
    "en": [
        "🔔 *ALERT:* A VIP member just had a GREAT session!\n\nResults like these happen when you have the right tools. 💪\n\nWant the same edge? 👇",
        "📱 *VIP WIN ALERT:* Another profitable session in the books!\n\nOur community is consistently winning.\n\nReady to join them? 👇",
        "💰 *TRADER ALERT:* Incredible session results today!\n\nThis is what happens with the right strategy and support. 🏆\n\nYour turn? 👇",
    ],
    "sw": [
        "🔔 *ARIFA:* Mwanachama wa VIP amepata kikao KIZURI sana!\n\nMatokeo kama haya hutokea ukiwa na zana sahihi. 💪\n\nUnataka faida hiyo? 👇",
        "📱 *ARIFA YA VIP WIN:* Kikao kingine chenye faida kimekamilika!\n\nJumuiya yetu inashinda kwa uthabiti.\n\nUko tayari kujiunga? 👇",
    ],
}

def get_win_notification(lang):
    pool = WIN_NOTIFICATIONS.get(lang, WIN_NOTIFICATIONS["en"])
    return random.choice(pool)

# ══════════════════════════════════════════════════════════════
#  COMMUNITY VIBE COUNTER (disabled)
# ══════════════════════════════════════════════════════════════

def get_active_traders_count():
    return ""

def build_welcome_text(lang, name, visit_count=1):
    """Build welcome text with smart greeting + daily quote"""
    urgency = get_urgency(lang)
    greeting = get_smart_greeting(lang)
    quote = get_daily_quote()
    base = ui("welcome", lang).format(
        name=escape_md(name), urgency=urgency, business=BUSINESS_NAME)
    if visit_count >= 3:
        scarcity = get_scarcity_msg(lang)
        return f"{greeting}\n\n{base}\n\n{scarcity}\n\n{quote}"
    return f"{greeting}\n\n{base}\n\n{quote}"


# ══════════════════════════════════════════════════════════════
#  SERVICE REPLIES
# ══════════════════════════════════════════════════════════════

SIGNALS_REPLIES = {
    "en": [
        "📊 *VIP SIGNALS — EVALON WINNERS* 🎯\n\n✅ 80–95% Win Rate\n✅ 3–10 signals daily\n✅ Real Forex pairs\n✅ Entry, TP & SL included\n✅ Works on Quotex & Pocket Option\n✅ 24/7 active team\n\n👇 Visit our website:",
        "🎯 *PRECISION SIGNALS* ⚡\n\n🔑 Each signal:\n• Real Forex pair\n• Direction (BUY/SELL)\n• Entry price, TP & SL\n\n📊 Quotex | Pocket Option | All brokers\n\n👇 Get access now:",
        "💎 *EVALON VIP SIGNALS* 🚀\n\n📈 Real price action\n📊 EUR/USD | GBP/USD | USD/JPY | XAU/USD\n⚡ Instant delivery\n\n👇 Start winning:",
    ],
    "sw": [
        "📊 *VIP SIGNALS — EVALON WINNERS* 🎯\n\n✅ Usahihi 80–95%\n✅ Signals 3–10 kila siku\n✅ Forex ya kweli\n✅ Entry, TP & SL\n✅ Quotex & Pocket Option\n\n👇 Tembelea website:",
        "🎯 *SIGNALS ZA USAHIHI* ⚡\n\n🔑 Kila signal:\n• Pair ya forex ya kweli\n• Mwelekeo (BUY/SELL)\n• Bei ya kuingia, TP & SL\n\n👇 Pata ufikiaji:",
    ],
    "ar": ["📊 *إشارات VIP — EVALON* 🎯\n\n✅ دقة 80–95%\n✅ 3–10 إشارات يومياً\n✅ فوركس حقيقي\n✅ دخول، TP و SL\n✅ Quotex و Pocket Option\n\n👇 زر موقعنا:"],
    "zh": ["📊 *VIP信号 — EVALON* 🎯\n\n✅ 80–95%胜率\n✅ 每日3–10个信号\n✅ 真实外汇\n✅ 入场、TP和SL\n✅ Quotex和Pocket Option\n\n👇 访问网站:"],
    "hi": ["📊 *VIP सिग्नल — EVALON* 🎯\n\n✅ 80–95% जीत दर\n✅ प्रतिदिन 3–10 सिग्नल\n✅ असली फॉरेक्स\n✅ Entry, TP और SL\n✅ Quotex और Pocket Option\n\n👇 वेबसाइट:"],
    "ru": ["📊 *VIP СИГНАЛЫ — EVALON* 🎯\n\n✅ Точность 80–95%\n✅ 3–10 сигналов в день\n✅ Реальный форекс\n✅ Вход, TP и SL\n✅ Quotex и Pocket Option\n\n👇 Сайт:"],
    "es": ["📊 *SEÑALES VIP — EVALON* 🎯\n\n✅ Precisión 80–95%\n✅ 3–10 señales diarias\n✅ Forex real\n✅ Entrada, TP y SL\n✅ Quotex y Pocket Option\n\n👇 Web:"],
    "fr": ["📊 *SIGNAUX VIP — EVALON* 🎯\n\n✅ Précision 80–95%\n✅ 3–10 signaux par jour\n✅ Forex réel\n✅ Entrée, TP et SL\n✅ Quotex et Pocket Option\n\n👇 Site:"],
    "pt": ["📊 *SINAIS VIP — EVALON* 🎯\n\n✅ Precisão 80–95%\n✅ 3–10 sinais diários\n✅ Forex real\n✅ Entrada, TP e SL\n✅ Quotex e Pocket Option\n\n👇 Site:"],
    "de": ["📊 *VIP-SIGNALE — EVALON* 🎯\n\n✅ Genauigkeit 80–95%\n✅ 3–10 Signale täglich\n✅ Echter Forex\n✅ Einstieg, TP und SL\n✅ Quotex und Pocket Option\n\n👇 Website:"],
    "ur": ["📊 *VIP سگنلز — EVALON* 🎯\n\n✅ 80–95% درستگی\n✅ روزانہ 3–10 سگنل\n✅ حقیقی فاریکس\n✅ Entry, TP اور SL\n✅ Quotex اور Pocket Option\n\n👇 ویب سائٹ:"],
    "ja": ["📊 *VIPシグナル — EVALON* 🎯\n\n✅ 80–95%勝率\n✅ 1日3–10シグナル\n✅ リアルFX\n✅ エントリー、TPとSL\n✅ QuotexとPocket Option\n\n👇 ウェブサイト:"],
    "it": ["📊 *SEGNALI VIP — EVALON* 🎯\n\n✅ Accuratezza 80-95%\n✅ 3-10 segnali al giorno\n✅ Forex reale\n✅ Entrata, TP e SL\n✅ Quotex e Pocket Option\n\n👇 Sito web:"],
    "ko": ["📊 *VIP 신호 — EVALON* 🎯\n\n✅ 80-95% 승률\n✅ 하루 3-10개 신호\n✅ 실제 외환\n✅ 진입, TP 및 SL\n✅ Quotex 및 Pocket Option\n\n👇 웹사이트:"],
    "tr": ["📊 *VIP SINYALLER — EVALON* 🎯\n\n✅ %80-95 Basari Orani\n✅ Gunluk 3-10 sinyal\n✅ Gercek Forex\n✅ Giris, TP ve SL\n✅ Quotex ve Pocket Option\n\n👇 Web sitesi:"],
    "fa": ["📊 *سیگنال های VIP — EVALON* 🎯\n\n✅ دقت 80-95%\n✅ 3-10 سیگنال روزانه\n✅ فارکس واقعی\n✅ ورود، TP و SL\n✅ Quotex و Pocket Option\n\n👇 وب سایت:"],
    "pl": ["📊 *SYGNALY VIP — EVALON* 🎯\n\n✅ Dokladnosc 80-95%\n✅ 3-10 sygnalow dziennie\n✅ Prawdziwy Forex\n✅ Wejscie, TP i SL\n✅ Quotex i Pocket Option\n\n👇 Strona:"],
    "uk": ["📊 *VIP СИГНАЛИ — EVALON* 🎯\n\n✅ Точнiсть 80-95%\n✅ 3-10 сигналiв на день\n✅ Реальний форекс\n✅ Вхiд, TP i SL\n✅ Quotex i Pocket Option\n\n👇 Сайт:"],
    "kk": ["📊 *VIP СИГНАЛДАР — EVALON* 🎯\n\n✅ Далдiк 80-95%\n✅ Кунiне 3-10 сигнал\n✅ Накты форекс\n✅ Кiру, TP жане SL\n✅ Quotex жане Pocket Option\n\n👇 Сайт:"],
    "cs": ["📊 *VIP SIGNALY — EVALON* 🎯\n\n✅ Presnost 80-95%\n✅ 3-10 signalu denne\n✅ Skutecny Forex\n✅ Vstup, TP a SL\n✅ Quotex a Pocket Option\n\n👇 Web:"],
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
    "ar": ["👥 *التداول الاجتماعي — EVALON* 🔄\n\nانسخ أفضل المتداولين تلقائياً!\n\n✅ نسخ تلقائي\n✅ Pocket Option\n✅ لا خبرة مطلوبة\n\n👇 زر موقعنا:"],
    "zh": ["👥 *社交交易 — EVALON* 🔄\n\n自动复制最佳交易者！\n\n✅ 自动复制\n✅ Pocket Option\n✅ 无需经验\n\n👇 访问网站:"],
    "hi": ["👥 *सोशल ट्रेडिंग — EVALON* 🔄\n\nसर्वश्रेष्ठ ट्रेडर्स को कॉपी करें!\n\n✅ ऑटो-कॉपी\n✅ Pocket Option\n✅ कोई अनुभव नहीं चाहिए\n\n👇 वेबसाइट:"],
    "ru": ["👥 *СОЦИАЛЬНЫЙ ТРЕЙДИНГ — EVALON* 🔄\n\nКопируйте лучших трейдеров автоматически!\n\n✅ Авто-копирование\n✅ Pocket Option\n✅ Опыт не нужен\n\n👇 Сайт:"],
    "es": ["👥 *TRADING SOCIAL — EVALON* 🔄\n\nCopia a los mejores traders automáticamente!\n\n✅ Auto-copia\n✅ Pocket Option\n✅ Sin experiencia necesaria\n\n👇 Web:"],
    "fr": ["👥 *TRADING SOCIAL — EVALON* 🔄\n\nCopiez les meilleurs traders automatiquement!\n\n✅ Auto-copie\n✅ Pocket Option\n✅ Aucune expérience requise\n\n👇 Site:"],
    "pt": ["👥 *TRADING SOCIAL — EVALON* 🔄\n\nCopie os melhores traders automaticamente!\n\n✅ Auto-cópia\n✅ Pocket Option\n✅ Sem experiência necessária\n\n👇 Site:"],
    "de": ["👥 *SOCIAL TRADING — EVALON* 🔄\n\nKopieren Sie die besten Trader automatisch!\n\n✅ Auto-Kopie\n✅ Pocket Option\n✅ Keine Erfahrung nötig\n\n👇 Website:"],
    "ur": ["👥 *سوشل ٹریڈنگ — EVALON* 🔄\n\nبہترین ٹریڈرز کو خودبخود کاپی کریں!\n\n✅ آٹو کاپی\n✅ Pocket Option\n✅ تجربہ ضروری نہیں\n\n👇 ویب سائٹ:"],
    "ja": ["👥 *ソーシャルトレード — EVALON* 🔄\n\nトップトレーダーを自動コピー！\n\n✅ 自動コピー\n✅ Pocket Option\n✅ 経験不要\n\n👇 ウェブサイト:"],
    "it": ["👥 *SOCIAL TRADING — EVALON* 🔄\n\nCopia i migliori trader automaticamente!\n\n✅ Copia automatica\n✅ Pocket Option\n✅ Nessuna esperienza\n\n👇 Sito web:"],
    "ko": ["👥 *소셜 트레이딩 — EVALON* 🔄\n\n최고의 트레이더를 자동으로 복사하세요!\n\n✅ 자동 복사\n✅ Pocket Option\n✅ 경험 불필요\n\n👇 웹사이트:"],
    "tr": ["👥 *SOSYAL TICARET — EVALON* 🔄\n\nEn iyi traderlari otomatik kopyala!\n\n✅ Otomatik kopyalama\n✅ Pocket Option\n✅ Deneyim gerekmez\n\n👇 Web sitesi:"],
    "fa": ["👥 *معاملات اجتماعی — EVALON* 🔄\n\nبهترین معامله گران را کپی کنید!\n\n✅ کپی خودکار\n✅ Pocket Option\n✅ بدون تجربه\n\n👇 وب سایت:"],
    "pl": ["👥 *HANDEL SPOLECZNOSCIOWY — EVALON* 🔄\n\nAutomatycznie kopiuj najlepszych traderow!\n\n✅ Automatyczne kopiowanie\n✅ Pocket Option\n✅ Bez doswiadczenia\n\n👇 Strona:"],
    "uk": ["👥 *СОЦIАЛЬНА ТОРГIВЛЯ — EVALON* 🔄\n\nАвтоматично копiюйте найкращих трейдерiв!\n\n✅ Авто-копiювання\n✅ Pocket Option\n✅ Досвiд не потрiбен\n\n👇 Сайт:"],
    "kk": ["👥 *АЛЕУМЕТТIК САУДА — EVALON* 🔄\n\nYздiк трейдерлердi автоматты кошiрiнiз!\n\n✅ Авто-кошiру\n✅ Pocket Option\n✅ Тажiрибе казет емес\n\n👇 Сайт:"],
    "cs": ["👥 *SOCIALNI OBCHODOVANI — EVALON* 🔄\n\nAutomaticky kopirujte nejlepsi tradery!\n\n✅ Automaticke kopirovani\n✅ Pocket Option\n✅ Bez zkusenosti\n\n👇 Web:"],
}

INDICATOR_REPLIES = {
    "en": [
        "📈 *FREE INDICATOR — EVALON WINNERS* 🎁\n\n100% FREE!\n\n✅ Buy/sell arrows on chart\n✅ All timeframes\n✅ No repaint\n✅ MT4, MT5 & web\n✅ Easy install + guide\n\n📲 Join FREE channel:",
        "🆓 *FREE INDICATOR — NO PAYMENT* 💎\n\n🔧 Non-repainting\n📊 20+ pairs\n⚡ OTC weekend trading\n\n👇 Get FREE:",
    ],
    "sw": [
        "📈 *INDICATOR YA BURE — EVALON* 🎁\n\nBURE KABISA!\n\n✅ Mishale ya BUY/SELL\n✅ Vipindi vyote\n✅ Haibadilishi\n✅ MT4, MT5 na web\n✅ Rahisi kusakinisha\n\n📲 Jiunge na channel ya BURE:",
        "🆓 *INDICATOR BURE* 💎\n\n🔧 Haibadilishi\n📊 Jozi 20+\n⚡ OTC mwishoni mwa wiki\n\n👇 Ipate BURE:",
    ],
    "ar": ["📈 *مؤشر مجاني — EVALON* 🎁\n\n100% مجاني!\n\n✅ أسهم شراء/بيع\n✅ جميع الأطر الزمنية\n✅ لا إعادة رسم\n✅ MT4 و MT5\n\n📲 القناة المجانية:"],
    "zh": ["📈 *免费指标 — EVALON* 🎁\n\n100%免费！\n\n✅ 买卖箭头\n✅ 所有时间框架\n✅ 不重绘\n✅ MT4和MT5\n\n📲 免费频道:"],
    "hi": ["📈 *मुफ्त इंडिकेटर — EVALON* 🎁\n\n100% मुफ्त!\n\n✅ BUY/SELL तीर\n✅ सभी टाइमफ्रेम\n✅ रिपेंट नहीं\n✅ MT4 और MT5\n\n📲 मुफ्त चैनल:"],
    "ru": ["📈 *БЕСПЛАТНЫЙ ИНДИКАТОР — EVALON* 🎁\n\n100% бесплатно!\n\n✅ Стрелки покупки/продажи\n✅ Все таймфреймы\n✅ Без перерисовки\n✅ MT4 и MT5\n\n📲 Бесплатный канал:"],
    "es": ["📈 *INDICADOR GRATIS — EVALON* 🎁\n\n100% gratis!\n\n✅ Flechas de compra/venta\n✅ Todos los marcos de tiempo\n✅ Sin repintar\n✅ MT4 y MT5\n\n📲 Canal gratuito:"],
    "fr": ["📈 *INDICATEUR GRATUIT — EVALON* 🎁\n\n100% gratuit!\n\n✅ Flèches achat/vente\n✅ Tous les délais\n✅ Pas de repeinture\n✅ MT4 et MT5\n\n📲 Canal gratuit:"],
    "pt": ["📈 *INDICADOR GRÁTIS — EVALON* 🎁\n\n100% grátis!\n\n✅ Setas de compra/venda\n✅ Todos os prazos\n✅ Sem repintura\n✅ MT4 e MT5\n\n📲 Canal gratuito:"],
    "de": ["📈 *KOSTENLOSER INDIKATOR — EVALON* 🎁\n\n100% kostenlos!\n\n✅ Kauf/Verkauf Pfeile\n✅ Alle Zeitrahmen\n✅ Kein Neuzeichnen\n✅ MT4 und MT5\n\n📲 Kostenloser Kanal:"],
    "ur": ["📈 *مفت انڈیکیٹر — EVALON* 🎁\n\n100% مفت!\n\n✅ خریداری/فروخت کے تیر\n✅ تمام ٹائم فریم\n✅ دوبارہ پینٹ نہیں\n✅ MT4 اور MT5\n\n📲 مفت چینل:"],
    "ja": ["📈 *無料インジケーター — EVALON* 🎁\n\n100%無料！\n\n✅ 売買矢印\n✅ 全タイムフレーム\n✅ 再描画なし\n✅ MT4とMT5\n\n📲 無料チャンネル:"],
    "it": ["📈 *INDICATORE GRATUITO — EVALON* 🎁\n\n100% GRATIS!\n\n✅ Frecce acquisto/vendita\n✅ Tutti i timeframe\n✅ Nessun repaint\n✅ MT4 e MT5\n\n📲 Canale gratuito:"],
    "ko": ["📈 *무료 인디케이터 — EVALON* 🎁\n\n100% 무료!\n\n✅ 매수/매도 화살표\n✅ 모든 타임프레임\n✅ 리페인트 없음\n✅ MT4 및 MT5\n\n📲 무료 채널:"],
    "tr": ["📈 *UCRETSIZ INDIKATÖR — EVALON* 🎁\n\n100% UCRETSIZ!\n\n✅ Al/Sat oklari\n✅ Tum zaman dilimleri\n✅ Yeniden boyama yok\n✅ MT4 ve MT5\n\n📲 Ucretsiz kanal:"],
    "fa": ["📈 *اندیکاتور رایگان — EVALON* 🎁\n\n100% رایگان!\n\n✅ فلش های خرید/فروش\n✅ همه تایم فریم ها\n✅ بدون ریپینت\n✅ MT4 و MT5\n\n📲 کانال رایگان:"],
    "pl": ["📈 *DARMOWY WSKAZNIK — EVALON* 🎁\n\n100% ZA DARMO!\n\n✅ Strzalki kupna/sprzedazy\n✅ Wszystkie ramy czasowe\n✅ Bez przerysowywania\n✅ MT4 i MT5\n\n📲 Darmowy kanal:"],
    "uk": ["📈 *БЕЗКОШТОВНИЙ IНДИКАТОР — EVALON* 🎁\n\n100% БЕЗКОШТОВНО!\n\n✅ Стрiлки купiвлi/продажу\n✅ Всi таймфрейми\n✅ Без перемальовування\n✅ MT4 i MT5\n\n📲 Безкоштовний канал:"],
    "kk": ["📈 *ТЕГIН ИНДИКАТОР — EVALON* 🎁\n\n100% ТЕГIН!\n\n✅ Сатып алу/сату корсеткiштерi\n✅ Барлык уакыт аралыктары\n✅ Кайта сызу жок\n✅ MT4 жане MT5\n\n📲 Тегiн арна:"],
    "cs": ["📈 *BEZPLATNY INDIKATOR — EVALON* 🎁\n\n100% ZDARMA!\n\n✅ Sipky nakup/prodej\n✅ Vsechny casove ramce\n✅ Bez prekreslování\n✅ MT4 a MT5\n\n📲 Bezplatny kanal:"],
}

AUTOBOT_REPLIES = {
    "en": [
        "🤖 *AUTO TRADING BOT — EVALON* 💎\n\nTrade automatically 24/7!\n\n✅ All brokers supported\n✅ Runs 24/7\n✅ No experience needed\n\n🏦 Quotex | Pocket Option | IQ Option | Deriv\n\n👇 Get it now:",
        "⚡ *EVALON AUTO BOT — 24/7* 🚀\n\nYou focus on life — bot focuses on profits!\n\n🔧 AI entry detection\n📱 Mobile notifications\n🔐 Funds stay in YOUR account\n\n👇 Website:",
    ],
    "sw": [
        "🤖 *AUTO TRADING BOT — EVALON* 💎\n\nBiashara otomatiki 24/7!\n\n✅ Mawakala WOTE\n✅ Inafanya kazi 24/7\n✅ Huhitaji uzoefu\n\n🏦 Quotex | Pocket Option | IQ Option | Deriv\n\n👇 Ipate sasa:",
        "⚡ *EVALON AUTO BOT — 24/7* 🚀\n\nWewe zingatia maisha — bot izingatie faida!\n\n🔧 AI detection\n📱 Arifa za simu\n🔐 Pesa zinabaki kwenye akaunti YAKO\n\n👇 Website:",
    ],
    "ar": ["🤖 *بوت التداول التلقائي — EVALON* 💎\n\nتداول تلقائياً 24/7!\n\n✅ جميع الوسطاء\n✅ يعمل 24/7\n✅ لا خبرة مطلوبة\n\n🏦 Quotex | Pocket Option | IQ Option | Deriv\n\n👇 احصل عليه الآن:"],
    "zh": ["🤖 *自动交易机器人 — EVALON* 💎\n\n24/7自动交易！\n\n✅ 支持所有经纪商\n✅ 24/7运行\n✅ 无需经验\n\n🏦 Quotex | Pocket Option | IQ Option | Deriv\n\n👇 立即获取:"],
    "hi": ["🤖 *ऑटो ट्रेडिंग बॉट — EVALON* 💎\n\n24/7 स्वचालित ट्रेडिंग!\n\n✅ सभी ब्रोकर\n✅ 24/7 चलता है\n✅ कोई अनुभव नहीं चाहिए\n\n🏦 Quotex | Pocket Option | IQ Option | Deriv\n\n👇 अभी पाएं:"],
    "ru": ["🤖 *АВТО ТОРГОВЫЙ БОТ — EVALON* 💎\n\nТоргуйте автоматически 24/7!\n\n✅ Все брокеры\n✅ Работает 24/7\n✅ Опыт не нужен\n\n🏦 Quotex | Pocket Option | IQ Option | Deriv\n\n👇 Получить:"],
    "es": ["🤖 *BOT DE TRADING AUTO — EVALON* 💎\n\nOpera automáticamente 24/7!\n\n✅ Todos los brokers\n✅ Funciona 24/7\n✅ Sin experiencia\n\n🏦 Quotex | Pocket Option | IQ Option | Deriv\n\n👇 Obtener ahora:"],
    "fr": ["🤖 *BOT DE TRADING AUTO — EVALON* 💎\n\nTradez automatiquement 24/7!\n\n✅ Tous les brokers\n✅ Fonctionne 24/7\n✅ Sans expérience\n\n🏦 Quotex | Pocket Option | IQ Option | Deriv\n\n👇 Obtenir maintenant:"],
    "pt": ["🤖 *BOT DE TRADING AUTO — EVALON* 💎\n\nNegocie automaticamente 24/7!\n\n✅ Todos os brokers\n✅ Funciona 24/7\n✅ Sem experiência\n\n🏦 Quotex | Pocket Option | IQ Option | Deriv\n\n👇 Obter agora:"],
    "de": ["🤖 *AUTO-TRADING-BOT — EVALON* 💎\n\nHandeln Sie automatisch 24/7!\n\n✅ Alle Broker\n✅ Läuft 24/7\n✅ Keine Erfahrung nötig\n\n🏦 Quotex | Pocket Option | IQ Option | Deriv\n\n👇 Jetzt holen:"],
    "ur": ["🤖 *آٹو ٹریڈنگ بوٹ — EVALON* 💎\n\n24/7 خودکار ٹریڈنگ!\n\n✅ تمام بروکرز\n✅ 24/7 چلتا ہے\n✅ تجربہ ضروری نہیں\n\n🏦 Quotex | Pocket Option | IQ Option | Deriv\n\n👇 ابھی حاصل کریں:"],
    "ja": ["🤖 *自動取引ボット — EVALON* 💎\n\n24/7自動取引！\n\n✅ 全ブローカー対応\n✅ 24/7稼働\n✅ 経験不要\n\n🏦 Quotex | Pocket Option | IQ Option | Deriv\n\n👇 今すぐ入手:"],
    "it": ["🤖 *BOT AUTOMATICO — EVALON* 💎\n\nOpera automaticamente 24/7!\n\n✅ Tutti i broker\n✅ Funziona 24/7\n✅ Nessuna esperienza\n\n🏦 Quotex | Pocket Option | IQ Option | Deriv\n\n👇 Ottieni ora:"],
    "ko": ["🤖 *자동 트레이딩 봇 — EVALON* 💎\n\n24/7 자동 거래!\n\n✅ 모든 브로커 지원\n✅ 24/7 작동\n✅ 경험 불필요\n\n🏦 Quotex | Pocket Option | IQ Option | Deriv\n\n👇 지금 받기:"],
    "tr": ["🤖 *OTOMATIK BOT — EVALON* 💎\n\n7/24 Otomatik Islem!\n\n✅ Tum brokerlar\n✅ 7/24 calisir\n✅ Deneyim gerekmez\n\n🏦 Quotex | Pocket Option | IQ Option | Deriv\n\n👇 Simdi al:"],
    "fa": ["🤖 *ربات خودکار — EVALON* 💎\n\nمعاملات خودکار 24/7!\n\n✅ همه بروکرها\n✅ 24/7 فعال\n✅ بدون تجربه\n\n🏦 Quotex | Pocket Option | IQ Option | Deriv\n\n👇 همین الان بگیرید:"],
    "pl": ["🤖 *AUTOMATYCZNY BOT — EVALON* 💎\n\nHandluj automatycznie 24/7!\n\n✅ Wszystkie brokery\n✅ Dziala 24/7\n✅ Bez doswiadczenia\n\n🏦 Quotex | Pocket Option | IQ Option | Deriv\n\n👇 Pobierz teraz:"],
    "uk": ["🤖 *АВТОМАТИЧНИЙ БОТ — EVALON* 💎\n\nТоргуйте автоматично 24/7!\n\n✅ Всi брокери\n✅ Працює 24/7\n✅ Досвiд не потрiбен\n\n🏦 Quotex | Pocket Option | IQ Option | Deriv\n\n👇 Отримати:"],
    "kk": ["🤖 *АВТОМАТТЫ БОТ — EVALON* 💎\n\nАвтоматты 24/7 сауда!\n\n✅ Барлык брокерлер\n✅ 24/7 жумыс iстейдi\n✅ Тажiрибе казет емес\n\n🏦 Quotex | Pocket Option | IQ Option | Deriv\n\n👇 Казiр алыныз:"],
    "cs": ["🤖 *AUTOMATICKY BOT — EVALON* 💎\n\nObchodujte automaticky 24/7!\n\n✅ Vsichni brokeři\n✅ Funguje 24/7\n✅ Bez zkusenosti\n\n🏦 Quotex | Pocket Option | IQ Option | Deriv\n\n👇 Ziskat nyni:"],
}

FREEBOT_REPLIES = {
    "en": ["🆓 *FREE MANUAL BOT — EVALON* 🤖\n\nGet our FREE trading bot!\n\n✅ Works on ALL brokers\n✅ Easy to use\n✅ Step-by-step guide\n\nChoose your broker 👇"],
    "sw": ["🆓 *FREE MANUAL BOT — EVALON* 🤖\n\nPata bot yetu ya BURE!\n\n✅ Mawakala WOTE\n✅ Rahisi kutumia\n✅ Mwongozo wa hatua kwa hatua\n\nChagua broker yako 👇"],
    "ar": ["🆓 *بوت مجاني — EVALON* 🤖\n\nاحصل على بوتنا المجاني!\n\n✅ يعمل مع جميع الوسطاء\n✅ سهل الاستخدام\n✅ دليل خطوة بخطوة\n\nاختر وسيطك 👇"],
    "zh": ["🆓 *免费手动机器人 — EVALON* 🤖\n\n获取我们的免费交易机器人！\n\n✅ 适用于所有经纪商\n✅ 易于使用\n✅ 逐步指南\n\n选择您的经纪商 👇"],
    "hi": ["🆓 *मुफ्त मैनुअल बॉट — EVALON* 🤖\n\nहमारा मुफ्त ट्रेडिंग बॉट पाएं!\n\n✅ सभी ब्रोकर पर काम करता है\n✅ उपयोग में आसान\n✅ चरण-दर-चरण गाइड\n\nअपना ब्रोकर चुनें 👇"],
    "ru": ["🆓 *БЕСПЛАТНЫЙ БОТ — EVALON* 🤖\n\nПолучите наш бесплатный торговый бот!\n\n✅ Работает со всеми брокерами\n✅ Прост в использовании\n✅ Пошаговое руководство\n\nВыберите брокера 👇"],
    "es": ["🆓 *BOT MANUAL GRATIS — EVALON* 🤖\n\nObtén nuestro bot de trading GRATIS!\n\n✅ Funciona con todos los brokers\n✅ Fácil de usar\n✅ Guía paso a paso\n\nElige tu broker 👇"],
    "fr": ["🆓 *BOT MANUEL GRATUIT — EVALON* 🤖\n\nObtenez notre bot de trading GRATUIT!\n\n✅ Fonctionne avec tous les brokers\n✅ Facile à utiliser\n✅ Guide étape par étape\n\nChoisissez votre broker 👇"],
    "pt": ["🆓 *BOT MANUAL GRÁTIS — EVALON* 🤖\n\nObtenha nosso bot de trading GRÁTIS!\n\n✅ Funciona com todos os brokers\n✅ Fácil de usar\n✅ Guia passo a passo\n\nEscolha seu broker 👇"],
    "de": ["🆓 *KOSTENLOSER MANUELLER BOT — EVALON* 🤖\n\nHolen Sie sich unseren kostenlosen Trading-Bot!\n\n✅ Funktioniert mit allen Brokern\n✅ Einfach zu bedienen\n✅ Schritt-für-Schritt-Anleitung\n\nWählen Sie Ihren Broker 👇"],
    "ur": ["🆓 *مفت مینوئل بوٹ — EVALON* 🤖\n\nہمارا مفت ٹریڈنگ بوٹ حاصل کریں!\n\n✅ تمام بروکرز پر کام کرتا ہے\n✅ استعمال میں آسان\n✅ مرحلہ وار گائیڈ\n\nاپنا بروکر منتخب کریں 👇"],
    "ja": ["🆓 *無料マニュアルボット — EVALON* 🤖\n\n無料トレーディングボットを入手！\n\n✅ 全ブローカー対応\n✅ 使いやすい\n✅ ステップバイステップガイド\n\nブローカーを選択 👇"],
    "it": ["🆓 *BOT GRATUITO — EVALON* 🤖\n\nOttieni il bot GRATIS!\n\n✅ Tutti i broker\n✅ Facile da usare\n✅ Guida passo passo\n\nScegli il broker 👇"],
    "ko": ["🆓 *무료 봇 — EVALON* 🤖\n\n무료 봇을 받으세요!\n\n✅ 모든 브로커 지원\n✅ 사용하기 쉬움\n✅ 단계별 가이드\n\n브로커 선택 👇"],
    "tr": ["🆓 *UCRETSIZ BOT — EVALON* 🤖\n\nUcretsiz botu al!\n\n✅ Tum brokerlar\n✅ Kullanimi kolay\n✅ Adim adim rehber\n\nBrokerini sec 👇"],
    "fa": ["🆓 *ربات رایگان — EVALON* 🤖\n\nربات رایگان ما را بگیرید!\n\n✅ همه بروکرها\n✅ استفاده آسان\n✅ راهنمای گام به گام\n\nبروکر خود را انتخاب کنید 👇"],
    "pl": ["🆓 *DARMOWY BOT — EVALON* 🤖\n\nZdobadz darmowego bota!\n\n✅ Wszystkie brokery\n✅ Latwy w uzyciu\n✅ Przewodnik krok po kroku\n\nWybierz brokera 👇"],
    "uk": ["🆓 *БЕЗКОШТОВНИЙ БОТ — EVALON* 🤖\n\nОтримайте безкоштовного бота!\n\n✅ Всi брокери\n✅ Простий у використаннi\n✅ Покрокове керiвництво\n\nОберiть брокера 👇"],
    "kk": ["🆓 *ТЕГIН БОТ — EVALON* 🤖\n\nТегiн ботты алыныз!\n\n✅ Барлык брокерлер\n✅ Колданылуы онай\n✅ Кадамдык нускаулык\n\nБрокердi танданыз 👇"],
    "cs": ["🆓 *BEZPLATNY BOT — EVALON* 🤖\n\nZiskejte bezplatneho bota!\n\n✅ Vsichni brokeři\n✅ Snadne pouziti\n✅ Pruvodce krok za krokem\n\nVyberte brokera 👇"],
}

# ══════════════════════════════════════════════════════════════
#  UI TRANSLATIONS — FIXED: All 12 languages fully translated
# ══════════════════════════════════════════════════════════════

UI = {
    "en": {
        "welcome": "👋 Welcome, *{name}!*\n\n{urgency}\n\n🏆 *{business}* — Where winners trade!\n\nWhat would you like to explore? 👇",
        "btn_services": "🏆 Our Services",
        "btn_referral": "🎁 Invite & Earn",
        "btn_stories": "⭐ Success Stories",
        "btn_language": "🌍 Language",
        "btn_spin": "🎰 Try Your Free Access — Lucky Spin!",
        "btn_whats_new": "🆕 What's New Today",
        "btn_vip_results": "🏆 Today's VIP Results",
        "btn_winners": "👑 Winners of the Week",
        "btn_my_streak": "🔥 My Daily Streak",
        "spin_wait": "⏳ Already spun today! Come back in {hours}h {mins}m 🕐",
        "spin_spinning": "🎰 Spinning...",
        "no_news": "📢 *No new updates yet!*\n\nCheck back later — our team posts updates regularly. 🔔",
        "no_vip": "📊 *No VIP results posted yet today!*\n\nJoin our VIP channel to get signals live:\n\nOr check back later — results are posted after each session! ⚡",
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
        "btn_whats_new": "🆕 What's New Today",
        "btn_vip_results": "🏆 Today's VIP Results",
        "btn_winners": "👑 Winners of the Week",
        "btn_my_streak": "🔥 My Daily Streak",
        "no_news": "📢 *No new updates yet!*\n\nCheck back later — our team posts updates regularly. 🔔",
        "no_vip": "📊 *No VIP results posted yet today!*\n\nJoin our VIP channel to get signals live!\n\nOr check back later — results are posted after each session! ⚡",
        "join_msg": "⚠️ *Please join our channel first!*\n\nJoin now and come back! 👇",
        "support_msg": "💬 *Support Request Received!* ✅\n\nOur team will contact you *within 5 hours.* ⏳\n\nPlease keep the bot open! 🙏",
        "fallback_msg": "🤔 I didn't find an answer for that.\n\nWould you like to speak with our support team?",
        "msg_received": "📨 Message received! Our team will reply shortly. 🙏",
        "referral_msg": "🎁 *YOUR REFERRAL LINK*\n\nYour link:\nhttps://t.me/{bot}?start=ref{uid}\n\nPeople invited: *{count}/{min}*\n{bar}\n\nInvite {needed} more to unlock your discount reward!\n{leaderboard}",
        "comeback_msg": "👋 Hey *{name}!* We missed you! 😊\n\n🔥 New signals & opportunities waiting!\n\n💎 *EVALON WINNERS* has exciting updates for you!\n\n👇 Come back and explore:",
        "rating_msg": "⭐ *How was your support experience?*\n\nPlease rate our service:",
        "rating_opinion_msg": "📝 *Thank you for the rating!*\n\nPlease share a short opinion about your experience (or type 'skip' to skip):",
        "rating_thanks": "🙏 Thank you for your feedback, *{name}!* ⭐",
        "poll_msg": "📊 *Quick Question!*\n\nWhich platform do you mainly use?",
        "welcome_video": "🎬 *Welcome to EVALON WINNERS!*\n\nWatch this intro to see how we help traders win! 🏆",
        "services_msg": "🏆 *OUR SERVICES*\n\nChoose a service to learn more 👇",
        "price_msg": "💰 *Pricing & Plans*\n\nVisit our website for latest pricing 👇",
        "join_pending": "⏳ *Request received!*\n\nAdmin will approve shortly. 🙏",
        "auto_clean_msg": "🔄 *Chat refreshed!*\n\nTap below to continue 👇",
        "session_ended": "👋 *Support chat has ended.*\n\nThank you for contacting us! 🙏",
        "btn_tip": "💡 Daily Tip",
        "btn_quiz": "🧠 Quiz",
        "btn_profile": "👤 My Profile",
        "btn_goal": "🎯 Set Goal",
        "btn_results_history": "📅 Past Results",
        "btn_challenge": "💪 Challenge",
        "btn_mood": "😊 My Mood",
        "btn_why_evalon": "🤔 Why EVALON?",
        "btn_win_alert": "🔔 Win Alert",
        "no_results_history": "📅 *No past results yet!*\n\nAdmin will post session results here. Check back soon! ⚡",
    },
    "sw": {
        "welcome": "👋 Karibu, *{name}!*\n\n{urgency}\n\n🏆 *{business}* — Mahali pa washindi!\n\nUnataka kuchunguza nini? 👇",
        "btn_services": "🏆 Huduma Zetu",
        "btn_referral": "🎁 Alika & Pata",
        "btn_stories": "⭐ Hadithi za Mafanikio",
        "btn_language": "🌍 Lugha",
        "btn_spin": "🎰 Jaribu Free Access Yako — Lucky Spin!",
        "btn_whats_new": "🆕 Nini Kipya Leo",
        "btn_vip_results": "🏆 Matokeo ya VIP Leo",
        "btn_winners": "👑 Washindi wa Wiki",
        "btn_my_streak": "🔥 Streak Yangu ya Kila Siku",
        "spin_wait": "⏳ Umeshaspinni leo! Rudi baada ya masaa {hours}h {mins}m 🕐",
        "spin_spinning": "🎰 Inazunguka...",
        "no_news": "📢 *Hakuna habari mpya bado!*\n\nRudi baadaye — timu yetu huchapisha masasisho mara kwa mara. 🔔",
        "no_vip": "📊 *Hakuna matokeo ya VIP bado leo!*\n\nJiunge na channel yetu ya VIP kupata signals moja kwa moja:\n\nAu rudi baadaye — matokeo huchapishwa baada ya kila kipindi! ⚡",
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
        "btn_whats_new": "🆕 Nini Kipya Leo",
        "btn_vip_results": "🏆 Matokeo ya VIP Leo",
        "btn_winners": "👑 Washindi wa Wiki",
        "btn_my_streak": "🔥 Streak Yangu ya Kila Siku",
        "no_news": "📢 *Hakuna habari mpya bado!*\n\nRudi baadaye — timu yetu huchapisha masasisho mara kwa mara. 🔔",
        "no_vip": "📊 *Hakuna matokeo ya VIP bado leo!*\n\nJiunge na channel yetu ya VIP kupata signals moja kwa moja!\n\nAu rudi baadaye — matokeo huchapishwa baada ya kila kipindi! ⚡",
        "join_msg": "⚠️ *Tafadhali jiunge na channel yetu kwanza!*\n\nJiunge sasa na urudi! 👇",
        "support_msg": "💬 *Ombi la Msaada Limepokelewa!* ✅\n\nTimu yetu itawasiliana nawe *ndani ya masaa 5.* ⏳\n\nKaa na bot wazi! 🙏",
        "fallback_msg": "🤔 Sikupata jibu la hilo.\n\nUnataka kuzungumza na timu yetu ya msaada?",
        "msg_received": "📨 Ujumbe umepokelewa! Timu yetu itajibu hivi karibuni. 🙏",
        "referral_msg": "🎁 *KIUNGO CHAKO CHA RUFAA*\n\nKiungo chako:\nhttps://t.me/{bot}?start=ref{uid}\n\nWatu wamealikwa: *{count}/{min}*\n{bar}\n\nAlika {needed} zaidi kufungua tuzo yako!\n{leaderboard}",
        "comeback_msg": "👋 Habari *{name}!* Tulikusahau! 😊\n\n🔥 Signals mpya, fursa mpya!\n\n💎 *EVALON WINNERS* ina mambo mapya!\n\n👇 Rudi na uchunguze:",
        "rating_msg": "⭐ *Huduma ya support ilikuwaje?*\n\nTupa alama:",
        "rating_opinion_msg": "📝 *Asante kwa alama!*\n\nTushirikishe maoni yako mafupi kuhusu uzoefu wako (au andika 'skip' kuruka):",
        "rating_thanks": "🙏 Asante kwa maoni yako, *{name}!* ⭐",
        "poll_msg": "📊 *Swali Moja!*\n\nUnatumia platform ipi zaidi?",
        "welcome_video": "🎬 *Karibu EVALON WINNERS!*\n\nAngalia video hii fupi! 🏆",
        "services_msg": "🏆 *HUDUMA ZETU*\n\nChagua huduma kujifunza zaidi 👇",
        "price_msg": "💰 *Bei na Mipango*\n\nTembelea website 👇",
        "join_pending": "⏳ *Ombi limepokelewa!*\n\nAdmin atakuidhibitisha. 🙏",
        "auto_clean_msg": "🔄 *Chat imesafishwa!*\n\nBonyeza hapa chini kuendelea 👇",
        "session_ended": "👋 *Mazungumzo ya msaada yamekwisha.*\n\nAsante kwa kuwasiliana nasi! 🙏",
        "btn_tip": "💡 Kidokezo cha Leo",
        "btn_quiz": "🧠 Maswali ya Maarifa",
        "btn_profile": "👤 Wasifu Wangu",
        "btn_goal": "🎯 Weka Lengo",
        "btn_results_history": "📅 Matokeo ya Nyuma",
        "btn_challenge": "💪 Changamoto",
        "btn_mood": "😊 Hali Yangu",
        "btn_why_evalon": "🤔 Kwa Nini EVALON?",
        "btn_win_alert": "🔔 Arifa ya Ushindi",
        "no_results_history": "📅 *Hakuna matokeo ya nyuma bado!*\n\nAdmin ataweka matokeo ya vikao hapa. Rudi baadaye! ⚡",
    },
    "ar": {
        "welcome": "👋 مرحباً، *{name}!*\n\n{urgency}\n\n🏆 *{business}* — حيث يتداول الفائزون!\n\nماذا تريد أن تستكشف؟ 👇",
        "btn_services": "🏆 خدماتنا",
        "btn_referral": "🎁 ادعُ واربح",
        "btn_stories": "⭐ قصص النجاح",
        "btn_language": "🌍 اللغة",
        "btn_spin": "🎰 دوران محظوظ — جرب حظك!",
        "spin_wait": "⏳ لقد درت اليوم! عد خلال {hours}h {mins}m 🕐",
        "spin_spinning": "🎰 جاري الدوران...",
        "btn_signals": "📊 إشارات VIP",
        "btn_social": "👥 التداول الاجتماعي",
        "btn_indicator": "📈 مؤشر مجاني",
        "btn_autobot": "🤖 بوت تلقائي",
        "btn_freebot": "🆓 بوت يدوي مجاني",
        "btn_website": "🌐 الموقع والأسعار",
        "btn_support": "💬 التواصل مع الدعم",
        "btn_back": "⬅️ رجوع",
        "btn_restart": "🚀 اضغط للبدء",
        "btn_free_indicator": "📲 احصل على المؤشر المجاني",
        "btn_join": "📢 انضم لقناتنا",
        "btn_poll_quotex": "📊 Quotex",
        "btn_poll_pocket": "💰 Pocket Option",
        "btn_poll_both": "✅ كلاهما",
        "btn_whats_new": "🆕 ما الجديد اليوم",
        "btn_vip_results": "🏆 نتائج VIP اليوم",
        "btn_winners": "👑 فائزو الأسبوع",
        "btn_my_streak": "🔥 سلسلتي اليومية",
        "no_news": "📢 *لا توجد تحديثات جديدة بعد!*\n\nتحقق لاحقاً — يقوم فريقنا بنشر التحديثات بانتظام. 🔔",
        "no_vip": "📊 *لا توجد نتائج VIP اليوم بعد!*\n\nانضم إلى قناة VIP الخاصة بنا للحصول على الإشارات مباشرة!\n\nأو تحقق لاحقاً! ⚡",
        "join_msg": "⚠️ *يرجى الانضمام إلى قناتنا أولاً!*\n\nانضم الآن وعد! 👇",
        "support_msg": "💬 *تم استلام طلب الدعم!* ✅\n\nسيتواصل معك فريقنا *خلال 5 ساعات.* ⏳\n\nيرجى إبقاء البوت مفتوحاً! 🙏",
        "fallback_msg": "🤔 لم أجد إجابة لذلك.\n\nهل تريد التحدث مع فريق الدعم؟",
        "msg_received": "📨 تم استلام الرسالة! سيرد فريقنا قريباً. 🙏",
        "referral_msg": "🎁 *رابط الإحالة الخاص بك*\n\nرابطك:\nhttps://t.me/{bot}?start=ref{uid}\n\nإحالاتك: {count}/{min}\n{bar}\n\nادعُ {needed} آخرين لفتح مكافأتك!\n{leaderboard}",
        "comeback_msg": "👋 مرحباً *{name}!* اشتقنا إليك! 😊\n\n🔥 إشارات جديدة وفرص في انتظارك!\n\n💎 *EVALON WINNERS* لديها تحديثات مثيرة!\n\n👇 عد واستكشف:",
        "rating_msg": "⭐ *كيف كانت تجربة الدعم؟*\n\nيرجى تقييم خدمتنا:",
        "rating_opinion_msg": "📝 *شكراً على التقييم!*\n\nشارك رأيك المختصر عن تجربتك (أو اكتب 'skip' للتخطي):",
        "rating_thanks": "🙏 شكراً على تعليقك، *{name}!* ⭐",
        "poll_msg": "📊 *سؤال سريع!*\n\nأي منصة تستخدم بشكل رئيسي؟",
        "welcome_video": "🎬 *مرحباً بك في EVALON WINNERS!*\n\nشاهد هذه المقدمة! 🏆",
        "services_msg": "🏆 *خدماتنا*\n\nاختر خدمة لمعرفة المزيد 👇",
        "price_msg": "💰 *الأسعار والخطط*\n\nزر موقعنا لأحدث الأسعار 👇",
        "join_pending": "⏳ *تم استلام الطلب!*\n\nسيوافق المشرف قريباً. 🙏",
        "auto_clean_msg": "🔄 *تم تحديث المحادثة!*\n\nاضغط أدناه للمتابعة 👇",
        "session_ended": "👋 *انتهت جلسة الدعم.*\n\nشكراً للتواصل معنا! 🙏",
    },
    "zh": {
        "welcome": "👋 欢迎，*{name}!*\n\n{urgency}\n\n🏆 *{business}* — 赢家交易的地方！\n\n您想探索什么？ 👇",
        "btn_services": "🏆 我们的服务",
        "btn_referral": "🎁 邀请赚钱",
        "btn_stories": "⭐ 成功故事",
        "btn_language": "🌍 语言",
        "btn_spin": "🎰 幸运转盘 — 试试你的运气！",
        "spin_wait": "⏳ 今天已经转过了！{hours}h {mins}m 后回来 🕐",
        "spin_spinning": "🎰 旋转中...",
        "btn_signals": "📊 VIP信号",
        "btn_social": "👥 社交交易",
        "btn_indicator": "📈 免费指标",
        "btn_autobot": "🤖 自动机器人",
        "btn_freebot": "🆓 免费手动机器人",
        "btn_website": "🌐 网站和价格",
        "btn_support": "💬 联系支持",
        "btn_back": "⬅️ 返回",
        "btn_restart": "🚀 点击开始",
        "btn_free_indicator": "📲 获取免费指标",
        "btn_join": "📢 加入我们的频道",
        "btn_poll_quotex": "📊 Quotex",
        "btn_poll_pocket": "💰 Pocket Option",
        "btn_poll_both": "✅ 两者都用",
        "btn_whats_new": "🆕 今日新动态",
        "btn_vip_results": "🏆 今日VIP成果",
        "btn_winners": "👑 本周获胜者",
        "btn_my_streak": "🔥 我的每日连胜",
        "no_news": "📢 *暂无新更新！*\n\n稍后再查看 — 我们的团队定期发布更新。 🔔",
        "no_vip": "📊 *今天还没有VIP成果！*\n\n加入我们的VIP频道实时获取信号！\n\n或稍后再查看！ ⚡",
        "join_msg": "⚠️ *请先加入我们的频道！*\n\n现在加入并返回！ 👇",
        "support_msg": "💬 *支持请求已收到！* ✅\n\n我们的团队将在 *5小时内* 联系您。 ⏳\n\n请保持机器人开启！ 🙏",
        "fallback_msg": "🤔 我没有找到答案。\n\n您想与我们的支持团队交谈吗？",
        "msg_received": "📨 消息已收到！我们的团队将很快回复。 🙏",
        "referral_msg": "🎁 *您的推荐链接*\n\n您的链接：\nhttps://t.me/{bot}?start=ref{uid}\n\n您的推荐：{count}/{min}\n{bar}\n\n再邀请 {needed} 人解锁奖励！\n{leaderboard}",
        "comeback_msg": "👋 嘿 *{name}!* 我们想念你！ 😊\n\n🔥 新信号和机会等着你！\n\n💎 *EVALON WINNERS* 有令人兴奋的更新！\n\n👇 回来探索：",
        "rating_msg": "⭐ *您的支持体验如何？*\n\n请为我们的服务评分：",
        "rating_opinion_msg": "📝 *感谢您的评分！*\n\n请分享您对体验的简短意见（或输入 'skip' 跳过）：",
        "rating_thanks": "🙏 感谢您的反馈，*{name}!* ⭐",
        "poll_msg": "📊 *快速问题！*\n\n您主要使用哪个平台？",
        "welcome_video": "🎬 *欢迎来到 EVALON WINNERS！*\n\n观看此介绍！ 🏆",
        "services_msg": "🏆 *我们的服务*\n\n选择服务了解更多 👇",
        "price_msg": "💰 *价格和计划*\n\n访问我们的网站查看最新价格 👇",
        "join_pending": "⏳ *请求已收到！*\n\n管理员将很快批准。 🙏",
        "auto_clean_msg": "🔄 *聊天已刷新！*\n\n点击下方继续 👇",
        "session_ended": "👋 *支持聊天已结束。*\n\n感谢您联系我们！ 🙏",
    },
    "hi": {
        "welcome": "👋 स्वागत है, *{name}!*\n\n{urgency}\n\n🏆 *{business}* — जहाँ विजेता व्यापार करते हैं!\n\nआप क्या जानना चाहते हैं? 👇",
        "btn_services": "🏆 हमारी सेवाएं",
        "btn_referral": "🎁 आमंत्रित करें & कमाएं",
        "btn_stories": "⭐ सफलता की कहानियां",
        "btn_language": "🌍 भाषा",
        "btn_spin": "🎰 लकी स्पिन — अपनी किस्मत आजमाएं!",
        "spin_wait": "⏳ आज पहले से स्पिन किया! {hours}h {mins}m में वापस आएं 🕐",
        "spin_spinning": "🎰 घुमा रहा है...",
        "btn_signals": "📊 VIP सिग्नल",
        "btn_social": "👥 सोशल ट्रेडिंग",
        "btn_indicator": "📈 मुफ्त इंडिकेटर",
        "btn_autobot": "🤖 ऑटो बॉट",
        "btn_freebot": "🆓 मुफ्त मैनुअल बॉट",
        "btn_website": "🌐 वेबसाइट और मूल्य",
        "btn_support": "💬 सहायता से संपर्क करें",
        "btn_back": "⬅️ वापस",
        "btn_restart": "🚀 शुरू करने के लिए टैप करें",
        "btn_free_indicator": "📲 मुफ्त इंडिकेटर पाएं",
        "btn_join": "📢 हमारे चैनल से जुड़ें",
        "btn_poll_quotex": "📊 Quotex",
        "btn_poll_pocket": "💰 Pocket Option",
        "btn_poll_both": "✅ दोनों",
        "btn_whats_new": "🆕 आज क्या नया है",
        "btn_vip_results": "🏆 आज के VIP परिणाम",
        "btn_winners": "👑 सप्ताह के विजेता",
        "btn_my_streak": "🔥 मेरी दैनिक स्ट्रीक",
        "no_news": "📢 *अभी कोई नया अपडेट नहीं!*\n\nबाद में जांचें — हमारी टीम नियमित रूप से अपडेट पोस्ट करती है। 🔔",
        "no_vip": "📊 *आज अभी तक कोई VIP परिणाम नहीं!*\n\nसिग्नल सीधे पाने के लिए हमारे VIP चैनल से जुड़ें!\n\nया बाद में जांचें! ⚡",
        "join_msg": "⚠️ *कृपया पहले हमारे चैनल से जुड़ें!*\n\nअभी जुड़ें और वापस आएं! 👇",
        "support_msg": "💬 *सहायता अनुरोध प्राप्त हुआ!* ✅\n\nहमारी टीम *5 घंटे के भीतर* आपसे संपर्क करेगी। ⏳\n\nकृपया बॉट खुला रखें! 🙏",
        "fallback_msg": "🤔 मुझे इसका उत्तर नहीं मिला।\n\nक्या आप हमारी सहायता टीम से बात करना चाहते हैं?",
        "msg_received": "📨 संदेश प्राप्त हुआ! हमारी टीम जल्द ही जवाब देगी। 🙏",
        "referral_msg": "🎁 *आपका रेफरल लिंक*\n\nआपका लिंक:\nhttps://t.me/{bot}?start=ref{uid}\n\nआपके रेफरल: {count}/{min}\n{bar}\n\nइनाम अनलॉक करने के लिए {needed} और को आमंत्रित करें!\n{leaderboard}",
        "comeback_msg": "👋 हेलो *{name}!* हमने आपको याद किया! 😊\n\n🔥 नए सिग्नल और अवसर इंतजार कर रहे हैं!\n\n💎 *EVALON WINNERS* के पास आपके लिए रोमांचक अपडेट हैं!\n\n👇 वापस आएं और एक्सप्लोर करें:",
        "rating_msg": "⭐ *आपका सहायता अनुभव कैसा था?*\n\nकृपया हमारी सेवा को रेट करें:",
        "rating_opinion_msg": "📝 *रेटिंग के लिए धन्यवाद!*\n\nकृपया अपने अनुभव के बारे में एक छोटी राय साझा करें (या 'skip' टाइप करें):",
        "rating_thanks": "🙏 आपकी प्रतिक्रिया के लिए धन्यवाद, *{name}!* ⭐",
        "poll_msg": "📊 *त्वरित प्रश्न!*\n\nआप मुख्य रूप से कौन सा प्लेटफॉर्म उपयोग करते हैं?",
        "welcome_video": "🎬 *EVALON WINNERS में आपका स्वागत है!*\n\nयह परिचय वीडियो देखें! 🏆",
        "services_msg": "🏆 *हमारी सेवाएं*\n\nअधिक जानने के लिए एक सेवा चुनें 👇",
        "price_msg": "💰 *मूल्य और योजनाएं*\n\nनवीनतम मूल्य के लिए हमारी वेबसाइट पर जाएं 👇",
        "join_pending": "⏳ *अनुरोध प्राप्त हुआ!*\n\nएडमिन जल्द ही अनुमोदन करेगा। 🙏",
        "auto_clean_msg": "🔄 *चैट रिफ्रेश हुई!*\n\nजारी रखने के लिए नीचे टैप करें 👇",
        "session_ended": "👋 *सहायता चैट समाप्त हो गई।*\n\nहमसे संपर्क करने के लिए धन्यवाद! 🙏",
    },
    "ru": {
        "welcome": "👋 Добро пожаловать, *{name}!*\n\n{urgency}\n\n🏆 *{business}* — Где торгуют победители!\n\nЧто вы хотите узнать? 👇",
        "btn_services": "🏆 Наши услуги",
        "btn_referral": "🎁 Пригласи и зарабатывай",
        "btn_stories": "⭐ Истории успеха",
        "btn_language": "🌍 Язык",
        "btn_spin": "🎰 Счастливый Спин — Испытайте Удачу!",
        "spin_wait": "⏳ Уже крутили сегодня! Вернитесь через {hours}h {mins}m 🕐",
        "spin_spinning": "🎰 Вращается...",
        "btn_signals": "📊 VIP сигналы",
        "btn_social": "👥 Социальная торговля",
        "btn_indicator": "📈 Бесплатный индикатор",
        "btn_autobot": "🤖 Авто бот",
        "btn_freebot": "🆓 Бесплатный ручной бот",
        "btn_website": "🌐 Сайт и цены",
        "btn_support": "💬 Связаться с поддержкой",
        "btn_back": "⬅️ Назад",
        "btn_restart": "🚀 Нажмите для начала",
        "btn_free_indicator": "📲 Получить бесплатный индикатор",
        "btn_join": "📢 Присоединиться к каналу",
        "btn_poll_quotex": "📊 Quotex",
        "btn_poll_pocket": "💰 Pocket Option",
        "btn_poll_both": "✅ Оба",
        "btn_whats_new": "🆕 Что нового сегодня",
        "btn_vip_results": "🏆 Результаты VIP сегодня",
        "btn_winners": "👑 Победители недели",
        "btn_my_streak": "🔥 Моя ежедневная серия",
        "no_news": "📢 *Новых обновлений пока нет!*\n\nПроверьте позже — наша команда публикует обновления регулярно. 🔔",
        "no_vip": "📊 *Результаты VIP сегодня ещё не опубликованы!*\n\nПрисоединитесь к нашему VIP-каналу!\n\nИли проверьте позже! ⚡",
        "join_msg": "⚠️ *Пожалуйста, сначала присоединитесь к нашему каналу!*\n\nПрисоединитесь сейчас и возвращайтесь! 👇",
        "support_msg": "💬 *Запрос поддержки получен!* ✅\n\nНаша команда свяжется с вами *в течение 5 часов.* ⏳\n\nПожалуйста, держите бота открытым! 🙏",
        "fallback_msg": "🤔 Я не нашел ответа на это.\n\nХотите поговорить с нашей командой поддержки?",
        "msg_received": "📨 Сообщение получено! Наша команда ответит скоро. 🙏",
        "referral_msg": "🎁 *ВАША РЕФЕРАЛЬНАЯ ССЫЛКА*\n\nВаша ссылка:\nhttps://t.me/{bot}?start=ref{uid}\n\nВаши рефералы: {count}/{min}\n{bar}\n\nПригласите ещё {needed} для разблокировки награды!\n{leaderboard}",
        "comeback_msg": "👋 Привет *{name}!* Мы скучали по тебе! 😊\n\n🔥 Новые сигналы и возможности ждут!\n\n💎 *EVALON WINNERS* имеет захватывающие обновления!\n\n👇 Возвращайся и исследуй:",
        "rating_msg": "⭐ *Как прошел ваш опыт поддержки?*\n\nПожалуйста, оцените наш сервис:",
        "rating_opinion_msg": "📝 *Спасибо за оценку!*\n\nПоделитесь кратким мнением о вашем опыте (или напишите 'skip' для пропуска):",
        "rating_thanks": "🙏 Спасибо за ваш отзыв, *{name}!* ⭐",
        "poll_msg": "📊 *Быстрый вопрос!*\n\nКакую платформу вы используете?",
        "welcome_video": "🎬 *Добро пожаловать в EVALON WINNERS!*\n\nПосмотрите это введение! 🏆",
        "services_msg": "🏆 *НАШИ УСЛУГИ*\n\nВыберите услугу, чтобы узнать больше 👇",
        "price_msg": "💰 *Цены и планы*\n\nПосетите наш сайт для актуальных цен 👇",
        "join_pending": "⏳ *Запрос получен!*\n\nАдмин одобрит скоро. 🙏",
        "auto_clean_msg": "🔄 *Чат обновлен!*\n\nНажмите ниже для продолжения 👇",
        "session_ended": "👋 *Чат поддержки завершен.*\n\nСпасибо за обращение! 🙏",
    },
    "es": {
        "welcome": "👋 Bienvenido, *{name}!*\n\n{urgency}\n\n🏆 *{business}* — ¡Donde comercian los ganadores!\n\n¿Qué deseas explorar? 👇",
        "btn_services": "🏆 Nuestros Servicios",
        "btn_referral": "🎁 Invitar y Ganar",
        "btn_stories": "⭐ Historias de Éxito",
        "btn_language": "🌍 Idioma",
        "btn_signals": "📊 Señales VIP",
        "btn_social": "👥 Trading Social",
        "btn_indicator": "📈 Indicador Gratis",
        "btn_autobot": "🤖 Bot Automático",
        "btn_freebot": "🆓 Bot Manual Gratis",
        "btn_website": "🌐 Sitio Web y Precios",
        "btn_support": "💬 Contactar Soporte",
        "btn_back": "⬅️ Atrás",
        "btn_restart": "🚀 Toca para Comenzar",
        "btn_free_indicator": "📲 Obtener Indicador GRATIS",
        "btn_join": "📢 Únete a Nuestro Canal",
        "btn_poll_quotex": "📊 Quotex",
        "btn_poll_pocket": "💰 Pocket Option",
        "btn_poll_both": "✅ Ambos",
        "btn_spin": "🎰 Giro de Suerte — ¡Prueba tu Suerte!",
        "spin_wait": "⏳ Ya giraste hoy! Vuelve en {hours}h {mins}m 🕐",
        "spin_spinning": "🎰 Girando...",
        "btn_whats_new": "🆕 Qué hay de nuevo hoy",
        "btn_vip_results": "🏆 Resultados VIP de hoy",
        "btn_winners": "👑 Ganadores de la semana",
        "btn_my_streak": "🔥 Mi racha diaria",
        "no_news": "📢 *¡No hay nuevas actualizaciones todavía!*\n\nVuelve más tarde — nuestro equipo publica actualizaciones regularmente. 🔔",
        "no_vip": "📊 *¡No hay resultados VIP publicados hoy todavía!*\n\n¡Únete a nuestro canal VIP para recibir señales en vivo!\n\n¡O vuelve más tarde! ⚡",
        "join_msg": "⚠️ *¡Por favor únete a nuestro canal primero!*\n\n¡Únete ahora y vuelve! 👇",
        "support_msg": "💬 *¡Solicitud de soporte recibida!* ✅\n\nNuestro equipo te contactará *en 5 horas.* ⏳\n\n¡Mantén el bot abierto! 🙏",
        "fallback_msg": "🤔 No encontré respuesta a eso.\n\n¿Te gustaría hablar con nuestro equipo de soporte?",
        "msg_received": "📨 ¡Mensaje recibido! Nuestro equipo responderá pronto. 🙏",
        "referral_msg": "🎁 *TU ENLACE DE REFERIDO*\n\nTu enlace:\nhttps://t.me/{bot}?start=ref{uid}\n\nTus referidos: {count}/{min}\n{bar}\n\n¡Invita {needed} más para desbloquear tu recompensa!\n{leaderboard}",
        "comeback_msg": "👋 ¡Hola *{name}!* ¡Te echamos de menos! 😊\n\n🔥 ¡Nuevas señales y oportunidades esperan!\n\n💎 ¡*EVALON WINNERS* tiene actualizaciones emocionantes!\n\n👇 Vuelve y explora:",
        "rating_msg": "⭐ *¿Cómo fue tu experiencia de soporte?*\n\nPor favor califica nuestro servicio:",
        "rating_opinion_msg": "📝 *¡Gracias por la calificación!*\n\nComparte una opinión breve sobre tu experiencia (o escribe 'skip' para omitir):",
        "rating_thanks": "🙏 ¡Gracias por tu opinión, *{name}!* ⭐",
        "poll_msg": "📊 *¡Pregunta rápida!*\n\n¿Qué plataforma usas principalmente?",
        "welcome_video": "🎬 *¡Bienvenido a EVALON WINNERS!*\n\n¡Mira esta introducción! 🏆",
        "services_msg": "🏆 *NUESTROS SERVICIOS*\n\nElige un servicio para saber más 👇",
        "price_msg": "💰 *Precios y Planes*\n\nVisita nuestro sitio web para precios actuales 👇",
        "join_pending": "⏳ *¡Solicitud recibida!*\n\nEl admin aprobará pronto. 🙏",
        "auto_clean_msg": "🔄 *¡Chat actualizado!*\n\nToca abajo para continuar 👇",
        "session_ended": "👋 *El chat de soporte ha finalizado.*\n\n¡Gracias por contactarnos! 🙏",
    },
    "fr": {
        "welcome": "👋 Bienvenue, *{name}!*\n\n{urgency}\n\n🏆 *{business}* — Là où les gagnants tradent!\n\nQue voulez-vous explorer? 👇",
        "btn_services": "🏆 Nos Services",
        "btn_referral": "🎁 Inviter et Gagner",
        "btn_stories": "⭐ Histoires de Succès",
        "btn_language": "🌍 Langue",
        "btn_signals": "📊 Signaux VIP",
        "btn_social": "👥 Trading Social",
        "btn_indicator": "📈 Indicateur Gratuit",
        "btn_autobot": "🤖 Bot Automatique",
        "btn_freebot": "🆓 Bot Manuel Gratuit",
        "btn_website": "🌐 Site Web et Prix",
        "btn_support": "💬 Contacter le Support",
        "btn_back": "⬅️ Retour",
        "btn_restart": "🚀 Appuyez pour Commencer",
        "btn_free_indicator": "📲 Obtenir l'Indicateur GRATUIT",
        "btn_join": "📢 Rejoindre Notre Canal",
        "btn_poll_quotex": "📊 Quotex",
        "btn_poll_pocket": "💰 Pocket Option",
        "btn_poll_both": "✅ Les Deux",
        "btn_spin": "🎰 Spin Chanceux — Tentez Votre Chance!",
        "spin_wait": "⏳ Déjà tourné aujourd'hui! Revenez dans {hours}h {mins}m 🕐",
        "spin_spinning": "🎰 Tourne...",
        "btn_whats_new": "🆕 Quoi de neuf aujourd'hui",
        "btn_vip_results": "🏆 Résultats VIP aujourd'hui",
        "btn_winners": "👑 Gagnants de la semaine",
        "btn_my_streak": "🔥 Ma série quotidienne",
        "no_news": "📢 *Pas encore de nouvelles mises à jour!*\n\nRevenez plus tard — notre équipe publie régulièrement. 🔔",
        "no_vip": "📊 *Pas encore de résultats VIP publiés aujourd'hui!*\n\nRejoignez notre canal VIP pour recevoir des signaux en direct!\n\nOu revenez plus tard! ⚡",
        "join_msg": "⚠️ *Veuillez d'abord rejoindre notre canal!*\n\nRejoignez maintenant et revenez! 👇",
        "support_msg": "💬 *Demande de support reçue!* ✅\n\nNotre équipe vous contactera *dans les 5 heures.* ⏳\n\nGardez le bot ouvert! 🙏",
        "fallback_msg": "🤔 Je n'ai pas trouvé de réponse.\n\nVoulez-vous parler à notre équipe de support?",
        "msg_received": "📨 Message reçu! Notre équipe répondra bientôt. 🙏",
        "referral_msg": "🎁 *VOTRE LIEN DE PARRAINAGE*\n\nVotre lien:\nhttps://t.me/{bot}?start=ref{uid}\n\nVos parrainages: {count}/{min}\n{bar}\n\nInvitez {needed} de plus pour débloquer votre récompense!\n{leaderboard}",
        "comeback_msg": "👋 Salut *{name}!* Vous nous avez manqué! 😊\n\n🔥 Nouveaux signaux et opportunités vous attendent!\n\n💎 *EVALON WINNERS* a des mises à jour passionnantes!\n\n👇 Revenez et explorez:",
        "rating_msg": "⭐ *Comment s'est passée votre expérience de support?*\n\nVeuillez noter notre service:",
        "rating_opinion_msg": "📝 *Merci pour la note!*\n\nPartagez une brève opinion sur votre expérience (ou écrivez 'skip' pour passer):",
        "rating_thanks": "🙏 Merci pour votre avis, *{name}!* ⭐",
        "poll_msg": "📊 *Question rapide!*\n\nQuelle plateforme utilisez-vous principalement?",
        "welcome_video": "🎬 *Bienvenue chez EVALON WINNERS!*\n\nRegardez cette introduction! 🏆",
        "services_msg": "🏆 *NOS SERVICES*\n\nChoisissez un service pour en savoir plus 👇",
        "price_msg": "💰 *Prix et Plans*\n\nVisitez notre site pour les derniers prix 👇",
        "join_pending": "⏳ *Demande reçue!*\n\nL'admin approuvera bientôt. 🙏",
        "auto_clean_msg": "🔄 *Chat actualisé!*\n\nAppuyez ci-dessous pour continuer 👇",
        "session_ended": "👋 *Le chat de support est terminé.*\n\nMerci de nous avoir contactés! 🙏",
    },
    "pt": {
        "welcome": "👋 Bem-vindo, *{name}!*\n\n{urgency}\n\n🏆 *{business}* — Onde os vencedores negociam!\n\nO que você quer explorar? 👇",
        "btn_services": "🏆 Nossos Serviços",
        "btn_referral": "🎁 Convidar e Ganhar",
        "btn_stories": "⭐ Histórias de Sucesso",
        "btn_language": "🌍 Idioma",
        "btn_signals": "📊 Sinais VIP",
        "btn_social": "👥 Trading Social",
        "btn_indicator": "📈 Indicador Grátis",
        "btn_autobot": "🤖 Bot Automático",
        "btn_freebot": "🆓 Bot Manual Grátis",
        "btn_website": "🌐 Site e Preços",
        "btn_support": "💬 Contatar Suporte",
        "btn_back": "⬅️ Voltar",
        "btn_restart": "🚀 Toque para Começar",
        "btn_free_indicator": "📲 Obter Indicador GRÁTIS",
        "btn_join": "📢 Junte-se ao Nosso Canal",
        "btn_poll_quotex": "📊 Quotex",
        "btn_poll_pocket": "💰 Pocket Option",
        "btn_poll_both": "✅ Ambos",
        "btn_spin": "🎰 Giro da Sorte — Tente sua Sorte!",
        "spin_wait": "⏳ Já girou hoje! Volte em {hours}h {mins}m 🕐",
        "spin_spinning": "🎰 Girando...",
        "btn_whats_new": "🆕 O que há de novo hoje",
        "btn_vip_results": "🏆 Resultados VIP de hoje",
        "btn_winners": "👑 Vencedores da semana",
        "btn_my_streak": "🔥 Minha sequência diária",
        "no_news": "📢 *Ainda não há novas atualizações!*\n\nVolte mais tarde — nossa equipe publica atualizações regularmente. 🔔",
        "no_vip": "📊 *Ainda não há resultados VIP publicados hoje!*\n\nJunte-se ao nosso canal VIP para receber sinais ao vivo!\n\nOu volte mais tarde! ⚡",
        "join_msg": "⚠️ *Por favor, junte-se ao nosso canal primeiro!*\n\nJunte-se agora e volte! 👇",
        "support_msg": "💬 *Solicitação de suporte recebida!* ✅\n\nNossa equipe entrará em contato *em 5 horas.* ⏳\n\nMantenha o bot aberto! 🙏",
        "fallback_msg": "🤔 Não encontrei resposta para isso.\n\nGostaria de falar com nossa equipe de suporte?",
        "msg_received": "📨 Mensagem recebida! Nossa equipe responderá em breve. 🙏",
        "referral_msg": "🎁 *SEU LINK DE REFERÊNCIA*\n\nSeu link:\nhttps://t.me/{bot}?start=ref{uid}\n\nSuas referências: {count}/{min}\n{bar}\n\nConvide {needed} a mais para desbloquear sua recompensa!\n{leaderboard}",
        "comeback_msg": "👋 Olá *{name}!* Sentimos sua falta! 😊\n\n🔥 Novos sinais e oportunidades aguardando!\n\n💎 *EVALON WINNERS* tem atualizações emocionantes!\n\n👇 Volte e explore:",
        "rating_msg": "⭐ *Como foi sua experiência de suporte?*\n\nPor favor, avalie nosso serviço:",
        "rating_opinion_msg": "📝 *Obrigado pela avaliação!*\n\nCompartilhe uma opinião breve sobre sua experiência (ou escreva 'skip' para pular):",
        "rating_thanks": "🙏 Obrigado pelo seu feedback, *{name}!* ⭐",
        "poll_msg": "📊 *Pergunta rápida!*\n\nQual plataforma você usa principalmente?",
        "welcome_video": "🎬 *Bem-vindo ao EVALON WINNERS!*\n\nAssista a esta introdução! 🏆",
        "services_msg": "🏆 *NOSSOS SERVIÇOS*\n\nEscolha um serviço para saber mais 👇",
        "price_msg": "💰 *Preços e Planos*\n\nVisite nosso site para os preços mais recentes 👇",
        "join_pending": "⏳ *Solicitação recebida!*\n\nO admin aprovará em breve. 🙏",
        "auto_clean_msg": "🔄 *Chat atualizado!*\n\nToque abaixo para continuar 👇",
        "session_ended": "👋 *O chat de suporte foi encerrado.*\n\nObrigado por entrar em contato! 🙏",
    },
    "de": {
        "welcome": "👋 Willkommen, *{name}!*\n\n{urgency}\n\n🏆 *{business}* — Wo Gewinner handeln!\n\nWas möchten Sie erkunden? 👇",
        "btn_services": "🏆 Unsere Dienste",
        "btn_referral": "🎁 Einladen und Verdienen",
        "btn_stories": "⭐ Erfolgsgeschichten",
        "btn_language": "🌍 Sprache",
        "btn_signals": "📊 VIP Signale",
        "btn_social": "👥 Social Trading",
        "btn_indicator": "📈 Kostenloser Indikator",
        "btn_autobot": "🤖 Auto Bot",
        "btn_freebot": "🆓 Kostenloser manueller Bot",
        "btn_website": "🌐 Website und Preise",
        "btn_support": "💬 Support kontaktieren",
        "btn_back": "⬅️ Zurück",
        "btn_restart": "🚀 Tippen zum Starten",
        "btn_free_indicator": "📲 Kostenlosen Indikator holen",
        "btn_join": "📢 Unserem Kanal beitreten",
        "btn_poll_quotex": "📊 Quotex",
        "btn_poll_pocket": "💰 Pocket Option",
        "btn_poll_both": "✅ Beide",
        "btn_spin": "🎰 Glücksrad — Versuchen Sie Ihr Glück!",
        "spin_wait": "⏳ Heute bereits gedreht! Kommen Sie in {hours}h {mins}m zurück 🕐",
        "spin_spinning": "🎰 Dreht sich...",
        "btn_whats_new": "🆕 Was gibt es heute Neues",
        "btn_vip_results": "🏆 Heutige VIP-Ergebnisse",
        "btn_winners": "👑 Gewinner der Woche",
        "btn_my_streak": "🔥 Meine tägliche Serie",
        "no_news": "📢 *Noch keine neuen Updates!*\n\nSchauen Sie später vorbei — unser Team veröffentlicht regelmäßig Updates. 🔔",
        "no_vip": "📊 *Heute noch keine VIP-Ergebnisse veröffentlicht!*\n\nTreten Sie unserem VIP-Kanal bei!\n\nOder schauen Sie später vorbei! ⚡",
        "join_msg": "⚠️ *Bitte treten Sie zuerst unserem Kanal bei!*\n\nJetzt beitreten und zurückkommen! 👇",
        "support_msg": "💬 *Support-Anfrage erhalten!* ✅\n\nUnser Team wird Sie *innerhalb von 5 Stunden* kontaktieren. ⏳\n\nBitte halten Sie den Bot offen! 🙏",
        "fallback_msg": "🤔 Ich habe keine Antwort darauf gefunden.\n\nMöchten Sie mit unserem Support-Team sprechen?",
        "msg_received": "📨 Nachricht erhalten! Unser Team wird bald antworten. 🙏",
        "referral_msg": "🎁 *IHR EMPFEHLUNGSLINK*\n\nIhr Link:\nhttps://t.me/{bot}?start=ref{uid}\n\nIhre Empfehlungen: {count}/{min}\n{bar}\n\nLaden Sie {needed} mehr ein, um Ihre Belohnung freizuschalten!\n{leaderboard}",
        "comeback_msg": "👋 Hey *{name}!* Wir haben Sie vermisst! 😊\n\n🔥 Neue Signale und Möglichkeiten warten!\n\n💎 *EVALON WINNERS* hat aufregende Updates!\n\n👇 Kommen Sie zurück und erkunden Sie:",
        "rating_msg": "⭐ *Wie war Ihre Support-Erfahrung?*\n\nBitte bewerten Sie unseren Service:",
        "rating_opinion_msg": "📝 *Danke für die Bewertung!*\n\nTeilen Sie eine kurze Meinung zu Ihrer Erfahrung mit (oder schreiben Sie 'skip' zum Überspringen):",
        "rating_thanks": "🙏 Danke für Ihr Feedback, *{name}!* ⭐",
        "poll_msg": "📊 *Schnelle Frage!*\n\nWelche Plattform nutzen Sie hauptsächlich?",
        "welcome_video": "🎬 *Willkommen bei EVALON WINNERS!*\n\nSchauen Sie sich diese Einführung an! 🏆",
        "services_msg": "🏆 *UNSERE DIENSTE*\n\nWählen Sie einen Dienst, um mehr zu erfahren 👇",
        "price_msg": "💰 *Preise und Pläne*\n\nBesuchen Sie unsere Website für aktuelle Preise 👇",
        "join_pending": "⏳ *Anfrage erhalten!*\n\nDer Admin wird bald genehmigen. 🙏",
        "auto_clean_msg": "🔄 *Chat aktualisiert!*\n\nTippen Sie unten, um fortzufahren 👇",
        "session_ended": "👋 *Der Support-Chat wurde beendet.*\n\nDanke, dass Sie uns kontaktiert haben! 🙏",
    },
    "ur": {
        "welcome": "👋 خوش آمدید، *{name}!*\n\n{urgency}\n\n🏆 *{business}* — جہاں فاتح تجارت کرتے ہیں!\n\nآپ کیا جاننا چاہتے ہیں؟ 👇",
        "btn_services": "🏆 ہماری خدمات",
        "btn_referral": "🎁 مدعو کریں اور کمائیں",
        "btn_stories": "⭐ کامیابی کی کہانیاں",
        "btn_language": "🌍 زبان",
        "btn_signals": "📊 VIP سگنلز",
        "btn_social": "👥 سوشل ٹریڈنگ",
        "btn_indicator": "📈 مفت انڈیکیٹر",
        "btn_autobot": "🤖 آٹو بوٹ",
        "btn_freebot": "🆓 مفت مینوئل بوٹ",
        "btn_website": "🌐 ویب سائٹ اور قیمتیں",
        "btn_support": "💬 سپورٹ سے رابطہ",
        "btn_back": "⬅️ واپس",
        "btn_restart": "🚀 شروع کرنے کے لیے ٹیپ کریں",
        "btn_free_indicator": "📲 مفت انڈیکیٹر حاصل کریں",
        "btn_join": "📢 ہمارے چینل میں شامل ہوں",
        "btn_poll_quotex": "📊 Quotex",
        "btn_poll_pocket": "💰 Pocket Option",
        "btn_poll_both": "✅ دونوں",
        "btn_spin": "🎰 لکی اسپن — اپنی قسمت آزمائیں!",
        "spin_wait": "⏳ آج پہلے سے اسپن کیا! {hours}h {mins}m میں واپس آئیں 🕐",
        "spin_spinning": "🎰 گھوم رہا ہے...",
        "btn_whats_new": "🆕 آج کیا نیا ہے",
        "btn_vip_results": "🏆 آج کے VIP نتائج",
        "btn_winners": "👑 ہفتے کے فاتحین",
        "btn_my_streak": "🔥 میری روزانہ اسٹریک",
        "no_news": "📢 *ابھی کوئی نئی اپڈیٹ نہیں!*\n\nبعد میں چیک کریں — ہماری ٹیم باقاعدگی سے اپڈیٹ پوسٹ کرتی ہے۔ 🔔",
        "no_vip": "📊 *آج ابھی تک کوئی VIP نتائج نہیں!*\n\nسگنل براہ راست پانے کے لیے ہمارے VIP چینل سے جڑیں!\n\nیا بعد میں چیک کریں! ⚡",
        "join_msg": "⚠️ *براہ کرم پہلے ہمارے چینل میں شامل ہوں!*\n\nابھی شامل ہوں اور واپس آئیں! 👇",
        "support_msg": "💬 *سپورٹ کی درخواست موصول ہوئی!* ✅\n\nہماری ٹیم *5 گھنٹوں کے اندر* آپ سے رابطہ کرے گی۔ ⏳\n\nبوٹ کھلا رکھیں! 🙏",
        "fallback_msg": "🤔 مجھے اس کا جواب نہیں ملا۔\n\nکیا آپ ہماری سپورٹ ٹیم سے بات کرنا چاہتے ہیں؟",
        "msg_received": "📨 پیغام موصول ہوا! ہماری ٹیم جلد جواب دے گی۔ 🙏",
        "referral_msg": "🎁 *آپ کا ریفرل لنک*\n\nآپ کا لنک:\nhttps://t.me/{bot}?start=ref{uid}\n\nآپ کے ریفرلز: {count}/{min}\n{bar}\n\nانعام کھولنے کے لیے {needed} مزید کو مدعو کریں!\n{leaderboard}",
        "comeback_msg": "👋 ہیلو *{name}!* ہم نے آپ کو یاد کیا! 😊\n\n🔥 نئے سگنلز اور مواقع انتظار میں ہیں!\n\n💎 *EVALON WINNERS* کے پاس دلچسپ اپڈیٹس ہیں!\n\n👇 واپس آئیں اور دریافت کریں:",
        "rating_msg": "⭐ *آپ کا سپورٹ تجربہ کیسا تھا؟*\n\nبراہ کرم ہماری سروس کو ریٹ کریں:",
        "rating_opinion_msg": "📝 *ریٹنگ کا شکریہ!*\n\nاپنے تجربے کے بارے میں مختصر رائے شیئر کریں (یا 'skip' لکھیں):",
        "rating_thanks": "🙏 آپ کے تاثرات کا شکریہ، *{name}!* ⭐",
        "poll_msg": "📊 *فوری سوال!*\n\nآپ بنیادی طور پر کون سا پلیٹ فارم استعمال کرتے ہیں؟",
        "welcome_video": "🎬 *EVALON WINNERS میں خوش آمدید!*\n\nیہ تعارف دیکھیں! 🏆",
        "services_msg": "🏆 *ہماری خدمات*\n\nمزید جاننے کے لیے سروس منتخب کریں 👇",
        "price_msg": "💰 *قیمتیں اور پلان*\n\nتازہ ترین قیمتوں کے لیے ہماری ویب سائٹ دیکھیں 👇",
        "join_pending": "⏳ *درخواست موصول ہوئی!*\n\nایڈمن جلد منظور کرے گا۔ 🙏",
        "auto_clean_msg": "🔄 *چیٹ ریفریش ہو گئی!*\n\nجاری رکھنے کے لیے نیچے ٹیپ کریں 👇",
        "session_ended": "👋 *سپورٹ چیٹ ختم ہو گئی۔*\n\nہم سے رابطہ کرنے کا شکریہ! 🙏",
    },
    "ja": {
        "welcome": "👋 ようこそ、*{name}!*\n\n{urgency}\n\n🏆 *{business}* — 勝者が取引する場所！\n\n何を探しますか？ 👇",
        "btn_services": "🏆 私たちのサービス",
        "btn_referral": "🎁 招待して稼ぐ",
        "btn_stories": "⭐ 成功事例",
        "btn_language": "🌍 言語",
        "btn_signals": "📊 VIPシグナル",
        "btn_social": "👥 ソーシャルトレード",
        "btn_indicator": "📈 無料インジケーター",
        "btn_autobot": "🤖 自動ボット",
        "btn_freebot": "🆓 無料マニュアルボット",
        "btn_website": "🌐 ウェブサイトと価格",
        "btn_support": "💬 サポートに連絡",
        "btn_back": "⬅️ 戻る",
        "btn_restart": "🚀 タップして開始",
        "btn_free_indicator": "📲 無料インジケーターを入手",
        "btn_join": "📢 チャンネルに参加",
        "btn_poll_quotex": "📊 Quotex",
        "btn_poll_pocket": "💰 Pocket Option",
        "btn_poll_both": "✅ 両方",
        "btn_spin": "🎰 ラッキースピン — 運試し！",
        "spin_wait": "⏳ 今日はもう回しました！{hours}h {mins}m 後に戻ってください 🕐",
        "spin_spinning": "🎰 回転中...",
        "btn_whats_new": "🆕 今日の新着情報",
        "btn_vip_results": "🏆 今日のVIP成果",
        "btn_winners": "👑 今週の勝者",
        "btn_my_streak": "🔥 毎日の連続記録",
        "no_news": "📢 *まだ新しい更新はありません！*\n\n後でチェックしてください — チームが定期的に更新を投稿します。 🔔",
        "no_vip": "📊 *今日はまだVIP成果が投稿されていません！*\n\nVIPチャンネルに参加してシグナルをリアルタイムで受け取ろう！\n\nまたは後でチェックしてください！ ⚡",
        "join_msg": "⚠️ *まず私たちのチャンネルに参加してください！*\n\n今すぐ参加して戻ってください！ 👇",
        "support_msg": "💬 *サポートリクエストを受信しました！* ✅\n\nチームが *5時間以内に* 連絡します。 ⏳\n\nボットを開いたままにしてください！ 🙏",
        "fallback_msg": "🤔 その答えが見つかりませんでした。\n\nサポートチームと話しますか？",
        "msg_received": "📨 メッセージを受信しました！チームがすぐに返信します。 🙏",
        "referral_msg": "🎁 *あなたの紹介リンク*\n\nあなたのリンク：\nhttps://t.me/{bot}?start=ref{uid}\n\nあなたの紹介：{count}/{min}\n{bar}\n\nあと {needed} 人招待して報酬をアンロック！\n{leaderboard}",
        "comeback_msg": "👋 こんにちは *{name}!* 会いたかった！ 😊\n\n🔥 新しいシグナルと機会が待っています！\n\n💎 *EVALON WINNERS* に興奮する更新があります！\n\n👇 戻って探索してください：",
        "rating_msg": "⭐ *サポート体験はいかがでしたか？*\n\nサービスを評価してください：",
        "rating_opinion_msg": "📝 *評価ありがとうございます！*\n\n体験について短い意見を共有してください（または 'skip' と入力してスキップ）：",
        "rating_thanks": "🙏 フィードバックありがとう、*{name}!* ⭐",
        "poll_msg": "📊 *簡単な質問！*\n\n主にどのプラットフォームを使用しますか？",
        "welcome_video": "🎬 *EVALON WINNERSへようこそ！*\n\nこの紹介を見てください！ 🏆",
        "services_msg": "🏆 *私たちのサービス*\n\n詳細はサービスを選択 👇",
        "price_msg": "💰 *価格とプラン*\n\n最新の価格はウェブサイトをご覧ください 👇",
        "join_pending": "⏳ *リクエストを受信しました！*\n\n管理者がすぐに承認します。 🙏",
        "auto_clean_msg": "🔄 *チャットが更新されました！*\n\n続けるには下をタップ 👇",
        "session_ended": "👋 *サポートチャットが終了しました。*\n\nご連絡ありがとうございました！ 🙏",
    },
}

# Add 8 new languages — copy English as base then override key strings
for _lc, _welcome, _btn_svc, _btn_ref, _btn_lang, _btn_spin, _spin_wait, _join, _support, _session, _referral_msg, _comeback, _rating, _rating_op, _rating_thanks, _price_msg in [
    ("it", "👋 Benvenuto, *{name}!*\n\n{urgency}\n\n🏆 *{business}* — Dove vincono i trader!\n\nCosa vuoi esplorare? 👇",
     "🏆 I Nostri Servizi", "🎁 Invita e Guadagna", "🌍 Lingua",
     "🎰 Prova il Tuo Accesso Gratuito — Spin Fortunato!",
     "⏳ Hai già girato oggi! Torna tra {hours}h {mins}m 🕐",
     "⚠️ *Unisciti prima al nostro canale!*\n\nUnisciti ora e torna! 👇",
     "💬 *Richiesta di supporto ricevuta!* ✅\n\nIl nostro team ti contatterà *entro 5 ore.* ⏳",
     "👋 *Chat di supporto terminata.*\n\nGrazie per averci contattato! 🙏",
     "🎁 *IL TUO LINK DI RIFERIMENTO*\n\nIl tuo link:\nhttps://t.me/{bot}?start=ref{uid}\n\nI tuoi riferimenti: {count}/{min}\n{bar}\n\nInvita altri {needed} per sbloccare il premio!\n{leaderboard}",
     "👋 Ciao *{name}!* Ci sei mancato! 😊\n\n🔥 Nuovi segnali e opportunità ti aspettano!\n\n💎 *EVALON WINNERS* ha aggiornamenti entusiasmanti!\n\n👇 Torna ed esplora:",
     "⭐ *Com'è stata la tua esperienza di supporto?*\n\nValuta il nostro servizio:",
     "📝 *Grazie per la valutazione!*\n\nCondividi una breve opinione (o scrivi 'skip' per saltare):",
     "🙏 Grazie per il tuo feedback, *{name}!* ⭐",
     "💰 *Scopri i Nostri Piani*\n\nVisita il nostro sito per tutti i dettagli 👇"),

    ("ko", "👋 환영합니다, *{name}!*\n\n{urgency}\n\n🏆 *{business}* — 승자들이 거래하는 곳!\n\n무엇을 탐색하시겠습니까? 👇",
     "🏆 서비스", "🎁 초대하고 수익 얻기", "🌍 언어",
     "🎰 무료 액세스 시도 — 럭키 스핀!",
     "⏳ 오늘 이미 돌렸습니다! {hours}h {mins}m 후에 돌아오세요 🕐",
     "⚠️ *먼저 채널에 참여해주세요!*\n\n지금 참여하고 돌아오세요! 👇",
     "💬 *지원 요청이 접수되었습니다!* ✅\n\n팀이 *5시간 이내에* 연락드립니다. ⏳",
     "👋 *지원 채팅이 종료되었습니다.*\n\n연락해 주셔서 감사합니다! 🙏",
     "🎁 *추천 링크*\n\n링크:\nhttps://t.me/{bot}?start=ref{uid}\n\n추천: {count}/{min}\n{bar}\n\n보상을 받으려면 {needed}명 더 초대하세요!\n{leaderboard}",
     "👋 안녕하세요 *{name}!* 보고 싶었어요! 😊\n\n🔥 새로운 신호와 기회가 기다립니다!\n\n💎 *EVALON WINNERS* 에 흥미진진한 업데이트가 있습니다!\n\n👇 돌아와서 탐색하세요:",
     "⭐ *지원 경험은 어떠셨나요?*\n\n서비스를 평가해주세요:",
     "📝 *평가해주셔서 감사합니다!*\n\n경험에 대한 간단한 의견을 공유하세요 (건너뛰려면 'skip' 입력):",
     "🙏 피드백 감사합니다, *{name}!* ⭐",
     "💰 *서비스 살펴보기*\n\n최신 정보는 웹사이트를 방문하세요 👇"),

    ("tr", "👋 Hoş geldiniz, *{name}!*\n\n{urgency}\n\n🏆 *{business}* — Kazananların işlem yaptığı yer!\n\nNe keşfetmek istersiniz? 👇",
     "🏆 Hizmetlerimiz", "🎁 Davet Et ve Kazan", "🌍 Dil",
     "🎰 Ücretsiz Erişimini Dene — Şanslı Çark!",
     "⏳ Bugün zaten çevirdiniz! {hours}h {mins}m sonra dönün 🕐",
     "⚠️ *Lütfen önce kanalımıza katılın!*\n\nŞimdi katılın ve geri dönün! 👇",
     "💬 *Destek talebi alındı!* ✅\n\nEkibimiz *5 saat içinde* sizinle iletişime geçecek. ⏳",
     "👋 *Destek sohbeti sona erdi.*\n\nBize ulaştığınız için teşekkürler! 🙏",
     "🎁 *REFERANS BAĞLANTINIZ*\n\nBağlantınız:\nhttps://t.me/{bot}?start=ref{uid}\n\nReferanslarınız: {count}/{min}\n{bar}\n\nÖdülünüzü açmak için {needed} kişi daha davet edin!\n{leaderboard}",
     "👋 Merhaba *{name}!* Sizi özledik! 😊\n\n🔥 Yeni sinyaller ve fırsatlar sizi bekliyor!\n\n💎 *EVALON WINNERS* heyecan verici güncellemelere sahip!\n\n👇 Geri dönün ve keşfedin:",
     "⭐ *Destek deneyiminiz nasıldı?*\n\nHizmetimizi değerlendirin:",
     "📝 *Değerlendirme için teşekkürler!*\n\nDeneyiminiz hakkında kısa bir görüş paylaşın (geçmek için 'skip' yazın):",
     "🙏 Geri bildiriminiz için teşekkürler, *{name}!* ⭐",
     "💰 *Hizmetlerimizi Keşfedin*\n\nTüm detaylar için web sitemizi ziyaret edin 👇"),

    ("fa", "👋 خوش آمدید، *{name}!*\n\n{urgency}\n\n🏆 *{business}* — جایی که برندگان معامله می‌کنند!\n\nمی‌خواهید چه چیزی را کشف کنید؟ 👇",
     "🏆 خدمات ما", "🎁 دعوت کنید و کسب درآمد کنید", "🌍 زبان",
     "🎰 دسترسی رایگان خود را امتحان کنید — چرخ شانس!",
     "⏳ امروز قبلاً چرخاندید! {hours}h {mins}m دیگر برگردید 🕐",
     "⚠️ *لطفاً ابتدا به کانال ما بپیوندید!*\n\nالان بپیوندید و برگردید! 👇",
     "💬 *درخواست پشتیبانی دریافت شد!* ✅\n\nتیم ما *ظرف ۵ ساعت* با شما تماس می‌گیرد. ⏳",
     "👋 *چت پشتیبانی پایان یافت.*\n\nممنون از تماس شما! 🙏",
     "🎁 *لینک معرفی شما*\n\nلینک شما:\nhttps://t.me/{bot}?start=ref{uid}\n\nمعرفی‌های شما: {count}/{min}\n{bar}\n\n{needed} نفر دیگر دعوت کنید تا جایزه‌تان را باز کنید!\n{leaderboard}",
     "👋 سلام *{name}!* دلمان برایتان تنگ شده بود! 😊\n\n🔥 سیگنال‌ها و فرصت‌های جدید منتظر شما هستند!\n\n💎 *EVALON WINNERS* به‌روزرسانی‌های هیجان‌انگیز دارد!\n\n👇 برگردید و کشف کنید:",
     "⭐ *تجربه پشتیبانی شما چگونه بود؟*\n\nلطفاً خدمات ما را ارزیابی کنید:",
     "📝 *ممنون از ارزیابی شما!*\n\nنظر کوتاهی درباره تجربه‌تان به اشتراک بگذارید (برای رد کردن 'skip' بنویسید):",
     "🙏 از بازخورد شما متشکریم، *{name}!* ⭐",
     "💰 *خدمات ما را کشف کنید*\n\nبرای جزئیات کامل از وب‌سایت ما دیدن کنید 👇"),

    ("pl", "👋 Witamy, *{name}!*\n\n{urgency}\n\n🏆 *{business}* — Gdzie handlują zwycięzcy!\n\nCo chcesz odkryć? 👇",
     "🏆 Nasze Usługi", "🎁 Zaproś i Zarabiaj", "🌍 Język",
     "🎰 Wypróbuj Darmowy Dostęp — Szczęśliwy Spin!",
     "⏳ Już kręciłeś dziś! Wróć za {hours}h {mins}m 🕐",
     "⚠️ *Dołącz najpierw do naszego kanału!*\n\nDołącz teraz i wróć! 👇",
     "💬 *Żądanie wsparcia otrzymane!* ✅\n\nNasz zespół skontaktuje się z Tobą *w ciągu 5 godzin.* ⏳",
     "👋 *Czat wsparcia zakończony.*\n\nDziękujemy za kontakt! 🙏",
     "🎁 *TWÓJ LINK POLECAJĄCY*\n\nTwój link:\nhttps://t.me/{bot}?start=ref{uid}\n\nTwoje polecenia: {count}/{min}\n{bar}\n\nZaproś jeszcze {needed} osób, aby odblokować nagrodę!\n{leaderboard}",
     "👋 Hej *{name}!* Tęskniliśmy za Tobą! 😊\n\n🔥 Nowe sygnały i okazje czekają!\n\n💎 *EVALON WINNERS* ma ekscytujące aktualizacje!\n\n👇 Wróć i odkryj:",
     "⭐ *Jak było Twoje doświadczenie z obsługą?*\n\nOceń naszą usługę:",
     "📝 *Dziękujemy za ocenę!*\n\nPodziel się krótką opinią (lub wpisz 'skip', aby pominąć):",
     "🙏 Dziękujemy za opinię, *{name}!* ⭐",
     "💰 *Odkryj Nasze Usługi*\n\nOdwiedź naszą stronę, aby zobaczyć wszystkie szczegóły 👇"),

    ("uk", "👋 Ласкаво просимо, *{name}!*\n\n{urgency}\n\n🏆 *{business}* — Де торгують переможці!\n\nЩо ви хочете дослідити? 👇",
     "🏆 Наші Послуги", "🎁 Запросіть і Заробляйте", "🌍 Мова",
     "🎰 Спробуйте Безкоштовний Доступ — Щасливий Спін!",
     "⏳ Ви вже крутили сьогодні! Поверніться через {hours}h {mins}m 🕐",
     "⚠️ *Будь ласка, спочатку приєднайтесь до нашого каналу!*\n\nПриєднайтесь зараз і поверніться! 👇",
     "💬 *Запит на підтримку отримано!* ✅\n\nНаша команда зв'яжеться з вами *протягом 5 годин.* ⏳",
     "👋 *Чат підтримки завершено.*\n\nДякуємо за звернення! 🙏",
     "🎁 *ВАШЕ РЕФЕРАЛЬНЕ ПОСИЛАННЯ*\n\nВаше посилання:\nhttps://t.me/{bot}?start=ref{uid}\n\nВаші реферали: {count}/{min}\n{bar}\n\nЗапросіть ще {needed} для отримання винагороди!\n{leaderboard}",
     "👋 Привіт *{name}!* Ми скучили за тобою! 😊\n\n🔥 Нові сигнали і можливості чекають!\n\n💎 *EVALON WINNERS* має захоплюючі оновлення!\n\n👇 Повернись і досліджуй:",
     "⭐ *Яким був ваш досвід підтримки?*\n\nОціните наш сервіс:",
     "📝 *Дякуємо за оцінку!*\n\nПоділіться коротким відгуком (або напишіть 'skip', щоб пропустити):",
     "🙏 Дякуємо за відгук, *{name}!* ⭐",
     "💰 *Досліджуйте Наші Послуги*\n\nВідвідайте наш сайт для всіх деталей 👇"),

    ("kk", "👋 Қош келдіңіз, *{name}!*\n\n{urgency}\n\n🏆 *{business}* — Жеңімпаздар сауда жасайтын жер!\n\nНені зерттегіңіз келеді? 👇",
     "🏆 Біздің Қызметтер", "🎁 Шақырып, Табыс Табыңыз", "🌍 Тіл",
     "🎰 Тегін Қолжетімділікті Сынаңыз — Бақытты Айналым!",
     "⏳ Бүгін айналдырдыңыз! {hours}h {mins}m кейін оралыңыз 🕐",
     "⚠️ *Алдымен арнамызға қосылыңыз!*\n\nҚазір қосылып, оралыңыз! 👇",
     "💬 *Қолдау сұранысы алынды!* ✅\n\nКоманда *5 сағат ішінде* хабарласады. ⏳",
     "👋 *Қолдау чаты аяқталды.*\n\nХабарласқаныңызға рахмет! 🙏",
     "🎁 *РЕФЕРАЛ СІЛТЕМЕҢІЗ*\n\nСілтемеңіз:\nhttps://t.me/{bot}?start=ref{uid}\n\nРефералдарыңыз: {count}/{min}\n{bar}\n\nСыйлықты ашу үшін {needed} адам шақырыңыз!\n{leaderboard}",
     "👋 Сәлем *{name}!* Сені сағындық! 😊\n\n🔥 Жаңа сигналдар мен мүмкіндіктер күтуде!\n\n💎 *EVALON WINNERS* тартымды жаңартулар ұсынады!\n\n👇 Оралып, зерттеңіз:",
     "⭐ *Қолдау тәжірибеңіз қандай болды?*\n\nКызметімізді бағалаңыз:",
     "📝 *Бағалағаныңызға рахмет!*\n\nТәжірибеңіз туралы қысқаша пікір бөлісіңіз (өткізіп жіберу үшін 'skip' жазыңыз):",
     "🙏 Пікіріңізге рахмет, *{name}!* ⭐",
     "💰 *Қызметтерімізді Зерттеңіз*\n\nТолық мәліметтер үшін сайтымызды қараңыз 👇"),

    ("cs", "👋 Vítejte, *{name}!*\n\n{urgency}\n\n🏆 *{business}* — Kde obchodují vítězové!\n\nCo chcete prozkoumat? 👇",
     "🏆 Naše Služby", "🎁 Pozvěte a Vydělávejte", "🌍 Jazyk",
     "🎰 Vyzkoušejte Bezplatný Přístup — Šťastný Spin!",
     "⏳ Dnes jste již točili! Vraťte se za {hours}h {mins}m 🕐",
     "⚠️ *Nejprve se připojte k našemu kanálu!*\n\nPřipojte se nyní a vraťte se! 👇",
     "💬 *Žádost o podporu přijata!* ✅\n\nNáš tým vás bude kontaktovat *do 5 hodin.* ⏳",
     "👋 *Chat podpory ukončen.*\n\nDěkujeme za kontakt! 🙏",
     "🎁 *VÁŠ REFERENČNÍ ODKAZ*\n\nVáš odkaz:\nhttps://t.me/{bot}?start=ref{uid}\n\nVaše doporučení: {count}/{min}\n{bar}\n\nPozvěte dalších {needed} pro odemknutí odměny!\n{leaderboard}",
     "👋 Ahoj *{name}!* Chyběl jsi nám! 😊\n\n🔥 Nové signály a příležitosti čekají!\n\n💎 *EVALON WINNERS* má vzrušující aktualizace!\n\n👇 Vrať se a prozkoumej:",
     "⭐ *Jak byl váš podpůrný zážitek?*\n\nOhodnoťte naši službu:",
     "📝 *Děkujeme za hodnocení!*\n\nPodělte se o krátký názor (nebo napište 'skip' pro přeskočení):",
     "🙏 Děkujeme za zpětnou vazbu, *{name}!* ⭐",
     "💰 *Prozkoumejte Naše Služby*\n\nNavštivte náš web pro všechny podrobnosti 👇"),
]:
    UI[_lc] = dict(UI["en"])  # copy English as base
    UI[_lc].update({
        "welcome": _welcome,
        "btn_services": _btn_svc,
        "btn_referral": _btn_ref,
        "btn_language": _btn_lang,
        "btn_spin": _btn_spin,
        "spin_wait": _spin_wait,
        "join_msg": _join,
        "support_msg": _support,
        "session_ended": _session,
        "referral_msg": _referral_msg,
        "comeback_msg": _comeback,
        "rating_msg": _rating,
        "rating_opinion_msg": _rating_op,
        "rating_thanks": _rating_thanks,
        "price_msg": _price_msg,
    })

# ── Update btn_website text for all languages to remove "Pricing" ──
_website_texts = {
    "en": "🌐 Visit Our Website",
    "sw": "🌐 Tembelea Website Yetu",
    "ar": "🌐 زيارة موقعنا",
    "zh": "🌐 访问我们的网站",
    "hi": "🌐 हमारी वेबसाइट देखें",
    "ru": "🌐 Посетите наш сайт",
    "es": "🌐 Visita Nuestro Sitio Web",
    "fr": "🌐 Visitez Notre Site Web",
    "pt": "🌐 Visite Nosso Site",
    "de": "🌐 Besuchen Sie Unsere Website",
    "ur": "🌐 ہماری ویب سائٹ دیکھیں",
    "ja": "🌐 ウェブサイトを見る",
    "it": "🌐 Visita il Nostro Sito",
    "ko": "🌐 웹사이트 방문하기",
    "tr": "🌐 Web Sitemizi Ziyaret Edin",
    "fa": "🌐 از وب‌سایت ما بازدید کنید",
    "pl": "🌐 Odwiedź Naszą Stronę",
    "uk": "🌐 Відвідайте Наш Сайт",
    "kk": "🌐 Сайтымызды Қараңыз",
    "cs": "🌐 Navštivte Náš Web",
}
for _lc, _txt in _website_texts.items():
    if _lc in UI:
        UI[_lc]["btn_website"] = _txt

# ══════════════════════════════════════════════════════════════
#  MISSING UI KEYS — Full translations for 8 partial languages
# ══════════════════════════════════════════════════════════════
_extra_ui = {
    "it": {
        "btn_signals": "\U0001f4ca Segnali VIP",
        "btn_social": "\U0001f465 Social Trading",
        "btn_indicator": "\U0001f4c8 Indicatore Gratuito",
        "btn_autobot": "\U0001f916 Auto Bot",
        "btn_freebot": "\U0001f193 Bot Manuale Gratuito",
        "btn_support": "\U0001f4ac Contatta Supporto",
        "btn_back": "\u2b05\ufe0f Indietro",
        "btn_restart": "\U0001f680 Tocca per Iniziare",
        "btn_free_indicator": "\U0001f4f2 Ottieni Indicatore GRATUITO",
        "btn_join": "\U0001f4e2 Unisciti al Canale",
        "btn_whats_new": "\U0001f195 Novita di Oggi",
        "btn_vip_results": "\U0001f3c6 Risultati VIP di Oggi",
        "btn_winners": "\U0001f451 Vincitori della Settimana",
        "btn_my_streak": "\U0001f525 La Mia Serie Giornaliera",
        "btn_tip": "\U0001f4a1 Consiglio del Giorno",
        "btn_quiz": "\U0001f9e0 Quiz",
        "btn_profile": "\U0001f464 Il Mio Profilo",
        "btn_results_history": "\U0001f4c5 Risultati Passati",
        "btn_stories": "\u2b50 Storie di Successo",
        "fallback_msg": "\U0001f914 Non ho trovato una risposta.\n\nVuoi parlare con il nostro team di supporto?",
        "msg_received": "\U0001f4e8 Messaggio ricevuto! Il nostro team rispondera a breve. \U0001f64f",
        "no_news": "\U0001f4e2 *Nessun aggiornamento ancora!*\n\nTorna piu tardi. \U0001f514",
        "no_vip": "\U0001f4ca *Nessun risultato VIP oggi!*\n\nUnisciti al canale VIP per segnali in diretta. \u26a1",
        "no_results_history": "\U0001f4c5 *Nessun risultato passato!*\n\nL admin pubblichera i risultati qui. \u26a1",
        "spin_spinning": "\U0001f3b0 Girando...",
    },
    "ko": {
        "btn_signals": "\U0001f4ca VIP \uc2e0\ud638",
        "btn_social": "\U0001f465 \uc18c\uc15c \ud2b8\ub808\uc774\ub529",
        "btn_indicator": "\U0001f4c8 \ubb34\ub8cc \uc778\ub514\ucf00\uc774\ud130",
        "btn_autobot": "\U0001f916 \uc790\ub3d9 \ubd07",
        "btn_freebot": "\U0001f193 \ubb34\ub8cc \uc218\ub3d9 \ubd07",
        "btn_support": "\U0001f4ac \uc9c0\uc6d0 \ubb38\uc758",
        "btn_back": "\u2b05\ufe0f \ub4a4\ub85c",
        "btn_restart": "\U0001f680 \uc2dc\uc791\ud558\ub824\uba74 \ud0ed\ud558\uc138\uc694",
        "btn_free_indicator": "\U0001f4f2 \ubb34\ub8cc \uc778\ub514\ucf00\uc774\ud130 \ubc1b\uae30",
        "btn_join": "\U0001f4e2 \ucc44\ub110 \ucc38\uc5ec",
        "btn_whats_new": "\U0001f195 \uc624\ub298\uc758 \uc0c8\uc18c\uc2dd",
        "btn_vip_results": "\U0001f3c6 \uc624\ub298\uc758 VIP \uacb0\uacfc",
        "btn_winners": "\U0001f451 \uc774\ubc88 \uc8fc \uc6b0\uc2b9\uc790",
        "btn_my_streak": "\U0001f525 \ub098\uc758 \uc77c\uc77c \uc5f0\uc18d",
        "btn_tip": "\U0001f4a1 \uc624\ub298\uc758 \ud301",
        "btn_quiz": "\U0001f9e0 \ud034\uc988",
        "btn_profile": "\U0001f464 \ub0b4 \ud504\ub85c\ud544",
        "btn_results_history": "\U0001f4c5 \uacfc\uac70 \uacb0\uacfc",
        "btn_stories": "\u2b50 \uc131\uacf5 \uc0ac\ub840",
        "fallback_msg": "\U0001f914 \ub2f5\ubcc0\uc744 \ucc3e\uc9c0 \ubabb\ud588\uc2b5\ub2c8\ub2e4.\n\n\uc9c0\uc6d0\ud300\uacfc \ub300\ud654\ud558\uc2dc\uaca0\uc2b5\ub2c8\uae4c?",
        "msg_received": "\U0001f4e8 \uba54\uc2dc\uc9c0\ub97c \ubc1b\uc558\uc2b5\ub2c8\ub2e4! \ud300\uc774 \uacf5 \ub2f5\ubcc0\ub4dc\ub9ac\uaca0\uc2b5\ub2c8\ub2e4. \U0001f64f",
        "no_news": "\U0001f4e2 *\uc544\uc9c1 \uc0c8\ub85c\uc6b4 \uc5c5\ub370\uc774\ud2b8\uac00 \uc5c6\uc2b5\ub2c8\ub2e4!*\n\n\ub098\uc911\uc5d0 \ub2e4\uc2dc \ud655\uc778\ud558\uc138\uc694. \U0001f514",
        "no_vip": "\U0001f4ca *\uc624\ub298 VIP \uacb0\uacfc\uac00 \uc544\uc9c1 \uac8c\uc2dc\ub418\uc9c0 \uc54a\uc558\uc2b5\ub2c8\ub2e4!*\n\nVIP \ucc44\ub110\uc5d0 \ucc38\uc5ec\ud558\uc138\uc694. \u26a1",
        "no_results_history": "\U0001f4c5 *\uc544\uc9c1 \uacfc\uac70 \uacb0\uacfc\uac00 \uc5c6\uc2b5\ub2c8\ub2e4!*\n\n\uad00\ub9ac\uc790\uac00 \uc138\uc158 \uacb0\uacfc\ub97c \uac8c\uc2dc\ud560 \uac83\uc785\ub2c8\ub2e4. \u26a1",
        "spin_spinning": "\U0001f3b0 \ub3cc\ub9ac\ub294 \uc911...",
    },
    "tr": {
        "btn_signals": "\U0001f4ca VIP Sinyaller",
        "btn_social": "\U0001f465 Sosyal Ticaret",
        "btn_indicator": "\U0001f4c8 Ucretsiz Gosterge",
        "btn_autobot": "\U0001f916 Otomatik Bot",
        "btn_freebot": "\U0001f193 Ucretsiz Manuel Bot",
        "btn_support": "\U0001f4ac Destek Ile Iletisim",
        "btn_back": "\u2b05\ufe0f Geri",
        "btn_restart": "\U0001f680 Baslamak Icin Dokun",
        "btn_free_indicator": "\U0001f4f2 UCRETSIZ Gosterge Al",
        "btn_join": "\U0001f4e2 Kanala Katil",
        "btn_whats_new": "\U0001f195 Bugunun Yenilikleri",
        "btn_vip_results": "\U0001f3c6 Bugunun VIP Sonuclari",
        "btn_winners": "\U0001f451 Haftanin Kazananlari",
        "btn_my_streak": "\U0001f525 Gunluk Serim",
        "btn_tip": "\U0001f4a1 Gunluk Ipucu",
        "btn_quiz": "\U0001f9e0 Quiz",
        "btn_profile": "\U0001f464 Profilim",
        "btn_results_history": "\U0001f4c5 Gecmis Sonuclar",
        "btn_stories": "\u2b50 Basari Hikayeleri",
        "fallback_msg": "\U0001f914 Bunun icin bir cevap bulamadim.\n\nDestek ekibimizle konusmak ister misiniz?",
        "msg_received": "\U0001f4e8 Mesaj alindi! Ekibimiz yakin zamanda yanitlayacak. \U0001f64f",
        "no_news": "\U0001f4e2 *Henuz yeni guncelleme yok!*\n\nDaha sonra tekrar kontrol edin. \U0001f514",
        "no_vip": "\U0001f4ca *Bugun VIP sonucu yayinlanmadi!*\n\nCanli sinyaller icin VIP kanalina katilin. \u26a1",
        "no_results_history": "\U0001f4c5 *Gecmis sonuc yok!*\n\nYonetici oturum sonuclarini buraya yayinlayacak. \u26a1",
        "spin_spinning": "\U0001f3b0 Donduruluyor...",
    },
    "fa": {
        "btn_signals": "\U0001f4ca \u0633\u06cc\u06af\u0646\u0627\u0644\u200c\u0647\u0627\u06cc VIP",
        "btn_social": "\U0001f465 \u0645\u0639\u0627\u0645\u0644\u0627\u062a \u0627\u062c\u062a\u0645\u0627\u0639\u06cc",
        "btn_indicator": "\U0001f4c8 \u0627\u0646\u062f\u06cc\u06a9\u0627\u062a\u0648\u0631 \u0631\u0627\u06cc\u06af\u0627\u0646",
        "btn_autobot": "\U0001f916 \u0631\u0628\u0627\u062a \u062e\u0648\u062f\u06a9\u0627\u0631",
        "btn_freebot": "\U0001f193 \u0631\u0628\u0627\u062a \u062f\u0633\u062a\u06cc \u0631\u0627\u06cc\u06af\u0627\u0646",
        "btn_support": "\U0001f4ac \u062a\u0645\u0627\u0633 \u0628\u0627 \u067e\u0634\u062a\u06cc\u0628\u0627\u0646\u06cc",
        "btn_back": "\u2b05\ufe0f \u0628\u0627\u0632\u06af\u0634\u062a",
        "btn_restart": "\U0001f680 \u0628\u0631\u0627\u06cc \u0634\u0631\u0648\u0639 \u0644\u0645\u0633 \u06a9\u0646\u06cc\u062f",
        "btn_free_indicator": "\U0001f4f2 \u062f\u0631\u06cc\u0627\u0641\u062a \u0627\u0646\u062f\u06cc\u06a9\u0627\u062a\u0648\u0631 \u0631\u0627\u06cc\u06af\u0627\u0646",
        "btn_join": "\U0001f4e2 \u0639\u0636\u0648\u06cc\u062a \u062f\u0631 \u06a9\u0627\u0646\u0627\u0644",
        "btn_whats_new": "\U0001f195 \u0627\u062e\u0628\u0627\u0631 \u0627\u0645\u0631\u0648\u0632",
        "btn_vip_results": "\U0001f3c6 \u0646\u062a\u0627\u06cc\u062c VIP \u0627\u0645\u0631\u0648\u0632",
        "btn_winners": "\U0001f451 \u0628\u0631\u0646\u062f\u06af\u0627\u0646 \u0647\u0641\u062a\u0647",
        "btn_my_streak": "\U0001f525 \u0631\u0634\u062a\u0647 \u0631\u0648\u0632\u0627\u0646\u0647 \u0645\u0646",
        "btn_tip": "\U0001f4a1 \u0646\u06a9\u062a\u0647 \u0631\u0648\u0632\u0627\u0646\u0647",
        "btn_quiz": "\U0001f9e0 \u0622\u0632\u0645\u0648\u0646",
        "btn_profile": "\U0001f464 \u067e\u0631\u0648\u0641\u0627\u06cc\u0644 \u0645\u0646",
        "btn_results_history": "\U0001f4c5 \u0646\u062a\u0627\u06cc\u062c \u06af\u0630\u0634\u062a\u0647",
        "btn_stories": "\u2b50 \u062f\u0627\u0633\u062a\u0627\u0646\u200c\u0647\u0627\u06cc \u0645\u0648\u0641\u0642\u06cc\u062a",
        "fallback_msg": "\U0001f914 \u067e\u0627\u0633\u062e\u06cc \u0628\u0631\u0627\u06cc \u0627\u06cc\u0646 \u067e\u06cc\u062f\u0627 \u0646\u06a9\u0631\u062f\u0645.\n\n\u0622\u06cc\u0627 \u0645\u06cc\u200c\u062e\u0648\u0627\u0647\u06cc\u062f \u0628\u0627 \u062a\u06cc\u0645 \u067e\u0634\u062a\u06cc\u0628\u0627\u0646\u06cc \u0635\u062d\u0628\u062a \u06a9\u0646\u06cc\u062f?",
        "msg_received": "\U0001f4e8 \u067e\u06cc\u0627\u0645 \u062f\u0631\u06cc\u0627\u0641\u062a \u0634\u062f! \u062a\u06cc\u0645 \u0645\u0627 \u0628\u0647 \u0632\u0648\u062f\u06cc \u067e\u0627\u0633\u062e \u062e\u0648\u0627\u0647\u062f \u062f\u0627\u062f. \U0001f64f",
        "no_news": "\U0001f4e2 *\u0647\u0646\u0648\u0632 \u0628\u0631\u0648\u0632\u0631\u0633\u0627\u0646\u06cc \u062c\u062f\u06cc\u062f\u06cc \u0646\u06cc\u0633\u062a!*\n\n\u0628\u0639\u062f\u0627 \u062f\u0648\u0628\u0627\u0631\u0647 \u0628\u0631\u0631\u0633\u06cc \u06a9\u0646\u06cc\u062f. \U0001f514",
        "no_vip": "\U0001f4ca *\u0627\u0645\u0631\u0648\u0632 \u0646\u062a\u06cc\u062c\u0647 VIP \u0645\u0646\u062a\u0634\u0631 \u0646\u0634\u062f\u0647!*\n\n\u0628\u0631\u0627\u06cc \u0633\u06cc\u06af\u0646\u0627\u0644 \u0632\u0646\u062f\u0647 \u0628\u0647 \u06a9\u0627\u0646\u0627\u0644 VIP \u0628\u067e\u06cc\u0648\u0646\u062f\u06cc\u062f. \u26a1",
        "no_results_history": "\U0001f4c5 *\u0647\u0646\u0648\u0632 \u0646\u062a\u06cc\u062c\u0647 \u06af\u0630\u0634\u062a\u0647\u200c\u0627\u06cc \u0646\u06cc\u0633\u062a!*\n\n\u0627\u062f\u0645\u06cc\u0646 \u0646\u062a\u0627\u06cc\u062c \u062c\u0644\u0633\u0627\u062a \u0631\u0627 \u0627\u06cc\u0646\u062c\u0627 \u0645\u0646\u062a\u0634\u0631 \u062e\u0648\u0627\u0647\u062f \u06a9\u0631\u062f. \u26a1",
        "spin_spinning": "\U0001f3b0 \u062f\u0631 \u062d\u0627\u0644 \u0686\u0631\u062e\u0634...",
    },
    "pl": {
        "btn_signals": "\U0001f4ca Sygna\u0142y VIP",
        "btn_social": "\U0001f465 Handel Spo\u0142eczno\u015bciowy",
        "btn_indicator": "\U0001f4c8 Darmowy Wska\u017anik",
        "btn_autobot": "\U0001f916 Automatyczny Bot",
        "btn_freebot": "\U0001f193 Darmowy Bot Manualny",
        "btn_support": "\U0001f4ac Kontakt z Pomoc\u0105",
        "btn_back": "\u2b05\ufe0f Wr\u00f3\u0107",
        "btn_restart": "\U0001f680 Dotknij aby Zacz\u0105\u0107",
        "btn_free_indicator": "\U0001f4f2 Pobierz DARMOWY Wska\u017anik",
        "btn_join": "\U0001f4e2 Do\u0142\u0105cz do Kana\u0142u",
        "btn_whats_new": "\U0001f195 Co Nowego Dzi\u015b",
        "btn_vip_results": "\U0001f3c6 Dzisiejsze Wyniki VIP",
        "btn_winners": "\U0001f451 Zwyci\u0119zcy Tygodnia",
        "btn_my_streak": "\U0001f525 Moja Codzienna Seria",
        "btn_tip": "\U0001f4a1 Codzienna Wskaz\u00f3wka",
        "btn_quiz": "\U0001f9e0 Quiz",
        "btn_profile": "\U0001f464 M\u00f3j Profil",
        "btn_results_history": "\U0001f4c5 Poprzednie Wyniki",
        "btn_stories": "\u2b50 Historie Sukcesu",
        "fallback_msg": "\U0001f914 Nie znalaz\u0142em odpowiedzi na to.\n\nChcesz porozmawia\u0107 z naszym zespo\u0142em wsparcia?",
        "msg_received": "\U0001f4e8 Wiadomo\u015b\u0107 odebrana! Nasz zesp\u00f3\u0142 odpowie wkr\u00f3tce. \U0001f64f",
        "no_news": "\U0001f4e2 *Brak nowych aktualizacji!*\n\nSprawdź ponownie później. \U0001f514",
        "no_vip": "\U0001f4ca *Dzi\u015b nie opublikowano wynik\u00f3w VIP!*\n\nDo\u0142\u0105cz do kana\u0142u VIP po sygna\u0142y na \u017cywo. \u26a1",
        "no_results_history": "\U0001f4c5 *Brak poprzednich wynik\u00f3w!*\n\nAdmin opublikuje tu wyniki sesji. \u26a1",
        "spin_spinning": "\U0001f3b0 Kr\u0119ci si\u0119...",
    },
    "uk": {
        "btn_signals": "\U0001f4ca VIP \u0421\u0438\u0433\u043d\u0430\u043b\u0438",
        "btn_social": "\U0001f465 \u0421\u043e\u0446\u0456\u0430\u043b\u044c\u043d\u0430 \u0422\u043e\u0440\u0433\u0456\u0432\u043b\u044f",
        "btn_indicator": "\U0001f4c8 \u0411\u0435\u0437\u043a\u043e\u0448\u0442\u043e\u0432\u043d\u0438\u0439 \u0406\u043d\u0434\u0438\u043a\u0430\u0442\u043e\u0440",
        "btn_autobot": "\U0001f916 \u0410\u0432\u0442\u043e \u0411\u043e\u0442",
        "btn_freebot": "\U0001f193 \u0411\u0435\u0437\u043a\u043e\u0448\u0442\u043e\u0432\u043d\u0438\u0439 \u0420\u0443\u0447\u043d\u0438\u0439 \u0411\u043e\u0442",
        "btn_support": "\U0001f4ac \u0417\u0432'\u044f\u0437\u0430\u0442\u0438\u0441\u044f \u0437 \u041f\u0456\u0434\u0442\u0440\u0438\u043c\u043a\u043e\u044e",
        "btn_back": "\u2b05\ufe0f \u041d\u0430\u0437\u0430\u0434",
        "btn_restart": "\U0001f680 \u041d\u0430\u0442\u0438\u0441\u043d\u0456\u0442\u044c \u0434\u043b\u044f \u041f\u043e\u0447\u0430\u0442\u043a\u0443",
        "btn_free_indicator": "\U0001f4f2 \u041e\u0442\u0440\u0438\u043c\u0430\u0442\u0438 \u0411\u0415\u0417\u041a\u041e\u0428\u0422\u041e\u0412\u041d\u0418\u0419 \u0406\u043d\u0434\u0438\u043a\u0430\u0442\u043e\u0440",
        "btn_join": "\U0001f4e2 \u041f\u0440\u0438\u0454\u0434\u043d\u0430\u0442\u0438\u0441\u044f \u0434\u043e \u041a\u0430\u043d\u0430\u043b\u0443",
        "btn_whats_new": "\U0001f195 \u0429\u043e \u041d\u043e\u0432\u043e\u0433\u043e \u0421\u044c\u043e\u0433\u043e\u0434\u043d\u0456",
        "btn_vip_results": "\U0001f3c6 \u0421\u044c\u043e\u0433\u043e\u0434\u043d\u0456\u0448\u043d\u0456 VIP \u0420\u0435\u0437\u0443\u043b\u044c\u0442\u0430\u0442\u0438",
        "btn_winners": "\U0001f451 \u041f\u0435\u0440\u0435\u043c\u043e\u0436\u0446\u0456 \u0422\u0438\u0436\u043d\u044f",
        "btn_my_streak": "\U0001f525 \u041c\u043e\u044f \u0429\u043e\u0434\u0435\u043d\u043d\u0430 \u0421\u0435\u0440\u0456\u044f",
        "btn_tip": "\U0001f4a1 \u0429\u043e\u0434\u0435\u043d\u043d\u0430 \u041f\u043e\u0440\u0430\u0434\u0430",
        "btn_quiz": "\U0001f9e0 \u0412\u0456\u043a\u0442\u043e\u0440\u0438\u043d\u0430",
        "btn_profile": "\U0001f464 \u041c\u0456\u0439 \u041f\u0440\u043e\u0444\u0456\u043b\u044c",
        "btn_results_history": "\U0001f4c5 \u041c\u0438\u043d\u0443\u043b\u0456 \u0420\u0435\u0437\u0443\u043b\u044c\u0442\u0430\u0442\u0438",
        "btn_stories": "\u2b50 \u0406\u0441\u0442\u043e\u0440\u0456\u0457 \u0423\u0441\u043f\u0456\u0445\u0443",
        "fallback_msg": "\U0001f914 \u042f \u043d\u0435 \u0437\u043d\u0430\u0439\u0448\u043e\u0432 \u0432\u0456\u0434\u043f\u043e\u0432\u0456\u0434\u0456.\n\n\u0425\u043e\u0447\u0435\u0442\u0435 \u043f\u043e\u0433\u043e\u0432\u043e\u0440\u0438\u0442\u0438 \u0437 \u043f\u0456\u0434\u0442\u0440\u0438\u043c\u043a\u043e\u044e?",
        "msg_received": "\U0001f4e8 \u041f\u043e\u0432\u0456\u0434\u043e\u043c\u043b\u0435\u043d\u043d\u044f \u043e\u0442\u0440\u0438\u043c\u0430\u043d\u043e! \u041d\u0430\u0448\u0430 \u043a\u043e\u043c\u0430\u043d\u0434\u0430 \u0441\u043a\u043e\u0440\u043e \u0432\u0456\u0434\u043f\u043e\u0432\u0456\u0441\u0442\u044c. \U0001f64f",
        "no_news": "\U0001f4e2 *\u0429\u0435 \u043d\u0435\u043c\u0430\u0454 \u043d\u043e\u0432\u0438\u0445 \u043e\u043d\u043e\u0432\u043b\u0435\u043d\u044c!*\n\n\u041f\u0435\u0440\u0435\u0432\u0456\u0440\u0442\u0435 \u043f\u0456\u0437\u043d\u0456\u0448\u0435. \U0001f514",
        "no_vip": "\U0001f4ca *\u0421\u044c\u043e\u0433\u043e\u0434\u043d\u0456 \u0440\u0435\u0437\u0443\u043b\u044c\u0442\u0430\u0442\u0456\u0432 VIP \u043d\u0435\u043c\u0430\u0454!*\n\n\u041f\u0440\u0438\u0454\u0434\u043d\u0430\u0439\u0442\u0435\u0441\u044c \u0434\u043e VIP \u043a\u0430\u043d\u0430\u043b\u0443. \u26a1",
        "no_results_history": "\U0001f4c5 *\u0429\u0435 \u043d\u0435\u043c\u0430\u0454 \u043c\u0438\u043d\u0443\u043b\u0438\u0445 \u0440\u0435\u0437\u0443\u043b\u044c\u0442\u0430\u0442\u0456\u0432!*\n\n\u0410\u0434\u043c\u0456\u043d \u043e\u043f\u0443\u0431\u043b\u0456\u043a\u0443\u0454 \u0440\u0435\u0437\u0443\u043b\u044c\u0442\u0430\u0442\u0438 \u0441\u0435\u0441\u0456\u0439 \u0442\u0443\u0442. \u26a1",
        "spin_spinning": "\U0001f3b0 \u041e\u0431\u0435\u0440\u0442\u0430\u0454\u0442\u044c\u0441\u044f...",
    },
    "kk": {
        "btn_signals": "\U0001f4ca VIP \u0421\u0438\u0433\u043d\u0430\u043b\u0434\u0430\u0440",
        "btn_social": "\U0001f465 \u04d8\u043b\u0435\u0443\u043c\u0435\u0442\u0442\u0456\u043a \u0421\u0430\u0443\u0434\u0430",
        "btn_indicator": "\U0001f4c8 \u0422\u0435\u0433\u0456\u043d \u0418\u043d\u0434\u0438\u043a\u0430\u0442\u043e\u0440",
        "btn_autobot": "\U0001f916 \u0410\u0432\u0442\u043e \u0411\u043e\u0442",
        "btn_freebot": "\U0001f193 \u0422\u0435\u0433\u0456\u043d \u049a\u043e\u043b\u043c\u0435\u043d \u0411\u043e\u0442",
        "btn_support": "\U0001f4ac \u049a\u043e\u043b\u0434\u0430\u0443\u043c\u0435\u043d \u0411\u0430\u0439\u043b\u0430\u043d\u044b\u0441",
        "btn_back": "\u2b05\ufe0f \u0410\u0440\u0442\u049b\u0430",
        "btn_restart": "\U0001f680 \u0411\u0430\u0441\u0442\u0430\u0443 \u04af\u0448\u0456\u043d \u0411\u0430\u0441\u044b\u04a3\u044b\u0437",
        "btn_free_indicator": "\U0001f4f2 \u0422\u0415\u0413\u0406\u041d \u0418\u043d\u0434\u0438\u043a\u0430\u0442\u043e\u0440 \u0410\u043b\u044b\u04a3\u044b\u0437",
        "btn_join": "\U0001f4e2 \u0410\u0440\u043d\u0430\u0493\u0430 \u049a\u043e\u0441\u044b\u043b\u0443",
        "btn_whats_new": "\U0001f195 \u0411\u04af\u0433\u0456\u043d\u0433\u0456 \u0416\u0430\u04a3\u0430\u043b\u044b\u049b\u0442\u0430\u0440",
        "btn_vip_results": "\U0001f3c6 \u0411\u04af\u0433\u0456\u043d\u0433\u0456 VIP \u041d\u04d9\u0442\u0438\u0436\u0435\u043b\u0435\u0440",
        "btn_winners": "\U0001f451 \u0410\u043f\u0442\u0430 \u0416\u0435\u04a3\u0456\u043c\u043f\u0430\u0437\u0434\u0430\u0440\u044b",
        "btn_my_streak": "\U0001f525 \u041c\u0435\u043d\u0456\u04a3 \u041a\u04af\u043d\u0434\u0435\u043b\u0456\u043a\u0442\u0456 \u0421\u0435\u0440\u0456\u044f\u043c",
        "btn_tip": "\U0001f4a1 \u041a\u04af\u043d\u0434\u0435\u043b\u0456\u043a \u041a\u0435\u04a3\u0435\u0441",
        "btn_quiz": "\U0001f9e0 \u0412\u0438\u043a\u0442\u043e\u0440\u0438\u043d\u0430",
        "btn_profile": "\U0001f464 \u041c\u0435\u043d\u0456\u04a3 \u041f\u0440\u043e\u0444\u0438\u043b\u0456\u043c",
        "btn_results_history": "\U0001f4c5 \u04e8\u0442\u043a\u0435\u043d \u041d\u04d9\u0442\u0438\u0436\u0435\u043b\u0435\u0440",
        "btn_stories": "\u2b50 \u0416\u0435\u0442\u0456\u0441\u0442\u0456\u043a \u0422\u0430\u0440\u0438\u0445\u0442\u0430\u0440\u044b",
        "fallback_msg": "\U0001f914 \u0411\u04b1\u043b \u04af\u0448\u0456\u043d \u0436\u0430\u0443\u0430\u043f \u0442\u0430\u043f\u043f\u0430\u0434\u044b\u043c.\n\n\u049a\u043e\u043b\u0434\u0430\u0443 \u043a\u043e\u043c\u0430\u043d\u0434\u0430\u0441\u044b\u043c\u0435\u043d \u0441\u04e9\u0439\u043b\u0435\u0441\u043a\u0456\u04a3\u0456\u0437 \u043a\u0435\u043b\u0435 \u043c\u0435?",
        "msg_received": "\U0001f4e8 \u0425\u0430\u0431\u0430\u0440\u043b\u0430\u043c\u0430 \u0430\u043b\u044b\u043d\u0434\u044b! \u041a\u043e\u043c\u0430\u043d\u0434\u0430\u043c\u044b\u0437 \u0436\u0430\u049b\u044b\u043d \u0430\u0440\u0430\u0434\u0430 \u0436\u0430\u0443\u0430\u043f \u0431\u0435\u0440\u0435\u0434\u0456. \U0001f64f",
        "no_news": "\U0001f4e2 *\u04d8\u043b\u0456 \u0436\u0430\u04a3\u0430 \u0436\u0430\u04a3\u0430\u0440\u0442\u0443\u043b\u0430\u0440 \u0436\u043e\u049b!*\n\n\u041a\u0435\u0439\u0456\u043d\u0440\u0435\u043a \u049b\u0430\u0439\u0442\u0430 \u0442\u0435\u043a\u0441\u0435\u0440\u0456\u04a3\u0456\u0437. \U0001f514",
        "no_vip": "\U0001f4ca *\u0411\u04af\u0433\u0456\u043d VIP \u043d\u04d9\u0442\u0438\u0436\u0435\u043b\u0435\u0440 \u04d9\u043b\u0456 \u0436\u0430\u0440\u0438\u044f\u043b\u0430\u043d\u0431\u0430\u0493\u0430\u043d!*\n\nVIP \u0430\u0440\u043d\u0430\u0441\u044b\u043d\u0430 \u049b\u043e\u0441\u044b\u043b\u044b\u04a3\u044b\u0437. \u26a1",
        "no_results_history": "\U0001f4c5 *\u04e8\u0442\u043a\u0435\u043d \u043d\u04d9\u0442\u0438\u0436\u0435\u043b\u0435\u0440 \u04d9\u043b\u0456 \u0436\u043e\u049b!*\n\n\u0410\u0434\u043c\u0438\u043d \u0441\u0435\u0441\u0441\u0438\u044f \u043d\u04d9\u0442\u0438\u0436\u0435\u043b\u0435\u0440\u0456\u043d \u043e\u0441\u044b\u043d\u0434\u0430 \u0436\u0430\u0440\u0438\u044f\u043b\u0430\u0439\u0434\u044b. \u26a1",
        "spin_spinning": "\U0001f3b0 \u0410\u0439\u043d\u0430\u043b\u0443\u0434\u0430...",
    },
    "cs": {
        "btn_signals": "\U0001f4ca VIP Sign\u00e1ly",
        "btn_social": "\U0001f465 Soci\u00e1ln\u00ed Obchodov\u00e1n\u00ed",
        "btn_indicator": "\U0001f4c8 Bezplatn\u00fd Indik\u00e1tor",
        "btn_autobot": "\U0001f916 Automatick\u00fd Bot",
        "btn_freebot": "\U0001f193 Bezplatn\u00fd Manu\u00e1ln\u00ed Bot",
        "btn_support": "\U0001f4ac Kontaktovat Podporu",
        "btn_back": "\u2b05\ufe0f Zp\u011bt",
        "btn_restart": "\U0001f680 Klepn\u011bte pro Za\u010d\u00e1tek",
        "btn_free_indicator": "\U0001f4f2 Z\u00edskat BEZPLATN\u00dd Indik\u00e1tor",
        "btn_join": "\U0001f4e2 P\u0159ipojit se ke Kan\u00e1lu",
        "btn_whats_new": "\U0001f195 Co Je Nov\u00e9ho Dnes",
        "btn_vip_results": "\U0001f3c6 Dne\u0161n\u00ed VIP V\u00fdsledky",
        "btn_winners": "\U0001f451 V\u00edt\u011bzov\u00e9 T\u00fddne",
        "btn_my_streak": "\U0001f525 M\u016fj Denn\u00ed Streak",
        "btn_tip": "\U0001f4a1 Denn\u00ed Tip",
        "btn_quiz": "\U0001f9e0 Kv\u00edz",
        "btn_profile": "\U0001f464 M\u016fj Profil",
        "btn_results_history": "\U0001f4c5 Minul\u00e9 V\u00fdsledky",
        "btn_stories": "\u2b50 P\u0159\u00edb\u011bhy \u00dasp\u011bchu",
        "fallback_msg": "\U0001f914 Nena\u0161el jsem odpov\u011b\u010f na to.\n\nChcete mluvit s na\u0161\u00edm t\u00fdmem podpory?",
        "msg_received": "\U0001f4e8 Zpr\u00e1va p\u0159ijata! N\u00e1\u0161 t\u00fdm odpov\u00ed brzy. \U0001f64f",
        "no_news": "\U0001f4e2 *Zat\u00edm \u017e\u00e1dn\u00e9 nov\u00e9 aktualizace!*\n\nZkuste to znovu pozd\u011bji. \U0001f514",
        "no_vip": "\U0001f4ca *Dnes nejsou zve\u0159ejn\u011bny \u017e\u00e1dn\u00e9 VIP v\u00fdsledky!*\n\nP\u0159ipojte se k VIP kan\u00e1lu pro \u017eiv\u00e9 sign\u00e1ly. \u26a1",
        "no_results_history": "\U0001f4c5 *Zat\u00edm \u017e\u00e1dn\u00e9 minul\u00e9 v\u00fdsledky!*\n\nAdmin sem zve\u0159ejn\u00ed v\u00fdsledky relac\u00ed. \u26a1",
        "spin_spinning": "\U0001f3b0 To\u010d\u00ed se...",
    },
}

for _lc, _keys in _extra_ui.items():
    if _lc in UI:
        UI[_lc].update(_keys)



# ── Referral discount messages ─────────────────────────────────
REFERRAL_DISCOUNT_MSG = {
    "en": (
        "🎉 *CONGRATULATIONS {name}!* 🏆\n\n"
        "You have successfully referred *{count} people* to EVALON WINNERS!\n\n"
        "🎁 *YOUR REWARD: 5% DISCOUNT!*\n\n"
        "You have earned a *5% discount* on ANY of our services!\n\n"
        "💡 But it gets better — keep inviting:\n"
        "• 10 referrals → 10% discount\n"
        "• 20 referrals → 20% discount\n"
        "• 50 referrals → 50% discount\n"
        "• 100 referrals → 70% discount 🔥\n\n"
        "The more you invite, the more you save!\n\n"
        "👇 Contact our team to redeem your discount:"
    ),
    "sw": (
        "🎉 *HONGERA {name}!* 🏆\n\n"
        "Umefanikiwa kuwalika *watu {count}* kwenye EVALON WINNERS!\n\n"
        "🎁 *ZAWADI YAKO: PUNGUZO LA 5%!*\n\n"
        "Umepata *punguzo la 5%* kwenye HUDUMA YOYOTE yetu!\n\n"
        "💡 Lakini inazidi kuwa nzuri — endelea kuwaandika:\n"
        "• Watu 10 → punguzo la 10%\n"
        "• Watu 20 → punguzo la 20%\n"
        "• Watu 50 → punguzo la 50%\n"
        "• Watu 100 → punguzo la 70% 🔥\n\n"
        "Unavyowaalika watu wengi zaidi, ndivyo unavyookoa zaidi!\n\n"
        "👇 Wasiliana na timu yetu kupata punguzo lako:"
    ),
}
# Use English for other languages
for _lc in ["ar","zh","hi","ru","es","fr","pt","de","ur","ja","it","ko","tr","fa","pl","uk","kk","cs"]:
    REFERRAL_DISCOUNT_MSG[_lc] = REFERRAL_DISCOUNT_MSG["en"]

# ── Onboarding messages (new users only, once) ─────────────────
ONBOARDING_VIDEO = "BAACAgQAAxkBAAID3WoKFvd6vxGTQBe9wd-2Gbh3uCMgAALEIAACgwZRUOtEi7uuFxmIOwQ"

ONBOARDING_TEXT = {
    "en": (
        "🤖 Hello *{name}*, Welcome to *Evalon Winners* 🚀\n\n"
        "I am a smart trading system created to help traders access useful tools, "
        "learning resources and different trading services for Binary Trading. 📈\n\n"
        "Inside, you will find systems designed to help you improve and grow your trading journey. 🔥\n\n"
        "My goal is to give traders one place with everything they need.\n\n"
        "From learning market analysis, understanding strategies, using trading tools "
        "and exploring better ways to improve trading knowledge and experience. 📊\n\n"
        "*Evalon Winners Trader* is made for both beginners and experienced traders.\n\n"
        "Whether you want to learn more, improve your strategy or explore smart trading systems, "
        "you are in the right place. 🚀✨\n\n"
        "Thank you for joining us.\n\n"
        "All services are ready inside our system and waiting for you to explore.\n\n"
        "*Press Continue to proceed* 🚀"
    ),
    "sw": (
        "🤖 Habari *{name}*, Karibu *Evalon Winners* 🚀\n\n"
        "Mimi ni mfumo wa biashara mahiri uliotengenezwa kusaidia wafanyabiashara kupata "
        "zana muhimu, rasilimali za kujifunza na huduma mbalimbali za biashara ya Binary. 📈\n\n"
        "Ndani, utapata mifumo iliyoundwa kukusaidia kuboresha na kukuza safari yako ya biashara. 🔥\n\n"
        "Lengo langu ni kuwapa wafanyabiashara mahali pamoja na kila wanachohitaji.\n\n"
        "Kuanzia kujifunza uchambuzi wa soko, kuelewa mikakati, kutumia zana za biashara "
        "na kuchunguza njia bora za kuboresha maarifa na uzoefu wa biashara. 📊\n\n"
        "*Evalon Winners Trader* imetengenezwa kwa wanaoanza na wafanyabiashara wenye uzoefu.\n\n"
        "Iwe unataka kujifunza zaidi, kuboresha mkakati wako au kuchunguza mifumo ya biashara mahiri, "
        "uko mahali pazuri. 🚀✨\n\n"
        "Asante kwa kujiunga nasi.\n\n"
        "Huduma zote zipo tayari ndani ya mfumo wetu na zinakusubiri kuzichunguza.\n\n"
        "*Bonyeza Endelea kuendelea* 🚀"
    ),
}
for _lc in ["ar","zh","hi","ru","es","fr","pt","de","ur","ja","it","ko","tr","fa","pl","uk","kk","cs"]:
    ONBOARDING_TEXT[_lc] = ONBOARDING_TEXT["en"]

def get_onboarding_text(lang, name):
    text = ONBOARDING_TEXT.get(lang, ONBOARDING_TEXT["en"])
    return text.format(name=escape_md(name))

def ui(key, lang):
    return UI.get(lang, UI["en"]).get(key, UI["en"].get(key, key))

def get_lang(context, user_id=None):
    """Load lang from DB if not in memory (survives restarts)"""
    lang = context.user_data.get("lang")
    if not lang and user_id:
        try:
            info = get_user_info(user_id)
            lang = info.get("lang", "en") or "en"
            context.user_data["lang"] = lang
        except:
            lang = "en"
    return lang or "en"

def get_replies(pool, lang):
    return pool.get(lang) or pool.get("en", ["Coming soon!"])

# ══════════════════════════════════════════════════════════════
#  FEEDBACK DATABASE SYSTEM
#  - Admin adds custom feedback via /feedbackadd
#  - All feedback stored in DB (custom + built-in)
#  - /feedback N — sends N mixed (EN-heavy) feedback
#  - /feedbackdlt — deletes all custom feedback from DB
#  - Built-in feedback always available as fallback
# ══════════════════════════════════════════════════════════════

def init_feedback_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS custom_feedback (
            id          SERIAL PRIMARY KEY,
            name        TEXT NOT NULL,
            flag        TEXT DEFAULT '🌍',
            text_val    TEXT NOT NULL,
            lang        TEXT DEFAULT 'en',
            added_at    TEXT DEFAULT NULL
        )
    """)
    conn.commit()
    conn.close()

def add_custom_feedback(name, flag, text_val, lang="en"):
    conn = get_conn()
    c = conn.cursor()
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    c.execute("""
        INSERT INTO custom_feedback (name, flag, text_val, lang, added_at)
        VALUES (%s, %s, %s, %s, %s)
    """, (name, flag, text_val, lang, now))
    conn.commit()
    conn.close()

def get_custom_feedback():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT name, flag, text_val, lang FROM custom_feedback ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return [(r[0], r[1], r[2], r[3]) for r in rows]

def delete_all_custom_feedback():
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM custom_feedback")
    count = c.rowcount
    conn.commit()
    conn.close()
    return count

def get_mixed_feedback(count):
    """
    Get N feedback — mixed languages, EN-heavy.
    Mix ratio: ~70% EN, ~20% SW, ~10% UR from built-in.
    Custom feedback from DB included and shuffled in.
    Same day = same order (rotates daily).
    """
    day_seed = datetime.now().timetuple().tm_yday + datetime.now().year
    rng = random.Random(day_seed)

    # Get custom feedback from DB
    custom = get_custom_feedback()

    # Build pool: EN-heavy mix
    en_pool = [(n, f, t) for n, f, t in FAKE_FEEDBACK["en"]]
    sw_pool = [(n, f, t) for n, f, t in FAKE_FEEDBACK["sw"]]
    ur_pool = [(n, f, t) for n, f, t in FAKE_FEEDBACK["ur"]]

    # Shuffle each pool with today's seed
    rng.shuffle(en_pool)
    rng.shuffle(sw_pool)
    rng.shuffle(ur_pool)

    # Interleave: pattern EN,EN,EN,EN,SW,EN,EN,EN,UR,EN...
    # Roughly 70% EN, 20% SW, 10% UR
    combined = []
    ei = si = ui_idx = 0
    pattern = ["en","en","en","en","sw","en","en","en","ur","en"]
    pi = 0
    while len(combined) < count * 3:  # build large pool then slice
        lang_pick = pattern[pi % len(pattern)]
        pi += 1
        if lang_pick == "en" and ei < len(en_pool):
            combined.append(en_pool[ei]); ei += 1
        elif lang_pick == "sw" and si < len(sw_pool):
            combined.append(sw_pool[si]); si += 1
        elif lang_pick == "ur" and ui_idx < len(ur_pool):
            combined.append(ur_pool[ui_idx]); ui_idx += 1
        else:
            # fallback to EN if pool exhausted
            if ei < len(en_pool):
                combined.append(en_pool[ei]); ei += 1
            elif si < len(sw_pool):
                combined.append(sw_pool[si]); si += 1
            else:
                break

    # Inject custom feedback at random positions
    if custom:
        custom_tuples = [(n, f, t) for n, f, t, l in custom]
        rng.shuffle(custom_tuples)
        for i, item in enumerate(custom_tuples):
            pos = rng.randint(0, max(0, len(combined)-1))
            combined.insert(pos, item)

    # Slice to requested count, cycling if needed
    result = []
    while len(result) < count:
        result.extend(combined)
    return result[:count]

# ══════════════════════════════════════════════════════════════
#  MESSAGE TRACKING
# ══════════════════════════════════════════════════════════════

def track_msg(chat_id, msg_id):
    if chat_id not in bot_msg_ids:
        bot_msg_ids[chat_id] = []
    bot_msg_ids[chat_id].append(msg_id)
    if len(bot_msg_ids[chat_id]) > 100:
        bot_msg_ids[chat_id] = bot_msg_ids[chat_id][-100:]

def track_support_msg(chat_id, msg_id):
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
    if chat_id in bot_msg_ids:
        for msg_id in bot_msg_ids[chat_id]:
            await safe_delete(context, chat_id, msg_id)
        bot_msg_ids[chat_id] = []

async def delete_support_msgs(context, chat_id):
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
    name = escape_md(user.full_name)
    username = escape_md(user.username or "NA")
    text = f"🆕 *New User!*\n\n👤 {name}\n🔗 @{username}\n🆔 `{user.id}`\n🕐 {now}"
    for aid in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=aid, text=text, parse_mode="Markdown")
        except Exception as e:
            logger.warning(f"Notify failed: {e}")

async def notify_support_request(context, user, lang):
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    name = escape_md(user.full_name)
    username = escape_md(user.username or "NA")
    text = (
        f"🆘 *Support Request*\n\n"
        f"👤 {name}\n🔗 @{username}\n"
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
#  AUTO CLEAN JOB
# ══════════════════════════════════════════════════════════════

async def auto_clean_chat(context: ContextTypes.DEFAULT_TYPE):
    job_data = context.job.data
    chat_id = job_data["chat_id"]
    lang    = job_data.get("lang", "en")
    name    = job_data.get("name", "")
    uid     = job_data.get("uid")

    if uid and active_support.get(uid):
        schedule_auto_clean(context, chat_id, lang, name, uid)
        return

    await delete_all_bot_msgs(context, chat_id)

    try:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        await asyncio.sleep(1.0)
        clean_text = get_auto_clean_msg(lang, name)
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text=clean_text,
            parse_mode="Markdown",
            protect_content=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(ui("btn_spin", lang), callback_data="do_spin")],
                [InlineKeyboardButton(ui("btn_services", lang), callback_data="menu_services")],
                [InlineKeyboardButton(ui("btn_restart", lang), callback_data="main_menu")],
            ]))
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
        text = ui("comeback_msg", lang).format(name=escape_md(name))
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
        [InlineKeyboardButton("🇮🇹 Italiano", callback_data="lang_it"),
         InlineKeyboardButton("🇰🇷 한국어", callback_data="lang_ko"),
         InlineKeyboardButton("🇹🇷 Türkçe", callback_data="lang_tr")],
        [InlineKeyboardButton("🇮🇷 فارسی", callback_data="lang_fa"),
         InlineKeyboardButton("🇵🇱 Polski", callback_data="lang_pl"),
         InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_uk")],
        [InlineKeyboardButton("🇰🇿 Қазақша", callback_data="lang_kk"),
         InlineKeyboardButton("🇨🇿 Čeština", callback_data="lang_cs")],
    ])

def main_menu(lang):
    rows = [
        [InlineKeyboardButton(ui("btn_services", lang), callback_data="menu_services")],
        [InlineKeyboardButton(ui("btn_whats_new", lang), callback_data="do_whats_new"),
         InlineKeyboardButton(ui("btn_vip_results", lang), callback_data="do_vip_results")],
        [InlineKeyboardButton(ui("btn_tip", lang), callback_data="do_tip"),
         InlineKeyboardButton(ui("btn_quiz", lang), callback_data="do_quiz")],
        [InlineKeyboardButton(ui("btn_winners", lang), callback_data="do_winners"),
         InlineKeyboardButton(ui("btn_my_streak", lang), callback_data="do_streak")],
        [InlineKeyboardButton(ui("btn_results_history", lang), callback_data="do_results_history"),
         InlineKeyboardButton(ui("btn_profile", lang), callback_data="do_profile")],
        [InlineKeyboardButton(ui("btn_spin", lang), callback_data="do_spin")],
    ]
    # Referral row — add Stories button only if admin has posted stories
    ref_row = [InlineKeyboardButton(ui("btn_referral", lang), callback_data="do_referral")]
    try:
        if has_stories():
            ref_row.append(InlineKeyboardButton(ui("btn_stories", lang), callback_data="do_stories"))
    except:
        pass
    rows.append(ref_row)
    rows.append([InlineKeyboardButton(ui("btn_language", lang), callback_data="change_lang")])
    return InlineKeyboardMarkup(rows)

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
    rows = [
        [InlineKeyboardButton("🌐 All Brokers Bot", url=FREE_BOT_LINKS["all_brokers"])],
        [InlineKeyboardButton("💎 Evalon Winners Bot", url=FREE_BOT_LINKS["evalon"])],
        [InlineKeyboardButton("🤖 Evalon AI Bot", url=FREE_BOT_LINKS["evalon_ai"])],
        [InlineKeyboardButton("📊 Quotex Pro Bot", url=FREE_BOT_LINKS["quotex"])],
        [InlineKeyboardButton("💰 Pocket Option Bot 🆕", callback_data="show_pocket_bot")],
    ]
    # Dynamically add admin-added bots from DB
    try:
        admin_bots = get_admin_bots()
        for bid, name, link, desc in admin_bots:
            rows.append([InlineKeyboardButton(f"🆕 {name}", url=link)])
    except:
        pass
    rows.append([InlineKeyboardButton(ui("btn_back", lang), callback_data="menu_services")])
    return InlineKeyboardMarkup(rows)

def svc_keyboard(lang, indicator=False, signals=False, autobot=False, social=False):
    rows = []

    # Video links per service
    if signals:
        rows.append([
            InlineKeyboardButton("▶️ Real Signal Results 🔥", url="https://youtu.be/rflkvCWG-fw?si=VFWoZO1cPqCQbg83"),
            InlineKeyboardButton("📱 Live Wins 1", url="https://vt.tiktok.com/ZSx2do7SF/"),
        ])
        rows.append([
            InlineKeyboardButton("📱 Live Wins 2", url="https://vt.tiktok.com/ZSx2d3RmU/"),
        ])

    if autobot:
        rows.append([
            InlineKeyboardButton("▶️ See Real Profits 🔥", url="https://youtu.be/q3Sa9ndExNc?si=MmMVL9F7t-fRzXQF"),
            InlineKeyboardButton("📱 Bot Wins Live", url="https://vt.tiktok.com/ZSx2RHF25/"),
        ])

    if social:
        rows.append([
            InlineKeyboardButton("▶️ Traders Winning Live 🔥", url="https://vt.tiktok.com/ZSx2RNM2m/"),
            InlineKeyboardButton("📱 Copy Trade Results", url="https://vt.tiktok.com/ZSx2dpgxt/"),
        ])

    if indicator:
        rows.append([InlineKeyboardButton(
            ui("btn_free_indicator", lang), url=INDICATOR_CHANNEL)])
        rows.append([
            InlineKeyboardButton("▶️ See It In Action 🔥", url="https://vt.tiktok.com/ZSx2dGWab/"),
            InlineKeyboardButton("📱 Real Results 2", url="https://vt.tiktok.com/ZSx2RQcpD/"),
        ])
        rows.append([
            InlineKeyboardButton("📱 Real Results 3", url="https://vt.tiktok.com/ZSx2RrX7T/"),
        ])

    rows.append([InlineKeyboardButton(ui("btn_website", lang), url=WEBSITE_URL)])
    rows.append([InlineKeyboardButton(ui("btn_support", lang), callback_data="do_support")])
    rows.append([InlineKeyboardButton(ui("btn_back", lang), callback_data="menu_services")])
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
    join_texts = {
        "en": "🚀 Join Us Now",
        "sw": "🚀 Jiunge Nasi Sasa",
        "ar": "🚀 انضم إلينا الآن",
        "zh": "🚀 立即加入我们",
        "hi": "🚀 अभी हमसे जुड़ें",
        "ru": "🚀 Присоединяйтесь сейчас",
        "es": "🚀 Únete ahora",
        "fr": "🚀 Rejoignez-nous maintenant",
        "pt": "🚀 Junte-se a nós agora",
        "de": "🚀 Jetzt mitmachen",
        "ur": "🚀 ابھی ہم سے جڑیں",
        "ja": "🚀 今すぐ参加",
    }
    btn_text = join_texts.get(lang, join_texts["en"])
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(btn_text, callback_data="menu_services")],
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

    # Track pending request so bot can verify membership
    pending_requests[user.id] = {
        "chat_id": chat.id, "chat_title": chat.title,
        "user": user, "time": now,
    }
    # NOTE: No admin notification here — admin uses separate bot for approvals
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
    lang = get_lang(context, user.id)
    register_user(user, referred_by=referred_by, lang=lang)

    if new_user:
        await notify_new_user(context, user)
        if referred_by:
            ref_count = get_referral_count(referred_by)
            # Notify referrer of discount milestones
            milestones = {5: 5, 10: 10, 20: 20, 50: 50, 100: 70}
            if ref_count in milestones:
                ref_info = get_user_info(referred_by)
                ref_lang = ref_info.get("lang", "en") or "en"
                ref_name = escape_md(ref_info['name'])
                discount = milestones[ref_count]
                discount_text = REFERRAL_DISCOUNT_MSG.get(ref_lang, REFERRAL_DISCOUNT_MSG["en"])
                try:
                    await context.bot.send_message(
                        chat_id=referred_by,
                        text=discount_text.format(name=ref_name, count=ref_count, discount=discount),
                        parse_mode="Markdown",
                        protect_content=True,
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🎁 Claim My Reward!", callback_data="claim_discount")
                        ]]))
                except:
                    pass
                # Also notify admin
                for aid in ADMIN_IDS:
                    try:
                        await context.bot.send_message(
                            chat_id=aid,
                            text=f"🏆 *REFERRAL MILESTONE!*\n\n👤 {ref_name}\n📊 Reached *{ref_count} referrals*\n🎁 Earned *{discount}% discount*",
                            parse_mode="Markdown")
                    except:
                        pass

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

    # NEW USER ONBOARDING — only once, only truly new users
    if new_user and not has_done_onboarding(user.id):
        await typing_action(cid, context, 1.0)
        # Step 1: Send video
        try:
            vid_msg = await context.bot.send_video(
                chat_id=cid,
                video=ONBOARDING_VIDEO,
                protect_content=True)
            track_msg(cid, vid_msg.message_id)
        except Exception as e:
            logger.warning(f"Onboarding video failed: {e}")

        await asyncio.sleep(1.0)

        # Step 2: Send onboarding text with Continue button
        onboard_text = get_onboarding_text(lang, user.first_name)
        onboard_msg = await send_protected_text(
            context, cid,
            onboard_text,
            InlineKeyboardMarkup([[
                InlineKeyboardButton("🚀 Continue", callback_data="onboarding_done")
            ]]))
        track_msg(cid, onboard_msg.message_id)
        context.user_data["onboarding_msg_ids"] = [
            vid_msg.message_id if 'vid_msg' in dir() else None,
            onboard_msg.message_id
        ]
        return

    visit_count = context.user_data.get("visit_count", 0) + 1
    context.user_data["visit_count"] = visit_count
    welcome_text = build_welcome_text(lang, user.first_name, visit_count)
    streak, is_new_record = update_streak(user.id)

    msg = await send_protected_photo(
        context, cid, WELCOME_IMAGE, welcome_text, main_menu(lang))
    context.user_data["last_bot_msg_id"] = msg.message_id
    track_msg(cid, msg.message_id)

    # Notify streak milestone silently after menu loads
    if streak in [3, 7, 14, 30, 60, 100]:
        badge_emoji, badge_name = get_streak_badge(streak)
        streak_texts = {
            "en": f"🔥 *{streak} Day Streak!* {badge_emoji}\n\nYou've been active for *{streak} days in a row!*\nYou just unlocked the *{badge_name}* badge! Keep it up! 💪",
            "sw": f"🔥 *Streak ya Siku {streak}!* {badge_emoji}\n\nUmekuwa hai kwa *siku {streak} mfululizo!*\nUmefungua badge ya *{badge_name}*! Endelea! 💪",
        }
        streak_text = streak_texts.get(lang, streak_texts["en"])
        try:
            streak_msg = await context.bot.send_message(
                chat_id=cid, text=streak_text,
                parse_mode="Markdown", protect_content=True)
            track_msg(cid, streak_msg.message_id)
        except:
            pass

    schedule_comeback(context, cid, user.first_name, lang)
    schedule_smart_comebacks(context, cid, user.first_name, lang)
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
                await context.bot.send_photo(
                    chat_id=uid, photo=replied_msg.photo[-1].file_id,
                    caption=replied_msg.caption or "",
                    parse_mode="Markdown")
            elif replied_msg and replied_msg.video:
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
                await context.bot.send_message(
                    chat_id=uid, text=replied_msg.text,
                    parse_mode="Markdown",
                    reply_markup=broadcast_keyboard(user_lang))
            elif context.args:
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
        safe_name = escape_md(name)
        top_text += f"{i}. {safe_name} — {refs} referrals\n"

    await update.message.reply_text(
        f"📊 *EVALON WINNERS — STATS*\n\n"
        f"👥 Total users: *{total}*\n"
        f"🆕 New today: *{new_today}*\n"
        f"🟢 Active 7d: *{active7}*\n"
        f"📅 Active 30d: *{active30}*\n"
        f"🆘 Active support: *{len(active_support)}*\n\n"
        f"🏆 *TOP REFERRERS:*\n{top_text or 'None yet'}\n\n"
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
        safe_name = escape_md(u['name'])
        text += f"👤 {safe_name} | `{uid}`\n"
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

    lang = get_lang(context, user.id)

    # Language select
    if data.startswith("lang_"):
        new_lang = data[5:]
        context.user_data["lang"] = new_lang
        register_user(user, lang=new_lang)
        await safe_delete(context, cid, query.message.message_id)
        await delete_all_bot_msgs(context, cid)
        await typing_action(cid, context, 1.5)

        if not await is_member(context, user.id):
            msg = await send_protected_text(
                context, cid, ui("join_msg", new_lang), join_keyboard(new_lang))
            context.user_data["last_bot_msg_id"] = msg.message_id
            track_msg(cid, msg.message_id)
            return

        welcome_text = build_welcome_text(new_lang, user.first_name)
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
            welcome_text = build_welcome_text(lang, user.first_name)
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
        welcome_text = build_welcome_text(lang, user.first_name)
        msg = await send_protected_photo(
            context, cid, WELCOME_IMAGE,
            f"✅ Got it!\n\n{welcome_text}", main_menu(lang))
        context.user_data["last_bot_msg_id"] = msg.message_id
        track_msg(cid, msg.message_id)
        schedule_comeback(context, cid, user.first_name, lang)
        schedule_auto_clean(context, cid, lang, user.first_name, user.id)
        return

    # FIX: User skips text opinion — MUST be BEFORE rate_ check to avoid int("skip") crash
    if data == "rate_skip":
        awaiting_rating_opinion.pop(user.id, None)
        await safe_delete(context, cid, query.message.message_id)
        await delete_all_bot_msgs(context, cid)
        await typing_action(cid, context, 1.0)
        welcome_text = build_welcome_text(lang, user.first_name)
        msg = await send_protected_photo(
            context, cid, WELCOME_IMAGE,
            f"{ui('rating_thanks', lang).format(name=escape_md(user.first_name))}\n\n{welcome_text}",
            main_menu(lang))
        context.user_data["last_bot_msg_id"] = msg.message_id
        track_msg(cid, msg.message_id)
        return

    # FIX: Rating — ask for text opinion after stars
    if data.startswith("rate_"):
        stars = int(data[5:])
        star_display = "⭐" * stars
        await safe_delete(context, cid, query.message.message_id)
        await typing_action(cid, context, 1.0)

        # Notify admin of star rating
        name = escape_md(user.full_name)
        for aid in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=aid,
                    text=f"⭐ *Rating received*\n\n👤 {name}\n🆔 `{user.id}`\n{star_display} ({stars}/5)\n\n⏳ Waiting for text opinion...",
                    parse_mode="Markdown")
            except:
                pass

        # Save stars and ask for text opinion
        awaiting_rating_opinion[user.id] = {"stars": stars, "star_display": star_display}

        msg = await send_protected_text(
            context, cid,
            ui("rating_opinion_msg", lang),
            InlineKeyboardMarkup([[
                InlineKeyboardButton("⏭ Skip", callback_data="rate_skip")
            ]]))
        track_msg(cid, msg.message_id)
        return

    # Navigation buttons
    await safe_delete(context, cid, query.message.message_id)
    await delete_all_bot_msgs(context, cid)
    await typing_action(cid, context, 1.5)

    if data == "main_menu":
        welcome_text = build_welcome_text(lang, user.first_name)
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
            context, cid, img, random.choice(replies), svc_keyboard(lang, signals=True))
        context.user_data["last_bot_msg_id"] = msg.message_id
        track_msg(cid, msg.message_id)
        schedule_fomo(context, cid, lang, "VIP Signals")

    elif data == "svc_social":
        replies = get_replies(SOCIAL_REPLIES, lang)
        img = rand_img(IMGS_SOCIAL, context.user_data, "last_img_social")
        msg = await send_protected_photo(
            context, cid, img, random.choice(replies), svc_keyboard(lang, social=True))
        context.user_data["last_bot_msg_id"] = msg.message_id
        track_msg(cid, msg.message_id)
        schedule_fomo(context, cid, lang, "Social Trading")

    elif data == "svc_indicator":
        replies = get_replies(INDICATOR_REPLIES, lang)
        img = rand_img(IMGS_INDICATOR, context.user_data, "last_img_indicator")
        msg = await send_protected_photo(
            context, cid, img, random.choice(replies),
            svc_keyboard(lang, indicator=True))
        context.user_data["last_bot_msg_id"] = msg.message_id
        track_msg(cid, msg.message_id)
        schedule_fomo(context, cid, lang, "Free Indicator")

    elif data == "svc_autobot":
        replies = get_replies(AUTOBOT_REPLIES, lang)
        img = rand_img(IMGS_AUTOBOT, context.user_data, "last_img_autobot")
        msg = await send_protected_photo(
            context, cid, img, random.choice(replies), svc_keyboard(lang, autobot=True))
        context.user_data["last_bot_msg_id"] = msg.message_id
        track_msg(cid, msg.message_id)
        schedule_fomo(context, cid, lang, "Auto Bot")

    elif data == "svc_freebot":
        replies = get_replies(FREEBOT_REPLIES, lang)
        img = rand_img(IMGS_FREEBOT, context.user_data, "last_img_freebot")
        msg = await send_protected_photo(
            context, cid, img, random.choice(replies), freebot_menu(lang))
        context.user_data["last_bot_msg_id"] = msg.message_id
        track_msg(cid, msg.message_id)
        schedule_fomo(context, cid, lang, "Free Manual Bot")

    # ── CLAIM DISCOUNT — validates referral count first ───────
    elif data == "claim_discount":
        ref_count = get_referral_count(user.id)
        if ref_count < REFERRAL_MIN:
            needed = REFERRAL_MIN - ref_count
            ref_link = f"https://t.me/{BOT_USERNAME}?start=ref{user.id}"
            error_texts = {
                "en": (
                    f"❌ *Not enough referrals yet!*\n\n"
                    f"📊 Your progress: *{ref_count}/{REFERRAL_MIN}*\n\n"
                    f"You need *{needed} more* people to unlock your discount.\n\n"
                    f"🔗 Share your link and keep inviting:\n{ref_link}\n\n"
                    f"The more you invite, the bigger your reward — up to *70% OFF!* 🔥"
                ),
                "sw": (
                    f"❌ *Bado huna rufaa za kutosha!*\n\n"
                    f"📊 Maendeleo yako: *{ref_count}/{REFERRAL_MIN}*\n\n"
                    f"Unahitaji *{needed} zaidi* kufungua punguzo lako.\n\n"
                    f"🔗 Shiriki kiungo chako na endelea kuwa kuita:\n{ref_link}\n\n"
                    f"Unavyowaleta watu wengi, tuzo yako inakuwa kubwa — hadi *70% PUNGUZO!* 🔥"
                ),
                "ar": (
                    f"❌ *ليس لديك إحالات كافية بعد!*\n\n"
                    f"📊 تقدمك: *{ref_count}/{REFERRAL_MIN}*\n\n"
                    f"تحتاج إلى *{needed} شخص آخر* لفتح خصمك.\n\n"
                    f"🔗 شارك رابطك وتابع الدعوة:\n{ref_link}\n\n"
                    f"كلما دعوت أكثر، كلما كانت مكافأتك أكبر — حتى *70% خصم!* 🔥"
                ),
                "ru": (
                    f"❌ *Недостаточно рефералов!*\n\n"
                    f"📊 Ваш прогресс: *{ref_count}/{REFERRAL_MIN}*\n\n"
                    f"Вам нужно ещё *{needed} человек* для разблокировки скидки.\n\n"
                    f"🔗 Поделитесь ссылкой:\n{ref_link}\n\n"
                    f"Чем больше людей, тем больше скидка — до *70%!* 🔥"
                ),
            }
            error_text = error_texts.get(lang, error_texts["en"])
            # Send error as plain (link not protected so easy to copy)
            await delete_all_bot_msgs(context, cid)
            try:
                msg = await context.bot.send_message(
                    chat_id=cid,
                    text=error_text,
                    parse_mode="Markdown",
                    protect_content=False,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(ui("btn_back", lang), callback_data="do_referral")]
                    ]))
                track_msg(cid, msg.message_id)
            except:
                pass
            return
        # Reached minimum — proceed to support
        await notify_support_request(context, user, lang)
        msg = await send_protected_text(
            context, cid, ui("support_msg", lang),
            InlineKeyboardMarkup([
                [InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")]
            ]))
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

        # MSG 1 — Main referral info
        ref_text = ui("referral_msg", lang).format(
            bot=BOT_USERNAME, uid=user.id,
            count=ref_count, min=REFERRAL_MIN,
            needed=needed, bar=bar,
            leaderboard=leaderboard)
        try:
            msg = await send_protected_text(
                context, cid, ref_text,
                InlineKeyboardMarkup([
                    [InlineKeyboardButton("👥 View My Referrals", callback_data="view_referrals")],
                    [InlineKeyboardButton(ui("btn_support", lang), callback_data="do_support")],
                    [InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")],
                ]))
            context.user_data["last_bot_msg_id"] = msg.message_id
            track_msg(cid, msg.message_id)
        except Exception as e:
            logger.warning(f"Referral msg failed: {e}")

        # MSG 2 — Link (plain, easy to copy)
        ref_link = f"https://t.me/{BOT_USERNAME}?start=ref{user.id}"
        try:
            link_msg = await context.bot.send_message(
                chat_id=cid,
                text=ref_link,
                protect_content=False)
            track_msg(cid, link_msg.message_id)
        except:
            pass

        # MSG 3 — Total count + persuasion (no % shown, just motivate)
        if ref_count >= REFERRAL_MIN:
            # Milestone reached — congratulate!
            congrats_texts = {
                "en": (
                    f"🎉 *CONGRATULATIONS {escape_md(user.first_name)}!*\n\n"
                    f"You have invited *{ref_count} people* and earned a *discount reward!*\n\n"
                    f"💰 Contact our team to claim your discount now!\n\n"
                    f"🚀 Keep inviting — the more people you bring, the bigger your reward gets up to *70% OFF* any service!"
                ),
                "sw": (
                    f"🎉 *HONGERA {escape_md(user.first_name)}!*\n\n"
                    f"Umemualika *watu {ref_count}* na umepata *tuzo ya punguzo!*\n\n"
                    f"💰 Wasiliana na timu yetu kudai punguzo lako sasa!\n\n"
                    f"🚀 Endelea kuwa kuita — unavyowaleta watu wengi, tuzo yako inakuwa kubwa zaidi hadi *70% PUNGUZO* kwenye huduma yoyote!"
                ),
                "ar": (
                    f"🎉 *تهانينا {escape_md(user.first_name)}!*\n\n"
                    f"لقد دعوت *{ref_count} شخص* وحصلت على *مكافأة خصم!*\n\n"
                    f"💰 تواصل مع فريقنا للمطالبة بخصمك الآن!\n\n"
                    f"🚀 استمر في الدعوة — كلما أحضرت أكثر، كلما كانت مكافأتك أكبر حتى *70% خصم*!"
                ),
                "ru": (
                    f"🎉 *ПОЗДРАВЛЯЕМ {escape_md(user.first_name)}!*\n\n"
                    f"Вы пригласили *{ref_count} человек* и заработали *скидку!*\n\n"
                    f"💰 Свяжитесь с нашей командой, чтобы получить скидку!\n\n"
                    f"🚀 Продолжайте приглашать — чем больше людей, тем больше скидка до *70%*!"
                ),
            }
            congrats = congrats_texts.get(lang, congrats_texts["en"])
            try:
                p_msg = await send_protected_text(
                    context, cid, congrats,
                    InlineKeyboardMarkup([
                        [InlineKeyboardButton("🎁 Claim My Discount Now!", callback_data="claim_discount")],
                        [InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")],
                    ]))
                track_msg(cid, p_msg.message_id)
            except:
                pass
        else:
            # Not yet reached — motivate without showing %
            persuasion_texts = {
                "en": (
                    f"📊 *Your Progress: {ref_count}/{REFERRAL_MIN} people invited*\n\n"
                    f"🎯 Invite just *{needed} more* friends to unlock your first reward!\n\n"
                    f"💡 *Why keep inviting?*\n"
                    f"Every person you invite grows your discount — the more you invite, the more you save on any of our services!\n\n"
                    f"Our top inviters enjoy up to *70% OFF* — it's completely free!\n\n"
                    f"🔗 Share your link above and start saving today!"
                ),
                "sw": (
                    f"📊 *Maendeleo Yako: {ref_count}/{REFERRAL_MIN} watu wamealikwa*\n\n"
                    f"🎯 Alika *{needed} zaidi* tu kufungua tuzo yako ya kwanza!\n\n"
                    f"💡 *Kwa nini uendelee kuwa kuita?*\n"
                    f"Kila mtu unayemwalika huongeza punguzo lako — unavyowaleta watu wengi zaidi, ndivyo unavyookoa zaidi kwenye huduma zetu!\n\n"
                    f"Wanaoalika wengi zaidi wanafurahia hadi *70% PUNGUZO* — ni bure kabisa!\n\n"
                    f"🔗 Shiriki kiungo chako hapo juu na uanze kuokoa leo!"
                ),
                "ar": (
                    f"📊 *تقدمك: {ref_count}/{REFERRAL_MIN} شخص مدعو*\n\n"
                    f"🎯 ادعُ *{needed} شخص آخر* فقط لفتح مكافأتك الأولى!\n\n"
                    f"💡 *لماذا تستمر في الدعوة؟*\n"
                    f"كل شخص تدعوه يزيد خصمك — كلما دعوت أكثر، كلما وفرت أكثر!\n\n"
                    f"أكثر الداعين يستمتعون بخصم يصل إلى *70%* — مجاناً تماماً!\n\n"
                    f"🔗 شارك رابطك أعلاه وابدأ التوفير اليوم!"
                ),
                "ru": (
                    f"📊 *Ваш прогресс: {ref_count}/{REFERRAL_MIN} человек приглашено*\n\n"
                    f"🎯 Пригласите ещё *{needed}* друзей для первой награды!\n\n"
                    f"💡 *Почему продолжать приглашать?*\n"
                    f"Каждый приглашённый увеличивает вашу скидку — чем больше людей, тем больше экономия!\n\n"
                    f"Топ инвайтеры получают до *70% скидки* — абсолютно бесплатно!\n\n"
                    f"🔗 Поделитесь ссылкой выше и начните экономить сегодня!"
                ),
            }
            persuasion = persuasion_texts.get(lang, persuasion_texts["en"])
            try:
                p_msg = await send_protected_text(
                    context, cid, persuasion,
                    InlineKeyboardMarkup([
                        [InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")],
                    ]))
                track_msg(cid, p_msg.message_id)
            except:
                pass

    elif data == "do_stories":
        all_stories = get_all_stories()
        back_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(ui("btn_services", lang), callback_data="menu_services")],
            [InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")],
        ])
        if not all_stories:
            msg = await send_protected_text(context, cid,
                "⭐ *SUCCESS STORIES*\n\nNo stories posted yet. Check back soon!", back_kb)
            track_msg(cid, msg.message_id)
        else:
            # Pick random story, different from last shown
            last_story_id = context.user_data.get("last_story_id")
            available = [s for s in all_stories if s["id"] != last_story_id] or all_stories
            story = random.choice(available)
            context.user_data["last_story_id"] = story["id"]
            caption = story.get("caption") or "⭐ Success Story"
            header = f"⭐ *SUCCESS STORIES*\n\n{caption}"
            # Navigation if multiple stories
            nav_row = []
            if len(all_stories) > 1:
                nav_row.append(InlineKeyboardButton("🔄 Next Story", callback_data="do_stories"))
            kb = InlineKeyboardMarkup([nav_row] + [
                [InlineKeyboardButton(ui("btn_services", lang), callback_data="menu_services")],
                [InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")],
            ] if nav_row else [
                [InlineKeyboardButton(ui("btn_services", lang), callback_data="menu_services")],
                [InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")],
            ])
            mid  = story.get("media_id")
            mtyp = story.get("media_type", "text")
            msg  = None
            try:
                if mid and mtyp == "photo":
                    msg = await context.bot.send_photo(chat_id=cid, photo=mid,
                        caption=header, parse_mode="Markdown", reply_markup=kb, protect_content=True)
                elif mid and mtyp == "video":
                    msg = await context.bot.send_video(chat_id=cid, video=mid,
                        caption=header, parse_mode="Markdown", reply_markup=kb, protect_content=True)
                else:
                    msg = await send_protected_text(context, cid, header, kb)
            except Exception:
                msg = await send_protected_text(context, cid, header, kb)
            context.user_data["last_bot_msg_id"] = msg.message_id
            track_msg(cid, msg.message_id)

    # ── WHAT'S NEW TODAY ───────────────────────────────────────
    elif data == "do_whats_new":
        content = get_dynamic_content("news")
        back_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")]
        ])
        if not content:
            msg = await send_protected_text(context, cid, ui("no_news", lang), back_kb)
        else:
            updated = content.get("updated_at", "")
            header = f"🆕 *WHAT'S NEW*\n\n_{updated}_\n\n" if updated else "🆕 *WHAT'S NEW*\n\n"
            if content.get("file_id") and content.get("file_type") == "photo":
                try:
                    msg = await context.bot.send_photo(
                        chat_id=cid, photo=content["file_id"],
                        caption=header + (content.get("text") or ""),
                        parse_mode="Markdown", protect_content=True, reply_markup=back_kb)
                except:
                    msg = await send_protected_text(context, cid, header + (content.get("text") or ""), back_kb)
            elif content.get("file_id") and content.get("file_type") == "video":
                try:
                    msg = await context.bot.send_video(
                        chat_id=cid, video=content["file_id"],
                        caption=header + (content.get("text") or ""),
                        parse_mode="Markdown", protect_content=True, reply_markup=back_kb)
                except:
                    msg = await send_protected_text(context, cid, header + (content.get("text") or ""), back_kb)
            else:
                msg = await send_protected_text(context, cid, header + (content.get("text") or ""), back_kb)
        track_msg(cid, msg.message_id)

    # ── TODAY'S VIP RESULTS ────────────────────────────────────
    elif data == "do_vip_results":
        content = get_dynamic_content("vip")
        back_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Join VIP Now", url=VIP_BOT_LINK)],
            [InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")]
        ])
        if not content:
            msg = await send_protected_text(context, cid, ui("no_vip", lang), back_kb)
        else:
            updated = content.get("updated_at", "")
            header = f"🏆 *TODAY'S VIP RESULTS*\n\n_{updated}_\n\n" if updated else "🏆 *TODAY'S VIP RESULTS*\n\n"
            if content.get("file_id") and content.get("file_type") == "photo":
                try:
                    msg = await context.bot.send_photo(
                        chat_id=cid, photo=content["file_id"],
                        caption=header + (content.get("text") or ""),
                        parse_mode="Markdown", protect_content=True, reply_markup=back_kb)
                except:
                    msg = await send_protected_text(context, cid, header + (content.get("text") or ""), back_kb)
            elif content.get("file_id") and content.get("file_type") == "video":
                try:
                    msg = await context.bot.send_video(
                        chat_id=cid, video=content["file_id"],
                        caption=header + (content.get("text") or ""),
                        parse_mode="Markdown", protect_content=True, reply_markup=back_kb)
                except:
                    msg = await send_protected_text(context, cid, header + (content.get("text") or ""), back_kb)
            else:
                msg = await send_protected_text(context, cid, header + (content.get("text") or ""), back_kb)
        track_msg(cid, msg.message_id)

    # ── WINNERS OF THE WEEK ────────────────────────────────────
    elif data == "do_winners":
        leaders = get_referral_leaderboard_daily()
        medals = ["👑", "🥈", "🥉", "4️⃣", "5️⃣"]
        week_num = datetime.now().isocalendar()[1]
        # Monday of current week
        now = datetime.now()
        monday = now - timedelta(days=now.weekday())
        sunday = monday + timedelta(days=6)
        week_range = f"{monday.strftime('%d %b')} – {sunday.strftime('%d %b')}"
        user_refs = get_referral_count(user.id)
        lines = [f"👑 *TOP INVITERS — THIS WEEK*\n📅 _{week_range}_\n\n"]
        for i, (name, flag, count) in enumerate(leaders):
            lines.append(f"{medals[i]} *{name}* {flag} — *{count} people invited*\n")
        lines.append(f"\n👤 *You:* {user_refs} people invited")
        top_count = leaders[-1][2] if leaders else 10
        if user_refs < top_count:
            gap = top_count - user_refs
            lines.append(f"\n💪 Invite *{gap} more* to enter the Top 5!")
        else:
            lines.append("\n🔥 *You're in the top tier! Keep going!*")
        lines.append("\n\n🔄 *Leaderboard resets every Monday!*\n🚀 Share your link → climb the ranks!")
        winners_text = "\n".join(lines)
        img = rand_img(SERVICE_PHOTOS, context.user_data, "last_img_winners")
        msg = await send_protected_photo(
            context, cid, img, winners_text,
            InlineKeyboardMarkup([
                [InlineKeyboardButton(ui("btn_referral", lang), callback_data="do_referral")],
                [InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")],
            ]))
        track_msg(cid, msg.message_id)

    # ── MY DAILY STREAK ────────────────────────────────────────
    elif data == "do_streak":
        streak, max_streak = get_streak(user.id)
        if streak == 0:
            streak = 1
        badge_emoji, badge_name = get_streak_badge(streak)
        next_days, next_emoji, next_name = get_next_badge(streak)
        streak_texts = {
            "en": (
                f"🔥 *YOUR DAILY STREAK*\n\n"
                f"{badge_emoji} *{badge_name}*\n\n"
                f"📅 Current streak: *{streak} days* 🔥\n"
                f"🏆 Best streak: *{max_streak} days*\n\n"
                f"{'🎯 Next badge: ' + next_emoji + ' *' + next_name + '* in *' + str(next_days - streak) + ' days!*' if next_days else '🌟 *You have reached the highest rank!*'}\n\n"
                f"Keep coming back every day to grow your streak!\n"
                f"Active members get priority rewards from our team. 💎"
            ),
            "sw": (
                f"🔥 *STREAK YAKO YA KILA SIKU*\n\n"
                f"{badge_emoji} *{badge_name}*\n\n"
                f"📅 Streak ya sasa: *siku {streak}* 🔥\n"
                f"🏆 Streak bora: *siku {max_streak}*\n\n"
                f"{'🎯 Badge inayofuata: ' + next_emoji + ' *' + next_name + '* baada ya siku *' + str(next_days - streak) + '*!' if next_days else '🌟 *Umefika kiwango cha juu kabisa!*'}\n\n"
                f"Endelea kurudi kila siku kukuza streak yako!\n"
                f"Wanachama wanaoshiriki hupata zawadi za kipaumbele. 💎"
            ),
        }
        streak_text = streak_texts.get(lang, streak_texts["en"])
        img = rand_img(SERVICE_PHOTOS, context.user_data, "last_img_streak")
        msg = await send_protected_photo(
            context, cid, img, streak_text,
            InlineKeyboardMarkup([
                [InlineKeyboardButton(ui("btn_services", lang), callback_data="menu_services")],
                [InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")],
            ]))
        track_msg(cid, msg.message_id)

    elif data == "do_tip":
        tip = get_daily_binary_tip()
        msg = await send_protected_text(
            context, cid, tip,
            InlineKeyboardMarkup([
                [InlineKeyboardButton(ui("btn_services", lang), callback_data="menu_services")],
                [InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")],
            ]))
        track_msg(cid, msg.message_id)

    elif data == "do_profile":
        profile_text = build_profile_text(user.id, lang)
        msg = await send_protected_text(
            context, cid, profile_text,
            InlineKeyboardMarkup([
                [InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")],
            ]))
        track_msg(cid, msg.message_id)

    elif data == "do_results_history":
        results = get_results_history(5)
        if not results:
            msg = await send_protected_text(
                context, cid, ui("no_results_history", lang),
                InlineKeyboardMarkup([[InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")]]))
        else:
            row = results[0]
            rid, caption, media_id, media_type, saved_at = row
            header = f"🏆 *PAST VIP RESULTS*\n\n📅 _{saved_at}_\n\n"
            back_kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Join VIP Now", url=VIP_BOT_LINK)],
                [InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")],
            ])
            if media_id and media_type == "photo":
                try:
                    msg = await context.bot.send_photo(
                        chat_id=cid, photo=media_id,
                        caption=header + (caption or ""),
                        parse_mode="Markdown", protect_content=True, reply_markup=back_kb)
                except:
                    msg = await send_protected_text(context, cid, header + (caption or ""), back_kb)
            elif media_id and media_type == "video":
                try:
                    msg = await context.bot.send_video(
                        chat_id=cid, video=media_id,
                        caption=header + (caption or ""),
                        parse_mode="Markdown", protect_content=True, reply_markup=back_kb)
                except:
                    msg = await send_protected_text(context, cid, header + (caption or ""), back_kb)
            else:
                msg = await send_protected_text(context, cid, header + (caption or ""), back_kb)
        track_msg(cid, msg.message_id)

    elif data == "do_quiz":
        context.user_data["quiz_idx"] = 0
        context.user_data["quiz_correct"] = 0
        q = QUIZ_QUESTIONS[0]
        opts = "\n".join([f"{i+1}. {o}" for i, o in enumerate(q["options"])])
        quiz_text = f"{q['q']}\n\n{opts}"
        buttons = [[InlineKeyboardButton(f"{i+1}", callback_data=f"quiz_ans_{i}")] for i in range(len(q["options"]))]
        buttons.append([InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")])
        msg = await send_protected_text(context, cid, quiz_text, InlineKeyboardMarkup(buttons))
        track_msg(cid, msg.message_id)

    elif data.startswith("quiz_ans_"):
        ans = int(data.split("_")[-1])
        q_idx = context.user_data.get("quiz_idx", 0)
        correct_count = context.user_data.get("quiz_correct", 0)
        if ans == QUIZ_QUESTIONS[q_idx]["answer"]:
            correct_count += 1
            feedback = f"✅ *Correct!* {QUIZ_QUESTIONS[q_idx]['explanation']}"
        else:
            feedback = f"❌ *Not quite!* {QUIZ_QUESTIONS[q_idx]['explanation']}"
        context.user_data["quiz_correct"] = correct_count
        next_q = q_idx + 1
        context.user_data["quiz_idx"] = next_q
        if next_q < len(QUIZ_QUESTIONS):
            q = QUIZ_QUESTIONS[next_q]
            opts = "\n".join([f"{i+1}. {o}" for i, o in enumerate(q["options"])])
            quiz_text = f"{feedback}\n\n{q['q']}\n\n{opts}"
            buttons = [[InlineKeyboardButton(f"{i+1}", callback_data=f"quiz_ans_{i}")] for i in range(len(q["options"]))]
            msg = await send_protected_text(context, cid, quiz_text, InlineKeyboardMarkup(buttons))
        else:
            save_quiz_score(user.id, correct_count)
            add_badge(user.id, "quiz_master")
            final = f"{feedback}\n\n🎓 *QUIZ COMPLETE!*\n\nYour score: *{correct_count}/{len(QUIZ_QUESTIONS)}*\n\n"
            if correct_count == len(QUIZ_QUESTIONS):
                final += "🏆 Perfect score! You're a trading genius! 🎉"
            elif correct_count >= 2:
                final += "💪 Great job! Keep learning and you'll be a pro! 📈"
            else:
                final += "📚 Keep studying — every expert was once a beginner! 💡"
            msg = await send_protected_text(
                context, cid, final,
                InlineKeyboardMarkup([[InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")]]))
        track_msg(cid, msg.message_id)

    elif data == "do_spin":
        if not can_spin_today(user.id):
            hours, mins = get_next_spin_time(user.id)
            await safe_delete(context, cid, query.message.message_id)
            await delete_all_bot_msgs(context, cid)
            wait_texts = {
                "en": f"⏳ *You have already used your Lucky Spin today!*\n\nYour next spin will be available in *{hours}h {mins}m* ⏰\n\nCome back then — big prizes are waiting for you! 🎁",
                "sw": f"⏳ *Umeshakutumia Lucky Spin yako ya leo!*\n\nSpin yako ijayo itapatikana baada ya *saa {hours} na dakika {mins}* ⏰\n\nRudi wakati huo — zawadi kubwa zinakusubiri! 🎁",
                "ar": f"⏳ *لقد استخدمت بالفعل دورتك المحظوظة اليوم!*\n\nستكون دورتك التالية متاحة خلال *{hours}h {mins}m* ⏰\n\nعد بعدها! 🎁",
                "zh": f"⏳ *您今天已经使用了幸运转盘！*\n\n下次可用时间：*{hours}h {mins}m* ⏰\n\n到时再来！ 🎁",
                "hi": f"⏳ *आप आज Lucky Spin उपयोग कर चुके हैं!*\n\nअगला spin *{hours}h {mins}m* में ⏰\n\nतब वापस आएं! 🎁",
                "ru": f"⏳ *Вы уже использовали Счастливый Спин сегодня!*\n\nСледующий спин через *{hours}h {mins}m* ⏰\n\nВозвращайтесь! 🎁",
                "es": f"⏳ *¡Ya usaste tu Giro de Suerte hoy!*\n\nPróximo giro en *{hours}h {mins}m* ⏰\n\n¡Vuelve entonces! 🎁",
                "fr": f"⏳ *Vous avez déjà utilisé votre Spin aujourd'hui!*\n\nProchain spin dans *{hours}h {mins}m* ⏰\n\nRevenez! 🎁",
                "pt": f"⏳ *Você já usou seu Giro hoje!*\n\nPróximo giro em *{hours}h {mins}m* ⏰\n\nVolte! 🎁",
                "de": f"⏳ *Sie haben Ihr Glücksrad heute bereits genutzt!*\n\nNächstes Drehen in *{hours}h {mins}m* ⏰\n\nKommen Sie zurück! 🎁",
                "ur": f"⏳ *آپ آج Lucky Spin استعمال کر چکے ہیں!*\n\nاگلا spin *{hours}h {mins}m* میں ⏰\n\nواپس آئیں! 🎁",
                "ja": f"⏳ *今日はすでにラッキースピンを使用しました！*\n\n次のスピン：*{hours}h {mins}m* 後 ⏰\n\nその時に戻ってください！ 🎁",
            }
            wait_text = wait_texts.get(lang, wait_texts["en"])
            msg = await send_protected_text(
                context, cid, wait_text,
                InlineKeyboardMarkup([
                    [InlineKeyboardButton(ui("btn_services", lang), callback_data="menu_services")],
                    [InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")],
                ]))
            track_msg(cid, msg.message_id)
            return

        # Record spin with user info
        record_spin(user.id, user.full_name, user.username or "")

        # Show spinning animation
        spin_msg = await send_protected_text(
            context, cid,
            SPIN_WHEEL_VISUAL + "      ✨ Spinning... ✨",
            InlineKeyboardMarkup([]))
        track_msg(cid, spin_msg.message_id)

        # Animate 8 frames — ~6 seconds (faster, avoids Telegram rate limit)
        # Frames: fast start → slow end (deceleration effect)
        spin_timings = [0.4, 0.4, 0.5, 0.6, 0.7, 0.8, 1.0, 1.2]
        for i, (frame, wait) in enumerate(zip(SPIN_FRAMES[:8], spin_timings)):
            await asyncio.sleep(wait)
            try:
                await context.bot.edit_message_text(
                    chat_id=cid,
                    message_id=spin_msg.message_id,
                    text=SPIN_WHEEL_VISUAL + "      ✨ " + frame + " ✨",
                    parse_mode="Markdown")
            except Exception as e:
                # If rate limited, just wait and continue
                if "retry" in str(e).lower():
                    await asyncio.sleep(2)
                # Don't break — continue to result

        await asyncio.sleep(0.8)

        # Get result — always a lose result
        prize_key, prize_emoji, is_win = do_spin()
        prize_text = get_prize_text(prize_key, lang)

        # Delete spin animation
        await safe_delete(context, cid, spin_msg.message_id)
        if spin_msg.message_id in bot_msg_ids.get(cid, []):
            bot_msg_ids[cid].remove(spin_msg.message_id)

        # Always show lose — but exciting message
        result_header = f"🎰 *LUCKY SPIN RESULT* 🎰\n\n{prize_text}"
        result_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Spin Again Tomorrow 🕐", callback_data="main_menu")],
            [InlineKeyboardButton(ui("btn_services", lang), callback_data="menu_services")],
            [InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")],
        ])
        # FIX: Wrap result sending in try/except — guaranteed something always shows
        msg = None
        try:
            img = random.choice(SERVICE_PHOTOS)
            msg = await context.bot.send_photo(
                chat_id=cid, photo=img, caption=result_header,
                parse_mode="Markdown", reply_markup=result_kb,
                protect_content=True)
        except Exception:
            pass

        if msg is None:
            try:
                msg = await context.bot.send_message(
                    chat_id=cid, text=result_header,
                    parse_mode="Markdown", reply_markup=result_kb,
                    protect_content=True)
            except Exception:
                pass

        if msg is None:
            # Last resort — plain text, no Markdown, no photo
            try:
                plain = f"🎰 LUCKY SPIN RESULT 🎰\n\n{prize_text}"
                msg = await context.bot.send_message(
                    chat_id=cid, text=plain,
                    reply_markup=result_kb,
                    protect_content=True)
            except Exception:
                pass

        if msg:
            track_msg(cid, msg.message_id)

        # Silently notify admin — no sound, just data tracking
        name = escape_md(user.full_name)
        username_str = escape_md(user.username or "NA")
        # Get total spins for this user
        from_db = get_top_spinners(limit=100)
        user_spins = next((r[3] for r in from_db if r[0] == user.id), 1)
        for aid in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=aid,
                    text=(
                        f"🎰 *Spin Activity*\n\n"
                        f"👤 {name} @{username_str}\n"
                        f"🆔 `{user.id}` | 🌍 {lang}\n"
                        f"🔢 Total spins: *{user_spins}*\n\n"
                        f"_Use /spinners to see most active players_"
                    ),
                    parse_mode="Markdown",
                    disable_notification=True)  # Silent notification
            except:
                pass

    # Admin: Connect
    elif data.startswith("con:"):
        parts = data.split(":")
        uid   = int(parts[1])
        ulang = parts[2] if len(parts) > 2 else "en"
        active_support[uid] = True
        # FIX: wrap edit in try/except — message may already be deleted
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

    # Admin: Disconnect
    elif data.startswith("dis:"):
        parts = data.split(":")
        uid   = int(parts[1])
        ulang = parts[2] if len(parts) > 2 else "en"
        active_support.pop(uid, None)
        # FIX: wrap edit in try/except
        try:
            await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🟢 Connect", callback_data=f"con:{uid}:{ulang}"),
                InlineKeyboardButton("🔴 Ended ✓", callback_data="noop"),
            ]]))
        except:
            pass

        await delete_support_msgs(context, uid)

        # FIX: session_ended has NO contact support button — just thank you
        try:
            msg = await context.bot.send_message(
                chat_id=uid,
                text=ui("session_ended", ulang),
                parse_mode="Markdown",
                protect_content=True,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        ui("btn_back", ulang), callback_data="main_menu")
                ]]))
            track_msg(uid, msg.message_id)
            await asyncio.sleep(2)
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
                safe_name = escape_md(req['user'].full_name)
                await query.message.edit_text(
                    f"✅ *Approved!*\n👤 {safe_name}",
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

    # ── GIVESPIN QUICK BUTTON from /spinners ──────────────────
    elif data.startswith("givespin_btn:"):
        uid_str = data.split(":")[1]
        await query.answer()
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=(
                f"📋 To reward this user, send:\n\n"
                f"`/givespin {uid_str} 3 signals`\n\n"
                f"Change the discount (3) and service (signals/social/indicator/autobot/any) as needed."
            ),
            parse_mode="Markdown")
        return

    # ── POCKET OPTION BOT — show video ────────────────────────
    elif data == "show_pocket_bot":
        try:
            pocket_texts = {
                "en": "💰 *POCKET OPTION BOT — NEW!* 🆕\n\n🤖 Our brand new Pocket Option trading bot is here!\n\n✅ Works on Pocket Option\n✅ Auto trading 24/7\n✅ Easy setup\n✅ Real results\n\n👇 Watch the bot in action:",
                "sw": "💰 *BOT YA POCKET OPTION — MPYA!* 🆕\n\n🤖 Bot yetu mpya kabisa ya Pocket Option ipo sasa!\n\n✅ Inafanya kazi kwenye Pocket Option\n✅ Biashara otomatiki 24/7\n✅ Usanidi rahisi\n✅ Matokeo ya kweli\n\n👇 Angalia bot ikifanya kazi:",
            }
            pocket_text = pocket_texts.get(lang, pocket_texts["en"])
            msg = await context.bot.send_video(
                chat_id=cid,
                video=FREE_BOT_LINKS["pocket"],
                caption=pocket_text,
                parse_mode="Markdown",
                protect_content=True,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(ui("btn_support", lang), callback_data="do_support")],
                    [InlineKeyboardButton(ui("btn_back", lang), callback_data="svc_freebot")],
                ]))
            track_msg(cid, msg.message_id)
        except Exception as e:
            logger.warning(f"Pocket bot video failed: {e}")
            msg = await send_protected_text(
                context, cid,
                "💰 *POCKET OPTION BOT — NEW!* 🆕\n\nContact our support team to get access to our new Pocket Option bot! 🤖",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton(ui("btn_support", lang), callback_data="do_support")],
                    [InlineKeyboardButton(ui("btn_back", lang), callback_data="svc_freebot")],
                ]))
            track_msg(cid, msg.message_id)

    elif data == "noop":
        pass

    # ── ONBOARDING CONTINUE ────────────────────────────────────
    elif data == "onboarding_done":
        # Delete all onboarding messages
        await safe_delete(context, cid, query.message.message_id)
        await delete_all_bot_msgs(context, cid)

        # Mark onboarding done in DB — never shows again
        mark_onboarding_done(user.id)

        await typing_action(cid, context, 1.0)

        # Show poll first
        poll_msg = await send_protected_text(
            context, cid, ui("poll_msg", lang), poll_keyboard(lang))
        context.user_data["last_bot_msg_id"] = poll_msg.message_id
        track_msg(cid, poll_msg.message_id)

    # ── VIEW MY REFERRALS LIST ─────────────────────────────────
    elif data == "view_referrals":
        ref_list = get_referred_users(user.id)
        ref_count = len(ref_list)
        if not ref_list:
            text = "👥 *Your Referrals*\n\nYou haven't invited anyone yet.\n\nShare your link and start earning discounts! 🎁"
        else:
            lines = [f"👥 *Your Referrals ({ref_count} people)*\n"]
            for i, (name_r, joined_r) in enumerate(ref_list[:20], 1):
                safe = escape_md(name_r or "Unknown")
                lines.append(f"{i}. {safe} — {joined_r[:10] if joined_r else '?'}")
            if ref_count > 20:
                lines.append(f"\n...and {ref_count - 20} more")
            text = "\n".join(lines)
        msg = await send_protected_text(
            context, cid, text,
            InlineKeyboardMarkup([
                [InlineKeyboardButton(ui("btn_back", lang), callback_data="do_referral")]
            ]))
        track_msg(cid, msg.message_id)

# ══════════════════════════════════════════════════════════════
#  TWO-WAY MESSAGING — Copy instead of Forward
# ══════════════════════════════════════════════════════════════

async def forward_to_admin(context, user, message):
    if not active_support.get(user.id):
        return

    name = escape_md(user.full_name)

    for aid in ADMIN_IDS:
        try:
            sent = None
            if message.text:
                # FIX: Use plain Markdown, not MarkdownV2 — consistent throughout
                sent = await context.bot.send_message(
                    chat_id=aid,
                    text=f"💬 *{name}* (`{user.id}`):\n\n{message.text}",
                    parse_mode="Markdown")
            elif message.photo:
                caption = f"📸 *{name}*"
                if message.caption:
                    caption += f"\n{message.caption}"
                sent = await context.bot.send_photo(
                    chat_id=aid,
                    photo=message.photo[-1].file_id,
                    caption=caption,
                    parse_mode="Markdown")
            elif message.video:
                caption = f"🎥 *{name}*"
                if message.caption:
                    caption += f"\n{message.caption}"
                sent = await context.bot.send_video(
                    chat_id=aid,
                    video=message.video.file_id,
                    caption=caption,
                    parse_mode="Markdown")
            elif message.voice:
                sent = await context.bot.send_voice(
                    chat_id=aid,
                    voice=message.voice.file_id)
            elif message.document:
                caption = f"📄 *{name}*"
                if message.caption:
                    caption += f"\n{message.caption}"
                sent = await context.bot.send_document(
                    chat_id=aid,
                    document=message.document.file_id,
                    caption=caption,
                    parse_mode="Markdown")
            elif message.sticker:
                sent = await context.bot.send_sticker(
                    chat_id=aid,
                    sticker=message.sticker.file_id)
            elif message.audio:
                sent = await context.bot.send_audio(
                    chat_id=aid,
                    audio=message.audio.file_id)

            if sent:
                reply_map[sent.message_id] = user.id

        except Exception as e:
            logger.warning(f"Forward to admin failed: {e}")

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

    lang = get_lang(context, user.id)
    register_user(user, lang=lang)

    # FIX: Check if user is giving rating text opinion
    if user.id in awaiting_rating_opinion and message.text:
        opinion_data = awaiting_rating_opinion.pop(user.id)
        stars = opinion_data["stars"]
        star_display = opinion_data["star_display"]
        opinion_text = message.text.strip()

        # Delete user's message and the opinion prompt
        await delete_user_msg(message)
        await delete_all_bot_msgs(context, cid)

        # Send full rating + opinion to admin
        name = escape_md(user.full_name)
        skip_text = "(skipped)" if opinion_text.lower() == "skip" else opinion_text
        for aid in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=aid,
                    text=f"⭐ *Full Rating*\n\n👤 {name}\n🆔 `{user.id}`\n{star_display} ({stars}/5)\n\n💬 Opinion: {skip_text}",
                    parse_mode="Markdown")
            except:
                pass

        await typing_action(cid, context, 1.0)
        welcome_text = build_welcome_text(lang, user.first_name)
        msg = await send_protected_photo(
            context, cid, WELCOME_IMAGE,
            f"{ui('rating_thanks', lang).format(name=escape_md(user.first_name))}\n\n{welcome_text}",
            main_menu(lang))
        context.user_data["last_bot_msg_id"] = msg.message_id
        track_msg(cid, msg.message_id)
        return

    # FIX: Check support session FIRST — before deleting anything
    if active_support.get(user.id):
        track_support_msg(cid, message.message_id)
        await forward_to_admin(context, user, message)
        return

    # Only delete for non-support users (melt effect)
    await delete_user_msg(message)

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
        welcome_text = build_welcome_text(lang, user.first_name)
        await reply_with_photo(WELCOME_IMAGE, welcome_text, main_menu(lang))

    elif any(w in low for w in [
        "signal","signals","vip","alert","ishara","forex signal","win rate","binary signal"
    ]):
        img = rand_img(IMGS_SIGNALS, context.user_data, "last_img_signals")
        await reply_with_photo(img, random.choice(get_replies(SIGNALS_REPLIES, lang)), svc_keyboard(lang, signals=True))

    elif any(w in low for w in [
        "social","copy","pocket","copy trade","copy trading","nakili"
    ]):
        img = rand_img(IMGS_SOCIAL, context.user_data, "last_img_social")
        await reply_with_photo(img, random.choice(get_replies(SOCIAL_REPLIES, lang)), svc_keyboard(lang, social=True))

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
        await reply_with_photo(img, random.choice(get_replies(AUTOBOT_REPLIES, lang)), svc_keyboard(lang, autobot=True))

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
            f"😊 Thank you, *{escape_md(user.first_name)}!* Always here for you. 🚀",
            InlineKeyboardMarkup([
                [InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")]
            ]))

    else:
        await reply_with_text(ui("fallback_msg", lang), support_keyboard(lang))

# ══════════════════════════════════════════════════════════════
#  /preview — Admin sees exactly what new user sees
# ══════════════════════════════════════════════════════════════

async def preview_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    user = update.effective_user
    cid  = update.effective_chat.id

    # Parse optional language arg: /preview sw  or /preview en
    lang = "en"
    if context.args:
        lang = context.args[0].lower().strip()
        if lang not in UI:
            lang = "en"

    await update.message.reply_text(
        f"👁 *PREVIEW MODE — New User Experience*\n\n"
        f"🌍 Language: `{lang}`\n\n"
        f"Sending you the full new-user flow now...\n"
        f"_(This is exactly what a new user sees)_",
        parse_mode="Markdown")

    await asyncio.sleep(1)

    # ── STEP 1: Language selector ──────────────────────────────
    await context.bot.send_message(
        chat_id=cid,
        text="━━━━━━━━━━━━━━━━━━\n📍 *STEP 1: Language Selector*\n━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown")
    await asyncio.sleep(0.5)
    await context.bot.send_message(
        chat_id=cid,
        text="🌍 *Welcome to EVALON WINNERS!*\n\nChoose your language / Chagua lugha yako:",
        parse_mode="Markdown",
        reply_markup=lang_keyboard())

    await asyncio.sleep(1.5)

    # ── STEP 2: Join channel prompt ────────────────────────────
    await context.bot.send_message(
        chat_id=cid,
        text="━━━━━━━━━━━━━━━━━━\n📍 *STEP 2: Channel Join Gate*\n━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown")
    await asyncio.sleep(0.5)
    await context.bot.send_message(
        chat_id=cid,
        text=ui("join_msg", lang),
        parse_mode="Markdown",
        reply_markup=join_keyboard(lang))

    await asyncio.sleep(1.5)

    # ── STEP 3: Onboarding video + text ───────────────────────
    await context.bot.send_message(
        chat_id=cid,
        text="━━━━━━━━━━━━━━━━━━\n📍 *STEP 3: Onboarding (New Users Only)*\n━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown")
    await asyncio.sleep(0.5)

    try:
        await context.bot.send_video(
            chat_id=cid,
            video=ONBOARDING_VIDEO)
    except Exception as e:
        await context.bot.send_message(
            chat_id=cid,
            text=f"⚠️ _Video failed to send: {e}_\n_(Video ID: {ONBOARDING_VIDEO})_",
            parse_mode="Markdown")

    await asyncio.sleep(1.0)

    onboard_text = get_onboarding_text(lang, user.first_name)
    await context.bot.send_message(
        chat_id=cid,
        text=onboard_text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🚀 Continue", callback_data="noop")
        ]]))

    await asyncio.sleep(1.5)

    # ── STEP 4: Poll ───────────────────────────────────────────
    await context.bot.send_message(
        chat_id=cid,
        text="━━━━━━━━━━━━━━━━━━\n📍 *STEP 4: Poll (After Continue)*\n━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown")
    await asyncio.sleep(0.5)
    await context.bot.send_message(
        chat_id=cid,
        text=ui("poll_msg", lang),
        parse_mode="Markdown",
        reply_markup=poll_keyboard(lang))

    await asyncio.sleep(1.5)

    # ── STEP 5: Main menu (welcome) ────────────────────────────
    await context.bot.send_message(
        chat_id=cid,
        text="━━━━━━━━━━━━━━━━━━\n📍 *STEP 5: Main Menu (After Poll)*\n━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown")
    await asyncio.sleep(0.5)

    welcome_text = build_welcome_text(lang, user.first_name)
    try:
        await context.bot.send_photo(
            chat_id=cid,
            photo=WELCOME_IMAGE,
            caption=welcome_text,
            parse_mode="Markdown",
            reply_markup=main_menu(lang))
    except:
        await context.bot.send_message(
            chat_id=cid,
            text=welcome_text,
            parse_mode="Markdown",
            reply_markup=main_menu(lang))

    await asyncio.sleep(1.0)

    # ── STEP 6: Services menu ──────────────────────────────────
    await context.bot.send_message(
        chat_id=cid,
        text="━━━━━━━━━━━━━━━━━━\n📍 *STEP 6: Services Menu*\n━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown")
    await asyncio.sleep(0.5)
    await context.bot.send_message(
        chat_id=cid,
        text=ui("services_msg", lang),
        parse_mode="Markdown",
        reply_markup=services_menu(lang))

    await asyncio.sleep(1.0)

    # ── STEP 7: Spin wheel ─────────────────────────────────────
    await context.bot.send_message(
        chat_id=cid,
        text="━━━━━━━━━━━━━━━━━━\n📍 *STEP 7: Lucky Spin (first time)*\n━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown")
    await asyncio.sleep(0.5)
    await context.bot.send_message(
        chat_id=cid,
        text=SPIN_WHEEL_VISUAL + "      ✨ Spinning... ✨",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 Spin Again Tomorrow 🕐", callback_data="noop"),
        ]]))

    await asyncio.sleep(1.0)

    # ── DONE ───────────────────────────────────────────────────
    await context.bot.send_message(
        chat_id=cid,
        text=(
            "━━━━━━━━━━━━━━━━━━\n"
            "✅ *PREVIEW COMPLETE!*\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            f"🌍 Language previewed: `{lang}`\n\n"
            "📌 *Quick Tips:*\n"
            "• `/preview sw` — preview in Swahili\n"
            "• `/preview ar` — preview in Arabic\n"
            "• `/preview en` — preview in English\n"
            "• Works for all 20 languages\n\n"
            "🗑 You can delete these messages manually."
        ),
        parse_mode="Markdown")

# ══════════════════════════════════════════════════════════════
#  /spinners — Admin sees most active spinners to pick winners
#  /givespin  — Admin manually gives discount to chosen user
# ══════════════════════════════════════════════════════════════

async def spinners_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    spinners = get_top_spinners(limit=10)
    if not spinners:
        await update.message.reply_text("🎰 No spinners yet.")
        return

    text = "🎰 *TOP ACTIVE SPINNERS*\n\n"
    text += "_Pick a winner and use /givespin to reward them_\n\n"
    kb = []
    medals = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
    for i, (uid, uname, uusername, total, last_spin) in enumerate(spinners):
        safe_name = escape_md(uname or str(uid))
        uun = f"@{uusername}" if uusername else "no username"
        last = last_spin[:10] if last_spin else "?"
        text += f"{medals[i]} {safe_name} ({uun})\n   🔢 *{total} spins* | Last: {last}\n\n"
        kb.append([InlineKeyboardButton(
            f"🎁 Reward: {(uname or str(uid))[:18]} ({total} spins)",
            callback_data=f"givespin_btn:{uid}"
        )])

    await update.message.reply_text(
        text, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb))


async def givespin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Usage: /givespin USER_ID DISCOUNT SERVICE
    Example: /givespin 123456789 3 signals
    Services: signals, social, indicator, autobot, any
    """
    if not is_admin(update.effective_user.id):
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "📋 *How to give a spin reward:*\n\n"
            "`/givespin USER_ID DISCOUNT SERVICE`\n\n"
            "*Examples:*\n"
            "• `/givespin 123456789 3 signals`\n"
            "• `/givespin 987654321 5 autobot`\n"
            "• `/givespin 111222333 2 any`\n\n"
            "*Services:* signals | social | indicator | autobot | any",
            parse_mode="Markdown")
        return

    try:
        target_uid = int(args[0])
        discount   = int(args[1].replace("%", ""))
        service    = args[2].lower() if len(args) > 2 else "any"
    except:
        await update.message.reply_text(
            "❌ Wrong format.\n\nUse: `/givespin USER_ID DISCOUNT SERVICE`",
            parse_mode="Markdown")
        return

    service_names = {
        "signals":   "📊 VIP Signals",
        "social":    "👥 Social Trading",
        "indicator": "📈 Free Indicator",
        "autobot":   "🤖 Auto Bot",
        "any":       "🏆 Any Service of Your Choice",
    }
    service_display = service_names.get(service, f"🎁 {service}")

    u_info = get_user_info(target_uid)
    ulang  = u_info.get("lang", "en") or "en"

    win_texts = {
        "en": (
            f"🎉 *CONGRATULATIONS! YOU WON!* 🎉\n\n"
            f"🎰 Our team reviewed your Lucky Spin activity and *selected you as a winner!*\n\n"
            f"🎁 You have earned a *{discount}% DISCOUNT* on:\n"
            f"*{service_display}*\n\n"
            f"This is your reward for being one of our most active members! 🏆\n\n"
            f"👇 Tap below to claim your prize now:"
        ),
        "sw": (
            f"🎉 *HONGERA! UMESHINDA!* 🎉\n\n"
            f"🎰 Timu yetu ilichunguza shughuli yako ya Lucky Spin na *kukuchagua kama mshindi!*\n\n"
            f"🎁 Umepata *Punguzo la {discount}%* kwenye:\n"
            f"*{service_display}*\n\n"
            f"Hii ni tuzo yako kwa kuwa mmoja wa wanachama wetu wanaoshiriki zaidi! 🏆\n\n"
            f"👇 Bonyeza hapa chini kupata tuzo yako sasa:"
        ),
        "ar": (
            f"🎉 *تهانينا! لقد فزت!* 🎉\n\n"
            f"🎰 راجع فريقنا نشاطك في Lucky Spin *واختارك فائزاً!*\n\n"
            f"🎁 حصلت على *خصم {discount}%* على:\n"
            f"*{service_display}*\n\n"
            f"هذه مكافأتك لكونك من أكثر أعضائنا نشاطاً! 🏆\n\n"
            f"👇 اضغط أدناه للمطالبة بجائزتك الآن:"
        ),
        "ru": (
            f"🎉 *ПОЗДРАВЛЯЕМ! ВЫ ВЫИГРАЛИ!* 🎉\n\n"
            f"🎰 Наша команда изучила вашу активность Lucky Spin и *выбрала вас победителем!*\n\n"
            f"🎁 Вы получили *скидку {discount}%* на:\n"
            f"*{service_display}*\n\n"
            f"Это ваша награда за то, что вы один из наших самых активных участников! 🏆\n\n"
            f"👇 Нажмите ниже, чтобы получить приз:"
        ),
        "zh": (
            f"🎉 *恭喜！您赢了！* 🎉\n\n"
            f"🎰 我们的团队审查了您的幸运转盘活动并*选择您为获胜者！*\n\n"
            f"🎁 您获得了 *{discount}% 折扣*：\n"
            f"*{service_display}*\n\n"
            f"这是您作为我们最活跃成员之一的奖励！ 🏆\n\n"
            f"👇 点击下方立即领取您的奖品："
        ),
    }
    win_msg = win_texts.get(ulang, win_texts["en"])

    try:
        await context.bot.send_message(
            chat_id=target_uid,
            text=win_msg,
            parse_mode="Markdown",
            protect_content=True,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🎁 Claim My Prize Now!", callback_data="do_support")
            ]]))
        active_support[target_uid] = True
        await update.message.reply_text(
            f"✅ *Reward sent successfully!*\n\n"
            f"👤 User ID: `{target_uid}`\n"
            f"🎁 Discount: *{discount}%*\n"
            f"📌 Service: {service_display}\n\n"
            f"User is now connected to support.\n"
            f"Reply to their messages to complete the transaction.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🟢 Open Chat", callback_data=f"con:{target_uid}:{ulang}")
            ]]))
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to send prize: {e}")

async def setnews_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /setnews Some text here
    Or reply to a photo/video with /setnews Optional caption
    """
    if not is_admin(update.effective_user.id):
        return
    msg = update.message
    replied = msg.reply_to_message
    text_val = " ".join(context.args) if context.args else None

    if replied and replied.photo:
        set_dynamic_content("news", text_value=text_val or replied.caption,
                            file_id=replied.photo[-1].file_id, file_type="photo")
    elif replied and replied.video:
        set_dynamic_content("news", text_value=text_val or replied.caption,
                            file_id=replied.video.file_id, file_type="video")
    elif text_val:
        set_dynamic_content("news", text_value=text_val)
    else:
        await msg.reply_text(
            "❌ Usage:\n• `/setnews Your text here`\n• Reply to photo/video + `/setnews`",
            parse_mode="Markdown")
        return
    await msg.reply_text("✅ *What's New* updated! Users will see it immediately.", parse_mode="Markdown")


async def setvip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /setvip Some text here
    Or reply to a photo/video with /setvip Optional caption
    """
    if not is_admin(update.effective_user.id):
        return
    msg = update.message
    replied = msg.reply_to_message
    text_val = " ".join(context.args) if context.args else None

    # ── AUTO-SAVE: Move existing VIP content to results_history before overwriting ──
    old_vip = get_dynamic_content("vip")
    auto_saved = False
    if old_vip and (old_vip.get("text") or old_vip.get("file_id")):
        saved_date = old_vip.get("updated_at", datetime.now().strftime("%d/%m/%Y %H:%M"))
        label = f"\U0001f4c5 Session: {saved_date}\n\n{old_vip.get('text') or ''}"
        auto_saved = save_result(
            result_date=saved_date,
            content_text=label.strip(),
            media_id=old_vip.get("file_id"),
            media_type=old_vip.get("file_type"),
        )

    if replied and replied.photo:
        set_dynamic_content("vip", text_value=text_val or replied.caption,
                            file_id=replied.photo[-1].file_id, file_type="photo")
    elif replied and replied.video:
        set_dynamic_content("vip", text_value=text_val or replied.caption,
                            file_id=replied.video.file_id, file_type="video")
    elif text_val:
        set_dynamic_content("vip", text_value=text_val)
    else:
        await msg.reply_text(
            "❌ Usage:\n• `/setvip Today: 8/10 signals won! 🔥`\n• Reply to photo/video + `/setvip`",
            parse_mode="Markdown")
        return

    saved_note = "\n\U0001f4e6 _Previous session auto-saved to Past Results._" if auto_saved else ""
    await msg.reply_text(
        f"\u2705 *VIP Results* updated! Users will see it immediately.{saved_note}",
        parse_mode="Markdown")


async def clearnews_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear news or vip content: /clearnews or /clearvip"""
    if not is_admin(update.effective_user.id):
        return
    cmd = update.message.text.strip().lower()
    key = "vip" if "vip" in cmd else "news"
    set_dynamic_content(key, text_value=None, file_id=None, file_type=None)
    label = "VIP Results" if key == "vip" else "Whats New"
    await update.message.reply_text(f"✅ *{label}* cleared.", parse_mode="Markdown")


async def results_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save today's session results to history: /results text or reply to photo/video"""
    if not is_admin(update.effective_user.id):
        return
    msg = update.message
    today = datetime.now().strftime("%d/%m/%Y")
    text = " ".join(context.args) if context.args else None

    if msg.reply_to_message:
        r = msg.reply_to_message
        if r.photo:
            fid = r.photo[-1].file_id
            cap = r.caption or text or ""
            save_result(today, cap, media_id=fid, media_type="photo")
            await msg.reply_text("✅ *Results saved!* (photo)", parse_mode="Markdown")
            return
        elif r.video:
            fid = r.video.file_id
            cap = r.caption or text or ""
            save_result(today, cap, media_id=fid, media_type="video")
            await msg.reply_text("✅ *Results saved!* (video)", parse_mode="Markdown")
            return

    if text:
        save_result(today, text)
        await msg.reply_text("✅ *Results saved!*", parse_mode="Markdown")
    else:
        await msg.reply_text(
            "❌ Usage:\n`/results Today 8/10 won!`\nor reply to a photo/video with `/results`",
            parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all admin commands"""
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text(
        "🤖 *EVALON WINNERS BOT — ADMIN COMMANDS*\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📊 *STATISTICS*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "`/stats` — Total users, active, new today, top referrers\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📢 *BROADCAST*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "`/broadcast text` — Send text to ALL users\n"
        "`/broadcast` _(reply to photo/video)_ — Send media to all\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🆕 *DYNAMIC CONTENT*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "`/setnews Your text` — Set What's New Today\n"
        "`/setnews` _(reply to photo/video)_ — Set with media\n"
        "`/setvip Today: 8/10 won!` — Set VIP Results\n"
        "`/setvip` _(reply to photo/video)_ — Set with media\n"
        "`/clearnews` — Clear What's New content\n"
        "`/clearvip` — Clear VIP Results content\n"
        "`/results Today: 8/10 won!` — Save session results to history\n"
        "`/results` _(reply to photo/video)_ — Save results with media\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "💬 *SUPPORT SESSIONS*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "`/sessions` — View & manage active support chats\n"
        "🟢 Connect button — Start chatting with user\n"
        "🔴 End Chat button — End session + send rating\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🎰 *SPIN WHEEL*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "`/spinners` — See top 10 most active spinners\n"
        "`/givespin USER_ID DISCOUNT SERVICE` — Give reward\n"
        "   Example: `/givespin 123456 3 signals`\n"
        "   Services: `signals` `social` `indicator` `autobot` `any`\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🔧 *UTILITIES*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "`/addphoto` _(reply to photo)_ — Add photo to service images pool\n"
        "`/addbot Name | Link | Desc` — Add new bot to Free Bots menu\n"
        "`/addbot` — List all added bots\n"
        "`/delbot ID` — Remove a bot from menu\n"
        "`/getid` _(reply to photo/video)_ — Get file\\_id\n"
        "`/preview` — Preview new user experience (English)\n"
        "`/preview sw` — Preview in any language\n"
        "`/feedback` — Send 5 mixed feedback (EN+SW+UR)\n"
        "`/feedback 70` — Send 70 mixed feedback\n"
        "`/feedbackadd Name | 🇳🇬 | Text` — Add custom feedback\n"
        "`/feedbacklist` — See all custom feedback\n"
        "`/feedbackdlt` — Delete ALL custom feedback\n"
        "`/help` — Show this message\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "⭐ *SUCCESS STORIES*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "`/addstory Your text` — Add text story\n"
        "`/addstory` _(reply to photo/video)_ — Add story with media\n"
        "`/liststories` — See all stories with IDs\n"
        "`/deletestory ID` — Delete a story by ID\n"
        "_Stories button appears in main menu only when at least 1 story exists_\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "💡 *TIPS*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "• To reply to user in support: reply to their forwarded message\n"
        "• `/setnews` and `/setvip` update instantly — no redeploy needed\n"
        "• `/spinners` shows who spins most — pick 1-2 winners per week",
        parse_mode="Markdown")


async def feedback_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Send N mixed feedback messages (EN-heavy, auto-mixed with SW & UR)
    Usage: /feedback        → 5 feedback
    Usage: /feedback 70     → 70 feedback
    Usage: /feedback 100    → 100 feedback
    """
    if not is_admin(update.effective_user.id):
        return

    args = context.args
    count = 5
    if args and args[0].isdigit():
        count = min(int(args[0]), 200)  # max 200

    custom_count = len(get_custom_feedback())

    await update.message.reply_text(
        f"📨 *FEEDBACK PREVIEW*\n\n"
        f"📊 Sending: *{count}* mixed feedback\n"
        f"🌍 Mix: ~70% English, ~20% Swahili, ~10% Urdu\n"
        f"✏️ Custom feedback in DB: *{custom_count}*\n\n"
        f"_Sending now — one by one..._",
        parse_mode="Markdown")

    feedbacks = get_mixed_feedback(count)
    await asyncio.sleep(0.5)

    for i, (name, flag, text) in enumerate(feedbacks, 1):
        await asyncio.sleep(0.9)
        msg_text = f"{flag} *{escape_md(name)}*\n\n_{escape_md(text)}_\n\n⭐⭐⭐⭐⭐"
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=msg_text,
                parse_mode="Markdown")
        except Exception as e:
            logger.warning(f"Feedback msg {i} failed: {e}")

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            f"✅ *Done! {count} feedback sent.*\n\n"
            f"📌 *Tips:*\n"
            f"• `/feedback 70` — send 70 mixed\n"
            f"• `/feedback 100` — send 100 mixed\n"
            f"• `/feedbackadd` — add your own feedback\n"
            f"• `/feedbackdlt` — delete all custom feedback\n"
            f"• `/feedbacklist` — see your custom feedback\n\n"
            f"🎬 Record screen then broadcast with `/broadcast`!"
        ),
        parse_mode="Markdown")


async def feedbackadd_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Add custom feedback to DB
    Usage: /feedbackadd Name | Flag | Your feedback text here
    Example: /feedbackadd John K. | 🇳🇬 | Made $500 this week with Evalon signals!
    """
    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text(
            "📝 *How to add custom feedback:*\n\n"
            "`/feedbackadd Name | Flag | Feedback text`\n\n"
            "*Examples:*\n"
            "• `/feedbackadd John K. | 🇳🇬 | Made $500 this week with Evalon signals! Amazing!`\n"
            "• `/feedbackadd Maria S. | 🇧🇷 | Best trading bot ever. 9/10 signals win!`\n"
            "• `/feedbackadd Hassan M. | 🇹🇿 | Auto bot ilifanya $180 nikiwa nimelala!`\n\n"
            "💡 *Tips:*\n"
            "• Use real-sounding names from different countries\n"
            "• Include dollar amounts for credibility\n"
            "• Mix languages for authenticity",
            parse_mode="Markdown")
        return

    full_text = " ".join(context.args)
    parts = [p.strip() for p in full_text.split("|")]

    if len(parts) < 3:
        await update.message.reply_text(
            "❌ Wrong format. Use:\n`/feedbackadd Name | Flag | Text`",
            parse_mode="Markdown")
        return

    name = parts[0]
    flag = parts[1]
    text_val = " | ".join(parts[2:])  # allow | in text itself

    add_custom_feedback(name, flag, text_val)
    total = len(get_custom_feedback())

    await update.message.reply_text(
        f"✅ *Custom feedback added!*\n\n"
        f"{flag} *{escape_md(name)}*\n_{escape_md(text_val)}_\n\n"
        f"📊 Total custom feedback in DB: *{total}*\n\n"
        f"_Use `/feedback 10` to preview mixed feedback_",
        parse_mode="Markdown")


async def feedbackdlt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete ALL custom feedback from DB"""
    if not is_admin(update.effective_user.id):
        return

    count = delete_all_custom_feedback()
    await update.message.reply_text(
        f"🗑 *All custom feedback deleted!*\n\n"
        f"Removed: *{count}* entries\n\n"
        f"_Built-in feedback (EN/SW/UR) is still available._",
        parse_mode="Markdown")


async def feedbacklist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all custom feedback in DB"""
    if not is_admin(update.effective_user.id):
        return

    custom = get_custom_feedback()
    if not custom:
        await update.message.reply_text(
            "📭 *No custom feedback in DB yet.*\n\nUse `/feedbackadd` to add some.",
            parse_mode="Markdown")
        return

    text = f"📋 *Custom Feedback ({len(custom)} entries):*\n\n"
    for i, (name, flag, fb_text, lang) in enumerate(custom[:20], 1):
        short = fb_text[:60] + "..." if len(fb_text) > 60 else fb_text
        text += f"{i}. {flag} *{escape_md(name)}*: _{escape_md(short)}_\n"
    if len(custom) > 20:
        text += f"\n_...and {len(custom) - 20} more_"

    await update.message.reply_text(text, parse_mode="Markdown")


def init_media_db():
    """Store admin-added photos/videos and bot links"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS admin_media (
            id          SERIAL PRIMARY KEY,
            media_type  TEXT NOT NULL,
            file_id     TEXT NOT NULL,
            caption     TEXT DEFAULT NULL,
            added_at    TEXT DEFAULT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS admin_bots (
            id          SERIAL PRIMARY KEY,
            name        TEXT NOT NULL,
            link        TEXT NOT NULL,
            description TEXT DEFAULT NULL,
            added_at    TEXT DEFAULT NULL
        )
    """)
    conn.commit()
    conn.close()

def add_admin_photo(file_id, caption=""):
    conn = get_conn()
    c = conn.cursor()
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    c.execute("INSERT INTO admin_media (media_type, file_id, caption, added_at) VALUES (%s,%s,%s,%s)",
              ("photo", file_id, caption, now))
    conn.commit()
    conn.close()

def get_admin_photos():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT file_id FROM admin_media WHERE media_type='photo'")
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]

def add_admin_bot(name, link, description=""):
    conn = get_conn()
    c = conn.cursor()
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    c.execute("INSERT INTO admin_bots (name, link, description, added_at) VALUES (%s,%s,%s,%s)",
              (name, link, description, now))
    conn.commit()
    conn.close()

def get_admin_bots():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, name, link, description FROM admin_bots ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return rows

def delete_admin_bot(bot_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM admin_bots WHERE id=%s", (bot_id,))
    conn.commit()
    conn.close()


async def addphoto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Add photo to SERVICE_PHOTOS pool — used in service replies
    Reply to a photo with /addphoto Optional caption
    """
    if not is_admin(update.effective_user.id):
        return
    msg = update.message
    replied = msg.reply_to_message

    if not replied or not replied.photo:
        await msg.reply_text(
            "📸 *How to add a photo:*\n\n"
            "1. Send a photo to the bot\n"
            "2. Reply to it with `/addphoto`\n"
            "3. It will be added to the service images pool\n\n"
            "The photo will appear randomly in service replies!",
            parse_mode="Markdown")
        return

    file_id = replied.photo[-1].file_id
    caption = " ".join(context.args) if context.args else replied.caption or ""
    add_admin_photo(file_id, caption)

    # Add to runtime pool too
    SERVICE_PHOTOS.append(file_id)

    await msg.reply_text(
        f"✅ *Photo added to service pool!*\n\n"
        f"`{file_id}`\n\n"
        f"Total photos in pool: *{len(SERVICE_PHOTOS)}*\n"
        f"It will now appear randomly in service replies.",
        parse_mode="Markdown")


async def addbot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Add new bot link to Free Bots menu
    Usage: /addbot BotName | https://t.me/YourBot | Description
    """
    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        bots = get_admin_bots()
        if not bots:
            await update.message.reply_text(
                "🤖 *How to add a bot:*\n\n"
                "`/addbot Name | Link | Description`\n\n"
                "Example:\n"
                "`/addbot Pocket Bot | https://t.me/PocketBot | New Pocket Option bot`\n\n"
                "Use `/delbotN` to delete (e.g. `/delbot3`)",
                parse_mode="Markdown")
        else:
            text = "🤖 *Your Added Bots:*\n\n"
            for bid, name, link, desc in bots:
                text += f"*{bid}.* {name}\n   {link}\n   _{desc}_\n\n"
            text += "Use `/delbot ID` to remove (e.g. `/delbot 3`)"
            await update.message.reply_text(text, parse_mode="Markdown")
        return

    full = " ".join(context.args)
    parts = [p.strip() for p in full.split("|")]
    if len(parts) < 2:
        await update.message.reply_text(
            "❌ Wrong format.\n`/addbot Name | Link | Description`",
            parse_mode="Markdown")
        return

    name = parts[0]
    link = parts[1]
    desc = parts[2] if len(parts) > 2 else ""
    add_admin_bot(name, link, desc)

    await update.message.reply_text(
        f"✅ *Bot added to Free Bots menu!*\n\n"
        f"🤖 *{escape_md(name)}*\n"
        f"🔗 {escape_md(link)}\n"
        f"_{escape_md(desc)}_\n\n"
        f"Users will see it in the Free Manual Bot section.",
        parse_mode="Markdown")


async def delbot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a bot by ID: /delbot 3"""
    if not is_admin(update.effective_user.id):
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: `/delbot ID`\nGet ID from `/addbot`", parse_mode="Markdown")
        return
    bot_id = int(context.args[0])
    delete_admin_bot(bot_id)
    await update.message.reply_text(f"✅ Bot #{bot_id} removed from menu.", parse_mode="Markdown")


async def addstory_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a success story — reply to photo/video/text with /addstory [caption]"""
    if not is_admin(update.effective_user.id):
        return
    msg = update.message
    replied = msg.reply_to_message
    caption = " ".join(context.args) if context.args else ""

    if replied and replied.photo:
        fid   = replied.photo[-1].file_id
        cap   = caption or replied.caption or "⭐ Success Story"
        sid   = add_story(cap, media_id=fid, media_type="photo")
        await msg.reply_text(f"✅ *Photo story added!*\nID: `{sid}`\n\n_{cap}_", parse_mode="Markdown")
    elif replied and replied.video:
        fid   = replied.video.file_id
        cap   = caption or replied.caption or "⭐ Success Story"
        sid   = add_story(cap, media_id=fid, media_type="video")
        await msg.reply_text(f"✅ *Video story added!*\nID: `{sid}`\n\n_{cap}_", parse_mode="Markdown")
    elif caption:
        sid = add_story(caption, media_type="text")
        await msg.reply_text(f"✅ *Text story added!*\nID: `{sid}`\n\n_{caption}_", parse_mode="Markdown")
    else:
        await msg.reply_text(
            "📖 *How to add a story:*\n\n"
            "• Text only: `/addstory Great results this week!`\n"
            "• Photo: Reply to photo with `/addstory Great results!`\n"
            "• Video: Reply to video with `/addstory Watch this win!`\n\n"
            "Users will see the ⭐ Stories button in the main menu once you add one.",
            parse_mode="Markdown")


async def liststories_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all stories with IDs — /liststories"""
    if not is_admin(update.effective_user.id):
        return
    stories = get_all_stories()
    if not stories:
        await update.message.reply_text("📭 No stories yet. Use /addstory to add one.")
        return
    lines = ["📖 *SUCCESS STORIES*\n"]
    for s in stories:
        mtype = s.get("media_type", "text")
        icon  = "📷" if mtype == "photo" else "🎥" if mtype == "video" else "📝"
        cap   = (s.get("caption") or "")[:60]
        lines.append(f"{icon} *ID {s['id']}* — _{cap}..._\n   Added: {s.get('created_at','')}")
    lines.append(f"\n*Total: {len(stories)} stories*")
    lines.append("Use `/deletestory [ID]` to remove one.")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def deletestory_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/deletestory [ID] — delete a story"""
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("Usage: `/deletestory [ID]`\nGet IDs from /liststories", parse_mode="Markdown")
        return
    try:
        sid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ ID must be a number.")
        return
    if delete_story(sid):
        remaining = len(get_all_stories())
        note = "" if remaining > 0 else "\n\n_No stories left — Stories button hidden from users._"
        await update.message.reply_text(f"✅ Story *{sid}* deleted.{note}", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ Story *{sid}* not found.", parse_mode="Markdown")


def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("getid", getid_command))
    app.add_handler(CommandHandler("sessions", sessions_command))
    app.add_handler(CommandHandler("preview", preview_command))
    app.add_handler(CommandHandler("spinners", spinners_command))
    app.add_handler(CommandHandler("givespin", givespin_command))
    app.add_handler(CommandHandler("setnews", setnews_command))
    app.add_handler(CommandHandler("setvip", setvip_command))
    app.add_handler(CommandHandler("clearnews", clearnews_command))
    app.add_handler(CommandHandler("clearvip", clearnews_command))
    app.add_handler(CommandHandler("results", results_command))
    app.add_handler(CommandHandler("feedback", feedback_command))
    app.add_handler(CommandHandler("feedbackadd", feedbackadd_command))
    app.add_handler(CommandHandler("feedbackdlt", feedbackdlt_command))
    app.add_handler(CommandHandler("feedbacklist", feedbacklist_command))
    app.add_handler(CommandHandler("addphoto", addphoto_command))
    app.add_handler(CommandHandler("addstory", addstory_command))
    app.add_handler(CommandHandler("liststories", liststories_command))
    app.add_handler(CommandHandler("deletestory", deletestory_command))
    app.add_handler(CommandHandler("addbot", addbot_command))
    app.add_handler(CommandHandler("delbot", delbot_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(ChatJoinRequestHandler(handle_join_request))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    # Health server for Render + Self-ping every 5 minutes
    import threading
    import urllib.request
    from http.server import HTTPServer, BaseHTTPRequestHandler
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK - EVALON BOT RUNNING')
        def log_message(self, *a): pass
    _port = int(os.environ.get('PORT', 8080))
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', _port), H).serve_forever(), daemon=True).start()

    # Self-ping every 5 minutes to prevent Render from sleeping
    def self_ping():
        import time
        url = os.environ.get('RENDER_EXTERNAL_URL', f'http://0.0.0.0:{_port}')
        while True:
            time.sleep(300)  # 5 minutes
            try:
                urllib.request.urlopen(url, timeout=10)
                logger.info("✅ Self-ping OK")
            except Exception as e:
                logger.warning(f"Self-ping failed: {e}")
    threading.Thread(target=self_ping, daemon=True).start()

    print(f"✅ {BUSINESS_NAME} Bot v6.9 is LIVE!")
    print("📋 Type /help in bot for all admin commands")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )

if __name__ == "__main__":
    main()
