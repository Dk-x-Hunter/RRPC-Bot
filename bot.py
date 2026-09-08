import os
import random

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = os.getenv("BOT_TOKEN")

# Active games
games = {}


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👑 <b>RAJA RANI POLICE CHOR</b> 👑\n\n"
        "🎮 Welcome!\n\n"
        "Use /startgame inside a group to create a game.\n\n"
        "⚠️ If you are playing, first press /start in my private chat "
        "so I can send you your secret role.",
        parse_mode="HTML",
    )


# =========================
# START GAME
# =========================

async def startgame(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_chat.type == "private":
        await update.message.reply_text(
            "❌ Start the game inside a group."
        )
        return

    chat_id = update.effective_chat.id

    if chat_id in games and not games[chat_id].get("finished", False):
        await update.message.reply_text(
            "⚠️ A game is already active in this group.\n\n"
            "Finish the current game before starting another one."
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
        "🎮 <b>RAJA RANI POLICE CHOR</b>\n\n"
        "👥 Choose how many players will play:\n\n"
        "Minimum: <b>5</b>\n"
        "Maximum: <b>10</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )


# =========================
# CHOOSE PLAYER COUNT
# =========================

async def choose_players(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    player_count = int(query.data.split("_")[1])

    games[chat_id] = {
        "max_players": player_count,
        "players": [],
        "started": False,
        "finished": False,
        "roles": {},
        "scores": {},
        "police_id": None,
        "chor_id": None,
    }

    keyboard = [
        [
            InlineKeyboardButton(
                "🎮 JOIN GAME",
                callback_data="join_game"
            )
        ]
    ]

    await query.edit_message_text(
        "🎮 <b>GAME LOBBY CREATED!</b>\n\n"
        f"👥 Players needed: <b>{player_count}</b>\n"
        f"✅ Joined: <b>0/{player_count}</b>\n\n"
        "👇 Press the button below to join.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )


# =========================
# JOIN GAME
# =========================

async def join_game(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    user = query.from_user

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
    })

    current = len(game["players"])
    maximum = game["max_players"]

    text = (
        "🎮 <b>RAJA RANI POLICE CHOR</b>\n\n"
        f"👥 Players needed: <b>{maximum}</b>\n"
        f"✅ Joined: <b>{current}/{maximum}</b>\n\n"
    )

    for i, player in enumerate(game["players"], 1):
        text += f"{i}. {player['name']}\n"

    # =========================
    # GAME FULL
    # =========================

    if current >= maximum:

        game["started"] = True

        await query.edit_message_text(
            text +
            "\n🔥 <b>ALL PLAYERS JOINED!</b>\n"
            "🎲 Assigning secret roles...",
            parse_mode="HTML",
        )

        await assign_roles(
            chat_id,
            context
        )

    else:

        keyboard = [
            [
                InlineKeyboardButton(
                    "🎮 JOIN GAME",
                    callback_data="join_game"
                )
            ]
        ]

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )


# =========================
# ASSIGN ROLES
# =========================

async def assign_roles(chat_id, context):

    game = games[chat_id]
    players = game["players"]

    shuffled = players.copy()
    random.shuffle(shuffled)

    # First four special roles
    special_roles = [
        "Raja 👑",
        "Rani 👸",
        "Police 👮",
        "Chor 🥷",
    ]

    roles = {}

    for i, player in enumerate(shuffled):

        if i < 4:
            role = special_roles[i]
        else:
            role = "Janta 👥"

        roles[player["id"]] = role

        game["scores"][player["id"]] = 0

    game["roles"] = roles

    # Find Police and Chor
    for player in players:

        role = roles[player["id"]]

        if role.startswith("Police"):
            game["police_id"] = player["id"]

        if role.startswith("Chor"):
            game["chor_id"] = player["id"]

    # Send private roles
    failed = []

    for player in players:

        role = roles[player["id"]]

        try:

            await context.bot.send_message(
                chat_id=player["id"],
                text=(
                    "🎭 <b>YOUR SECRET ROLE</b>\n\n"
                    f"Your role is:\n\n"
                    f"<b>{role}</b>\n\n"
                    "🤫 Don't tell anyone your role!"
                ),
                parse_mode="HTML",
            )

        except Exception:
            failed.append(player["name"])

    # Game announcement
    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            "🔥 <b>GAME STARTED!</b> 🔥\n\n"
            "🎭 All roles have been assigned.\n"
            "📩 Check your private chat with the bot.\n\n"
            "👮 <b>Police</b> must identify the Chor.\n"
            "🥷 <b>Chor</b> must avoid being caught.\n\n"
            "⏳ Police will now make the guess."
        ),
        parse_mode="HTML",
    )

    # Tell players who didn't allow private messages
    if failed:

        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "⚠️ <b>IMPORTANT</b>\n\n"
                "Some players haven't started the bot in private chat.\n\n"
                "Those players may not have received their role.\n\n"
                "Ask them to open the bot and press /start."
            ),
            parse_mode="HTML",
        )

    # Give Police the guess buttons
    await send_police_guess(chat_id, context)


