"""
╔══════════════════════════════════════════════════════════════╗
║         EVALON WINNERS — TELEGRAM SUPPORT BOT v6.5          ║
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
    conn.commit()
    conn.close()
    init_spin_db()

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
#  SPIN WHEEL — DATABASE & PRIZE LOGIC
# ══════════════════════════════════════════════════════════════

def init_spin_db():
    """Create spin_log table if not exists"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS spin_log (
            user_id   BIGINT PRIMARY KEY,
            last_spin TEXT DEFAULT NULL,
            total_spins INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def can_spin_today(uid):
    """Returns True if user has not spun today"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT last_spin FROM spin_log WHERE user_id=%s", (uid,))
    row = c.fetchone()
    conn.close()
    if not row or not row[0]:
        return True
    today = datetime.now().strftime("%d/%m/%Y")
    return row[0] != today

def record_spin(uid):
    """Record today's spin for user"""
    conn = get_conn()
    c = conn.cursor()
    today = datetime.now().strftime("%d/%m/%Y")
    c.execute("""
        INSERT INTO spin_log (user_id, last_spin, total_spins)
        VALUES (%s, %s, 1)
        ON CONFLICT (user_id) DO UPDATE
        SET last_spin=EXCLUDED.last_spin,
            total_spins=spin_log.total_spins+1
    """, (uid, today))
    conn.commit()
    conn.close()

def get_next_spin_time():
    """Returns how many hours until midnight (next spin)"""
    now = datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    from datetime import timedelta
    next_midnight = midnight + timedelta(days=1)
    diff = next_midnight - now
    hours = int(diff.seconds / 3600)
    mins  = int((diff.seconds % 3600) / 60)
    return hours, mins

# ── SPIN WHEEL PRIZES ──────────────────────────────────────────
# Probability breakdown (total = 100):
#   WIN prizes  =  5% combined (nadra sana — 1 kati ya 20)
#   LOSE prizes = 95% combined (hakuna zawadi)
#
# WIN slots (5%):
#   private_session = 2%  (nadra zaidi)
#   free_bot        = 2%  (nadra)
#   free_signal     = 1%  (nadra zaidi)
#
# LOSE slots (95%):
#   try_again       = 40%
#   almost          = 30%
#   better_luck     = 25%

SPIN_PRIZES = [
    # (weight, prize_key, emoji, is_win)
    (2,  "private_session", "🎯", True),
    (2,  "free_bot",        "🤖", True),
    (1,  "free_signal",     "📊", True),
    (40, "try_again",       "🔄", False),
    (30, "almost",          "😅", False),
    (25, "better_luck",     "💪", False),
]

