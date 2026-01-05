import pytest
from flask import Flask, request, jsonify
from unittest.mock import patch, MagicMock
from datetime import datetime

# Import your Flask app and API
from app import app, ArticleScraper, check_which_site, cna, straits, youtube, others

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_youtube_transcript():
    with patch('youtube_transcript_api.YouTubeTranscriptApi.get_transcript') as mock_transcript:
        yield mock_transcript

@pytest.fixture
def mock_newspaper_article():
    with patch('newspaper.Article') as mock_article:
        yield mock_article

def test_health_check(client):
    response = client.get('/scraper/')
    assert response.status_code == 200
    assert response.json == {"status": "ok"}

# def test_get_transcript_success(client, mock_youtube_transcript):
#     mock_youtube_transcript.return_value = [{'text': 'Hello world'}, {'text': 'This is a test'}]
#     response = client.get('/scraper/get-transcript?url=https://www.youtube.com/watch?v=test_id')
#     assert response.status_code == 200
#     assert response.json == {'transcript': 'Hello world This is a test'}

# def test_get_transcript_no_url(client):
#     response = client.get('/scraper/get-transcript')
#     assert response.status_code == 400
#     assert response.json == {'error': 'No URL provided'}

# def test_get_transcript_invalid_url(client, mock_youtube_transcript):
#     mock_youtube_transcript.side_effect = Exception("Invalid URL")
#     response = client.get('/scraper/get-transcript?url=invalid_url')
#     assert response.status_code == 500
#     assert response.json.get('error')

def test_get_article_valid(client):
    # Mock the requests.get to prevent actual network calls
    with patch('requests.get') as mock_get:
        # Simulate a successful response for both sites (straits or cna)
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b"<html><body><h1>Test Headline</h1><div class='text-long'>Test body</div><div class='article-publish'>2023-01-01</div></body></html>"

        # Mock check_which_site to return the mocked data from cna or straits
        with patch('app.check_which_site') as mock_check:
            # Mock the return value of check_which_site
            mock_check.return_value = {
                'headline': 'Test Headline',
                'body': 'Test Body',
                'publish_date': '2023-01-01',
            }

            response = client.get('/scraper/get-article?url=https://www.channelnewsasia.com')
            assert response.status_code == 200
            assert response.json == mock_check.return_value

def test_get_article_youtube_valid(client):
    # Mock the requests.get to prevent actual network calls
    with patch('requests.get') as mock_get:
        # Simulate a successful response for youtube
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b"<html><body><h1>Test Headline</h1><div class='text-long'>Test body</div><div class='article-publish'>2023-01-01</div></body></html>"

        # Mock check_which_site to return the mocked data from cna or straits
        with patch('app.check_which_site') as mock_check:
            # Mock the return value of check_which_site
            mock_check.return_value = {
                'headline': 'Test Headline',
                'body': 'Test Body'
            }

            response = client.get('/scraper/get-article?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ')
            assert response.status_code == 200
            assert response.json == mock_check.return_value

def test_get_article_no_url(client):
    response = client.get('/scraper/get-article?url=')
    assert response.status_code == 400
    assert response.json == {"message": "No URL provided"}

def test_get_article_invalid_url(client):
    response = client.get('/scraper/get-article?url=invalid_url')
    assert response.status_code == 400
    assert response.json == {"message": "Invalid URL format"}

def test_get_article_unsupported(client):
    response = client.get('/scraper/get-article?url=http://unsupported.com')
    assert response.status_code == 400
    assert response.json == {"message": "Invalid URL format / Unsupported site"}


# def test_get_article3k_valid(client):
#     # Mock the `Article` class from newspaper3k
#     with patch('app.Article') as MockArticle:
#         # Create a mock article instance
#         mock_article = MagicMock()
        
#         # Set up the mock return values for the article methods
#         mock_article.title = 'Test Headline'
#         mock_article.text = 'Test Body'
#         mock_article.summary = 'Test Summary'
#         mock_article.publish_date = MagicMock()
#         mock_article.publish_date.strftime.return_value = '2023-01-01'
        
#         # Mock the methods download, parse, and nlp to do nothing (no actual HTTP requests)
#         mock_article.download.return_value = None
#         mock_article.parse.return_value = None
#         mock_article.nlp.return_value = None
        
