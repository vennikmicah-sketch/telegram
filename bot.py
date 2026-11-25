import os
import json
import time
import asyncio
import aiohttp
from pathlib import Path
from telebot.async_telebot import AsyncTeleBot
from telebot import types

TOKEN = os.getenv("BOT_TOKEN") or "9106886265:AAHNEYxZoGmcfTc059hOSGFLJNTCoyQyF64"
if not TOKEN:
    raise RuntimeError("BOT_TOKEN missing")

bot = AsyncTeleBot(TOKEN)
DATA_FILE = Path("data.json")

# ── persistence ──────────────────────────────────────────────────────────────

def load_data():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"admins": [], "stats": {"checked": 0, "hits": 0, "fails": 0}}


def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)


data = load_data()

# ── service list (100+) ──────────────────────────────────────────────────────

SERVICES = {
    # Streaming
    "netflix": {"name": "Netflix", "type": "account", "emoji": "🎬"},
    "disney": {"name": "Disney+", "type": "account", "emoji": "🏰"},
    "hulu": {"name": "Hulu", "type": "account", "emoji": "🟢"},
    "hbo": {"name": "HBO Max", "type": "account", "emoji": "🟣"},
    "prime": {"name": "Amazon Prime", "type": "account", "emoji": "📦"},
    "paramount": {"name": "Paramount+", "type": "account", "emoji": "🔵"},
    "peacock": {"name": "Peacock", "type": "account", "emoji": "🦚"},
    "appletv": {"name": "Apple TV+", "type": "account", "emoji": "🍎"},
    "crunchyroll": {"name": "Crunchyroll", "type": "account", "emoji": "🍙"},
    "funimation": {"name": "Funimation", "type": "account", "emoji": "🍥"},
    "youtube": {"name": "YouTube Premium", "type": "account", "emoji": "▶️"},
    "twitch": {"name": "Twitch", "type": "account", "emoji": "💜"},
    # Music
    "spotify": {"name": "Spotify", "type": "account", "emoji": "🎧"},
    "deezer": {"name": "Deezer", "type": "account", "emoji": "🎵"},
    "applemusic": {"name": "Apple Music", "type": "account", "emoji": "🎶"},
    "tidal": {"name": "Tidal", "type": "account", "emoji": "🌊"},
    "soundcloud": {"name": "SoundCloud", "type": "account", "emoji": "☁️"},
    "amazonmusic": {"name": "Amazon Music", "type": "account", "emoji": "🎼"},
    # Gaming
    "steam": {"name": "Steam", "type": "account", "emoji": "🎮"},
    "epic": {"name": "Epic Games", "type": "account", "emoji": "🕹️"},
    "xbox": {"name": "Xbox / Game Pass", "type": "account", "emoji": "❎"},
    "playstation": {"name": "PlayStation", "type": "account", "emoji": "🅿"},
    "nintendo": {"name": "Nintendo", "type": "account", "emoji": "🔴"},
    "riot": {"name": "Riot Games", "type": "account", "emoji": "⚔️"},
    "ubisoft": {"name": "Ubisoft", "type": "account", "emoji": "🎯"},
    "ea": {"name": "EA / Origin", "type": "account", "emoji": "🅰️"},
    "rockstar": {"name": "Rockstar", "type": "account", "emoji": "⭐"},
    "battlenet": {"name": "Battle.net", "type": "account", "emoji": "❄️"},
    # Social / Mail
    "instagram": {"name": "Instagram", "type": "account", "emoji": "📸"},
    "twitter": {"name": "Twitter / X", "type": "account", "emoji": "🐦"},
    "facebook": {"name": "Facebook", "type": "account", "emoji": "📘"},
    "tiktok": {"name": "TikTok", "type": "account", "emoji": "🎵"},
    "snapchat": {"name": "Snapchat", "type": "account", "emoji": "👻"},
    "reddit": {"name": "Reddit", "type": "account", "emoji": "👽"},
    "discord": {"name": "Discord", "type": "account", "emoji": "💬"},
    "telegram": {"name": "Telegram", "type": "account", "emoji": "✈️"},
    "gmail": {"name": "Gmail", "type": "account", "emoji": "📧"},
    "outlook": {"name": "Outlook", "type": "account", "emoji": "📨"},
    "yahoo": {"name": "Yahoo Mail", "type": "account", "emoji": "📬"},
    "proton": {"name": "ProtonMail", "type": "account", "emoji": "🔒"},
    # Shopping / Food
    "amazon": {"name": "Amazon", "type": "account", "emoji": "📦"},
    "ebay": {"name": "eBay", "type": "account", "emoji": "🛒"},
    "walmart": {"name": "Walmart", "type": "account", "emoji": "🏪"},
    "target": {"name": "Target", "type": "account", "emoji": "🎯"},
    "uber": {"name": "Uber", "type": "account", "emoji": "🚗"},
    "ubereats": {"name": "Uber Eats", "type": "account", "emoji": "🍔"},
    "doordash": {"name": "DoorDash", "type": "account", "emoji": "🚪"},
    "grubhub": {"name": "Grubhub", "type": "account", "emoji": "🍕"},
    "instacart": {"name": "Instacart", "type": "account", "emoji": "🥦"},
    # VPN / Tools
    "nordvpn": {"name": "NordVPN", "type": "account", "emoji": "🛡️"},
    "expressvpn": {"name": "ExpressVPN", "type": "account", "emoji": "🔐"},
    "surfshark": {"name": "Surfshark", "type": "account", "emoji": "🦈"},
    "cyberghost": {"name": "CyberGhost", "type": "account", "emoji": "👻"},
    "protonvpn": {"name": "ProtonVPN", "type": "account", "emoji": "🔑"},
    "canva": {"name": "Canva", "type": "account", "emoji": "🎨"},
    "adobe": {"name": "Adobe", "type": "account", "emoji": "🅰️"},
    "microsoft": {"name": "Microsoft 365", "type": "account", "emoji": "🪟"},
    "dropbox": {"name": "Dropbox", "type": "account", "emoji": "📁"},
    "notion": {"name": "Notion", "type": "account", "emoji": "📝"},
    # Extra popular
    "onlyfans": {"name": "OnlyFans", "type": "account", "emoji": "💙"},
    "patreon": {"name": "Patreon", "type": "account", "emoji": "🧡"},
    "chatgpt": {"name": "ChatGPT / OpenAI", "type": "account", "emoji": "🤖"},
    "claude": {"name": "Claude / Anthropic", "type": "account", "emoji": "🧠"},
    "midjourney": {"name": "Midjourney", "type": "account", "emoji": "🖼️"},
    "github": {"name": "GitHub", "type": "account", "emoji": "🐙"},
    "gitlab": {"name": "GitLab", "type": "account", "emoji": "🦊"},
    "linkedin": {"name": "LinkedIn", "type": "account", "emoji": "💼"},
    "pinterest": {"name": "Pinterest", "type": "account", "emoji": "📌"},
    "tumblr": {"name": "Tumblr", "type": "account", "emoji": "📘"},
    "vk": {"name": "VK", "type": "account", "emoji": "🔵"},
    "okru": {"name": "OK.ru", "type": "account", "emoji": "🟠"},
    "roblox": {"name": "Roblox", "type": "account", "emoji": "🧱"},
    "minecraft": {"name": "Minecraft", "type": "account", "emoji": "⛏️"},
    "fortnite": {"name": "Fortnite", "type": "account", "emoji": "🔫"},
    "valorant": {"name": "Valorant", "type": "account", "emoji": "🎯"},
    "league": {"name": "League of Legends", "type": "account", "emoji": "⚔️"},
    "genshin": {"name": "Genshin Impact", "type": "account", "emoji": "⚡"},
    "honkai": {"name": "Honkai Star Rail", "type": "account", "emoji": "🚂"},
    "bilibili": {"name": "Bilibili", "type": "account", "emoji": "📺"},
    "iqiyi": {"name": "iQiyi", "type": "account", "emoji": "▶️"},
    "youku": {"name": "Youku", "type": "account", "emoji": "📹"},
    "wetv": {"name": "WeTV", "type": "account", "emoji": "📱"},
    "viu": {"name": "Viu", "type": "account", "emoji": "👀"},
    "hotstar": {"name": "Disney+ Hotstar", "type": "account", "emoji": "⭐"},
    "zee5": {"name": "ZEE5", "type": "account", "emoji": "🟣"},
    "sonyliv": {"name": "SonyLIV", "type": "account", "emoji": "📺"},
    "voot": {"name": "Voot", "type": "account", "emoji": "🟠"},
    "altbalaji": {"name": "ALTBalaji", "type": "account", "emoji": "🎬"},
    "mxplayer": {"name": "MX Player", "type": "account", "emoji": "▶️"},
    "gaana": {"name": "Gaana", "type": "account", "emoji": "🎵"},
    "jiosaavn": {"name": "JioSaavn", "type": "account", "emoji": "🎶"},
    "wynk": {"name": "Wynk Music", "type": "account", "emoji": "🎧"},
    "hungama": {"name": "Hungama", "type": "account", "emoji": "🎤"},
    "careem": {"name": "Careem", "type": "account", "emoji": "🚕"},
    "talabat": {"name": "Talabat", "type": "account", "emoji": "🍔"},
    "noon": {"name": "Noon", "type": "account", "emoji": "🛒"},
    "jarir": {"name": "Jarir", "type": "account", "emoji": "📚"},
    "extra": {"name": "Extra", "type": "account", "emoji": "🏪"},
    "namshi": {"name": "Namshi", "type": "account", "emoji": "👗"},
    "shein": {"name": "SHEIN", "type": "account", "emoji": "👚"},
    "aliexpress": {"name": "AliExpress", "type": "account", "emoji": "📦"},
    "wish": {"name": "Wish", "type": "account", "emoji": "🎁"},
    "etsy": {"name": "Etsy", "type": "account", "emoji": "🧶"},
    "shopify": {"name": "Shopify", "type": "account", "emoji": "🛍️"},
    "stripe": {"name": "Stripe", "type": "account", "emoji": "💳"},
    "paypal": {"name": "PayPal", "type": "account", "emoji": "💰"},
    "venmo": {"name": "Venmo", "type": "account", "emoji": "💸"},
    "cashapp": {"name": "Cash App", "type": "account", "emoji": "💵"},
    "revolut": {"name": "Revolut", "type": "account", "emoji": "🏦"},
    "wise": {"name": "Wise", "type": "account", "emoji": "🌍"},
    "binance": {"name": "Binance", "type": "account", "emoji": "🟡"},
    "coinbase": {"name": "Coinbase", "type": "account", "emoji": "🔵"},
    "crypto": {"name": "Crypto.com", "type": "account", "emoji": "🪙"},
    "metamask": {"name": "MetaMask", "type": "account", "emoji": "🦊"},
}

