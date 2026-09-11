import os
import random

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = os.getenv("BOT_TOKEN")

# Games currently running in memory
games = {}

# Overall player statistics
stats = {}


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👑 *Raja Rani Police Chor* 👑\n\n"
        "🎮 Welcome to the game!\n\n"
        "Use /startgame in a group to create a game.",
        parse_mode="Markdown",
    )


# =========================
# START GAME
# =========================

async def startgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text(
            "❌ Please use /startgame inside a Telegram group."
        )
        return

    chat_id = update.effective_chat.id

    if chat_id in games and not games[chat_id]["finished"]:
        await update.message.reply_text(
            "⚠️ A game is already running in this group!"
        )
        return

    keyboard = [
        [
            InlineKeyboardButton("5 Players", callback_data="players_5"),
            InlineKeyboardButton("6 Players", callback_data="players_6"),
        ],
        [
            InlineKeyboardButton("7 Players", callback_data="players_7"),
            InlineKeyboardButton("8 Players", callback_data="players_8"),
        ],
        [
            InlineKeyboardButton("9 Players", callback_data="players_9"),
            InlineKeyboardButton("10 Players", callback_data="players_10"),
        ],
    ]

    await update.message.reply_text(
        "👑 *RAJA RANI POLICE CHOR* 👑\n\n"
        "👥 Select number of players:\n\n"
        "Minimum: 5\n"
        "Maximum: 10",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


# =========================
# PLAYER COUNT
# =========================

async def choose_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    player_count = int(query.data.split("_")[1])

    creator = query.from_user

    games[chat_id] = {
        "creator_id": creator.id,
        "creator_name": creator.full_name,
        "max_players": player_count,
        "players": [],
        "started": False,
        "finished": False,
        "roles": {},
        "police": None,
        "chor": None,
        "guessed": False,
        "scores_awarded": False,
    }

    keyboard = [
        [
            InlineKeyboardButton(
                "🎮 JOIN GAME",
                callback_data="join_game"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ CANCEL GAME",
                callback_data="cancel_game"
            )
        ],
    ]

    await query.edit_message_text(
        f"🎮 *GAME LOBBY CREATED!*\n\n"
        f"👤 Host: {creator.full_name}\n"
        f"👥 Selected players: {player_count}\n"
        f"✅ Joined: 0/{player_count}\n\n"
        f"👇 Press JOIN GAME to participate.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


# =========================
# JOIN GAME
# =========================

async def join_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    chat_id = query.message.chat_id

    if chat_id not in games:
        await query.answer(
            "❌ No active game!",
            show_alert=True
        )
        return

    game = games[chat_id]

    if game["started"]:
        await query.answer(
            "❌ Game already started!",
            show_alert=True
        )
        return

    if any(p["id"] == user.id for p in game["players"]):
        await query.answer(
            "😂 You already joined!",
            show_alert=True
        )
        return

    if len(game["players"]) >= game["max_players"]:
        await query.answer(
            "❌ Game is full!",
            show_alert=True
        )
        return

    game["players"].append({
        "id": user.id,
        "name": user.full_name,
        "username": user.username,
    })

    current = len(game["players"])
    maximum = game["max_players"]

    text = (
        "👑 *RAJA RANI POLICE CHOR* 👑\n\n"
        f"👥 Players: {current}/{maximum}\n\n"
    )

    for i, player in enumerate(game["players"], 1):
        text += f"{i}. {player['name']}\n"

    if current >= maximum:
        game["started"] = True

        await query.edit_message_text(
            text +
            "\n🔥 *ALL PLAYERS JOINED!*\n"
            "🎲 Roles are being assigned...\n"
            "📩 Check your DM!",
            parse_mode="Markdown",
        )

        await assign_roles(chat_id, context)

    else:
        keyboard = [
            [
                InlineKeyboardButton(
                    "🎮 JOIN GAME",
                    callback_data="join_game"
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ CANCEL GAME",
                    callback_data="cancel_game"
                )
            ],
        ]

        await query.edit_message_text(
            text +
            "\n👇 Press JOIN GAME to participate.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )


# =========================
# CANCEL GAME
# =========================

async def cancel_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    user_id = query.from_user.id

    if chat_id not in games:
        await query.edit_message_text(
            "❌ There is no active game."
        )
        return

    game = games[chat_id]

    # Only creator can cancel
    if user_id != game["creator_id"]:
        await query.answer(
            "❌ Only the game creator can cancel the game!",
            show_alert=True
        )
        return

    if game["started"]:
        await query.answer(
            "❌ Game has already started!",
            show_alert=True
        )
        return

    del games[chat_id]

    await query.edit_message_text(
        "❌ *GAME CANCELLED!*\n\n"
        "The game lobby has been cancelled by the creator.",
        parse_mode="Markdown",
    )


# =========================
# ROLE ASSIGNMENT
# =========================

async def assign_roles(chat_id, context):
    game = games[chat_id]

    players = game["players"].copy()
    random.shuffle(players)

    role_names = [
        "👑 Raja",
        "👸 Rani",
        "🧑‍💼 Mantri",
        "👮 Police",
        "🕵️ Chor",
    ]

    for i, player in enumerate(players):
        if i < 5:
            role = role_names[i]
        else:
            role = "👥 Janta"

        game["roles"][player["id"]] = role

        if role == "👮 Police":
            game["police"] = player["id"]

        if role == "🕵️ Chor":
            game["chor"] = player["id"]

        # Initialize stats
        if player["id"] not in stats:
            stats[player["id"]] = {
                "name": player["name"],
                "games": 0,
                "raja": 0,
                "rani": 0,
                "mantri": 0,
                "police": 0,
                "chor": 0,
                "janta": 0,
                "caught": 0,
                "escaped": 0,
                "points": 0,
            }

        stats[player["id"]]["games"] += 1

        role_key = {
            "👑 Raja": "raja",
            "👸 Rani": "rani",
            "🧑‍💼 Mantri": "mantri",
            "👮 Police": "police",
            "🕵️ Chor": "chor",
            "👥 Janta": "janta",
        }[role]

        stats[player["id"]][role_key] += 1

        # Send role privately
        try:
            await context.bot.send_message(
                chat_id=player["id"],
                text=(
                    "🎭 *YOUR RRPC ROLE*\n\n"
                    f"Your role is: *{role}*\n\n"
                    "🤫 Keep your role secret!"
                ),
                parse_mode="Markdown",
            )
        except Exception:
            pass

    await announce_roles(chat_id, context)


# =========================
# GROUP ANNOUNCEMENT
# =========================

async def announce_roles(chat_id, context):
    game = games[chat_id]

    police = next(
        p for p in game["players"]
        if p["id"] == game["police"]
    )

    raja = next(
        p for p in game["players"]
        if game["roles"][p["id"]] == "👑 Raja"
    )

    text = (
        "🚨 *GAME STARTED!* 🚨\n\n"
        f"👑 Raja: *{raja['name']}*\n"
        f"👮 Police: *{police['name']}*\n\n"
        "🤫 Other roles are SECRET.\n\n"
        "👮 *Police, find the Chor!*\n\n"
        "Use:\n"
        "`/chor NUMBER`\n\n"
        "Example: `/chor 3`"
    )

    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode="Markdown",
    )

    player_text = "🔢 *POLICE TARGET LIST*\n\n"

    for i, player in enumerate(game["players"], 1):
        player_text += f"{i}. {player['name']}\n"

    await context.bot.send_message(
        chat_id=chat_id,
        text=player_text,
        parse_mode="Markdown",
    )


# =========================
# POLICE GUESS
# =========================

async def chor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text(
            "❌ Use /chor inside the game group."
        )
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if chat_id not in games:
        await update.message.reply_text(
            "❌ No active game."
        )
        return

    game = games[chat_id]

    if not game["started"] or game["finished"]:
        await update.message.reply_text(
            "❌ No active guessing round."
        )
        return

    if user_id != game["police"]:
        await update.message.reply_text(
            "❌ Only 👮 Police can use /chor."
        )
        return

    if game["guessed"]:
        await update.message.reply_text(
            "⚠️ Police has already made the guess."
        )
        return

    if not context.args:
        await update.message.reply_text(
            "❌ Use:\n/chor NUMBER\n\nExample:\n/chor 3"
        )
        return

    try:
        number = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Please enter a valid player number."
        )
        return

    if number < 1 or number > len(game["players"]):
        await update.message.reply_text(
            f"❌ Choose a number between 1 and {len(game['players'])}."
        )
        return

    selected_player = game["players"][number - 1]

    if selected_player["id"] == game["police"]:
        await update.message.reply_text(
            "😂 Bro, you are Police yourself!\n"
            "Choose another player."
        )
        return

    game["guessed"] = True

    if selected_player["id"] == game["chor"]:
        await correct_guess(
            chat_id,
            selected_player,
            context,
        )
    else:
        await wrong_guess(
            chat_id,
            selected_player,
            context,
        )


# =========================
# CORRECT GUESS
# =========================

async def correct_guess(chat_id, selected_player, context):
    game = games[chat_id]

    game["finished"] = True

    police_id = game["police"]
    chor_id = game["chor"]

    stats[police_id]["points"] += 2000
    stats[chor_id]["caught"] += 1

    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            "🎯 *POLICE CAUGHT THE CHOR!*\n\n"
            f"👮 Police: *{get_name(game, police_id)}*\n"
            f"🕵️ Chor: *{selected_player['name']}*\n"
            f"🆔 Chor ID: `{chor_id}`\n\n"
            "🤣 *TU KATTU CHOR HAI!* 🤣\n\n"
            "👮 Police gets +2000 points.\n"
            "🕵️ Chor gets 0 points."
        ),
        parse_mode="Markdown",
    )

    await reveal_all(chat_id, context)