#         # Set the mock article instance to be returned by the `Article` constructor
#         MockArticle.return_value = mock_article
        
#         response = client.get('/scraper/get-article3k?url=https://example.com/article')
#         assert response.status_code == 200
#         assert response.json == {
#             'headline': 'Test Headline',
#             'body': 'Test Body',
#             'publish_date': '2023-01-01',
#             'summary': 'Test Summary'
#         }


# def test_get_article3k_no_url(client):
#     response = client.get('/scraper/get-article3k')
#     assert response.status_code == 400
#     assert response.json == {'error': 'No URL provided'}

def test_get_article_straits(client):
    with patch('app.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.content = """
        <div class="headline-container">Test Headline</div>
        <p class="paragraph-base">Test Body</p>
        <button class="updated-timestamp">UPDATED 2023-01-01</button>
        """.encode('utf-8')
        mock_get.return_value = mock_response

        response = client.get('/scraper/get-article?url=https://www.straitstimes.com/article')
        assert response.status_code == 200
        assert response.json == {
            'headline': 'Test Headline',
            'body': 'Test Body',
            'publish_date': '2023-01-01'
        }

def test_get_article_3k(client):
    with patch('app.requests.get') as mock_get:
        with patch('app.Article') as MockArticle:
            # Create a mock article instance
            mock_article = MagicMock()
            
            # Set up the mock return values for the article methods
            mock_article.title = 'Test Headline'
            mock_article.text = 'Test Body'
            mock_article.summary = 'Test Summary'
            mock_article.publish_date = MagicMock()
            mock_article.publish_date.strftime.return_value = None
            
            # Mock the methods download, parse, and nlp to do nothing (no actual HTTP requests)
            mock_article.download.return_value = None
            mock_article.parse.return_value = None
            mock_article.nlp.return_value = None
            
            # Set the mock article instance to be returned by the `Article` constructor
            MockArticle.return_value = mock_article
            
            response = client.get('/scraper/get-article?url=https://example.com/article')
        assert response.status_code == 200
        assert response.json == {
            'headline': 'Test Headline',
            'body': 'Test Body',
            'publish_date': None,
        }



def test_get_article_cna(client):
    with patch('app.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.content = """
        <h1 class="h1--page-title">Test Headline</h1>
        <div class="text"><div class="text-long">Test Body</div></div>
        <div class="article-publish">01 Jan 2025 07:48PM</div>
        """.encode('utf-8')
        mock_get.return_value = mock_response

        response = client.get('/scraper/get-article?url=https://www.channelnewsasia.com/article')
        assert response.status_code == 200
        assert response.json == {
            'headline': 'Test Headline',
            'body': 'Test Body',
            'publish_date': '2025-01-01'
        }


def test_get_article_youtube_method(client):
    with patch('app.requests.get') as mock_get, \
        patch('app.YouTubeTranscriptApi.get_transcript') as mock_transcript:
        
        # Mock the requests.get response
        mock_response = MagicMock()
        mock_response.text = "<html><head><title>Test Headline - YouTube</title></head></html>"
        mock_get.return_value = mock_response

        response = client.get('/scraper/get-article?url=https://www.youtube.com/watch?v=test_id')

        # Assertions
        assert response.status_code == 200  # Check status code
        assert response.json == {
            'headline': 'Test Headline ',
            'body': '',
        }

def test_get_article_no_url(client):
    response = client.get('/scraper/get-article')
    assert response.status_code == 400
    assert response.json == {'error': 'No URL provided'}

def test_get_latest_articles(client):
    with patch('app.retrieve_straits_urls') as mock_straits, patch('app.retrieve_cna_urls') as mock_cna:
        mock_straits.return_value = ['https://www.straitstimes.com/article1', 'https://www.straitstimes.com/article2']
        mock_cna.return_value = ['https://www.channelnewsasia.com/article1', 'https://www.channelnewsasia.com/article2']

        response = client.get('/scraper/get-latest-articles?num_articles=2')
        assert response.status_code == 200
        assert len(response.json['straitstimes']) == 2
        assert len(response.json['cna']) == 2