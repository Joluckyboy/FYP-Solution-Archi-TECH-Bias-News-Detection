from bs4 import BeautifulSoup as bs
import requests
from urllib.parse import urlparse
from datetime import datetime
from flask import Flask, request, jsonify
app = Flask(__name__)

from youtube_transcript_api import YouTubeTranscriptApi

# THIS WAS/IS TEST CODE
# # This is the webpage to scrape
# link = "https://www.straitstimes.com/singapore/non-stop-heavy-downpours-to-resume-jan-17-to-19-as-a-second-monsoon-surge-descends"

# # Returns the whole page source
# res = requests.get(link)


# soup = bs(res.content,"html.parser")

# headline = soup.find("div",class_="headline-container")
# # print(headline.text)

# body = soup.find_all("p","paragraph-base")

# body_full = ""

# for para in body:
#     body_full += para.text

# full = headline.text + "\n" + body_full

# print(full)

from flask_swagger_ui import get_swaggerui_blueprint

SWAGGER_URL="/swagger"
API_URL="/static/swagger.json"

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': 'Scraper API'
    }
)
app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)


# This is for pulling transcripts from youtube to analyze
def get_full_transcript(video_id):
    try:
        # Get transcript from video_id, comes as a dict with the timestamp
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        
        # Join all text segments together into one string
        full_text = " ".join([segment['text'] for segment in transcript])
        
        return full_text
    
    except Exception as e:
        return str(e)
    

@app.route('/scraper/get-transcript', methods=['GET'])
def get_transcript():
    # Get the video URL
    video_url = request.args.get('url')
    
    if not video_url:
        return jsonify({"error": "No URL provided"}), 400
    
    # Extract video ID from URL
    try:
        video_id = video_url.split('v=')[-1]  # Get the video ID
        if '&' in video_id:
            video_id = video_id.split('&')[0]  # Clean video ID if it has additional parameters like if you have the timestamp in the link that someone gave you
    except Exception as e:
        return jsonify({"error": "Invalid YouTube URL"}), 400
    
    # Get the transcript for the video
    transcript_text = get_full_transcript(video_id)
    
    if "Error" in transcript_text:
        return jsonify({"error": transcript_text}), 500
    
    return jsonify({"transcript": transcript_text})
    



@app.route('/scraper/get-article', methods=['GET'])
def get_article():
    url = request.args.get('url')
    # Returns the whole page source
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        return jsonify({"error": "Invalid URL format"}), 400


    return check_which_site(url)


def straits(url):
    res = requests.get(url)

    soup = bs(res.content,"html.parser")

    headline = soup.find("div",class_="headline-container")
    # print(headline.text)

    body = soup.find_all("p","paragraph-base")

    body_full = ""

    for para in body:
        body_full += para.text

    full = headline.text + "\n" + body_full
    return jsonify({"headline": headline.text,
                    "body": body_full})

def cna(url):
    url = request.args.get('url')
    # Returns the whole page source
    res = requests.get(url)

    soup = bs(res.content,"html.parser")  
    # Removing the bold text from images
    if soup.find("strong"):
        soup.strong.extract()


    headline = soup.find("h1",class_="h1--page-title")
    # print(headline.text)
    headline = headline.text

    body = soup.find_all("div", class_="text-long")

    # For loop line is just removing the SEO stuff
    to_remove = soup.find_all("div", class_=["desktop-liner","mobile-liner"])
    for seg in to_remove:
        seg.decompose()
        
    full=''

    for divs in body:
        if divs.find("strong"):
            continue
        full += divs.text

    publish_date = soup.find("div", "article-publish")
    # print(publish_date)

    date_info = soup.find('div', class_='article-publish')

    publish_date = date_info.contents[0].strip() # This retuns a string
    publish_date_obj = datetime.strptime(publish_date, "%d %b %Y %I:%M%p")
    
    updated_date_str = date_info.span.text # Returns something like this (Updated: 25 Jan 2025 11:15AM)
    updated_date = updated_date_str.strip("()").replace("Updated: ", "") # It's still a string here, just removed the paranthesis and Updated:
    updated_date_obj = datetime.strptime(updated_date, "%d %b %Y %I:%M%p")
    

    print(publish_date_obj.date())
    print(" updated_date_obj:", updated_date_obj.date())

    return jsonify({
        "headline": headline.strip().replace("\n", " "),
        "body": full.strip().replace("\n", " "),
        "publish_date": publish_date_obj,
        "updated_date": updated_date_obj
    })

def check_which_site(url):
    parse = urlparse(url).netloc
    if ("straitstimes" in parse.split(".")):
        return straits(url)
    elif ("channelnewsasia" in parse.split(".")):
        return cna(url)
    else:
        return "Error"


if __name__ == '__main__':
    app.run(debug=True)
