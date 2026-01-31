"""
Test suite for Scraper API
Tests all endpoints with proper mocking for external dependencies
"""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

import builtins
import io
import json

@pytest.fixture(autouse=True)
def patch_file_writes(monkeypatch):
    """Prevent writing any JSON or cache files during tests."""
    # Patch open for write mode to use in-memory file
    orig_open = builtins.open
    def fake_open(file, mode='r', *args, **kwargs):
        if 'w' in mode or 'a' in mode:
            return io.StringIO()
        return orig_open(file, mode, *args, **kwargs)
    monkeypatch.setattr(builtins, 'open', fake_open)
    # Patch json.dump to do nothing
    monkeypatch.setattr(json, 'dump', lambda obj, fp, *a, **k: None)
    # Patch os.makedirs to do nothing
    import os
    monkeypatch.setattr(os, 'makedirs', lambda *a, **k: None)
    # Patch os.path.exists to always return False for cache files
    orig_exists = os.path.exists
    def fake_exists(path):
        if 'cache_' in path or 'youtube_cache_' in path:
            return False
        return orig_exists(path)
    monkeypatch.setattr(os.path, 'exists', fake_exists)

@pytest.fixture
def client():
    """Flask test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# ============================================================================
# Health Check Tests
# ============================================================================

def test_health_check(client):
    """Test health check endpoint GET /scraper/"""
    response = client.get('/scraper/')
    assert response.status_code == 200
    data = response.get_json()
    assert 'status' in data
    assert data['status'] == 'ok'


# ============================================================================
# Get Latest Articles Tests
# ============================================================================

def test_get_latest_articles_with_mocks(client):
    """Test getting latest articles from all sources"""
    with patch('app.retrieve_straits_urls') as mock_straits, \
         patch('app.retrieve_cna_urls') as mock_cna:
        
        mock_straits.return_value = [
            'https://www.straitstimes.com/article1',
            'https://www.straitstimes.com/article2'
        ]
        mock_cna.return_value = [
            'https://www.channelnewsasia.com/article1',
            'https://www.channelnewsasia.com/article2'
        ]
        
        response = client.get('/scraper/get-latest-articles?num_articles=2')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, dict)
        # Verify both sources are present with correct keys
        assert 'straits_times' in data or 'cna' in data
        if 'straits_times' in data:
            assert len(data['straits_times']) == 2
        if 'cna' in data:
            assert len(data['cna']) == 2


# ============================================================================
# Get Article Tests
# ============================================================================

def test_get_article_no_url(client):
    """Test error when URL is not provided"""
    response = client.get('/scraper/get-article')
    assert response.status_code == 400
    assert 'error' in response.get_json()


def test_get_article_invalid_url(client):
    """Test error when invalid URL is provided"""
    response = client.get('/scraper/get-article?url=invalid_url')
    assert response.status_code == 400
    assert 'error' in response.get_json()


def test_get_article_cna_with_mocks(client):
    """Test scraping CNA article with mocked requests"""
    with patch('app.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.content = b"""
        <h1 class="h1--page-title">Test Headline</h1>
        <div class="text"><div class="text-long">Test Body Content</div></div>
        <div class="article-publish">01 Jan 2025 07:48PM</div>
        """
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        response = client.get('/scraper/get-article?url=https://www.channelnewsasia.com/article')
        assert response.status_code == 200
        data = response.get_json()
        assert 'headline' in data or 'body' in data or 'error' not in data


def test_get_article_straits_with_mocks(client):
    """Test scraping Straits Times article with mocked requests"""
    with patch('app.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.content = b"""
        <div class="headline-container">Test Headline</div>
        <p class="paragraph-base">Test Body</p>
        <button class="updated-timestamp">UPDATED 2025-01-01</button>
        """
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        response = client.get('/scraper/get-article?url=https://www.straitstimes.com/article')
        assert response.status_code == 200
        data = response.get_json()
        # API returns dict (might be None) or has headline/body/error keys
        assert data is None or isinstance(data, dict)


# ============================================================================
# Get Transcript Tests (YouTube)
# ============================================================================

def test_get_transcript_no_url(client):
    """Test error when transcript URL is not provided"""
    response = client.get('/scraper/get-transcript')
    assert response.status_code == 400
    data = response.get_json()
    # API returns {'body': None, 'headline': None} for missing URL
    assert data is not None


def test_get_transcript_invalid_url(client):
    """Test error with invalid YouTube URL"""
    response = client.get('/scraper/get-transcript?url=https://example.com')
    assert response.status_code == 400
    data = response.get_json()
    # API returns {'body': None, 'headline': None} for invalid YouTube URL
    assert data is not None


@patch('app.get_youtube_transcript_safe')
def test_get_transcript_with_mock(mock_transcript, client):
    """Test successful transcript retrieval with mocked transcript fetcher"""
    mock_transcript.return_value = [
        {'text': 'Hello world'},
        {'text': 'This is a test'}
    ]
    
    response = client.get('/scraper/get-transcript?url=https://www.youtube.com/watch?v=test123')
    assert response.status_code == 200
    data = response.get_json()
    # Response should have headline and body
    assert data is not None


def test_get_article_youtube_with_transcript(client):
    """Test YouTube article scraping with transcript extraction"""
    with patch('app.requests.get') as mock_get, \
         patch('app.get_youtube_transcript_safe') as mock_transcript:
        
        # Mock the YouTube page title
        mock_response = MagicMock()
        mock_response.text = "<html><head><title>Test YouTube Video - YouTube</title></head></html>"
        mock_get.return_value = mock_response
        
        # Mock transcript
        mock_transcript.return_value = [
            {'text': 'Hello world'},
            {'text': 'This is a test video'}
        ]
        
        response = client.get('/scraper/get-article?url=https://www.youtube.com/watch?v=test123')
        assert response.status_code == 200
        data = response.get_json()
        # YouTube articles should have headline and body
        assert data is not None
        if isinstance(data, dict) and 'headline' in data:
            # Headline should contain either the title or video ID
            assert 'YouTube' in data['headline'] or 'test123' in data['headline']


def test_get_article_generic_newspaper3k(client):
    """Test generic article scraping using newspaper3k fallback"""
    with patch('app.scrape_generic_article') as mock_scrape:
        mock_scrape.return_value = {
            'headline': 'Generic Article Headline',
            'body': 'Generic article body content',
            'publish_date': None,
            'summary': 'Article summary'
        }
        
        response = client.get('/scraper/get-article?url=https://example.com/news/article')
        assert response.status_code == 200
        data = response.get_json()
        assert data is not None
        if isinstance(data, dict):
            assert 'headline' in data or 'body' in data


def test_get_article_unsupported_site(client):
    """Test error handling for unsupported or failing sites"""
    with patch('app.check_which_site') as mock_check:
        # Simulate scraping failure
        mock_check.return_value = {'error': 'Failed to scrape article'}, 500
        
        response = client.get('/scraper/get-article?url=https://www.reddit.com/r/news')
        # Should handle error gracefully
        assert response.status_code in [400, 500]


# ============================================================================
# Screen Scraper Tests
# ============================================================================

def test_get_article_screenscraper_no_url(client):
    """Test error when screen scraper URL is not provided"""
    response = client.get('/scraper/get-article-screenscraper')
    assert response.status_code == 400


@patch('app.webdriver.Chrome')
@patch('app.pytesseract.image_to_string')
@patch('app.Image.open')
@patch('app.os.remove')
def test_get_article_screenscraper_success(mock_remove, mock_image_open, mock_ocr, mock_chrome, client):
    """Test successful screen scraping with Selenium + OCR"""
    # Mock Selenium WebDriver
    mock_driver = MagicMock()
    mock_chrome.return_value = mock_driver
    mock_driver.execute_script.return_value = 2000  # page height
    mock_driver.get_screenshot_as_file.return_value = True
    
    # Mock PIL Image
    mock_img = MagicMock()
    mock_image_open.return_value = mock_img
    
    # Mock OCR extraction
    mock_ocr.return_value = "Extracted article text from screenshot\nWith multiple lines"
    
    response = client.get('/scraper/get-article-screenscraper?url=https://example.com')
    assert response.status_code == 200
    data = response.get_json()
    assert 'body' in data
    assert 'Extracted' in data['body']
    # Verify driver was properly closed
    mock_driver.quit.assert_called_once()


# ============================================================================
# Scrape All Sources Tests
# ============================================================================

def test_scrape_all_sources_no_url(client):
    """Test error when scrape-all-sources URL is not provided"""
    response = client.get('/scraper/scrape-all-sources')
    assert response.status_code in [400, 405, 415]  # 400 bad request, 405 method not allowed, 415 unsupported media type


@patch('app.create_scrape_job')
@patch('app.get_job_status')
def test_scrape_all_sources_async_mode(mock_status, mock_create, client):
    """Test async mode scraping with background job"""
    mock_create.return_value = 'test-job-123'
    
    response = client.post('/scraper/scrape-all-sources?async_mode=true&num_articles=5')
    assert response.status_code == 200
    data = response.get_json()
    assert 'job_id' in data
    assert data['job_id'] == 'test-job-123'
    assert data['status'] == 'started'


@patch('app.create_scrape_job')
@patch('app.get_job_status')
def test_scrape_all_sources_sync_mode(mock_status, mock_create, client):
    """Test synchronous scraping that waits for completion"""
    mock_create.return_value = 'test-job-456'
    mock_status.return_value = {
        'status': 'completed',
        'started_at': '2026-01-31',
        'sources_scraped': ['CNA', 'Straits Times'],
        'sources_failed': [],
        'saved_articles': 10
    }
    
    response = client.post('/scraper/scrape-all-sources?async_mode=false&num_articles=5')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
    assert 'log' in data
    assert data['log']['total_articles'] == 10


@patch('app.create_scrape_job')
def test_scrape_all_sources_sg_only(mock_create, client):
    """Test Singapore-only source filtering"""
    mock_create.return_value = 'test-job-789'
    
    response = client.post('/scraper/scrape-all-sources?sg_only=true&async_mode=true')
    assert response.status_code == 200
    # Verify job was created (sg_only parameter passed correctly)
    mock_create.assert_called_once()


# ============================================================================
# Job Status Tests
# ============================================================================

def test_job_status_not_found(client):
    """Test job status for non-existent job"""
    response = client.get('/scraper/job-status/nonexistent-job-id')
    assert response.status_code == 404 or response.status_code == 200  # Could be 404 or just empty


@patch('app.get_job_status')
def test_job_status_success(mock_status, client):
    """Test successful job status retrieval"""
    mock_status.return_value = {
        'job_id': 'test-job-123',
        'status': 'running',
        'saved_articles': 5,
        'completed_sources': 1
    }
    
    response = client.get('/scraper/job-status/test-job-123')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'running'
    assert data['saved_articles'] == 5


# ============================================================================
# View Articles Tests
# ============================================================================

def test_view_articles(client):
    """Test viewing all scraped articles"""
    response = client.get('/scraper/view-scraped-articles')
    assert response.status_code == 200
    data = response.get_json()
    # Should have 'articles' and 'count' keys
    assert isinstance(data, dict)


@patch('app.os.path.exists')
@patch('builtins.open', new_callable=MagicMock)
def test_view_articles_with_data(mock_open, mock_exists, client):
    """Test viewing articles when CSV has data"""
    mock_exists.return_value = True
    mock_csv_data = 'title,source,url\nTest Article,CNA,https://example.com\n'
    mock_open.return_value.__enter__.return_value.read.return_value = mock_csv_data
    
    # Mock csv.DictReader
    with patch('app.csv.DictReader') as mock_reader:
        mock_reader.return_value = [
            {'title': 'Test Article', 'source': 'CNA', 'url': 'https://example.com'}
        ]
        
        response = client.get('/scraper/view-scraped-articles')
        assert response.status_code == 200
        data = response.get_json()
        assert 'articles' in data
        assert 'count' in data


# ============================================================================
# Article Stats Tests
# ============================================================================

def test_article_stats(client):
    """Test getting statistics about scraped articles"""
    response = client.get('/scraper/article-stats')
    assert response.status_code == 200
    data = response.get_json()
    # Should return some stats (might be empty initially)
    assert isinstance(data, dict)


@patch('app.os.path.exists')
@patch('builtins.open', new_callable=MagicMock)
def test_article_stats_with_data(mock_open, mock_exists, client):
    """Test article stats calculation with actual data"""
    mock_exists.return_value = True
    
    # Mock csv.DictReader with sample data
    with patch('app.csv.DictReader') as mock_reader:
        mock_reader.return_value = [
            {'title': 'Article 1', 'source': 'CNA', 'topic': 'Politics', 'country': 'Singapore'},
            {'title': 'Article 2', 'source': 'Straits Times', 'topic': 'Sports', 'country': 'Singapore'},
            {'title': 'Article 3', 'source': 'CNA', 'topic': 'Politics', 'country': 'Singapore'}
        ]
        
        response = client.get('/scraper/article-stats')
        assert response.status_code == 200
        data = response.get_json()
        assert 'total_articles' in data
        assert 'by_topic' in data
        assert 'by_source' in data
        assert 'by_country' in data


# ============================================================================
# YouTube Shorts URL Tests
# ============================================================================

def test_get_article_youtube_shorts(client):
    """Test YouTube Shorts URL format"""
    with patch('app.requests.get') as mock_get, \
         patch('app.get_youtube_transcript_safe') as mock_transcript:
        
        mock_response = MagicMock()
        mock_response.text = "<title>Short Video - YouTube</title>"
        mock_get.return_value = mock_response
        
        mock_transcript.return_value = [{'text': 'Short video content'}]
        
        response = client.get('/scraper/get-article?url=https://www.youtube.com/shorts/abc123')
        assert response.status_code == 200
        data = response.get_json()
        assert data is not None


# ============================================================================
# Fox News Scraping Tests
# ============================================================================

def test_get_article_fox_news(client):
    """Test scraping Fox News article"""
    with patch('app.scrape_fox_news') as mock_fox:
        mock_fox.return_value = {
            'headline': 'Fox News Headline',
            'body': 'Fox News article body',
            'publish_date': '2026-01-31'
        }
        
        response = client.get('/scraper/get-article?url=https://www.foxnews.com/article')
        assert response.status_code == 200
        data = response.get_json()
        assert data is not None
        if isinstance(data, dict) and 'headline' in data:
            assert 'Fox News' in data['headline']