# Cookie-capable services (subset that commonly use cookies)
COOKIE_SERVICES = {
    "netflix", "disney", "hulu", "hbo", "prime", "spotify", "crunchyroll",
    "instagram", "twitter", "facebook", "tiktok", "discord", "steam",
    "epic", "nordvpn", "canva", "adobe", "chatgpt", "github"
}

# ── simple check simulation (replace with real APIs later) ───────────────────

async def check_account(service: str, combo: str, mode: str = "account") -> dict:
    """
    Placeholder checker. Replace the body with real endpoints.
    Returns: {"status": "hit"|"fail"|"custom", "info": str}
    """
    await asyncio.sleep(0.15)  # rate-limit friendly delay

    if ":" not in combo and mode == "account":
        return {"status": "fail", "info": "Invalid format (need email:pass)"}

    # Demo logic — replace with real requests
    # For now random-ish based on string length so it feels alive
    h = hash(combo + service) % 100
    if h < 18:
        return {"status": "hit", "info": f"{SERVICES[service]['name']} · valid"}
    elif h < 25:
        return {"status": "custom", "info": "2FA / locked / need verify"}
    else:
        return {"status": "fail", "info": "Invalid credentials"}


async def check_cookie(service: str, cookie: str) -> dict:
    await asyncio.sleep(0.15)
    if len(cookie) < 20:
        return {"status": "fail", "info": "Cookie too short"}
    h = hash(cookie + service) % 100
    if h < 22:
        return {"status": "hit", "info": f"{SERVICES[service]['name']} cookie · valid"}
    elif h < 30:
        return {"status": "custom", "info": "Expired / partial"}
    else:
        return {"status": "fail", "info": "Dead cookie"}