# =========================
# WRONG GUESS
# =========================

async def wrong_guess(chat_id, selected_player, context):
    game = games[chat_id]

    game["finished"] = True

    police_id = game["police"]
    chor_id = game["chor"]

    stats[chor_id]["points"] += 2000
    stats[chor_id]["escaped"] += 1

    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            "❌ *POLICE GUESSED WRONG!*\n\n"
            f"👮 Police chose: *{selected_player['name']}*\n\n"
            "🤣 *Abe Police ke nam me nikamma nithalla h police ke nam pe dhabba h tu, "
            "kya police banega re apna kattu nai bacha sakta!* 🤣\n\n"
            f"🕵️ Actual Chor: *{get_name(game, chor_id)}*\n"
            f"🆔 Chor ID: `{chor_name}`\n\n"
            "🕵️ Chor gets +2000 points!"
        ),
        parse_mode="Markdown",
    )

    await reveal_all(chat_id, context)


# =========================
# REVEAL ALL ROLES
# =========================

async def reveal_all(chat_id, context):
    game = games[chat_id]

    text = "🎭 *ALL ROLES REVEALED*\n\n"

    points = {
        "👑 Raja": 5000,
        "👸 Rani": 4000,
        "🧑‍💼 Mantri": 3000,
        "👮 Police": 0,
        "🕵️ Chor": 0,
        "👥 Janta": 1000,
    }

    for i, player in enumerate(game["players"], 1):
        role = game["roles"][player["id"]]

        text += (
            f"{i}. {player['name']}\n"
            f"   {role}\n"
        )

        # Award base role points only once
        if not game["scores_awarded"]:
            if role in points:
                stats[player["id"]]["points"] += points[role]

    game["scores_awarded"] = True

    text += "\n💰 *SCORES UPDATED!*"

    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode="Markdown",
    )