SPIN_PRIZE_TEXT = {
    "private_session": {
        "en": "🎯 *JACKPOT! You won a FREE Private Support Session!*\n\nOur team will contact you personally. 🏆",
        "sw": "🎯 *JACKPOT! Umeshinda Private Support Session BURE!*\n\nTimu yetu itawasiliana nawe kibinafsi. 🏆",
        "ar": "🎯 *جائزة كبرى! لقد فزت بجلسة دعم خاصة مجانية!*\n\nسيتواصل معك فريقنا شخصياً. 🏆",
        "zh": "🎯 *头奖！您赢得了免费私人支持课程！*\n\n我们的团队将亲自联系您。 🏆",
        "hi": "🎯 *जैकपॉट! आपने मुफ्त प्राइवेट सपोर्ट सेशन जीता!*\n\nहमारी टीम आपसे व्यक्तिगत रूप से संपर्क करेगी। 🏆",
        "ru": "🎯 *ДЖЕКПОТ! Вы выиграли БЕСПЛАТНУЮ приватную сессию!*\n\nНаша команда свяжется с вами лично. 🏆",
        "es": "🎯 *JACKPOT! Ganaste una sesión privada GRATIS!*\n\nNuestro equipo te contactará personalmente. 🏆",
        "fr": "🎯 *JACKPOT! Vous avez gagné une session privée GRATUITE!*\n\nNotre équipe vous contactera personnellement. 🏆",
        "pt": "🎯 *JACKPOT! Você ganhou uma sessão privada GRÁTIS!*\n\nNossa equipe entrará em contato pessoalmente. 🏆",
        "de": "🎯 *JACKPOT! Sie haben eine KOSTENLOSE private Sitzung gewonnen!*\n\nUnser Team wird Sie persönlich kontaktieren. 🏆",
        "ur": "🎯 *جیک پاٹ! آپ نے مفت پرائیویٹ سپورٹ سیشن جیتا!*\n\nہماری ٹیم آپ سے ذاتی طور پر رابطہ کرے گی۔ 🏆",
        "ja": "🎯 *ジャックポット！無料プライベートサポートセッション獲得！*\n\nチームが個人的に連絡します。 🏆",
    },
    "free_bot": {
        "en": "🤖 *WINNER! You won a FREE Manual Bot!*\n\nCheck our Free Bot section to claim it. 🎁",
        "sw": "🤖 *MSHINDI! Umeshinda Manual Bot BURE!*\n\nAngalia sehemu ya Free Bot kupata yako. 🎁",
        "ar": "🤖 *فائز! لقد فزت ببوت يدوي مجاني!*\n\nتحقق من قسم البوت المجاني للمطالبة به. 🎁",
        "zh": "🤖 *获胜者！您赢得了免费手动机器人！*\n\n查看我们的免费机器人部分领取。 🎁",
        "hi": "🤖 *विजेता! आपने मुफ्त मैनुअल बॉट जीता!*\n\nइसे प्राप्त करने के लिए फ्री बॉट सेक्शन देखें। 🎁",
        "ru": "🤖 *ПОБЕДИТЕЛЬ! Вы выиграли БЕСПЛАТНОГО ручного бота!*\n\nЗайдите в раздел Free Bot для получения. 🎁",
        "es": "🤖 *GANADOR! Ganaste un Bot Manual GRATIS!*\n\nRevisa la sección Free Bot para reclamarlo. 🎁",
        "fr": "🤖 *GAGNANT! Vous avez gagné un Bot Manuel GRATUIT!*\n\nConsultez la section Free Bot pour le réclamer. 🎁",
        "pt": "🤖 *VENCEDOR! Você ganhou um Bot Manual GRÁTIS!*\n\nVerifique a seção Free Bot para reivindicá-lo. 🎁",
        "de": "🤖 *GEWINNER! Sie haben einen KOSTENLOSEN manuellen Bot gewonnen!*\n\nSehen Sie im Free Bot Bereich nach. 🎁",
        "ur": "🤖 *فاتح! آپ نے مفت مینوئل بوٹ جیتا!*\n\nحاصل کرنے کے لیے فری بوٹ سیکشن دیکھیں۔ 🎁",
        "ja": "🤖 *当選！無料マニュアルボット獲得！*\n\nフリーボットセクションで受け取ってください。 🎁",
    },
    "free_signal": {
        "en": "📊 *LUCKY! You won a FREE VIP Signal today!*\n\nOur team will send it to you shortly. ⚡",
        "sw": "📊 *BAHATI! Umeshinda Signal moja ya VIP BURE leo!*\n\nTimu yetu itakutumia hivi karibuni. ⚡",
        "ar": "📊 *محظوظ! لقد فزت بإشارة VIP مجانية اليوم!*\n\nسيرسلها لك فريقنا قريباً. ⚡",
        "zh": "📊 *幸运！今天赢得了一个免费VIP信号！*\n\n我们的团队将很快发送给您。 ⚡",
        "hi": "📊 *भाग्यशाली! आज मुफ्त VIP सिग्नल जीता!*\n\nहमारी टीम इसे जल्द भेजेगी। ⚡",
        "ru": "📊 *ВЕЗЁТ! Вы выиграли БЕСПЛАТНЫЙ VIP сигнал сегодня!*\n\nНаша команда отправит его скоро. ⚡",
        "es": "📊 *SUERTE! Ganaste una señal VIP GRATIS hoy!*\n\nNuestro equipo te la enviará pronto. ⚡",
        "fr": "📊 *CHANCE! Vous avez gagné un signal VIP GRATUIT aujourd'hui!*\n\nNotre équipe vous l'enverra bientôt. ⚡",
        "pt": "📊 *SORTE! Você ganhou um sinal VIP GRÁTIS hoje!*\n\nNossa equipe enviará em breve. ⚡",
        "de": "📊 *GLÜCK! Sie haben heute ein KOSTENLOSES VIP-Signal gewonnen!*\n\nUnser Team wird es bald senden. ⚡",
        "ur": "📊 *خوش قسمت! آج مفت VIP سگنل جیتا!*\n\nہماری ٹیم جلد بھیجے گی۔ ⚡",
        "ja": "📊 *ラッキー！今日の無料VIPシグナル獲得！*\n\nチームがすぐに送ります。 ⚡",
    },
    "try_again": {
        "en": "🔄 *Not this time!*\n\nKeep spinning tomorrow — big wins are coming! 💪",
        "sw": "🔄 *Si leo!*\n\nEndelea kesho — ushindi mkubwa unakuja! 💪",
        "ar": "🔄 *ليس هذه المرة!*\n\nاستمر في الغد — الفوز الكبير قادم! 💪",
        "zh": "🔄 *这次不行！*\n\n明天继续旋转——大奖即将来临！ 💪",
        "hi": "🔄 *इस बार नहीं!*\n\nकल फिर कोशिश करें — बड़ी जीत आने वाली है! 💪",
        "ru": "🔄 *Не в этот раз!*\n\nПродолжайте завтра — большие выигрыши ждут! 💪",
        "es": "🔄 *Esta vez no!*\n\nSigue girando mañana — grandes ganancias vienen! 💪",
        "fr": "🔄 *Pas cette fois!*\n\nContinuez demain — de grandes victoires arrivent! 💪",
        "pt": "🔄 *Não desta vez!*\n\nContinue amanhã — grandes ganhos estão vindo! 💪",
        "de": "🔄 *Nicht dieses Mal!*\n\nWeiter morgen — große Gewinne kommen! 💪",
        "ur": "🔄 *اس بار نہیں!*\n\nکل دوبارہ کوشش کریں — بڑی جیت آنے والی ہے! 💪",
        "ja": "🔄 *今回は残念！*\n\n明日また回してください — 大きな勝利が来ます！ 💪",
    },
    "almost": {
        "en": "😅 *So close! Almost won!*\n\nTomorrow is your day — spin again! 🎰",
        "sw": "😅 *Karibu sana! Ulikaribia kushinda!*\n\nKesho ni siku yako — spin tena! 🎰",
        "ar": "😅 *قريب جداً! كدت تفوز!*\n\nغداً هو يومك — استمر في الدوران! 🎰",
        "zh": "😅 *非常接近！差点赢了！*\n\n明天是你的日子——再次旋转！ 🎰",
        "hi": "😅 *बहुत करीब! लगभग जीत गए!*\n\nकल आपका दिन है — फिर से घुमाएं! 🎰",
        "ru": "😅 *Так близко! Почти выиграли!*\n\nЗавтра ваш день — крутите снова! 🎰",
        "es": "😅 *Muy cerca! Casi ganaste!*\n\nMañana es tu día — gira de nuevo! 🎰",
        "fr": "😅 *Tellement proche! Presque gagné!*\n\nDemain c'est votre jour — tournez encore! 🎰",
        "pt": "😅 *Tão perto! Quase ganhou!*\n\nAmanhã é o seu dia — gire novamente! 🎰",
        "de": "😅 *So nah! Fast gewonnen!*\n\nMorgen ist Ihr Tag — drehen Sie erneut! 🎰",
        "ur": "😅 *بہت قریب! تقریباً جیت گئے!*\n\nکل آپ کا دن ہے — دوبارہ گھمائیں! 🎰",
        "ja": "😅 *惜しい！もう少しで当選！*\n\n明日はあなたの日です — また回しましょう！ 🎰",
    },
    "better_luck": {
        "en": "💪 *Better luck tomorrow!*\n\nEvery spin brings you closer to winning! 🌟",
        "sw": "💪 *Bahati njema kesho!*\n\nKila spin inakukaribishia ushindi! 🌟",
        "ar": "💪 *حظ أوفر غداً!*\n\nكل دورة تقربك من الفوز! 🌟",
        "zh": "💪 *明天好运！*\n\n每次旋转让您更接近获胜！ 🌟",
        "hi": "💪 *कल बेहतर किस्मत!*\n\nहर स्पिन आपको जीत के करीब लाती है! 🌟",
        "ru": "💪 *Больше удачи завтра!*\n\nКаждый спин приближает вас к победе! 🌟",
        "es": "💪 *Mejor suerte mañana!*\n\nCada giro te acerca a ganar! 🌟",
        "fr": "💪 *Meilleure chance demain!*\n\nChaque tour vous rapproche de la victoire! 🌟",
        "pt": "💪 *Melhor sorte amanhã!*\n\nCada giro te aproxima de ganhar! 🌟",
        "de": "💪 *Mehr Glück morgen!*\n\nJedes Drehen bringt Sie näher an den Gewinn! 🌟",
        "ur": "💪 *کل زیادہ قسمت!*\n\nہر spin آپ کو جیت کے قریب لاتی ہے! 🌟",
        "ja": "💪 *明日は幸運を！*\n\n毎回のスピンが勝利に近づけます！ 🌟",
    },
}