# ── user state ───────────────────────────────────────────────────────────────

user_state = {}  # user_id -> {"service": str, "mode": "account"|"cookie", "lines": []}


def main_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        types.KeyboardButton("🔍 Check Accounts"),
        types.KeyboardButton("🍪 Check Cookies"),
        types.KeyboardButton("📋 Services"),
        types.KeyboardButton("📊 Stats"),
        types.KeyboardButton("ℹ️ Help"),
    )
    return kb


def services_keyboard(page: int = 0, mode: str = "account"):
    keys = sorted(SERVICES.keys())
    if mode == "cookie":
        keys = [k for k in keys if k in COOKIE_SERVICES]
    per_page = 20
    start = page * per_page
    chunk = keys[start:start + per_page]
    kb = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for k in chunk:
        s = SERVICES[k]
        buttons.append(types.InlineKeyboardButton(
            f"{s['emoji']} {s['name']}",
            callback_data=f"svc:{mode}:{k}"
        ))
    kb.add(*buttons)
    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("⬅️ Prev", callback_data=f"page:{mode}:{page-1}"))
    if start + per_page < len(keys):
        nav.append(types.InlineKeyboardButton("Next ➡️", callback_data=f"page:{mode}:{page+1}"))
    if nav:
        kb.row(*nav)
    return kb


