import importlib
import sys

import pandas as pd
import pytest


def load_app_module():
    for name in ['app', 'methods', 'redis_cache', 'vars', 's3_sync', 'api_models', 'dashboard_methods', 'visualisations', 'explanations']:
        sys.modules.pop(name, None)
    return importlib.import_module('app')


def test_process_url_returns_complete_redis_cache_without_hitting_services(monkeypatch):
    app_module = load_app_module()
    cached = {
        'url': 'https://example.com/a',
        'sentiment_result': {'ok': True},
        'emotion_result': {'ok': True},
        'propaganda_result': {'ok': True},
        'factcheck_result': [{'statement': 'x'}],
        'summarise_result': 'summary',
        'data_summary': {'done': True},
    }

    monkeypatch.setattr(app_module.redis_cache, 'get_cached_result', lambda url: cached)
    monkeypatch.setattr(app_module.redis_cache, 'is_analysis_complete', lambda data: True)

    def should_not_run(*args, **kwargs):
        raise AssertionError('service/database should not be called when redis cache is complete')

    monkeypatch.setattr(app_module.methods, 'check_exists', should_not_run)

    result = app_module.process_url('https://example.com/a', return_news=True, background=False)
    assert result == cached


def test_process_url_existing_complete_article_returns_db_result_and_caches(monkeypatch):
    app_module = load_app_module()
    existing = {
        'url': 'https://example.com/b',
        'title': 'Headline',
        'content': 'Body',
        'sentiment_result': {'ok': True},
        'emotion_result': {'ok': True},
        'propaganda_result': {'ok': True},
        'factcheck_result': [{'statement': 'x'}],
        'summarise_result': 'summary',
        'political_bias_result': {'score': 0.2},
        'data_summary': {'done': True},
    }
    cached = {}

    monkeypatch.setattr(app_module.redis_cache, 'get_cached_result', lambda url: None)
    monkeypatch.setattr(
        app_module.redis_cache,
        'cache_result',
        lambda url, data: cached.update({'url': url, 'data': data})
    )
    monkeypatch.setattr(app_module.methods, 'check_exists', lambda url: {'exists': True})
    monkeypatch.setattr(app_module.methods, 'get_news', lambda url: existing)

    result = app_module.process_url('https://example.com/b', return_news=True, background=False)

    assert result == existing
    assert cached['url'] == 'https://example.com/b'
    assert cached['data']['title'] == 'Headline'


def test_process_url_retries_only_missing_analyses_synchronously(monkeypatch):
    app_module = load_app_module()
    existing = {
        'url': 'https://example.com/c',
        'title': 'Headline',
        'content': 'Body text',
        'sentiment_result': None,
        'emotion_result': {'ok': True},
        'propaganda_result': None,
        'factcheck_result': [{'statement': 'already'}],
        'summarise_result': 'summary',
        'data_summary': {},
    }
    calls = []

    monkeypatch.setattr(app_module.redis_cache, 'get_cached_result', lambda url: None)
    monkeypatch.setattr(app_module.redis_cache, 'cache_result', lambda *args, **kwargs: None)
    monkeypatch.setattr(app_module.redis_cache, 'is_analysis_complete', lambda data: False)
    monkeypatch.setattr(app_module.methods, 'check_exists', lambda url: {'exists': True})
    monkeypatch.setattr(app_module.methods, 'get_news', lambda url: existing)
    monkeypatch.setattr(app_module.methods, 'get_sentiment', lambda text, url, title: calls.append('sentiment') or {'sentiment_result': {'x': 1}})
    monkeypatch.setattr(app_module.methods, 'get_propaganda', lambda text, url, title: calls.append('propaganda') or {'propaganda_result': {'x': 1}})
    monkeypatch.setattr(app_module.methods, 'get_data_summary', lambda *args, **kwargs: calls.append(f"summary:{kwargs.get('trigger')}") or {'done': True})
    monkeypatch.setattr(app_module.methods, 'get_emotion', lambda *args, **kwargs: calls.append('emotion') or {})
    monkeypatch.setattr(app_module.methods, 'get_summarise', lambda *args, **kwargs: calls.append('summarise') or {})
    monkeypatch.setattr(app_module.methods, 'get_fact_check', lambda *args, **kwargs: calls.append('factcheck') or [])

    result = app_module.process_url('https://example.com/c', return_news=True, background=False)

    assert result == existing
    assert 'sentiment' in calls
    assert 'propaganda' in calls
    assert 'emotion' not in calls
    assert 'summarise' not in calls
    assert 'factcheck' not in calls
    assert any(item.startswith('summary:') for item in calls)


