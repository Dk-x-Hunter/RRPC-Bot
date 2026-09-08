import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👑 Raja Rani Police Chor Bot 👑\n\n"
        "🎮 Bot is online!\n"
        "Use /startgame to begin a game."
    )


async def startgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎮 Raja Rani Police Chor Game\n\n"
        "Choose the number of players:\n"
        "Minimum: 5\n"
        "Maximum: 10\n\n"
        "Game system coming next 🔥"
    )


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("startgame", startgame))

    print("🤖 RRPC Bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()