# =========================
# STATS
# =========================

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in stats:
        await update.message.reply_text(
            "📊 No stats yet. Play a game first!"
        )
        return

    s = stats[user_id]

    await update.message.reply_text(
        "📊 *YOUR RRPC STATS*\n\n"
        f"🎮 Games: {s['games']}\n\n"
        f"👑 Raja: {s['raja']}\n"
        f"👸 Rani: {s['rani']}\n"
        f"🧑‍💼 Mantri: {s['mantri']}\n"
        f"👮 Police: {s['police']}\n"
        f"🕵️ Chor: {s['chor']}\n"
        f"👥 Janta: {s['janta']}\n\n"
        f"🎯 Chor caught: {s['caught']}\n"
        f"🏃 Chor escaped: {s['escaped']}\n\n"
        f"💰 Total points: {s['points']}",
        parse_mode="Markdown",
    )


# =========================
# HELPERS
# =========================

def get_name(game, user_id):
    for player in game["players"]:
        if player["id"] == user_id:
            return player["name"]

    return "Unknown"


# =========================
# MAIN
# =========================

def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("startgame", startgame))
    app.add_handler(CommandHandler("chor", chor))
    app.add_handler(CommandHandler("stats", show_stats))

    app.add_handler(
        CallbackQueryHandler(
            choose_players,
            pattern=r"^players_(?:[5-9]|10)$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            join_game,
            pattern=r"^join_game$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            cancel_game,
            pattern=r"^cancel_game$"
        )
    )

    print("🤖 RRPC Bot started...")

    app.run_polling()


if __name__ == "__main__":
    main()