# ── handlers ─────────────────────────────────────────────────────────────────

@bot.message_handler(commands=["start", "help"])
async def cmd_start(message):
    text = (
        "🦅 *Multi-Service Account & Cookie Checker*\n\n"
        f"• *{len(SERVICES)}+* services loaded\n"
        "• Account mode (`email:pass`)\n"
        "• Cookie mode\n"
        "• Bulk check (send .txt or paste lines)\n\n"
        "Use the buttons below or type a service name."
    )
    await bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=main_keyboard())


@bot.message_handler(func=lambda m: m.text == "🔍 Check Accounts")
async def btn_check_accounts(message):
    user_state[message.from_user.id] = {"mode": "account"}
    await bot.send_message(
        message.chat.id,
        "Select a service (Account mode):",
        reply_markup=services_keyboard(0, "account")
    )


@bot.message_handler(func=lambda m: m.text == "🍪 Check Cookies")
async def btn_check_cookies(message):
    user_state[message.from_user.id] = {"mode": "cookie"}
    await bot.send_message(
        message.chat.id,
        "Select a service (Cookie mode):",
        reply_markup=services_keyboard(0, "cookie")
    )


@bot.message_handler(func=lambda m: m.text == "📋 Services")
async def btn_services(message):
    lines = [f"{v['emoji']} `{k}` — {v['name']}" for k, v in sorted(SERVICES.items())]
    # split to avoid message too long
    chunk = 40
    for i in range(0, len(lines), chunk):
        await bot.send_message(
            message.chat.id,
            "\n".join(lines[i:i+chunk]),
            parse_mode="Markdown"
        )


@bot.message_handler(func=lambda m: m.text == "📊 Stats")
async def btn_stats(message):
    s = data["stats"]
    text = (
        f"📊 *Stats*\n\n"
        f"Checked: `{s['checked']}`\n"
        f"Hits: `{s['hits']}`\n"
        f"Fails: `{s['fails']}`\n"
        f"Services: `{len(SERVICES)}`"
    )
    await bot.send_message(message.chat.id, text, parse_mode="Markdown")


@bot.message_handler(func=lambda m: m.text == "ℹ️ Help")
async def btn_help(message):
    text = (
        "*How to use*\n\n"
        "1. Tap *Check Accounts* or *Check Cookies*\n"
        "2. Pick a service\n"
        "3. Send combos (`email:pass` one per line) or a `.txt` file\n"
        "4. Bot returns hits / fails / custom\n\n"
        "Cookie mode: paste full cookie string or one cookie per line."
    )
    await bot.send_message(message.chat.id, text, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda c: c.data.startswith("page:"))
async def cb_page(call):
    _, mode, page = call.data.split(":")
    page = int(page)
    await bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.message_id,
        reply_markup=services_keyboard(page, mode)
    )
    await bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("svc:"))
async def cb_service(call):
    _, mode, key = call.data.split(":")
    if key not in SERVICES:
        await bot.answer_callback_query(call.id, "Unknown service")
        return
    user_state[call.from_user.id] = {"service": key, "mode": mode}
    s = SERVICES[key]
    await bot.answer_callback_query(call.id)
    await bot.send_message(
        call.message.chat.id,
        f"Selected: {s['emoji']} *{s['name']}* ({mode})\n\n"
        f"Now send combos (`email:pass`) or a `.txt` file.\n"
        f"One per line.",
        parse_mode="Markdown"
    )


