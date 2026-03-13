import importlib
import sys

import pytest


def load_app_module():
    for name in ['app', 'methods', 'redis_cache', 'vars', 's3_sync', 'api_models']:
        sys.modules.pop(name, None)
    return importlib.import_module('app')


def test_new_query_endpoint_full_new_article_flow(monkeypatch):
    app_module = load_app_module()

    final_news = {
        'url': 'https://example.com/story',
        'id': 'news-001',
        'title': 'Headline',
        'content': 'Body',
        'sentiment_result': {'positive': 0.5},
        'emotion_result': {'joy': 0.8},
        'propaganda_result': {'severity': 'Low'},
        'factcheck_result': [{'statement': 'Claim', 'correctness': 'factual', 'explanation': 'Verified', 'citations': ['https://source.test']}],
        'summarise_result': 'Summary',
        'data_summary': {'overview': 'Done'},
    }

    monkeypatch.setattr(app_module.redis_cache, 'get_cached_result', lambda url: None)
    monkeypatch.setattr(app_module.redis_cache, 'is_analysis_complete', lambda data: True)
    monkeypatch.setattr(app_module.redis_cache, 'cache_result', lambda *args, **kwargs: None)
    monkeypatch.setattr(app_module.methods, 'check_exists', lambda url: {'exists': False})
    monkeypatch.setattr(app_module.methods, 'extract_news', lambda url: {'headline': 'Headline', 'body': 'Body'})
    monkeypatch.setattr(app_module.methods, 'create_news', lambda url, title, content: {'id': 'news-001'})
    monkeypatch.setattr(app_module.methods, 'get_news', lambda url: final_news)
    monkeypatch.setattr(app_module.methods, 'get_sentiment', lambda *args, **kwargs: {'sentiment_result': {'positive': 0.5}})
    monkeypatch.setattr(app_module.methods, 'get_emotion', lambda *args, **kwargs: {'emotion_result': {'joy': 0.8}})
    monkeypatch.setattr(app_module.methods, 'get_propaganda', lambda *args, **kwargs: {'propaganda_result': {'severity': 'Low'}})
    monkeypatch.setattr(app_module.methods, 'get_summarise', lambda *args, **kwargs: {'response': 'Summary'})
    monkeypatch.setattr(app_module.methods, 'get_fact_check', lambda *args, **kwargs: [{'statement': 'Claim', 'correctness': 'factual', 'explanation': 'Verified', 'citations': ['https://source.test']}])
    monkeypatch.setattr(app_module.methods, 'get_data_summary', lambda *args, **kwargs: {'overview': 'Done'})

    response = app_module.new_query(app_module.URLwithBG(url='https://example.com/story', background=False, force=False))

    assert response['id'] == 'news-001'
    assert response['data_summary'] == {'overview': 'Done'}


def test_new_query_endpoint_returns_cached_existing_article_without_reanalysis(monkeypatch):
    app_module = load_app_module()

    cached = {
        'url': 'https://example.com/cached',
        'id': 'news-002',
        'title': 'Cached headline',
        'content': 'Cached body',
        'sentiment_result': {'positive': 0.1},
        'emotion_result': {'joy': 0.2},
        'propaganda_result': {'severity': 'Low'},
        'factcheck_result': [{'statement': 'Claim', 'correctness': 'factual', 'explanation': 'Verified', 'citations': ['https://source.test']}],
        'summarise_result': 'Summary',
        'data_summary': {'overview': 'Cached'},
    }

    monkeypatch.setattr(app_module.redis_cache, 'get_cached_result', lambda url: cached)
    monkeypatch.setattr(app_module.redis_cache, 'is_analysis_complete', lambda data: True)

    def should_not_run(*args, **kwargs):
        raise AssertionError('downstream services should not run for a complete cached article')

    monkeypatch.setattr(app_module.methods, 'check_exists', should_not_run)

    response = app_module.new_query(app_module.URLwithBG(url='https://example.com/cached', background=False, force=False))

    assert response['id'] == 'news-002'
    assert response['title'] == 'Cached headline'


def test_new_query_force_flag_is_forwarded_to_process_url(monkeypatch):
    app_module = load_app_module()
    captured = {}

    def fake_process(url, return_news=False, background=True, force_reanalyze=False):
        captured.update({
            'url': url,
            'return_news': return_news,
            'background': background,
            'force_reanalyze': force_reanalyze,
        })
        return {'ok': True}

    monkeypatch.setattr(app_module, 'process_url', fake_process)
    response = app_module.new_query(app_module.URLwithBG(url='https://example.com/force', background=False, force=True))

    assert response == {'ok': True}
    assert captured == {
        'url': 'https://example.com/force',
        'return_news': True,
        'background': False,
        'force_reanalyze': True,
    }


def test_retrieve_existing_query_returns_db_news(monkeypatch):
    import asyncio

    app_module = load_app_module()
    monkeypatch.setattr(app_module.methods, 'get_news_by_id', lambda news_id: {'id': news_id, 'title': 'Saved article'})
    response = asyncio.run(app_module.retrieve_query('news-42'))
    assert response == {'id': 'news-42', 'title': 'Saved article'}
