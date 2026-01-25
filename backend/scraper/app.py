from flask import Flask, request, jsonify, abort
from flask_restx import Api, Resource, fields, marshal
from flask_swagger_ui import get_swaggerui_blueprint
from youtube_transcript_api import YouTubeTranscriptApi
from newspaper import Article
from bs4 import BeautifulSoup as bs
import requests
from urllib.parse import urlparse
from datetime import datetime
from urllib.parse import urljoin

from flask_cors import CORS

app = Flask(__name__)
CORS(app)

api = Api(
    app,
    version="1.0",
    title="Scraper API",
    description="Scrapes news articles for their body text",
)

# Define the API namespaces
ns = api.namespace("scraper", description="Scraping news articles and transcripts")
api.add_namespace(ns)

# # Model for the response of get-transcript
transcript_model = api.model(
    "Transcript",
    {
        "headline": fields.String(description="Full title of the video"),
        "body": fields.String(description="Full transcript of the video"),
    },
)

# Model for the response of get-article
article_model = api.model(
    "Article",
    {
        "headline": fields.String(description="Article headline"),
        "body": fields.String(description="Article body"),
        "publish_date": fields.String(description="Article publish date"),
        "summary": fields.String(
            description="Article summary"
        ),  # Only article3k returns summary
    },
)

error_model = api.model("Error", {"error": fields.String(description="Error message")})


@ns.route("/")
class HealthCheck(Resource):
    def get(self):
        return jsonify({"status": "ok"})


# Endpoint to retrieve the latest articles from CNA and Straitstimes
@ns.route("/get-latest-articles")
class LatestArticleScraper(Resource):
    @api.doc(
        description="Extracts the latest article URL links from CNA and Straitstimes."
    )
    @api.param(
        "num_articles", "Number of articles to retrieve per source", required=False
    )
    def get(self):
        article_nums = request.args.get("num_articles")
        article_nums = int(article_nums) if article_nums else 10
        try:
            return {
                "straitstimes": retrieve_straits_urls(article_nums),
                "cna": retrieve_cna_urls(article_nums),
            }
        except Exception as e:
            print(e)
            return {"error": "Failed to retrieve latest articles"}, 500


def retrieve_straits_urls(specified_length: int):
    """
    Helper function to retrieve k (specified_length) latest article URLs from straitstimes
    """
    base_url = "https://www.straitstimes.com"
    res = requests.get(f"{base_url}/singapore/latest")
    soup = bs(res.content, "html.parser")
    article_anchors = soup.find_all("a", class_="stretched-link")

    article_urls = []
    for a_tag in article_anchors:
        if len(article_urls) >= specified_length:
            break
        if a_tag and a_tag.get("href"):
            relative_url = a_tag["href"]
            absolute_url = urljoin(base_url, relative_url)
            article_urls.append(absolute_url)

    return article_urls


def retrieve_cna_urls(specified_length: int):
    """
    Helper function to retrieve latest cna articles URLs
    """
    base_url = "https://www.channelnewsasia.com/singapore"
    res = requests.get(f"{base_url}")
    soup = bs(res.content, "html.parser")
    article_anchors = soup.find_all("a", class_="list-object__heading-link")

    article_urls = []
    for a_tag in article_anchors:
        if len(article_urls) >= specified_length:
            break
        if a_tag and a_tag.get("href"):
            relative_url = a_tag.get("href")
            absolute_url = urljoin(base_url, relative_url)
            article_urls.append(absolute_url)

    return article_urls


# ---------------------------------------
# Endpoint to get article from specific sites (Straits Times | OR | CNA)
@ns.route("/get-article")
class ArticleScraper(Resource):
    @api.doc(
        description="Extract article body and metadata from news sites.",
        responses={
            200: ("Success", article_model),
            400: "Not Found - Missing URL or Invalid URL",
        },
    )
    @api.param("url", "Article URL", required=True)
    # @api.marshal_with(article_model)
    def get(self):
        url = request.args.get("url")
        if not url:
            return {"error": "No URL provided"}, 400
            # abort(400, description="No URL provided")

        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            abort(400, description="Invalid URL format")

        return check_which_site(url)


# Identify which site URL is sent to change the scraping tags
def straits(url):
    res = requests.get(url)
    soup = bs(res.content, "html.parser")

    # Try multiple selectors for headline (Straits Times changes their HTML structure)
    headline_elem = (
        soup.find("div", class_="headline-container")
        or soup.find("h1", class_="headline")
        or soup.find("h1")
        or soup.find("div", class_="article-headline")
    )
    headline = headline_elem.text if headline_elem else "Headline not found"

    # Try multiple selectors for body paragraphs
    body_paras = soup.find_all("p", "paragraph-base")
    if not body_paras:
        body_paras = soup.find_all("p", class_="article-content-p")
    if not body_paras:
        body_paras = soup.find_all("p")
    body = "".join([para.text for para in body_paras])

    # Try multiple selectors for publish date
    if soup.find("button", class_="updated-timestamp"):
        publish_date = soup.find("button", class_="updated-timestamp").text.replace(
            "UPDATED ", ""
        )
    elif soup.find("div", class_="font-primary text-xs uppercase block mt-2.5"):
        publish_date = soup.find(
            "div", class_="font-primary text-xs uppercase block mt-2.5"
        ).text
    else:
        publish_date = "Date not found"

    return {
        "headline": headline.strip().replace("\n", " "),
        "body": body.strip().replace("\n", " "),
        "publish_date": publish_date,
    }


