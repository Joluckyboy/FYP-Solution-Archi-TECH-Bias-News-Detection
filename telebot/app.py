from telegram import ForceReply, Update
from telegram.error import NetworkError, TimedOut
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


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors gracefully so transient network issues don't crash the bot."""
    if isinstance(context.error, (NetworkError, TimedOut)):
        logger.warning(f"Network error (will retry automatically): {context.error}")
        return
    logger.error("Unhandled exception:", exc_info=context.error)


def run_bot() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # Register error handler so network errors don't crash the bot
    application.add_error_handler(error_handler)

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
    # misfire_grace_time: if the bot was down at 08:00, still run the digest
    # within a 6-hour grace window after restart
    job_queue = application.job_queue
    job_queue.run_daily(
        handlers.send_digest,
        time=datetime.time(hour=8, minute=0, tzinfo=datetime.timezone.utc),
        name="daily_bias_digest",
        job_kwargs={"misfire_grace_time": 6 * 3600},
    )

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

# def main():
    # asyncio.run(run_bot())


if __name__ == '__main__':
    run_bot()