@bot.message_handler(content_types=["document"])
async def handle_file(message):
    uid = message.from_user.id
    state = user_state.get(uid)
    if not state or "service" not in state:
        await bot.reply_to(message, "Pick a service first (Check Accounts / Check Cookies).")
        return

    doc = message.document
    if not doc.file_name.lower().endswith(".txt"):
        await bot.reply_to(message, "Only .txt files supported.")
        return

    file_info = await bot.get_file(doc.file_id)
    downloaded = await bot.download_file(file_info.file_path)
    text = downloaded.decode("utf-8", errors="ignore")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        await bot.reply_to(message, "File empty.")
        return

    await run_check(message, state["service"], state["mode"], lines)


@bot.message_handler(func=lambda m: True)
async def handle_text(message):
    uid = message.from_user.id
    state = user_state.get(uid)
    if not state or "service" not in state:
        # try treat as service name shortcut
        key = message.text.strip().lower().replace(" ", "").replace("+", "")
        if key in SERVICES:
            user_state[uid] = {"service": key, "mode": "account"}
            s = SERVICES[key]
            await bot.reply_to(
                message,
                f"Selected {s['emoji']} *{s['name']}*\nSend combos or .txt",
                parse_mode="Markdown"
            )
            return
        return

    lines = [ln.strip() for ln in message.text.splitlines() if ln.strip()]
    if not lines:
        return
    await run_check(message, state["service"], state["mode"], lines)


async def run_check(message, service: str, mode: str, lines: list):
    s = SERVICES[service]
    total = len(lines)
    status_msg = await bot.reply_to(
        message,
        f"⏳ Checking *{total}* against {s['emoji']} {s['name']}..."
    )

    hits, fails, customs = [], [], []
    for i, line in enumerate(lines, 1):
        if mode == "cookie":
            res = await check_cookie(service, line)
        else:
            res = await check_account(service, line, mode)

        data["stats"]["checked"] += 1
        if res["status"] == "hit":
            hits.append(f"`{line}` — {res['info']}")
            data["stats"]["hits"] += 1
        elif res["status"] == "custom":
            customs.append(f"`{line}` — {res['info']}")
        else:
            fails.append(f"`{line}` — {res['info']}")
            data["stats"]["fails"] += 1

        if i % 25 == 0:
            await bot.edit_message_text(
                f"⏳ {i}/{total} checked...",
                message.chat.id,
                status_msg.message_id
            )

    save_data(data)

    summary = (
        f"✅ *Done* — {s['emoji']} {s['name']}\n\n"
        f"Total: `{total}`\n"
        f"Hits: `{len(hits)}`\n"
        f"Custom: `{len(customs)}`\n"
        f"Fails: `{len(fails)}`"
    )
    await bot.edit_message_text(summary, message.chat.id, status_msg.message_id, parse_mode="Markdown")

    if hits:
        await send_chunked(message.chat.id, "🟢 *HITS*\n" + "\n".join(hits))
    if customs:
        await send_chunked(message.chat.id, "🟡 *CUSTOM*\n" + "\n".join(customs))
    # fails usually too noisy — skip or send only if few
    if fails and len(fails) <= 30:
        await send_chunked(message.chat.id, "🔴 *FAILS*\n" + "\n".join(fails))


async def send_chunked(chat_id, text, limit=3500):
    if len(text) <= limit:
        await bot.send_message(chat_id, text, parse_mode="Markdown")
        return
    lines = text.split("\n")
    buf = []
    size = 0
    for ln in lines:
        if size + len(ln) + 1 > limit:
            await bot.send_message(chat_id, "\n".join(buf), parse_mode="Markdown")
            buf = [ln]
            size = len(ln)
        else:
            buf.append(ln)
            size += len(ln) + 1
    if buf:
        await bot.send_message(chat_id, "\n".join(buf), parse_mode="Markdown")


# ── main ─────────────────────────────────────────────────────────────────────

async def main():
    print("Telegram Multi-Checker starting...")
    await bot.infinity_polling()


if __name__ == "__main__":
    asyncio.run(main())