def cna(url):
    res = requests.get(url)
    soup = bs(res.content, "html.parser")
    headline = soup.find("h1", class_="h1--page-title").text
    body = "".join([div.text for div in soup.find_all("div", "text")])

    full = body

    publish_date = soup.find("div", class_="article-publish").text.strip()

    date_info = soup.find("div", class_="article-publish")

    publish_date = date_info.contents[0].strip()  # This retuns a string
    publish_date_obj = datetime.strptime(publish_date, "%d %b %Y %I:%M%p")
    publish_date_str = publish_date_obj.strftime("%Y-%m-%d")

    return {
        "headline": headline.strip().replace("\n", " "),
        "body": full.strip().replace("\n", " "),
        "publish_date": publish_date_str,
        # "updated_date": updated_date_obj
    }


def youtube(video_url, video_id):
    try:
        # Get the title of the youtube video
        res = requests.get(video_url)
        soup = bs(res.text, "html.parser")
        title = str(soup.title.text)
        # The title will have - Youtube at the end, this will remove it
        title = title.split("-")[:-1]

        # Join to turn it back into an unbroken string
        title = "-".join(title)

        # Get the transcript for the video, need to build it since it comes as a list of dictionaries
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        full_text = " ".join([segment["text"] for segment in transcript])
        # return {'transcript': full_text}
        return marshal({"headline": title, "body": full_text}, transcript_model), 200
    except Exception as e:
        return {"error": str(e)}, 500


def others(url):
    """
    Others is referring to non cna/straits news sites. Fox is manually scraped since 3k can't handle it
    """
    parse = urlparse(url).netloc
    paywall = False
    try:
        if "fox" in parse:
            res = requests.get(url)
            soup = bs(res.content, "html.parser")
            if soup.find("div", class_="paywall"):
                paywall = True

            headline = soup.find("h1", class_="headline").text

            if paywall == False:
                article = soup.find("div", class_="article-body")
            else:
                article = soup.find("div", class_="paywall")
            body = ""
            # print(article.text)
            for child in article.children:
                # print(child.name)
                if child.name == "p":
                    if child.find("strong"):
                        continue
                    # print(child.get_text())
                    body += child.get_text() + " "
            print(body)

            return {
                "headline": headline,
                "body": body.strip(),
                # 'summary': summary.strip().replace("\n", " ")
            }
        else:
            print("Using newspaper3k")
            article = Article(url)
            article.download()
            article.parse()
            # article.nlp()

            publish_date = (
                article.publish_date.strftime("%Y-%m-%d")
                if article.publish_date
                else None
            )
            body = article.text
            # summary = article.summary
            headline = article.title

            return {
                "headline": headline.strip().replace("\n", " "),
                "body": body.strip().replace("\n", " "),
                "publish_date": publish_date,
                # 'summary': summary.strip().replace("\n", " ")
            }
    except:
        print("Unsupported site, 400")
        return {"message": "Invalid URL format / Unsupported site"}, 400


def check_which_site(url):
    parse = urlparse(url).netloc
    if "straitstimes" in parse.split("."):
        return straits(url)
    elif "channelnewsasia" in parse.split("."):
        return cna(url)
    elif "youtube" in parse.split(".") or "youtu" in parse.split("."):
        video_url = request.args.get("url")
        if "youtube.com" in video_url:
            if "/shorts/" in video_url:  # Check if it's a YouTube Short
                video_id = video_url.split("/shorts/")[
                    1
                ]  # Get the video ID after '/shorts/'
            else:
                video_id = video_url.split("v=")[-1]
                if "&" in video_id:
                    video_id = video_id.split("&")[0]
            if "&" in video_id:
                video_id = video_id.split("&")[
                    0
                ]  # Clean video ID if it has additional parameters
        # This is checking for shortened links. You get these when you click on share on the youtube video
        elif "youtu.be" in video_url:
            video_id = video_url.split("/")[-1].split("?")[0]
        return youtube(video_url, video_id)
    else:
        return others(url)


# -----------------------------------

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import os
from datetime import datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import uuid  # Used for unique generation of image names

from PIL import Image
import pytesseract


@ns.route("/get-article-screenscraper")
class ArticleScraper(Resource):
    @api.doc(params={"url": "Scrren scrapes the provided URL"})
    @api.response(200, "Success")
    @api.response(400, "Invalid URL")
    @api.response(500, "Internal Server Error")
    @api.marshal_with(article_model)
    def get(self):
        url = request.args.get("url")
        if not url:
            api.abort(400, "URL parameter is required")

        random_uuid = uuid.uuid4()
        ss_string = random_uuid

        options = Options()
        options.add_argument(
            "--headless"
        )  # Set headless otherwise it only takes a screenshot of the viewport
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("blink-settings=imagesEnabled=false")

        driver = webdriver.Chrome(options=options)

        try:
            driver.get(url)
            time.sleep(3)
            page_height = driver.execute_script("return document.body.scrollHeight")
            driver.set_window_size(1920, page_height)

            image_name = f"{ss_string}.png"
            driver.get_screenshot_as_file(image_name)

            extracted_text = (
                pytesseract.image_to_string(Image.open(image_name))
                .strip()
                .replace("\n", " ")
            )
            return jsonify({"body": extracted_text})
        except Exception as e:
            api.abort(500, f"An error occurred: {str(e)}")
        finally:
            driver.quit()


if __name__ == "__main__":
    app.run(debug=True)
