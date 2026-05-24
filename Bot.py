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
║  ✅ NEW: Health server for Render.com                        ║
║  ✅ FIXED: Urgency — no specific numbers                     ║
║  ✅ FIXED: Join VIP — new link                               ║
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
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

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
    c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS badges TEXT DEFAULT '[]'")
    c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS streak INTEGER DEFAULT 0")
    c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS quiz_score INTEGER DEFAULT 0")
    c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS goal TEXT DEFAULT NULL")
    c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS goal_date TEXT DEFAULT NULL")
    c.execute("""
        CREATE TABLE IF NOT EXISTS results_history (
            id          SERIAL PRIMARY KEY,
            result_date TEXT NOT NULL,
            content     TEXT NOT NULL,
            media_id    TEXT DEFAULT NULL,
            media_type  TEXT DEFAULT NULL,
            posted_at   TEXT NOT NULL
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

FAKE_WINNER_NAMES = [
    ("James O.", "Nigeria"), ("Maria S.", "Brazil"), ("Ahmed R.", "Egypt"),
    ("Linda T.", "Kenya"), ("Carlos M.", "Mexico"), ("Priya K.", "India"),
    ("Ivan P.", "Russia"), ("Fatima A.", "Morocco"), ("David L.", "Ghana"),
    ("Sarah W.", "South Africa"), ("Omar H.", "Saudi Arabia"), ("Ana C.", "Colombia"),
    ("Michael B.", "Uganda"), ("Yuki T.", "Japan"), ("Hassan M.", "Tanzania"),
    ("Elena V.", "Ukraine"), ("John K.", "Nigeria"), ("Amina D.", "Senegal"),
    ("Peter N.", "Zimbabwe"), ("Sofia R.", "Argentina"), ("Ali H.", "Pakistan"),
    ("Grace A.", "Cameroon"), ("Lucas F.", "Portugal"), ("Zara M.", "Malaysia"),
    ("Emmanuel O.", "Ivory Coast"), ("Natalia K.", "Poland"), ("Kwame A.", "Ghana"),
    ("Isabella L.", "Brazil"), ("Tariq B.", "Jordan"), ("Mercy W.", "Kenya"),
]

FAKE_AMOUNTS = [
    173000, 142500, 98750, 215300, 87600, 164200, 119800, 203400,
    91200, 178900, 134600, 256100, 76400, 189300, 112700, 147800,
    225600, 83900, 196400, 158200, 231700, 94500, 167300, 108600,
]

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
    "🎰 *LUCKY SPIN — EVALON WINNERS* 🎰\n\n"
    "╔═══════════════════════╗\n"
    "║  🎯  🤖  📊  💎  🔄  ║\n"
    "║  🎁  🏆  ⚡  🌟  🎊  ║\n"
    "╚═══════════════════════╝\n\n"
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
#  COMMUNITY VIBE COUNTER
#  Active Traders: starts 30,009 → grows daily → 100k in 90 days
#  At 100k: fluctuates between 145,100–145,900
#  Online Now: starts 346, varies by hour
# ══════════════════════════════════════════════════════════════

# Bot launch date — day 0
BOT_LAUNCH_DATE = datetime(2026, 5, 24)  # bot launch date

def get_active_traders_count():
    return ""

def get_streak(uid):
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT streak FROM users WHERE id=%s", (uid,))
        row = c.fetchone()
        conn.close()
        return row[0] or 0 if row else 0
    except:
        return 0

# ══════════════════════════════════════════════════════════════
#  PROGRESS TRACKER
# ══════════════════════════════════════════════════════════════

def get_member_days(uid):
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT joined FROM users WHERE id=%s", (uid,))
        row = c.fetchone()
        conn.close()
        if row and row[0]:
            joined = datetime.strptime(row[0], "%d/%m/%Y %H:%M")
            return (datetime.now() - joined).days
        return 0
    except:
        return 0

def build_profile_text(uid, lang):
    days = get_member_days(uid)
    streak_val, _ = update_streak(uid)
    streak = streak_val
    badges = get_user_badges(uid)
    ref_count = get_referral_count(uid)
    badge_display = " ".join([ACHIEVEMENTS[b][0] for b in badges if b in ACHIEVEMENTS]) or "None yet"
    quiz_score = get_quiz_score(uid)
    profile = (
        "👤 *YOUR PROFILE*\n\n"
        f"📅 Member for: *{days} days*\n"
        f"🔥 Current streak: *{streak} days*\n"
        f"👥 Referrals: *{ref_count}*\n"
        f"🏆 Quiz score: *{quiz_score}/3*\n"
        f"🎖 Badges: {badge_display}\n\n"
        "💪 Keep going — you're doing great!"
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
#  STORY MODE — for new users
# ══════════════════════════════════════════════════════════════

STORIES = {
    "en": [
        "📖 *A trader's story...*\n\nJohn was losing money every week...\nHe tried everything — YouTube, courses, signals...\nNothing worked.\n\nThen he found EVALON WINNERS.\n\nWeek 1: +$180\nWeek 2: +$340\nMonth 1: +$1,200\n\n*Will YOUR story be next?* 🏆",
        "📖 *From broke to profitable...*\n\nSarah had $200 left in her account.\nShe almost gave up on trading forever.\n\nOne decision changed everything.\n\nShe joined EVALON. Followed the system.\nStayed consistent.\n\n3 months later — she quit her 9-5.\n\n*Your breakthrough is one step away.* 💎",
    ],
    "sw": [
        "📖 *Hadithi ya mfanyabiashara...*\n\nJohn alikuwa anapoteza pesa kila wiki...\nAlijaribu kila kitu — YouTube, kozi, signals...\nHakuna kilichofanya kazi.\n\nKisha akapata EVALON WINNERS.\n\nWiki 1: +$180\nWiki 2: +$340\nMwezi 1: +$1,200\n\n*Je, hadithi YAKO itakuwa ya pili?* 🏆",
        "📖 *Kutoka hasara hadi faida...*\n\nSarah alikuwa na $200 tu akaunti yake.\nAlikaribia kuacha biashara milele.\n\nUamuzi mmoja ulibadilisha kila kitu.\n\nAlijiunga EVALON. Akafuata mfumo.\nAkabaki thabiti.\n\nMiezi 3 baadaye — aliondoka kazini kwake.\n\n*Mafanikio yako yako hatua moja tu mbele.* 💎",
    ],
}

def get_random_story(lang):
    pool = STORIES.get(lang, STORIES["en"])
    return random.choice(pool)

# ══════════════════════════════════════════════════════════════
#  VIP TEASE — shown when viewing free services
# ══════════════════════════════════════════════════════════════

VIP_TEASE = {
    "en": [
        "💎 *Psst... did you know?*\n\nVIP members get tools that make this 3x more powerful.\n\nCurious? 👇",
        "🔥 *Free is great — but VIP is legendary!*\n\nSee the difference for yourself 👇",
        "⚡ *You're using the free version.*\n\nImagine having the premium upgrade...\n\nThe gap is bigger than you think. 👇",
    ],
    "sw": [
        "💎 *Psst... unajua?*\n\nWanachama wa VIP wanapata zana zinazofanya hii kuwa na nguvu 3x zaidi.\n\nUna udadisi? 👇",
        "🔥 *Bure ni nzuri — lakini VIP ni ya ajabu!*\n\nTazama tofauti mwenyewe 👇",
        "⚡ *Unatumia toleo la bure.*\n\nFikiria kuwa na uboreshaji wa premium...\n\nTofauti ni kubwa kuliko unavyofikiri. 👇",
    ],
}

def get_vip_tease(lang):
    pool = VIP_TEASE.get(lang, VIP_TEASE["en"])
    return random.choice(pool)

# ══════════════════════════════════════════════════════════════
#  MOOD CHECK
# ══════════════════════════════════════════════════════════════

MOOD_RESPONSES = {
    "ready": {
        "en": "🔥 *THAT'S THE SPIRIT!*\n\nYou're in the right mindset — traders who enter with confidence WIN more.\n\nLet's explore what we have for you! 👇",
        "sw": "🔥 *HIYO NDIYO ROHO!*\n\nUko katika hali nzuri ya akili — wafanyabiashara wanaoingia kwa ujasiri WANASHINDA zaidi.\n\nHebu tuchunguze kilichopo kwako! 👇",
    },
    "thinking": {
        "en": "🤔 *Still thinking? That's smart!*\n\nThe best traders don't rush — they analyze.\n\nLet me show you something that might help you decide 👇",
        "sw": "🤔 *Bado unafikiri? Hiyo ni akili!*\n\nWafanyabiashara bora hawaharakishi — wanachanganua.\n\nNiruhusu nikuonyeshe kitu kitakachokusaidia kuamua 👇",
    },
    "start_today": {
        "en": "💰 *TODAY IS THE DAY!*\n\nEvery successful trader started with ONE decision.\n\nYou're making that decision RIGHT NOW. Let's go! 👇",
        "sw": "💰 *LEO NI SIKU HIYO!*\n\nKila mfanyabiashara mwenye mafanikio alianza na UAMUZI MMOJA.\n\nUnafanya uamuzi huo SASA HIVI. Twende! 👇",
    },
}

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
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text=fomo_msgs.get(lang, fomo_msgs["en"]),
            parse_mode="Markdown",
            protect_content=True,
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
        when=1800,  # 30 minutes
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
            parse_mode="Markdown",
            protect_content=True,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🚀 I'm Back!", callback_data="main_menu")
            ]]))
    except:
        pass

# ══════════════════════════════════════════════════════════════
#  FEAR OF MISSING OUT — 3 days no action
# ══════════════════════════════════════════════════════════════

async def send_fomo_3day(context):
    job_data = context.job.data
    chat_id = job_data["chat_id"]
    name    = job_data.get("name", "")
    lang    = job_data.get("lang", "en")

    msgs = {
        "en": f"⚠️ *{name}, your VIP opportunity is closing!*\n\nYou had a chance at our exclusive offer...\n\nOthers have taken your spot already.\n\nBut we kept ONE spot reserved for you.\n\n⏰ This is your LAST chance — act now!",
        "sw": f"⚠️ *{name}, fursa yako ya VIP inafungwa!*\n\nUlikuwa na nafasi ya ofa yetu ya kipekee...\n\nWengine wamechukua nafasi yako tayari.\n\nLakini tuliweka nafasi MOJAiliyohifadhiwa kwako.\n\n⏰ Hii ndiyo NAFASI YAKO YA MWISHO — chukua hatua sasa!",
    }
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=msgs.get(lang, msgs["en"]),
            parse_mode="Markdown",
            protect_content=True,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Claim My Spot!", callback_data="menu_services")
            ]]))
    except:
        pass

# ══════════════════════════════════════════════════════════════
#  SMART COMEBACK — week 1, 2, 3 (different messages)
# ══════════════════════════════════════════════════════════════

COMEBACK_MSGS = {
    1: {  # Week 1
        "en": "👋 *Hey {name}! It's been a week!*\n\n🔥 The market has been WILD this week!\n\nTraders who stayed consistent saw amazing results.\n\nDon't miss week 2 — it's usually even BETTER! 💎",
        "sw": "👋 *Habari {name}! Imekuwa wiki!*\n\n🔥 Soko limekuwa LA KUCHEKESHA wiki hii!\n\nWafanyabiashara waliobaki thabiti walipata matokeo ya ajabu.\n\nUsikose wiki ya 2 — kawaida ni BORA zaidi! 💎",
    },
    2: {  # Week 2
        "en": "🌟 *{name}, you're 2 weeks in!*\n\n💎 This is where real traders are MADE.\n\nThe ones who push through week 2 are the ones who change their lives.\n\nYou've got this. Come back and WIN! 🏆",
        "sw": "🌟 *{name}, uko wiki 2!*\n\n💎 Hapa ndipo wafanyabiashara wa kweli WANAUNDWA.\n\nWale wanaopita wiki ya 2 ndio wanaobadilisha maisha yao.\n\nUnaweza. Rudi na USHINDE! 🏆",
    },
    3: {  # Week 3
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
            chat_id=chat_id,
            photo=img,
            caption=text,
            parse_mode="Markdown",
            protect_content=True,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🚀 Let's Go!", callback_data="menu_services"),
                InlineKeyboardButton("💬 Support", callback_data="do_support"),
            ]]))
    except:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="Markdown",
                protect_content=True,
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
#  SCARCITY + SOCIAL PROOF
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
#  WIN NOTIFICATION SIMULATOR
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
        "💰 *ARIFA YA TRADER:* Matokeo ya kikao ya ajabu leo!\n\nHii ndio hutokea na mkakati na msaada sahihi. 🏆\n\nZamu yako? 👇",
    ],
}

def get_win_notification(lang):
    pool = WIN_NOTIFICATIONS.get(lang, WIN_NOTIFICATIONS["en"])
    return random.choice(pool)

# ══════════════════════════════════════════════════════════════
#  COMPETITOR COMPARISON
# ══════════════════════════════════════════════════════════════

COMPARISON_TEXT = {
    "en": (
        "🆚 *WHY CHOOSE EVALON WINNERS?*\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "❌ *Others:*\n"
        "• Fake signals with no proof\n"
        "• No support after payment\n"
        "• Disappear after 1 month\n"
        "• No refunds, no accountability\n"
        "• Copy-paste strategies that don't work\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "✅ *EVALON WINNERS:*\n"
        "• Real strategies, real results\n"
        "• 24/7 support team always here\n"
        "• Consistent community of winners\n"
        "• Free tools to get you started\n"
        "• Transparent — we show what we do\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "The choice is clear. 💎"
    ),
    "sw": (
        "🆚 *KWA NINI CHAGUA EVALON WINNERS?*\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "❌ *Wengine:*\n"
        "• Signals za uongo bila uthibitisho\n"
        "• Hakuna msaada baada ya malipo\n"
        "• Wanatoweka baada ya mwezi 1\n"
        "• Hakuna marejesho, hakuna uwajibikaji\n"
        "• Mikakati ya kunakili haifanyi kazi\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "✅ *EVALON WINNERS:*\n"
        "• Mikakati ya kweli, matokeo ya kweli\n"
        "• Timu ya msaada 24/7 ipo daima\n"
        "• Jumuiya thabiti ya washindi\n"
        "• Zana za bure kukusaidia kuanza\n"
        "• Uwazi — tunaonyesha tunachofanya\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Chaguo ni wazi. 💎"
    ),
}

# ══════════════════════════════════════════════════════════════
#  REFERRAL CHALLENGE — weekly
# ══════════════════════════════════════════════════════════════

def get_weekly_challenge(lang):
    week_num = datetime.now().isocalendar()[1]
    challenges = {
        "en": [
            f"🏆 *WEEK {week_num} CHALLENGE:*\n\nInvite 3 friends this week → Get a FREE bonus!\n\nChallenge ends Sunday midnight. ⏰",
            f"🎯 *WEEKLY CHALLENGE #{week_num}:*\n\nBring 2 new traders to EVALON → Unlock exclusive rewards!\n\nTime is ticking... ⚡",
            f"💥 *TRADER CHALLENGE WEEK {week_num}:*\n\nShare your referral link with 5 people → Win big!\n\nLet's go! 🚀",
        ],
        "sw": [
            f"🏆 *CHANGAMOTO YA WIKI {week_num}:*\n\nAlika marafiki 3 wiki hii → Pata bonasi ya BURE!\n\nChangamoto inaisha Jumapili usiku wa manane. ⏰",
            f"🎯 *CHANGAMOTO YA WIKI #{week_num}:*\n\nLeta wafanyabiashara wapya 2 kwa EVALON → Fungua zawadi za kipekee!\n\nWakati unaendelea... ⚡",
            f"💥 *CHANGAMOTO YA TRADER WIKI {week_num}:*\n\nSharehu kiungo chako cha rufaa na watu 5 → Shinda sana!\n\nTwende! 🚀",
        ],
    }
    pool = challenges.get(lang, challenges["en"])
    return pool[week_num % len(pool)]

# ══════════════════════════════════════════════════════════════
#  TIME CAPSULE
# ══════════════════════════════════════════════════════════════

def save_goal(uid, goal_text):
    try:
        conn = get_conn()
        c = conn.cursor()
        now = datetime.now().strftime("%d/%m/%Y")
        c.execute("UPDATE users SET goal=%s, goal_date=%s WHERE id=%s",
                  (goal_text[:200], now, uid))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def get_goal(uid):
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT goal, goal_date FROM users WHERE id=%s", (uid,))
        row = c.fetchone()
        conn.close()
        if row and row[0]:
            return row[0], row[1]
        return None, None
    except:
        return None, None

async def send_time_capsule(context):
    job_data = context.job.data
    uid     = job_data["uid"]
    chat_id = job_data["chat_id"]
    lang    = job_data.get("lang", "en")
    goal, goal_date = get_goal(uid)
    if not goal:
        return
    msgs = {
        "en": f"📬 *TIME CAPSULE — 3 months ago you wrote:*\n\n'{goal}'\n\n📅 Date set: {goal_date}\n\n💭 Have you achieved it?\n\nWhatever the answer — keep going. The journey is the reward. 🏆",
        "sw": f"📬 *SANDUKU LA WAKATI — miezi 3 iliyopita uliandika:*\n\n'{goal}'\n\n📅 Tarehe iliyowekwa: {goal_date}\n\n💭 Umefanikiwa?\n\nJibu lolote — endelea. Safari ndiyo thamani. 🏆",
    }
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=msgs.get(lang, msgs["en"]),
            parse_mode="Markdown",
            protect_content=True,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🎯 Set New Goal", callback_data="set_goal"),
            ]]))
    except:
        pass

# ══════════════════════════════════════════════════════════════
#  LOYALTY REWARDS — 3 months
# ══════════════════════════════════════════════════════════════

def check_loyalty_reward(uid, days, lang):
    if days == 90:
        msgs = {
            "en": "👑 *LOYALTY REWARD!*\n\n3 months with EVALON — you've EARNED a special reward!\n\n🎁 Contact support to claim your exclusive loyalty bonus!",
            "sw": "👑 *ZAWADI YA UAMINIFU!*\n\nMiezi 3 na EVALON — umePATIKANA zawadi maalum!\n\n🎁 Wasiliana na msaada kudai bonasi yako ya kipekee ya uaminifu!",
        }
        return msgs.get(lang, msgs["en"])
    return None

# ══════════════════════════════════════════════════════════════
#  MINI QUIZ
# ══════════════════════════════════════════════════════════════

QUIZ_QUESTIONS = [
    {
        "q": "📊 *QUIZ Q1:* In binary options, what does it mean when you place a CALL trade?",
        "options": ["🔴 You expect price to go DOWN", "🟢 You expect price to go UP", "⚪ You expect price to stay the same"],
        "answer": 1,
        "explanation": "✅ Correct! A CALL trade means you believe the price will be HIGHER at expiry."
    },
    {
        "q": "💰 *QUIZ Q2:* What is the SAFEST rule for trade size in binary options?",
        "options": ["💸 50% of your account", "✅ 2-5% of your account", "🎲 As much as possible"],
        "answer": 1,
        "explanation": "✅ Correct! Never risk more than 2-5% per trade — this protects your capital."
    },
    {
        "q": "⏰ *QUIZ Q3:* When is usually the BEST time to trade binary options?",
        "options": ["🌙 Late night (2AM-6AM)", "✅ London-NY overlap (1PM-5PM GMT)", "🌅 Early morning (5AM-7AM)"],
        "answer": 1,
        "explanation": "✅ Correct! The London-New York overlap has the most liquidity and clearest signals."
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
            INSERT INTO results_history (result_date, content, media_id, media_type, posted_at)
            VALUES (%s, %s, %s, %s, %s)
        """, (result_date, content_text[:2000], media_id, media_type, now))
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
            SELECT id, result_date, content, media_id, media_type, posted_at
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
            SELECT id, result_date, content, media_id, media_type, posted_at
            FROM results_history WHERE id=%s
        """, (rid,))
        row = c.fetchone()
        conn.close()
        return row
    except:
        return None



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
#  BUILD WELCOME TEXT
# ══════════════════════════════════════════════════════════════

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

def main_menu(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(ui("btn_services", lang), callback_data="menu_services")],
        [InlineKeyboardButton(ui("btn_tip", lang), callback_data="do_tip"),
         InlineKeyboardButton(ui("btn_quiz", lang), callback_data="do_quiz")],
        [InlineKeyboardButton(ui("btn_referral", lang), callback_data="do_referral"),
         InlineKeyboardButton(ui("btn_challenge", lang), callback_data="do_challenge")],
        [InlineKeyboardButton(ui("btn_mood", lang), callback_data="do_mood"),
         InlineKeyboardButton(ui("btn_profile", lang), callback_data="do_profile")],
        [InlineKeyboardButton(ui("btn_stories", lang), callback_data="do_stories"),
         InlineKeyboardButton(ui("btn_why_evalon", lang), callback_data="do_why_evalon")],
        [InlineKeyboardButton(ui("btn_results_history", lang), callback_data="do_results_history"),
         InlineKeyboardButton(ui("btn_goal", lang), callback_data="set_goal")],
        [InlineKeyboardButton(ui("btn_spin", lang), callback_data="do_spin"),
         InlineKeyboardButton(ui("btn_my_streak", lang), callback_data="do_streak")],
        [InlineKeyboardButton(ui("btn_language", lang), callback_data="change_lang")],
    ])

def services_menu(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(ui("btn_signals", lang), callback_data="svc_signals"),
         InlineKeyboardButton(ui("btn_social", lang), callback_data="svc_social")],
        [InlineKeyboardButton(ui("btn_indicator", lang), callback_data="svc_indicator"),
         InlineKeyboardButton(ui("btn_autobot", lang), callback_data="svc_autobot")],
        [InlineKeyboardButton(ui("btn_freebot", lang), callback_data="svc_freebot")],
        [InlineKeyboardButton(ui("btn_win_alert", lang), callback_data="do_win_alert"),
         InlineKeyboardButton(ui("btn_why_evalon", lang), callback_data="do_why_evalon")],
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

    # Update streak
    streak_val, _ = update_streak(user.id)
    streak = streak_val
    if streak == 3:
        add_badge(user.id, "streak_3")
    elif streak == 7:
        add_badge(user.id, "streak_7")

    # Check member milestones
    days = get_member_days(user.id)

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

    welcome_text = build_welcome_text(lang, user.first_name, visit_count)

    # Update daily streak silently
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

    schedule_smart_comebacks(context, cid, user.first_name, lang)
    schedule_auto_clean(context, cid, lang, user.first_name, user.id)
    # Anti-ghost: 7 days inactive reminder
    if context.job_queue:
        job_name = f"ghost_{cid}"
        for job in context.job_queue.get_jobs_by_name(job_name):
            job.schedule_removal()
        context.job_queue.run_once(
            send_anti_ghost,
            when=7 * 24 * 3600,
            data={"chat_id": cid, "name": user.first_name, "lang": lang},
            name=job_name)
    # FOMO 3-day
    if context.job_queue:
        job_name = f"fomo3_{cid}"
        for job in context.job_queue.get_jobs_by_name(job_name):
            job.schedule_removal()
        context.job_queue.run_once(
            send_fomo_3day,
            when=3 * 24 * 3600,
            data={"chat_id": cid, "name": user.first_name, "lang": lang},
            name=job_name)

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
                await context.bot.send_chat_action(chat_id=uid, action=ChatAction.TYPING)
                await asyncio.sleep(random.uniform(1.5, 2.8))
                await context.bot.send_message(
                    chat_id=uid, text=replied_msg.text,
                    parse_mode="Markdown",
                    reply_markup=broadcast_keyboard(user_lang))
            elif context.args:
                await context.bot.send_chat_action(chat_id=uid, action=ChatAction.TYPING)
                await asyncio.sleep(random.uniform(1.5, 2.8))
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

    # Story continue → show welcome video + poll
    if data == "story_continue":
        await safe_delete(context, cid, query.message.message_id)
        await delete_all_bot_msgs(context, cid)
        await typing_action(cid, context, 1.2)
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
        schedule_smart_comebacks(context, cid, user.first_name, lang)
        schedule_auto_clean(context, cid, lang, user.first_name, user.id)
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

    # FIX: User skips text opinion
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
        schedule_smart_comebacks(context, cid, user.first_name, lang)
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
        # VIP Tease after viewing free indicator
        if context.job_queue:
            job_name = f"vip_tease_{cid}"
            for job in context.job_queue.get_jobs_by_name(job_name):
                job.schedule_removal()
            async def send_tease(ctx):
                try:
                    tease = get_vip_tease(lang)
                    m = await ctx.bot.send_message(
                        chat_id=cid, text=tease,
                        parse_mode="Markdown",
                        protect_content=True,
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton(ui("btn_services", lang), callback_data="menu_services")
                        ]]))
                    track_msg(cid, m.message_id)
                except: pass
            context.job_queue.run_once(send_tease, when=120, name=job_name)

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
        # Success Mirror — show encouraging message before connecting
        mirror_msgs = {
            "en": "💪 *Before we connect you...*\n\nTraders who stay consistent with EVALON see results of +90% and beyond in their sessions.\n\nYou\'re on the right path — our team is here to help you get there! 🏆",
            "sw": "💪 *Kabla ya kukuunganisha...*\n\nWafanyabiashara wanaobaki thabiti na EVALON wanaona matokeo ya +90% na zaidi kwenye vikao vyao.\n\nUko njiani sahihi — timu yetu iko hapa kukusaidia kufika huko! 🏆",
        }
        mirror = mirror_msgs.get(lang, mirror_msgs["en"])
        mirror_msg = await send_protected_text(
            context, cid, mirror,
            InlineKeyboardMarkup([[
                InlineKeyboardButton("💬 Connect Me Now", callback_data="do_support_confirm")
            ]]))
        track_msg(cid, mirror_msg.message_id)
        return

    elif data == "do_support_confirm":
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
            [InlineKeyboardButton("📲 Join VIP Channel", url=VIP_BOT_LINK)],
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
        winners = get_fake_weekly_winners()
        medals = ["👑", "🥈", "🥉", "4️⃣", "5️⃣"]
        week_num = datetime.now().isocalendar()[1]
        lines = [f"👑 *EVALON WINNERS — WEEK {week_num}*\n\n"]
        lines.append("🔥 *Top 5 VIP Traders This Week:*\n")
        for i, (name, country, amount) in enumerate(winners):
            lines.append(f"{medals[i]} *{name}* 🌍 {country}\n   💰 Earned: *${amount:,}* this week\n")
        lines.append("\n🚀 *Want to be on this list next week?*\nJoin our VIP Signals and start winning!")
        winners_text = "\n".join(lines)
        img = rand_img(SERVICE_PHOTOS, context.user_data, "last_img_winners")
        msg = await send_protected_photo(
            context, cid, img, winners_text,
            InlineKeyboardMarkup([
                [InlineKeyboardButton(ui("btn_services", lang), callback_data="menu_services")],
                [InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")],
            ]))
        track_msg(cid, msg.message_id)

    # ── MY DAILY STREAK ────────────────────────────────────────
    elif data == "do_streak":
        streak, max_streak, _ = update_streak(user.id)
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
            SPIN_WHEEL_VISUAL + "🎰 *Spinning...*\n\n▶️ 🎯 🤖 📊 💎 🔄 🎁 🏆",
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
                    text=SPIN_WHEEL_VISUAL + "🎰 *Spinning...*\n\n" + frame,
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
        img = random.choice(SERVICE_PHOTOS)
        msg = await send_protected_photo(context, cid, img, result_header, result_kb)
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


    # ── DAILY TIP ──────────────────────────────────────────────
    elif data == "do_tip":
        tip = get_daily_binary_tip()
        msg = await send_protected_text(
            context, cid,
            f"💡 *FREE BINARY TIP OF THE DAY*\n\n{tip}\n\n_Come back tomorrow for a new tip!_ 📅",
            InlineKeyboardMarkup([
                [InlineKeyboardButton(ui("btn_quiz", lang), callback_data="do_quiz")],
                [InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")],
            ]))
        track_msg(cid, msg.message_id)

    # ── MOOD CHECK ─────────────────────────────────────────────
    elif data == "do_mood":
        msg = await send_protected_text(
            context, cid,
            "😊 *HOW ARE YOU FEELING ABOUT TRADING TODAY?*\n\nYour mindset is everything! 💪",
            InlineKeyboardMarkup([
                [InlineKeyboardButton(ui("mood_ready", lang), callback_data="mood_ready")],
                [InlineKeyboardButton(ui("mood_thinking", lang), callback_data="mood_thinking")],
                [InlineKeyboardButton(ui("mood_today", lang), callback_data="mood_start_today")],
            ]))
        track_msg(cid, msg.message_id)

    elif data in ["mood_ready", "mood_thinking", "mood_start_today"]:
        mood_key = data.replace("mood_start_today", "start_today")
        response = MOOD_RESPONSES.get(mood_key, MOOD_RESPONSES.get("ready", {}))
        text = response.get(lang, response.get("en", "🔥 Great mindset!"))
        img = rand_img(SERVICE_PHOTOS, context.user_data, "last_img_mood")
        msg = await send_protected_photo(
            context, cid, img, text,
            InlineKeyboardMarkup([
                [InlineKeyboardButton(ui("btn_services", lang), callback_data="menu_services")],
                [InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")],
            ]))
        track_msg(cid, msg.message_id)

    # ── MINI QUIZ ──────────────────────────────────────────────
    elif data == "do_quiz":
        q = QUIZ_QUESTIONS[0]
        opts = q["options"]
        msg = await send_protected_text(
            context, cid,
            q["q"],
            InlineKeyboardMarkup([
                [InlineKeyboardButton(opts[0], callback_data="quiz_0_0")],
                [InlineKeyboardButton(opts[1], callback_data="quiz_0_1")],
                [InlineKeyboardButton(opts[2], callback_data="quiz_0_2")],
                [InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")],
            ]))
        context.user_data["quiz_score"] = 0
        track_msg(cid, msg.message_id)

    elif data.startswith("quiz_"):
        parts = data.split("_")
        q_idx = int(parts[1])
        ans = int(parts[2])
        correct = QUIZ_QUESTIONS[q_idx]["answer"]
        score = context.user_data.get("quiz_score", 0)
        if ans == correct:
            score += 1
            context.user_data["quiz_score"] = score
            feedback = f"✅ *Correct!* {QUIZ_QUESTIONS[q_idx]['explanation']}"
        else:
            feedback = f"❌ *Not quite!* {QUIZ_QUESTIONS[q_idx]['explanation']}"

        next_q = q_idx + 1
        if next_q < len(QUIZ_QUESTIONS):
            q = QUIZ_QUESTIONS[next_q]
            opts = q["options"]
            msg = await send_protected_text(
                context, cid,
                f"{feedback}\n\n---\n\n{q['q']}",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton(opts[0], callback_data=f"quiz_{next_q}_0")],
                    [InlineKeyboardButton(opts[1], callback_data=f"quiz_{next_q}_1")],
                    [InlineKeyboardButton(opts[2], callback_data=f"quiz_{next_q}_2")],
                ]))
        else:
            # Quiz complete
            final_score = score
            save_quiz_score(user.id, final_score)
            if final_score == 3:
                result_text = ui("quiz_perfect", lang)
                add_badge(user.id, "quiz_master")
                for aid in ADMIN_IDS:
                    try:
                        await context.bot.send_message(
                            chat_id=aid,
                            text=f"🏅 *Badge Earned!*\n\n👤 {user.full_name} (`{user.id}`)\n🎓 Quiz Master badge!",
                            parse_mode="Markdown")
                    except:
                        pass
            elif final_score >= 2:
                result_text = ui("quiz_good", lang).format(score=final_score)
            else:
                result_text = ui("quiz_try", lang).format(score=final_score)

            msg = await send_protected_text(
                context, cid,
                f"{feedback}\n\n---\n\n{result_text}",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton(ui("btn_tip", lang), callback_data="do_tip")],
                    [InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")],
                ]))
        track_msg(cid, msg.message_id)

    # ── MY PROFILE ─────────────────────────────────────────────
    elif data == "do_profile":
        days = get_member_days(user.id)
        streak_val, _ = update_streak(user.id)
        streak = streak_val
        profile_text = build_profile_text(user.id, lang)

        # Check celebration milestones
        celebration = get_celebration_message(days, lang)
        if celebration:
            await send_protected_text(
                context, cid, celebration,
                InlineKeyboardMarkup([[
                    InlineKeyboardButton(ui("btn_support", lang), callback_data="do_support")
                ]]))

        # Check loyalty reward
        loyalty = check_loyalty_reward(user.id, days, lang)
        if loyalty:
            await send_protected_text(
                context, cid, loyalty,
                InlineKeyboardMarkup([[
                    InlineKeyboardButton(ui("btn_support", lang), callback_data="do_support")
                ]]))

        msg = await send_protected_text(
            context, cid, profile_text,
            InlineKeyboardMarkup([
                [InlineKeyboardButton(ui("btn_quiz", lang), callback_data="do_quiz"),
                 InlineKeyboardButton(ui("btn_goal", lang), callback_data="set_goal")],
                [InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")],
            ]))
        track_msg(cid, msg.message_id)

    # ── SET GOAL ───────────────────────────────────────────────
    elif data == "set_goal":
        msg = await send_protected_text(
            context, cid,
            ui("goal_prompt", lang),
            InlineKeyboardMarkup([[
                InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")
            ]]))
        context.user_data["awaiting_goal"] = True
        track_msg(cid, msg.message_id)

    # ── WHY EVALON ─────────────────────────────────────────────
    elif data == "do_why_evalon":
        text = COMPARISON_TEXT.get(lang, COMPARISON_TEXT["en"])
        msg = await send_protected_text(
            context, cid, text,
            InlineKeyboardMarkup([
                [InlineKeyboardButton(ui("btn_services", lang), callback_data="menu_services")],
                [InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")],
            ]))
        track_msg(cid, msg.message_id)

    # ── RESULTS HISTORY ────────────────────────────────────────
    elif data == "do_results_history":
        results = get_results_history(5)
        if not results:
            msg = await send_protected_text(
                context, cid,
                ui("no_results", lang),
                InlineKeyboardMarkup([[
                    InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")
                ]]))
        else:
            kb = []
            for r in results:
                rid, rdate, content_text, media_id, media_type, posted_at = r
                btn_label = f"📅 {rdate}"
                kb.append([InlineKeyboardButton(btn_label, callback_data=f"view_result_{rid}")])
            kb.append([InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")])
            msg = await send_protected_text(
                context, cid,
                "📅 *PAST RESULTS*\n\nTap a date to view results 👇",
                InlineKeyboardMarkup(kb))
        track_msg(cid, msg.message_id)

    elif data.startswith("view_result_"):
        rid = int(data.split("_")[2])
        result = get_result_by_id(rid)
        if result:
            rid2, rdate, content_text, media_id, media_type, posted_at = result
            header = f"📅 *Results — {rdate}*\n\n"
            if media_id and media_type == "photo":
                try:
                    msg = await context.bot.send_photo(
                        chat_id=cid, photo=media_id,
                        caption=header + content_text,
                        parse_mode="Markdown",
                        protect_content=True,
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton(ui("btn_back", lang), callback_data="do_results_history")
                        ]]))
                except:
                    msg = await send_protected_text(
                        context, cid, header + content_text,
                        InlineKeyboardMarkup([[
                            InlineKeyboardButton(ui("btn_back", lang), callback_data="do_results_history")
                        ]]))
            elif media_id and media_type == "video":
                try:
                    msg = await context.bot.send_video(
                        chat_id=cid, video=media_id,
                        caption=header + content_text,
                        parse_mode="Markdown",
                        protect_content=True,
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton(ui("btn_back", lang), callback_data="do_results_history")
                        ]]))
                except:
                    msg = await send_protected_text(
                        context, cid, header + content_text,
                        InlineKeyboardMarkup([[
                            InlineKeyboardButton(ui("btn_back", lang), callback_data="do_results_history")
                        ]]))
            else:
                msg = await send_protected_text(
                    context, cid, header + content_text,
                    InlineKeyboardMarkup([[
                        InlineKeyboardButton(ui("btn_back", lang), callback_data="do_results_history")
                    ]]))
            track_msg(cid, msg.message_id)

    # ── WEEKLY CHALLENGE ───────────────────────────────────────
    elif data == "do_challenge":
        challenge = get_weekly_challenge(lang)
        ref_count = get_referral_count(user.id)
        bar = make_progress_bar(ref_count, REFERRAL_MIN)
        msg = await send_protected_text(
            context, cid,
            f"{challenge}\n\n{bar}\n\n👥 Your referrals: *{ref_count}*",
            InlineKeyboardMarkup([
                [InlineKeyboardButton(ui("btn_referral", lang), callback_data="do_referral")],
                [InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")],
            ]))
        track_msg(cid, msg.message_id)

    # ── WIN ALERT ──────────────────────────────────────────────
    elif data == "do_win_alert":
        alert = get_win_notification(lang)
        msg = await send_protected_text(
            context, cid, alert,
            InlineKeyboardMarkup([
                [InlineKeyboardButton(ui("btn_services", lang), callback_data="menu_services")],
                [InlineKeyboardButton(ui("btn_back", lang), callback_data="main_menu")],
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
        # Personality — human-like fallback
        human_fallback = {
            "en": "🤔 Hmm, I didn't quite get that...\n\nBut hey — I'm here to help you WIN! 💪\n\nWhat would you like to explore?",
            "sw": "🤔 Hmm, sijaelewa vizuri...\n\nLakini hei — niko hapa kukusaidia KUSHINDA! 💪\n\nUnataka kuchunguza nini?",
        }
        fallback_text = human_fallback.get(lang, human_fallback["en"])
        await reply_with_text(fallback_text, support_keyboard(lang))

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
        text=SPIN_WHEEL_VISUAL + "🎰 *Spinning...*\n\n▶️ 🎯 🤖 📊 💎 🔄 🎁 🏆",
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
    await msg.reply_text("✅ *VIP Results* updated! Users will see it immediately.", parse_mode="Markdown")


async def clearnews_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear news or vip content: /clearnews or /clearvip"""
    if not is_admin(update.effective_user.id):
        return
    cmd = update.message.text.strip().lower()
    key = "vip" if "vip" in cmd else "news"
    set_dynamic_content(key, text_value=None, file_id=None, file_type=None)
    label = "VIP Results" if key == "vip" else "Whats New"
    await update.message.reply_text(f"✅ *{label}* cleared.", parse_mode="Markdown")


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
        "`/results Your text` — Save today's session results to history\n"
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