def test_process_url_rescrapes_existing_article_when_db_content_missing(monkeypatch):
    app_module = load_app_module()
    existing = {
        'url': 'https://example.com/missing-content',
        'title': '',
        'content': '',
        'sentiment_result': None,
        'emotion_result': None,
        'propaganda_result': None,
        'factcheck_result': None,
        'summarise_result': None,
        'data_summary': None,
    }
    calls = []

    monkeypatch.setattr(app_module.redis_cache, 'get_cached_result', lambda url: None)
    monkeypatch.setattr(app_module.redis_cache, 'cache_result', lambda *args, **kwargs: None)
    monkeypatch.setattr(app_module.redis_cache, 'is_analysis_complete', lambda data: True)
    monkeypatch.setattr(app_module.methods, 'check_exists', lambda url: {'exists': True})
    monkeypatch.setattr(app_module.methods, 'get_news', lambda url: existing)
    monkeypatch.setattr(app_module.methods, 'extract_news', lambda url: {'headline': 'Recovered title', 'body': 'Recovered body'})
    monkeypatch.setattr(app_module.methods, 'get_sentiment', lambda *args, **kwargs: calls.append('sentiment') or {'sentiment_result': {'ok': True}})
    monkeypatch.setattr(app_module.methods, 'get_emotion', lambda *args, **kwargs: calls.append('emotion') or {'emotion_result': {'ok': True}})
    monkeypatch.setattr(app_module.methods, 'get_propaganda', lambda *args, **kwargs: calls.append('propaganda') or {'propaganda_result': {'ok': True}})
    monkeypatch.setattr(app_module.methods, 'get_summarise', lambda *args, **kwargs: calls.append('summarise') or {'response': 'summary'})
    monkeypatch.setattr(app_module.methods, 'get_fact_check', lambda *args, **kwargs: calls.append('factcheck') or [{'statement': 'x'}])
    monkeypatch.setattr(app_module.methods, 'get_data_summary', lambda *args, **kwargs: calls.append('data_summary') or {'done': True})

    app_module.process_url('https://example.com/missing-content', return_news=False, background=False)
    assert set(['sentiment', 'emotion', 'propaganda', 'summarise', 'factcheck']).issubset(set(calls))


def test_process_url_force_reanalyze_deletes_redis_cache_and_runs_full_analysis(monkeypatch):
    app_module = load_app_module()
    final_news = {
        'url': 'https://example.com/force',
        'title': 'Headline',
        'content': 'Body text',
        'sentiment_result': {'ok': True},
        'emotion_result': {'ok': True},
        'propaganda_result': {'ok': True},
        'factcheck_result': [{'statement': 'x'}],
        'summarise_result': 'summary',
        'data_summary': {'done': True},
    }
    calls = []

    monkeypatch.setattr(app_module.redis_cache, 'delete_cached_result', lambda url: calls.append(('delete_cache', url)))
    monkeypatch.setattr(app_module.redis_cache, 'get_cached_result', lambda url: {'stale': True})
    monkeypatch.setattr(app_module.redis_cache, 'cache_result', lambda *args, **kwargs: calls.append(('cache', kwargs if kwargs else args)))
    monkeypatch.setattr(app_module.redis_cache, 'is_analysis_complete', lambda data: True)
    monkeypatch.setattr(app_module.methods, 'check_exists', lambda url: {'exists': True})
    monkeypatch.setattr(app_module.methods, 'get_news', lambda url: final_news)
    monkeypatch.setattr(app_module.methods, 'get_sentiment', lambda *args, **kwargs: calls.append('sentiment') or {'sentiment_result': {'ok': True}})
    monkeypatch.setattr(app_module.methods, 'get_emotion', lambda *args, **kwargs: calls.append('emotion') or {'emotion_result': {'ok': True}})
    monkeypatch.setattr(app_module.methods, 'get_propaganda', lambda *args, **kwargs: calls.append('propaganda') or {'propaganda_result': {'ok': True}})
    monkeypatch.setattr(app_module.methods, 'get_summarise', lambda *args, **kwargs: calls.append('summarise') or {'response': 'summary'})
    monkeypatch.setattr(app_module.methods, 'get_fact_check', lambda *args, **kwargs: calls.append('factcheck') or [{'statement': 'x'}])
    monkeypatch.setattr(app_module.methods, 'get_data_summary', lambda *args, **kwargs: calls.append('data_summary') or {'done': True})

    result = app_module.process_url('https://example.com/force', return_news=True, background=False, force_reanalyze=True)

    assert result == final_news
    assert ('delete_cache', 'https://example.com/force') in calls
    for expected in ['sentiment', 'emotion', 'propaganda', 'summarise', 'factcheck', 'data_summary']:
        assert expected in calls