# Spinning animation frames
SPIN_FRAMES = [
    "🎰 *|* 🎯 *|* 🤖 *|* 📊 *|* 💎 *|* 🔄 *|* 🎁",
    "🎰 *|* 🔄 *|* 🎯 *|* 🤖 *|* 📊 *|* 💎 *|* 🎁",
    "🎰 *|* 💎 *|* 🔄 *|* 🎯 *|* 🤖 *|* 📊 *|* 🎁",
    "🎰 *|* 📊 *|* 💎 *|* 🔄 *|* 🎯 *|* 🤖 *|* 🎁",
    "🎰 *|* 🤖 *|* 📊 *|* 💎 *|* 🔄 *|* 🎯 *|* 🎁",
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
        "🔥 HIGH DEMAND! 12 traders joined in the last hour!",
        "⏰ TODAY ONLY! Special offer expires at midnight!",
        "🚨 ALMOST FULL! VIP channel closing new members soon!",
        "💥 LAST CHANCE! Don't miss today's winning signals!",
    ],
    "sw": [
        "⚠️ NAFASI CHACHE! Nafasi chache za VIP zimebaki leo!",
        "🔥 MAHITAJI MAKUBWA! Wafanyabiashara 12 walijiunga saa moja iliyopita!",
        "⏰ LEO TU! Ofa maalum inaisha usiku wa manane!",
        "🚨 KARIBU KUJAA! Channel ya VIP itafunga wanachama wapya hivi karibuni!",
        "💥 NAFASI YA MWISHO! Usikose signals za kushinda za leo!",
    ],
    "ar": [
        "⚠️ مقاعد محدودة! بقيت مقاعد VIP قليلة فقط اليوم!",
        "🔥 طلب عالٍ! انضم 12 متداولاً في الساعة الماضية!",
        "⏰ اليوم فقط! ينتهي العرض الخاص عند منتصف الليل!",
    ],
    "zh": [
        "⚠️ 名额有限！今天只剩几个VIP名额！",
        "🔥 需求旺盛！过去一小时有12名交易者加入！",
        "⏰ 仅限今天！特别优惠将于午夜到期！",
    ],
    "hi": [
        "⚠️ सीमित स्लॉट! आज केवल कुछ VIP स्पॉट बचे हैं!",
        "🔥 उच्च मांग! पिछले एक घंटे में 12 ट्रेडर्स जुड़े!",
        "⏰ आज ही! विशेष ऑफर आधी रात को समाप्त होता है!",
    ],
    "ru": [
        "⚠️ ОГРАНИЧЕННЫЕ МЕСТА! Осталось несколько VIP мест!",
        "🔥 ВЫСОКИЙ СПРОС! 12 трейдеров присоединились за последний час!",
        "⏰ ТОЛЬКО СЕГОДНЯ! Специальное предложение истекает в полночь!",
    ],
    "es": [
        "⚠️ PLAZAS LIMITADAS! Solo quedan pocas plazas VIP hoy!",
        "🔥 ALTA DEMANDA! 12 traders se unieron en la última hora!",
        "⏰ SOLO HOY! La oferta especial expira a medianoche!",
    ],
    "fr": [
        "⚠️ PLACES LIMITÉES! Il ne reste que quelques places VIP aujourd'hui!",
        "🔥 FORTE DEMANDE! 12 traders ont rejoint la dernière heure!",
        "⏰ AUJOURD'HUI SEULEMENT! L'offre spéciale expire à minuit!",
    ],
    "pt": [
        "⚠️ VAGAS LIMITADAS! Apenas algumas vagas VIP restam hoje!",
        "🔥 ALTA DEMANDA! 12 traders entraram na última hora!",
        "⏰ SOMENTE HOJE! Oferta especial expira à meia-noite!",
    ],
    "de": [
        "⚠️ BEGRENZTE PLÄTZE! Nur noch wenige VIP-Plätze heute!",
        "🔥 HOHE NACHFRAGE! 12 Trader sind in der letzten Stunde beigetreten!",
        "⏰ NUR HEUTE! Sonderangebot läuft um Mitternacht ab!",
    ],
    "ur": [
        "⚠️ محدود نشستیں! آج صرف چند VIP نشستیں باقی ہیں!",
        "🔥 زیادہ مانگ! پچھلے گھنٹے میں 12 ٹریڈرز شامل ہوئے!",
        "⏰ صرف آج! خصوصی پیشکش آدھی رات کو ختم ہوتی ہے!",
    ],
    "ja": [
        "⚠️ 限定スロット！今日のVIPスポットはわずかです！",
        "🔥 高需要！過去1時間で12人のトレーダーが参加しました！",
        "⏰ 本日限り！特別オファーは真夜中に終了します！",
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
        "btn_spin": "🎰 Lucky Spin — Try Your Luck!",
        "spin_wait": "⏳ Already spun today! Come back in {hours}h {mins}m 🕐",
        "spin_spinning": "🎰 Spinning...",
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
        "referral_msg": "🎁 *YOUR REFERRAL LINK*\n\nYour link:\nhttps://t.me/{bot}?start=ref{uid}\n\nYour referrals: {count}/{min}\n{bar}\n\nRefer {needed} more to unlock your reward!\n{leaderboard}",
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
    },
    "sw": {
        "welcome": "👋 Karibu, *{name}!*\n\n{urgency}\n\n🏆 *{business}* — Mahali pa washindi!\n\nUnataka kuchunguza nini? 👇",
        "btn_services": "🏆 Huduma Zetu",
        "btn_referral": "🎁 Alika & Pata",
        "btn_stories": "⭐ Hadithi za Mafanikio",
        "btn_language": "🌍 Lugha",
        "btn_spin": "🎰 Spin ya Bahati — Jaribu Bahati Yako!",
        "spin_wait": "⏳ Umeshaspinni leo! Rudi baada ya masaa {hours}h {mins}m 🕐",
        "spin_spinning": "🎰 Inazunguka...",
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
        "referral_msg": "🎁 *KIUNGO CHAKO CHA RUFAA*\n\nKiungo chako:\nhttps://t.me/{bot}?start=ref{uid}\n\nRufaa zako: {count}/{min}\n{bar}\n\nAlika {needed} zaidi kufungua zawadi!\n{leaderboard}",
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
    ])

