from newspaper import Article
import requests
from urllib.parse import urlparse
import newspaper

from flask import Flask, request, jsonify
app = Flask(__name__)

# WIP - There's still more features to explore, but for now it is effectively just replicating what htmlScraper.py is doing with some extra fields

# This is just old test code
# cna = newspaper.build("http://cnn.com")
# url = 'https://cnalifestyle.channelnewsasia.com/entertainment/singapore-playwright-jonathan-lim-dies-age-50-459101'
# article = Article(url)
# article.download()
# article.parse()

# print(article.text)
# print("---------------------------------------------------------------------------")
# article.nlp()
# print(article.keywords)
# print(article.summary)

# Note: If you plan to use the summary and NLP stuff, you need NLTK
# If you keep getting a error on the punkt tokenizer, try running these two lines
# -------------------------------
# import nltk
# nltk.download(punkt)
# -------------------------------
# NLTK installs their punkt tokenizer differntly from how the code is expecting it. NLTK will just have pickle files insisde
# The code is looking for a folder for the language



@app.route('/get-article', methods=['GET'])
def get_article():
    url = request.args.get('url')
    article = Article(url)
    article.download()
    article.parse()
    article.nlp()
    date_publish=article.publish_date.strftime('%Y-%m-%d') # Comes in as datetime
    body=article.text
    sum=article.summary

    headline = article.title
    return jsonify({
        "headline": headline.strip().replace("\n", " "),
        "body": body.strip().replace("\n", " "),
        "publish_date": date_publish,
        "summary": sum.strip().replace("\n", " ")
    })


# if __name__ == '__main__':
#     app.run(debug=True)