def test_process_url_new_article_runs_full_analysis_synchronously(monkeypatch):
    app_module = load_app_module()
    final_news = {
        'url': 'https://example.com/d',
        'title': 'Headline',
        'content': 'Body text',
        'sentiment_result': {'ok': True},
        'emotion_result': {'ok': True},
        'propaganda_result': {'ok': True},
        'factcheck_result': [{'statement': 'x'}],
        'summarise_result': 'summary',
        'data_summary': {'done': True},
    }
    calls = []

    monkeypatch.setattr(app_module.redis_cache, 'get_cached_result', lambda url: None)
    monkeypatch.setattr(app_module.redis_cache, 'is_analysis_complete', lambda data: True)
    monkeypatch.setattr(app_module.redis_cache, 'cache_result', lambda *args, **kwargs: calls.append('cache'))
    monkeypatch.setattr(app_module.methods, 'check_exists', lambda url: {'exists': False})
    monkeypatch.setattr(app_module.methods, 'extract_news', lambda url: {'headline': 'Headline', 'body': 'Body text'})
    monkeypatch.setattr(app_module.methods, 'create_news', lambda url, title, content: {'id': 'abc123'})
    monkeypatch.setattr(app_module.methods, 'get_news', lambda url: final_news)
    monkeypatch.setattr(app_module.methods, 'get_sentiment', lambda *args, **kwargs: calls.append('sentiment') or {'sentiment_result': {'ok': True}})
    monkeypatch.setattr(app_module.methods, 'get_emotion', lambda *args, **kwargs: calls.append('emotion') or {'emotion_result': {'ok': True}})
    monkeypatch.setattr(app_module.methods, 'get_propaganda', lambda *args, **kwargs: calls.append('propaganda') or {'propaganda_result': {'ok': True}})
    monkeypatch.setattr(app_module.methods, 'get_summarise', lambda *args, **kwargs: calls.append('summarise') or {'response': 'summary'})
    monkeypatch.setattr(app_module.methods, 'get_fact_check', lambda *args, **kwargs: calls.append('factcheck') or [{'statement': 'x'}])
    monkeypatch.setattr(app_module.methods, 'get_data_summary', lambda *args, **kwargs: calls.append(f"summary:{kwargs.get('trigger')}") or {'done': True})

    result = app_module.process_url('https://example.com/d', return_news=True, background=False)

    assert result == final_news
    for expected in ['sentiment', 'emotion', 'propaganda', 'summarise', 'factcheck', 'cache']:
        assert expected in calls


def test_process_url_background_retry_returns_existing_without_running_duplicate_job(monkeypatch):
    app_module = load_app_module()
    existing = {
        'url': 'https://example.com/retry-bg',
        'title': 'Headline',
        'content': 'Body',
        'sentiment_result': None,
        'emotion_result': {'ok': True},
        'propaganda_result': {'ok': True},
        'factcheck_result': [{'statement': 'x'}],
        'summarise_result': 'summary',
        'data_summary': {'done': True},
    }
    started = []

    monkeypatch.setattr(app_module.redis_cache, 'get_cached_result', lambda url: None)
    monkeypatch.setattr(app_module.methods, 'check_exists', lambda url: {'exists': True})
    monkeypatch.setattr(app_module.methods, 'get_news', lambda url: existing)
    monkeypatch.setattr(app_module, '_start_unique_background', lambda url, job_type, target: started.append((url, job_type)) or False)

    result = app_module.process_url('https://example.com/retry-bg', return_news=True, background=True)

    assert result == existing
    assert started == [('https://example.com/retry-bg', 'retry')]


