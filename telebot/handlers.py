from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import pyshorteners

import requests
import vars as vars

TINY_URL = pyshorteners.Shortener().tinyurl.short

##########################
##########################
##########################
# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")


##########################
##########################
##########################

async def non_url_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    await update.message.reply_text("Please only send URLs")

# Function to handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # send message to user "processing..."
    await update.message.reply_text("Processing...")
    await update.message.reply_text("This might take a few mintues! Unmute us and we will let you know when the results are ready!")

    url = update.message.text

    data = {"url": url, "background": False}
    try:
        response = requests.post(vars.application_url + "/application/new_query", json=data)
        if response.status_code == 400 and ('detail' in response.json().keys()):
            await update.message.reply_text("SORRY! I am unable to process this URL. Ensure that it is not empty and is a URL from a valid news site. If this keeps happening, try again later!")
            return
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
        await update.message.reply_text("SORRY! I am unable to process this URL. Ensure that it is not empty and is a URL from a valid news site. If this keeps happening, try again later!")
        return

    results = response.json()
    # pprint.pprint(results)
    news_id = results.get('id', 'No ID available')  if results.get('id') else 'No ID available'
    title = results.get('title', 'No title available') if results.get('title') else 'No title available'
    sentiment_result = results.get('sentiment_result', {}) if results.get('sentiment_result') else {}
    emotion_result = results.get('emotion_result', {}).get('weighted_avg', {}) if results.get('emotion_result') else {}
    propaganda_result = results.get('propaganda_result', {}).get('propaganda_probability', 0) if results.get('propaganda_result') else 0
    factcheck_result = results.get('factcheck_result') if results.get('factcheck_result') else []
    summarise_result = results.get("summarise_result") if results.get("summarise_result") else "No summary available"


    # get the sentiment result with the highest score + keep the score
    sentiment_result = dict(sorted(sentiment_result.items(), key=lambda item: item[1], reverse=True))

    # get the top 5 emotions
    emotion_result = sorted(emotion_result.items(), key=lambda x: x[1], reverse=True)[:5]    ##[('joy', 0.6033682227134705), ('sadness', 0.6033682227134705), ('fear', 0.6033682227134705), ('anger', 0.6033682227134705), ('surprise', 0.6033682227134705)]
    
    # get the fact-check result
    compiled_factcheck_result = {"total": 0}
    for factcheck in factcheck_result:
        if factcheck["correctness"] not in compiled_factcheck_result:
            compiled_factcheck_result[factcheck["correctness"]] = 0
        compiled_factcheck_result[factcheck["correctness"]] += 1
        compiled_factcheck_result["total"] += 1

    # print(compiled_factcheck_result)        ## {'total': 11, 'factual': 6, 'cannot be determined': 3, 'unfactual': 2}

    redirect_url = TINY_URL(f"{vars.web_url}/#/results/{news_id}?redirect=true")

    reply_text = (
        f"\U0001F4F0 Title:\n {title}\n\n"
        + "\U0001F4DD Summary:\n"
        + "\n".join([f"• {paragraph.strip()}\n" for paragraph in summarise_result.split("\n\n")])
        + "\n"
        + "\n"
        + "Analysis Results:\n"
        "-------------------------------------\n"
        f"\u2705 Fact-Checking ({compiled_factcheck_result['total']} statements made):\n"\
        + "\n".join([f"• {compiled_factcheck_result[factcheck]} {factcheck}" for factcheck in compiled_factcheck_result if factcheck != 'total'])
        + "\n"
        + "\n"
        f"\U0001F44D\U0001F3FB Sentiment Analysis:\n"
        # + f"{sentiment_result[0]} ({sentiment_result[1]*100:.2f}%)\n"
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
    