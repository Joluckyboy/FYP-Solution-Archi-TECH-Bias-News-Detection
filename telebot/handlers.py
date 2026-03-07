from telegram import Update
from telegram.ext import ContextTypes
import requests  # type: ignore
import vars as vars


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
            rf"Hi {user.mention_html()}! Send me a news article URL and I will analyze it for you!",
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    if update.message:
        await update.message.reply_text("Help!")


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
        "-------------------------------------\n"
        f"See full article breakdown at {redirect_url}"
    )

    await update.message.reply_text(reply_text)