def test_process_url_raises_400_when_scraper_cannot_extract_content(monkeypatch):
    app_module = load_app_module()

    monkeypatch.setattr(app_module.redis_cache, 'get_cached_result', lambda url: None)
    monkeypatch.setattr(app_module.methods, 'check_exists', lambda url: {'exists': False})
    monkeypatch.setattr(app_module.methods, 'extract_news', lambda url: {'headline': '', 'body': ''})

    with pytest.raises(app_module.HTTPException) as exc:
        app_module.process_url('https://example.com/invalid', return_news=True, background=False)

    assert exc.value.status_code == 400


def test_process_url_converts_invalid_url_abort_to_http_400(monkeypatch):
    app_module = load_app_module()

    class FakeAbort(Exception):
        def __init__(self):
            self.description = 'Invalid URL format'

    monkeypatch.setattr(app_module.redis_cache, 'get_cached_result', lambda url: None)
    monkeypatch.setattr(app_module.methods, 'check_exists', lambda url: {'exists': False})
    monkeypatch.setattr(app_module.methods, 'extract_news', lambda url: (_ for _ in ()).throw(FakeAbort()))

    with pytest.raises(app_module.HTTPException) as exc:
        app_module.process_url('bad-url', return_news=True, background=False)

    assert exc.value.status_code == 400
    assert exc.value.detail == 'Invalid URL'


def test_new_query_requires_url():
    app_module = load_app_module()
    with pytest.raises(app_module.HTTPException) as exc:
        app_module.new_query(app_module.URLwithBG(url=None, background=False, force=False))
    assert exc.value.status_code == 400


def test_start_unique_background_blocks_duplicate_and_releases_after_completion(monkeypatch):
    app_module = load_app_module()
    ran = []
    threads = []

    class ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self.target = target
            threads.append(self)
        def start(self):
            self.target()

    monkeypatch.setattr(app_module.threading, 'Thread', ImmediateThread)
    app_module._active_retry_urls.clear()

    assert app_module._start_unique_background('https://example.com/u', 'retry', lambda: ran.append('done')) is True
    assert ran == ['done']
    # target already completed, so second start should be allowed again
    assert app_module._start_unique_background('https://example.com/u', 'retry', lambda: ran.append('done2')) is True
    assert ran == ['done', 'done2']


def test_get_articles_by_keyword_matches_exact_phrase_all_words_and_partial_multiword(monkeypatch):
    app_module = load_app_module()
    df = pd.DataFrame([
        {'title': 'Singapore election debate heats up', 'summary': 'Candidates debate housing policy', 'url': 'u1'},
        {'title': 'Housing policy sparks public debate', 'summary': 'Singapore election season continues', 'url': 'u2'},
        {'title': 'Singapore politics update', 'summary': 'Election housing issue appears again', 'url': 'u3'},
        {'title': 'Sports news only', 'summary': 'Nothing relevant here', 'url': 'u4'},
    ])
    monkeypatch.setattr(app_module, 'read_scraped_articles', lambda: df)

    result = app_module.get_articles_by_keyword('Singapore election housing')
    urls = [item['url'] for item in result['articles']]
    assert 'u1' in urls  # exact/all-words
    assert 'u2' in urls  # all words across title+summary
    assert 'u3' in urls  # 2 of 3 words present
    assert 'u4' not in urls


def test_get_articles_by_keyword_returns_empty_when_dataframe_empty(monkeypatch):
    app_module = load_app_module()
    monkeypatch.setattr(app_module, 'read_scraped_articles', lambda: pd.DataFrame())
    assert app_module.get_articles_by_keyword('anything') == {'articles': []}


def test_dashboard_and_visualisation_and_scraper_stats_map_exceptions(monkeypatch):
    app_module = load_app_module()

    monkeypatch.setattr(app_module.dashboard_methods, 'load_dashboard_data', lambda: (_ for _ in ()).throw(FileNotFoundError('missing dashboard file')))
    with pytest.raises(app_module.HTTPException) as exc1:
        app_module.get_bias_dashboard()
    assert exc1.value.status_code == 404

    monkeypatch.setattr(app_module.visualisations, 'load_visualisations_data', lambda: (_ for _ in ()).throw(RuntimeError('boom')))
    with pytest.raises(app_module.HTTPException) as exc2:
        app_module.get_visualisations()
    assert exc2.value.status_code == 500

    monkeypatch.setattr(app_module.explanations, 'load_scraper_stats', lambda: (_ for _ in ()).throw(FileNotFoundError('missing stats')))
    with pytest.raises(app_module.HTTPException) as exc3:
        app_module.get_scraper_stats()
    assert exc3.value.status_code == 404