# ══════════════════════════════════════════════════════════════
#  HEALTH SERVER — Required for Render.com deployment
# ══════════════════════════════════════════════════════════════

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')
    def log_message(self, *a):
        pass  # Suppress logs

def start_health_server():
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"✅ Health server running on port {port}")


async def results_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to post session results"""
    if not is_admin(update.effective_user.id):
        return

    replied = update.message.reply_to_message
    today = datetime.now().strftime("%d/%m/%Y")

    if not replied and not context.args:
        await update.message.reply_text(
            "📊 *Post Session Results*\n\n"
            "Usage:\n"
            "• Reply to a photo/video + `/results` — saves with media\n"
            "• `/results Your text here` — saves text only\n\n"
            f"Today's date: *{today}*",
            parse_mode="Markdown")
        return

    content_text = ""
    media_id = None
    media_type = None

    if replied:
        if replied.photo:
            media_id = replied.photo[-1].file_id
            media_type = "photo"
            content_text = replied.caption or ""
        elif replied.video:
            media_id = replied.video.file_id
            media_type = "video"
            content_text = replied.caption or ""
        elif replied.text:
            content_text = replied.text
    elif context.args:
        content_text = " ".join(context.args)

    if save_result(today, content_text, media_id, media_type):
        await update.message.reply_text(
            f"✅ *Results saved for {today}!*\n\n"
            f"Users can view them via '📅 Past Results' button.",
            parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Failed to save results.")

def main():
    start_health_server()
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CommandHandler("results", results_command))
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
    app.add_handler(CommandHandler("feedback", feedback_command))
    app.add_handler(CommandHandler("feedbackadd", feedbackadd_command))
    app.add_handler(CommandHandler("feedbackdlt", feedbackdlt_command))
    app.add_handler(CommandHandler("feedbacklist", feedbacklist_command))
    app.add_handler(CommandHandler("addphoto", addphoto_command))
    app.add_handler(CommandHandler("addbot", addbot_command))
    app.add_handler(CommandHandler("delbot", delbot_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(ChatJoinRequestHandler(handle_join_request))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    print(f"✅ {BUSINESS_NAME} Bot v7.0 is LIVE!")
    print("📋 Type /help in bot for all admin commands")

    # Self-ping every 5 minutes to prevent Render from sleeping
    import urllib.request
    def self_ping():
        import time
        url = os.environ.get('RENDER_EXTERNAL_URL', f'http://0.0.0.0:{int(os.environ.get("PORT", 8080))}')
        while True:
            time.sleep(300)
            try:
                urllib.request.urlopen(url, timeout=10)
                logger.info("✅ Self-ping OK")
            except Exception as e:
                logger.warning(f"Self-ping failed: {e}")
    threading.Thread(target=self_ping, daemon=True).start()

    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )

if __name__ == "__main__":
    main()
