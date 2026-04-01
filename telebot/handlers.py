from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import Forbidden
import requests  # type: ignore
import logging
import vars as vars

logger = logging.getLogger(__name__)


def normalize_bias_label(raw: str) -> str:
    """Normalise bias labels to canonical values used across the app."""
    s = str(raw or "").strip().lower().replace("_", "-").replace(" ", "-")
    if s in ("leaning-left", "lean-left"):
        return "lean-left"
    if s in ("leaning-right", "lean-right"):
        return "lean-right"
    if s == "centre":
        return "center"
    if s in ("left", "center", "right"):
        return s
    return s or "unknown"


def format_bias_label(raw: str) -> str:
    """Human-readable bias label from canonical form."""
    return normalize_bias_label(raw).replace("-", " ").title()


def shorten_url(url: str) -> str:
    """Shorten URL using TinyURL API v3"""
    if not vars.tinyurl_token:
        return url

    try:
        response = requests.post(
            "https://api.tinyurl.com/create",
            headers={
                "Authorization": f"Bearer {vars.tinyurl_token}",
                "Content-Type": "application/json"
            },
            json={
                "url": url,
                "domain": "tinyurl.com"
            },
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            return data.get("data", {}).get("tiny_url", url)
        else:
            return url
    except Exception:
        return url


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    if update.message and user:
        await update.message.reply_html(
            rf"Hi {user.mention_html()}! Welcome to <b>Checkmate</b> - your news bias detector."
            "\n\nHere's what I can do:"
            "\n\n<b>Analyze an article</b> - Just send me any news URL and I'll check it for:"
            "\n  - Fact-checking &amp; accuracy"
            "\n  - Sentiment &amp; emotion analysis"
            "\n  - Propaganda detection"
            "\n  - Political bias rating (Left / Center / Right)"
            "\n\n<b>/source</b> &lt;domain&gt; - Check a news source's credibility (e.g. /source cna)"
            "\n<b>/subscribe</b> - Get a daily digest of politically biased articles"
            "\n<b>/unsubscribe</b> - Stop receiving the daily digest"
            "\n<b>/help</b> - See all available commands"
            "\n\nTry it out! Paste a news article link to get started.",
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    if update.message:
        await update.message.reply_text(
            "Available commands:\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/source <domain> - Check credibility of a news source (e.g. /source cna.com)\n"
            "/subscribe - Get a daily digest of politically biased articles\n"
            "/unsubscribe - Stop receiving the daily digest\n\n"
            "Or just send me a news article URL to analyze!\n"
            "I'll check facts, sentiment, emotion, propaganda, and political bias."
        )


async def source_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check credibility of a news source via /source <domain>."""
    if not update.message:
        return

    if not context.args:
        await update.message.reply_text(
            "Please provide a domain. Example: /source cna.com"
        )
        return

    domain = context.args[0].strip().lower()

    await update.message.reply_text(f"Looking up credibility data for {domain}...")

    try:
        response = requests.get(
            vars.application_url + "/application/source_credibility",
            params={"domain": domain},
            timeout=15
        )
        data = response.json()
    except Exception as e:
        await update.message.reply_text(f"Error fetching source data: {e}")
        return

    if data.get("status") == "no_data":
        msg = data.get("message", "No data available for this source yet. "
                       "Submit an article from this source to start building its profile.")
        suggestions = data.get("suggestions", [])
        if suggestions:
            msg += "\n\nDid you mean:\n"
            msg += "\n".join([f"  \u2022 /source {s}" for s in suggestions])
        await update.message.reply_text(msg)
        return

    # Build the reply
    label = data.get("label", "Unknown")
    score = data.get("credibility_score")
    total = data.get("articles_analyzed", 0)
    avg_prop = data.get("avg_propaganda_probability", 0)
    accuracy = data.get("factual_accuracy_rate", 0)
    sentiment = data.get("avg_sentiment", {})
    leaning = format_bias_label(data.get("sentiment_leaning", "Unknown"))
    techniques = data.get("top_propaganda_techniques", [])

    score_line = f"{score}/100" if score is not None else "N/A"

    reply = (
        f"\U0001F50D Source Credibility Report: {domain}\n"
        "=====================================\n"
        f"\n"
        f"\U0001F3AF Credibility Score: {score_line}\n"
        f"\U0001F3F7\ufe0f Label: {label}\n"
        f"\U0001F4CA Articles Analyzed: {total}\n"
        f"\n"
        f"\u2696\ufe0f Avg Propaganda Probability: {avg_prop*100:.1f}%\n"
        f"\u2705 Factual Accuracy Rate: {accuracy*100:.1f}%\n"
        f"\n"
        f"\U0001F44D\U0001F3FB Avg Sentiment Distribution:\n"
    )

    if sentiment:
        for key in ("positive", "negative", "neutral"):
            val = sentiment.get(key, 0)
            reply += f"  \u2022 {key.capitalize()}: {val*100:.1f}%\n"
    else:
        reply += "  No sentiment data available\n"

    reply += f"\n\U0001F9ED Sentiment Leaning: {leaning}\n"

    if techniques:
        reply += "\n\U0001F6A9 Most Common Propaganda Techniques:\n"
        for t in techniques:
            reply += f"  \u2022 {t['technique']} ({t['count']}x)\n"

    reply += "====================================="

    await update.message.reply_text(reply)


async def non_url_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    if update.message:
        await update.message.reply_text("Please only send URLs")

# Function to handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    await update.message.reply_text("Processing...")
    await update.message.reply_text("This might take a few minutes! Unmute us and we will let you know when the results are ready!")

    url = update.message.text

    data = {"url": url, "background": False}
    try:
        response = requests.post(
            vars.application_url + "/application/new_query", json=data)
        if response.status_code == 400 and ('detail' in response.json().keys()):
            await update.message.reply_text("SORRY! I am unable to process this URL. Ensure that it is not empty and is a URL from a valid news site. If this keeps happening, try again later!")
            return
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
        await update.message.reply_text("SORRY! I am unable to process this URL. Ensure that it is not empty and is a URL from a valid news site. If this keeps happening, try again later!")
        return

    results = response.json()
    news_id = results.get('id', 'No ID available') if results.get('id') else 'No ID available'
    title = results.get('title', 'No title available') if results.get('title') else 'No title available'

    # Extract only the 3 numeric sentiment scores — ignore everything else
    raw_sentiment = results.get('sentiment_result', {}) if results.get('sentiment_result') else {}
    sentiment_result = {
        k: v for k, v in raw_sentiment.items()
        if k in ('positive', 'negative', 'neutral') and isinstance(v, (int, float))
    }

    emotion_result = results.get('emotion_result', {}).get(
        'weighted_avg', {}) if results.get('emotion_result') else {}
    propaganda_result = results.get('propaganda_result', {}).get(
        'propaganda_probability', 0) if results.get('propaganda_result') else 0
    factcheck_result = results.get('factcheck_result') if results.get('factcheck_result') else []
    summarise_result = results.get("summarise_result") if results.get("summarise_result") else "No summary available"
    political_bias = results.get('political_bias_result', {}) if results.get('political_bias_result') else {}
    bias_rating = format_bias_label(political_bias.get('rating', 'N/A')) if political_bias else 'N/A'

    # Sort sentiment by score descending
    sentiment_result = dict(
        sorted(sentiment_result.items(), key=lambda item: item[1], reverse=True))

    # get the top 5 emotions
    # [('joy', 0.6033682227134705), ('sadness', 0.6033682227134705), ('fear', 0.6033682227134705), ('anger', 0.6033682227134705), ('surprise', 0.6033682227134705)]
    emotion_result = sorted(emotion_result.items(), key=lambda x: x[1], reverse=True)[:5]

    # get the fact-check result
    compiled_factcheck_result = {"total": 0}
    for factcheck in factcheck_result:
        if factcheck["correctness"] not in compiled_factcheck_result:
            compiled_factcheck_result[factcheck["correctness"]] = 0
        compiled_factcheck_result[factcheck["correctness"]] += 1
        compiled_factcheck_result["total"] += 1

    # Create the full URL and try to shorten it
    full_url = f"{vars.web_url}/#/results/{news_id}?redirect=true"
    try:
        redirect_url = shorten_url(full_url)
    except Exception as e:
        # If shortening fails, use the full URL
        redirect_url = full_url

    reply_text = (
        f"\U0001F4F0 Title:\n {title}\n\n"
        + "\U0001F4DD Summary:\n"
        + "\n".join([f"• {paragraph.strip()}\n" for paragraph in summarise_result.split("\n\n")])
        + "\n"
        + "\n"
        + "Analysis Results:\n"
        "-------------------------------------\n"
        f"\u2705 Fact-Checking ({compiled_factcheck_result['total']} statements made):\n"
        + "\n".join([f"• {compiled_factcheck_result[factcheck]} {factcheck}" for factcheck in compiled_factcheck_result if factcheck != 'total'])
        + "\n"
        + "\n"
        f"\U0001F44D\U0001F3FB Sentiment Analysis:\n"
        + "\n".join([f"• {sentiment}: {score*100:.2f}%" for sentiment, score in sentiment_result.items()])
        + "\n"
        + "\n"
        "\U0001F914 Emotion Analysis (Top 5 Emotions):\n"
        # loop through the top 5 emotions in emotion_result and append it to a list with "•" as a bullet point
        + "\n".join([f"• {emotion[0]}: {emotion[1]*100:.2f}%" for emotion in emotion_result])
        + "\n"
        + "\n"
        f"\u2696\ufe0f Propaganda Probability: {propaganda_result*100:.2f}%\n"
        + "\n"
        f"\U0001F3DB\ufe0f Political Bias: {bias_rating}\n"
        + (
            (
                ("\U0001F7E2 Topics Covered: " + ", ".join(political_bias["topics"]["covered"]) + "\n"
                 if political_bias.get("topics", {}).get("covered") else "")
                + ("\U0001F534 Topics Omitted: " + ", ".join(political_bias["topics"]["omitted"]) + "\n"
                   if political_bias.get("topics", {}).get("omitted") else "")
            ) if political_bias else ""
        )
        + "-------------------------------------\n"
        f"See full article breakdown at {redirect_url}"
    )

    await update.message.reply_text(reply_text)


# ── Digest Subscription Commands ─────────────────────────────────────────────

async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Subscribe the user to the daily bias digest."""
    if not update.message or not update.effective_user or not update.effective_chat:
        return

    telegram_user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    try:
        response = requests.post(
            vars.application_url + "/application/digest/subscribe",
            params={"telegram_user_id": telegram_user_id, "chat_id": chat_id},
            timeout=10
        )
        if response.status_code == 200:
            await update.message.reply_text(
                "\u2705 You're subscribed to the daily bias digest!\n\n"
                "Every day at 4:00 PM (SGT), you'll receive a summary of recently "
                "analyzed articles that show notable political bias.\n\n"
                "Use /unsubscribe to stop receiving digests."
            )
        else:
            await update.message.reply_text("Something went wrong. Please try again later.")
    except Exception as e:
        logger.error(f"Error subscribing user {telegram_user_id}: {e}")
        await update.message.reply_text("Something went wrong. Please try again later.")


async def unsubscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unsubscribe the user from the daily bias digest."""
    if not update.message or not update.effective_user:
        return

    telegram_user_id = update.effective_user.id

    try:
        response = requests.post(
            vars.application_url + "/application/digest/unsubscribe",
            params={"telegram_user_id": telegram_user_id},
            timeout=10
        )
        if response.status_code == 200:
            await update.message.reply_text(
                "\u274c You've been unsubscribed from the daily bias digest.\n\n"
                "Use /subscribe to re-subscribe anytime."
            )
        else:
            await update.message.reply_text("You don't appear to be subscribed, or something went wrong.")
    except Exception as e:
        logger.error(f"Error unsubscribing user {telegram_user_id}: {e}")
        await update.message.reply_text("Something went wrong. Please try again later.")


async def send_digest(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Scheduled job: send the daily bias digest to all subscribers."""
    try:
        # 1. Get active subscriptions
        subs_response = requests.get(
            vars.application_url + "/application/digest/subscriptions",
            timeout=10
        )
        subscriptions = subs_response.json().get("subscriptions", [])
        if not subscriptions:
            logger.info("No active digest subscribers, skipping.")
            return

        # 2. Get recent biased articles (last 24h, non-center political bias)
        articles_response = requests.get(
            vars.application_url + "/application/digest/recent-biased",
            params={"hours": 24},
            timeout=15
        )
        articles = articles_response.json().get("articles", [])

        if not articles:
            logger.info("No biased articles in the last 24h, skipping digest.")
            return

        # 3. Build digest message (top 5 articles)
        from datetime import datetime, timedelta, timezone
        today = datetime.now(timezone.utc).strftime("%d %b %Y")
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%d %b %Y")

        bias_emoji = {
            "left": "\U0001F7E6",         # blue square
            "lean-left": "\U0001F539",   # small blue diamond
            "lean-right": "\U0001F538",  # small orange diamond
            "right": "\U0001F7E5",         # red square
        }

        top_articles = articles[:5]
        message = (
            "\U0001F4F0 Checkmate Daily Bias Digest\n"
            "=====================================\n"
            f"Period: {yesterday} \u2192 {today}\n"
            f"Articles with notable bias: {len(articles)}\n\n"
        )

        for i, article in enumerate(top_articles, 1):
            title = article.get("title", "Untitled")
            rating = normalize_bias_label(article.get("bias_rating", "unknown"))
            rating_display = format_bias_label(rating)
            emoji = bias_emoji.get(rating, "\U0001F3DB\ufe0f")
            summary = article.get("summarise_result", "")
            # Take first sentence of summary, stripping newlines first
            # Use regex to split on sentence-ending periods (not list numbers like "1.")
            if summary:
                import re
                flat_summary = summary.replace("\n", " ").strip()
                match = re.search(r'(?<!\d)\.(?:\s|$)', flat_summary)
                if match:
                    first_sentence = flat_summary[:match.end()].strip()
                else:
                    first_sentence = flat_summary
            else:
                first_sentence = "No summary available."
            if len(first_sentence) > 120:
                first_sentence = first_sentence[:117] + "..."

            news_id = article.get("id", "")
            full_url = f"{vars.web_url}/#/results/{news_id}?redirect=true"
            try:
                short_url = shorten_url(full_url)
            except Exception:
                short_url = full_url

            message += (
                f"{i}. {title}\n"
                f"   {emoji} Political Bias: {rating_display}\n"
                f"   \U0001F4DD {first_sentence}\n"
                f"   \U0001F517 {short_url}\n\n"
            )

        message += (
            "=====================================\n"
            "/unsubscribe to stop receiving digests."
        )

        # 4. Send to all subscribers
        for sub in subscriptions:
            chat_id = sub.get("chat_id")
            try:
                await context.bot.send_message(chat_id=chat_id, text=message)
            except Forbidden:
                # User blocked the bot — auto-unsubscribe
                tid = sub.get("telegram_user_id")
                logger.warning(f"User {tid} blocked bot, auto-unsubscribing.")
                try:
                    requests.post(
                        vars.application_url + "/application/digest/unsubscribe",
                        params={"telegram_user_id": tid},
                        timeout=5
                    )
                except Exception:
                    pass
            except Exception as e:
                logger.error(f"Failed to send digest to chat {chat_id}: {e}")

        logger.info(f"Digest sent to {len(subscriptions)} subscriber(s) with {len(articles)} biased article(s).")

    except Exception as e:
        logger.error(f"Error in send_digest job: {e}")
