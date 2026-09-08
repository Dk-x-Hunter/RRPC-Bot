import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = os.getenv("BOT_TOKEN")

# Temporary game data
games = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👑 Raja Rani Police Chor 👑\n\n"
        "🎮 Welcome!\n"
        "Use /startgame to create a game."
    )


async def startgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text(
            "❌ Start the game inside a group."
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
        "🎮 *RAJA RANI POLICE CHOR*\n\n"
        "👥 Choose how many players will play:\n\n"
        "Minimum: 5\n"
        "Maximum: 10",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def choose_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    player_count = int(query.data.split("_")[1])

    games[chat_id] = {
        "max_players": player_count,
        "players": [],
        "started": False,
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
        f"🎮 *Game Lobby Created!*\n\n"
        f"👥 Players needed: {player_count}\n"
        f"✅ Joined: 0/{player_count}\n\n"
        f"👇 Press the button below to join!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


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

    # Prevent duplicate joining
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
        "🎮 *RAJA RANI POLICE CHOR*\n\n"
        f"👥 Players needed: {maximum}\n"
        f"✅ Joined: {current}/{maximum}\n\n"
    )

    for i, player in enumerate(game["players"], 1):
        text += f"{i}. {player['name']}\n"

    if current >= maximum:
        game["started"] = True

        text += (
            "\n🔥 *ALL PLAYERS JOINED!*\n"
            "🎲 Preparing the game...\n\n"
            "⏳ Role assignment will be added next."
        )

        await query.edit_message_text(
            text,
            parse_mode="Markdown"
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
            parse_mode="Markdown",
        )


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("startgame", startgame))

    app.add_handler(
        CallbackQueryHandler(
            choose_players,
            pattern=r"^players_[5-9]|players_10$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            join_game,
            pattern=r"^join_game$"
        )
    )

    print("🤖 RRPC Bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()