# =========================
# POLICE GUESS
# =========================

async def send_police_guess(chat_id, context):

    game = games[chat_id]

    police_id = game["police_id"]

    if not police_id:
        return

    buttons = []

    for player in game["players"]:

        if player["id"] == police_id:
            continue

        buttons.append(
            [
                InlineKeyboardButton(
                    f"🔍 {player['name']}",
                    callback_data=f"guess_{player['id']}"
                )
            ]
        )

    try:

        await context.bot.send_message(
            chat_id=police_id,
            text=(
                "👮 <b>YOU ARE THE POLICE</b>\n\n"
                "🥷 Find the Chor!\n\n"
                "👇 Choose the player you think is the Chor."
            ),
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="HTML",
        )

    except Exception:

        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "⚠️ Police could not receive the private message.\n\n"
                "Police must open the bot and press /start."
            ),
            parse_mode="HTML",
        )


# =========================
# POLICE GUESS HANDLER
# =========================

async def police_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    police_id = query.from_user.id

    # Find the game containing this police
    chat_id = None
    game = None

    for gid, g in games.items():

        if (
            g.get("police_id") == police_id
            and g.get("started")
            and not g.get("finished")
        ):
            chat_id = gid
            game = g
            break

    if not game:

        await query.answer(
            "❌ No active police game.",
            show_alert=True
        )
        return

    guessed_id = int(query.data.split("_")[1])

    # Prevent multiple guesses
    if game.get("police_guessed", False):

        await query.answer(
            "❌ You already made your guess!",
            show_alert=True
        )
        return

    game["police_guessed"] = True

    chor_id = game["chor_id"]

    guessed_player = None

    for player in game["players"]:

        if player["id"] == guessed_id:
            guessed_player = player
            break

    if not guessed_player:
        return

    # =========================
    # CORRECT
    # =========================

    if guessed_id == chor_id:

        game["scores"][police_id] += 500

        result = (
            "🎯 <b>POLICE CAUGHT THE CHOR!</b>\n\n"
            f"👮 Police: <b>{query.from_user.full_name}</b>\n"
            f"🥷 Chor: <b>{guessed_player['name']}</b>\n\n"
            "🏆 Police wins this round!\n"
            "💰 Police gets <b>+500 points</b>."
        )

    # =========================
    # WRONG
    # =========================

    else:

        game["scores"][chor_id] += 500

        chor_name = "Unknown"

        for player in game["players"]:

            if player["id"] == chor_id:
                chor_name = player["name"]
                break

        result = (
            "❌ <b>POLICE GUESSED WRONG!</b>\n\n"
            f"👮 Police guessed: <b>{guessed_player['name']}</b>\n"
            f"🥷 Actual Chor: <b>{chor_name}</b>\n\n"
            "🥷 Chor escapes!\n"
            "💰 Chor gets <b>+500 points</b>."
        )

    game["finished"] = True

    await context.bot.send_message(
        chat_id=chat_id,
        text=result,
        parse_mode="HTML",
    )

    await show_scores(chat_id, context)


# =========================
# SHOW SCORES
# =========================

async def show_scores(chat_id, context):

    game = games[chat_id]

    text = (
        "🏆 <b>ROUND RESULT</b>\n\n"
        "📊 <b>SCORES</b>\n\n"
    )

    sorted_players = sorted(
        game["players"],
        key=lambda p: game["scores"].get(p["id"], 0),
        reverse=True,
    )

    for i, player in enumerate(sorted_players, 1):

        score = game["scores"].get(player["id"], 0)

        role = game["roles"].get(
            player["id"],
            "Unknown"
        )

        text += (
            f"{i}. {player['name']}\n"
            f"   🎭 {role}\n"
            f"   💰 {score} points\n\n"
        )

    text += (
        "🎮 <b>Round finished!</b>\n\n"
        "Use /startgame to create a new game."
    )

    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode="HTML",
    )


# =========================
# MAIN
# =========================

def main():

    if not TOKEN:
        raise RuntimeError(
            "BOT_TOKEN is not set"
        )

    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("startgame", startgame)
    )

    # Player count
    app.add_handler(
        CallbackQueryHandler(
            choose_players,
            pattern=r"^players_(5|6|7|8|9|10)$"
        )
    )

    # Join game
    app.add_handler(
        CallbackQueryHandler(
            join_game,
            pattern=r"^join_game$"
        )
    )

    # Police guess
    app.add_handler(
        CallbackQueryHandler(
            police_guess,
            pattern=r"^guess_\d+$"
        )
    )

    print("🤖 RRPC Bot started...")

    app.run_polling()


if __name__ == "__main__":
    main()