def main_menu(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(ui("btn_services", lang), callback_data="menu_services")],
        [InlineKeyboardButton(ui("btn_spin", lang), callback_data="do_spin")],
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

    name = escape_md(user.full_name)
    username = escape_md(user.username or "NA")

    btns = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user.id}"),
        InlineKeyboardButton("❌ Decline", callback_data=f"decline_{user.id}"),
    ]])
    for aid in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=aid,
                text=f"📨 *New Join Request*\n\n👤 {name}\n🔗 @{username}\n🆔 `{user.id}`\n📢 {chat.title}\n🕐 {now}",
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
    lang = get_lang(context, user.id)
    register_user(user, referred_by=referred_by, lang=lang)

    if new_user:
        await notify_new_user(context, user)
        if referred_by:
            ref_count = get_referral_count(referred_by)
            if ref_count >= REFERRAL_MIN:
                ref_info = get_user_info(referred_by)
                ref_name = escape_md(ref_info['name'])
                for aid in ADMIN_IDS:
                    try:
                        await context.bot.send_message(
                            chat_id=aid,
                            text=f"🏆 *REFERRAL REWARD!*\n\n👤 {ref_name} reached {ref_count} referrals!\n🎁 Give them a reward!",
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
        name=escape_md(user.first_name), urgency=urgency, business=BUSINESS_NAME)

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

        urgency = get_urgency(new_lang)
        welcome_text = ui("welcome", new_lang).format(
            name=escape_md(user.first_name), urgency=urgency, business=BUSINESS_NAME)
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
                name=escape_md(user.first_name), urgency=urgency, business=BUSINESS_NAME)
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
            name=escape_md(user.first_name), urgency=urgency, business=BUSINESS_NAME)
        msg = await send_protected_photo(
            context, cid, WELCOME_IMAGE,
            f"✅ Got it!\n\n{welcome_text}", main_menu(lang))
        context.user_data["last_bot_msg_id"] = msg.message_id
        track_msg(cid, msg.message_id)
        schedule_comeback(context, cid, user.first_name, lang)
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
        urgency = get_urgency(lang)
        welcome_text = ui("welcome", lang).format(
            name=escape_md(user.first_name), urgency=urgency, business=BUSINESS_NAME)
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
        urgency = get_urgency(lang)
        welcome_text = ui("welcome", lang).format(
            name=escape_md(user.first_name), urgency=urgency, business=BUSINESS_NAME)
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
            context, cid, img, random.choice(replies), 
