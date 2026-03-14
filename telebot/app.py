from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

import handlers as handlers
import logging
import os
import datetime

import vars as vars


# Define your bot token "get from BotFather"
TOKEN = vars.telebot_token

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def run_bot() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(CommandHandler("help", handlers.help_command))
    application.add_handler(CommandHandler("source", handlers.source_command))
    application.add_handler(CommandHandler("subscribe", handlers.subscribe_command))
    application.add_handler(CommandHandler("unsubscribe", handlers.unsubscribe_command))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.Entity("url") & ~filters.COMMAND, handlers.handle_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.non_url_message))

    # Schedule daily bias digest at 08:00 UTC
    job_queue = application.job_queue
    job_queue.run_daily(
        handlers.send_digest,
        time=datetime.time(hour=8, minute=0, tzinfo=datetime.timezone.utc),
        name="daily_bias_digest"
    )

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

# def main():
    # asyncio.run(run_bot())


if __name__ == '__main__':
    run_bot()