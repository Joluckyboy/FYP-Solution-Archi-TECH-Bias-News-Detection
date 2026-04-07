import importlib
import sys
from types import SimpleNamespace
from werkzeug.exceptions import BadRequest

import pytest


def load_methods_module():
    for name in ['methods', 'vars']:
        sys.modules.pop(name, None)
    return importlib.import_module('methods')


def test_sample_text_returns_original_for_short_text():
    methods = load_methods_module()
    text = 'This is short. Still short.'
    assert methods._sample_text(text, max_chars=100) == text


def test_sample_text_preserves_beginning_middle_and_end_for_long_text():
    methods = load_methods_module()
    sentences = [f'Sentence {i}.' for i in range(1, 31)]
    text = ' '.join(sentences)

    sampled = methods._sample_text(text, max_chars=400)

    assert 'Sentence 1.' in sampled
    assert any(s in sampled for s in ['Sentence 12.', 'Sentence 13.', 'Sentence 14.'])
    assert any(s in sampled for s in ['Sentence 28.', 'Sentence 29.', 'Sentence 30.'])
    assert len(sampled) <= 400


def test_sample_text_falls_back_to_character_truncation_when_no_sentence_boundaries():
    methods = load_methods_module()
    text = 'x' * 200
    sampled = methods._sample_text(text, max_chars=50)
    assert sampled == 'x' * 50


def test_sample_text_truncates_at_sentence_boundary_when_possible():
    methods = load_methods_module()
    text = ' '.join(['A very long sentence with filler text.' for _ in range(500)])
    sampled = methods._sample_text(text, max_chars=200)
    assert len(sampled) <= 200
    assert sampled.endswith('.') or len(sampled) == 200


@pytest.mark.parametrize(
    'raw,expected',
    [
        (
            [{'statement': 'Claim', 'accuracy': 'FACTUAL', 'explanation': 'Correct', 'citations': 'https://a'}],
            [{'statement': 'Claim', 'correctness': 'factual', 'explanation': 'Correct', 'citations': ['https://a']}],
        ),
        (
            [{'statement': 'Claim', 'correctness': 'not-valid', 'explanation': 'Unknown', 'citations': {'bad': 1}}],
            [{'statement': 'Claim', 'correctness': 'cannot be determined', 'explanation': 'Unknown', 'citations': []}],
        ),
        (
            [{'statement': 123, 'correctness': 'factual', 'explanation': 'x', 'citations': []}],
            [],
        ),
    ],
)
def test_sanitize_factcheck_data_normalizes_and_filters(raw, expected):
    methods = load_methods_module()
    assert methods.sanitize_factcheck_data(raw) == expected


def test_extract_news_aborts_for_invalid_url(monkeypatch):
    methods = load_methods_module()

    def fake_get(*args, **kwargs):
        return SimpleNamespace(status_code=400, json=lambda: {})

    monkeypatch.setattr(methods.requests, 'get', fake_get)

    with pytest.raises(BadRequest) as exc:
        methods.extract_news('not-a-url')

    assert exc.value.code == 400
    assert exc.value.description == 'Invalid URL format'


def test_get_sentiment_samples_long_text_and_persists_result(monkeypatch):
    methods = load_methods_module()
    calls = {'post': [], 'put': []}
    original_text = ' '.join([f'Sentence {i}. This is extra filler text to make the article long enough for sampling.' for i in range(1, 220)])

    def fake_post(url, json=None, timeout=None):
        calls['post'].append({'url': url, 'json': json, 'timeout': timeout})
        return SimpleNamespace(
            status_code=200,
            json=lambda: {
                'sentiment_result': {'positive': 0.7, 'negative': 0.1, 'neutral': 0.2},
                'sentence_sentiments': [{'sentence': 'A', 'label': 'positive'}],
            },
        )

    def fake_put(url, json=None, timeout=None):
        calls['put'].append({'url': url, 'json': json, 'timeout': timeout})
        return SimpleNamespace(status_code=200, json=lambda: {'ok': True})

    monkeypatch.setattr(methods.requests, 'post', fake_post)
    monkeypatch.setattr(methods.requests, 'put', fake_put)

    result = methods.get_sentiment(original_text, 'https://example.com/news', 'Headline')

    assert result['sentiment_result']['positive'] == 0.7
    assert calls['post'][0]['url'].endswith('/sentiment/analyze_sentiment')
    assert len(calls['post'][0]['json']['text']) < len(original_text)
    assert calls['put'][0]['url'].endswith('/database/sentiment/')
    assert calls['put'][0]['json']['sentiment_result']['sentence_sentiments'] == [{'sentence': 'A', 'label': 'positive'}]


def test_get_sentiment_returns_empty_dict_on_service_failure(monkeypatch):
    methods = load_methods_module()

    def fake_post(*args, **kwargs):
        raise RuntimeError('service down')

    monkeypatch.setattr(methods.requests, 'post', fake_post)
    assert methods.get_sentiment('text', 'https://example.com', 'Title') == {}


def test_get_emotion_returns_empty_dict_on_service_failure(monkeypatch):
    methods = load_methods_module()

    def fake_post(*args, **kwargs):
        raise RuntimeError('service down')

    monkeypatch.setattr(methods.requests, 'post', fake_post)
    assert methods.get_emotion('text', 'https://example.com', 'Title') == {}


def test_get_propaganda_persists_result(monkeypatch):
    methods = load_methods_module()
    captured = {}

    def fake_post(url, json=None, timeout=None):
        captured['post'] = {'url': url, 'json': json, 'timeout': timeout}
        return SimpleNamespace(json=lambda: {'propaganda_result': {'severity': 'Low'}})

    def fake_put(url, json=None, timeout=None):
        captured['put'] = {'url': url, 'json': json, 'timeout': timeout}
        return SimpleNamespace(status_code=200, json=lambda: {'ok': True})

    monkeypatch.setattr(methods.requests, 'post', fake_post)
    monkeypatch.setattr(methods.requests, 'put', fake_put)

    result = methods.get_propaganda('body', 'https://example.com', 'Title')

    assert result == {'propaganda_result': {'severity': 'Low'}}
    assert captured['post']['url'].endswith('/propaganda/analyze_propaganda')
    assert captured['put']['json']['propaganda_result'] == {'severity': 'Low'}


def test_get_fact_check_sanitizes_and_persists(monkeypatch):
    methods = load_methods_module()
    saved = {}

    def fake_post(url, json=None):
        return SimpleNamespace(json=lambda: {
            'response': [
                {'statement': 'Claim', 'accuracy': 'FACTUAL', 'explanation': 'Verified', 'citations': 'https://source.test'},
                {'statement': 'Claim 2', 'correctness': 'bad-value', 'explanation': 'Unknown', 'citations': None},
            ]
        })

    def fake_put(url, json=None):
        saved['url'] = url
        saved['json'] = json
        return SimpleNamespace(status_code=200, json=lambda: {'ok': True})

    monkeypatch.setattr(methods.requests, 'post', fake_post)
    monkeypatch.setattr(methods.requests, 'put', fake_put)

    result = methods.get_fact_check('body', 'https://example.com/story', 'Title')

    assert result[0]['correctness'] == 'factual'
    assert result[0]['citations'] == ['https://source.test']
    assert result[1]['correctness'] == 'cannot be determined'
    assert saved['url'].endswith('/database/factcheck/')
    assert saved['json']['factcheck_result'] == result


def test_get_fact_check_returns_empty_list_when_service_payload_missing_response(monkeypatch):
    methods = load_methods_module()

    monkeypatch.setattr(methods.requests, 'post', lambda *args, **kwargs: SimpleNamespace(json=lambda: {'error': 'keys missing'}))
    assert methods.get_fact_check('body', 'https://example.com/story', 'Title') == []


def test_get_summarise_returns_empty_dict_when_service_payload_missing_response(monkeypatch):
    methods = load_methods_module()

    monkeypatch.setattr(methods.requests, 'post', lambda *args, **kwargs: SimpleNamespace(json=lambda: {'error': 'keys missing'}))
    assert methods.get_summarise('body', 'https://example.com/story', 'Title') == {}


def test_get_data_summary_fetches_missing_analysis_inputs_from_db(monkeypatch):
    methods = load_methods_module()
    saved = {}

    monkeypatch.setattr(methods, 'get_news', lambda url: {
        'sentiment_result': {'positive': 0.1},
        'emotion_result': {'joy': 0.9},
        'propaganda_result': {'severity': 'Low'},
        'summarise_result': 'summary',
        'data_summary': {'existing': 'keep'},
    })

    def fake_post(url, json=None):
        assert json['sentiment_result'] == {'positive': 0.1}
        assert json['emotion_result'] == {'joy': 0.9}
        assert json['propaganda_result'] == {'severity': 'Low'}
        assert json['summarise_result'] == 'summary'
        return SimpleNamespace(json=lambda: {'response': {'emotion_summary': 'new'}})

    def fake_put(url, json=None):
        saved['url'] = url
        saved['json'] = json
        return SimpleNamespace(status_code=200, json=lambda: {'ok': True})

    monkeypatch.setattr(methods.requests, 'post', fake_post)
    monkeypatch.setattr(methods.requests, 'put', fake_put)

    result = methods.get_data_summary(
        text='body',
        url='https://example.com/news',
        title='Headline',
        trigger='refresh',
    )

    assert result.get('emotion_summary') == 'new'
    assert saved['url'].endswith('/database/ModelDataSummary/')
    assert saved['json']['url'] == 'https://example.com/news'
    assert saved['json']['data_summary'].get('emotion_summary') == 'new'


def test_get_data_summary_persists_generated_summary(monkeypatch):
    methods = load_methods_module()
    saved = {}

    monkeypatch.setattr(methods, 'get_news', lambda url: {
        'data_summary': {'sentiment_summary': 'old'}
    })

    def fake_post(url, json=None):
        assert json['sentiment_result'] == {'positive': 0.1}
        assert json['emotion_result'] == {'joy': 0.8}
        assert json['propaganda_result'] == {'severity': 'Low'}
        assert json['summarise_result'] == 'summary'
        return SimpleNamespace(json=lambda: {'response': {'emotion_summary': 'new'}})

    def fake_put(url, json=None):
        saved['url'] = url
        saved['json'] = json
        return SimpleNamespace(status_code=200, json=lambda: {'ok': True})

    monkeypatch.setattr(methods.requests, 'post', fake_post)
    monkeypatch.setattr(methods.requests, 'put', fake_put)

    result = methods.get_data_summary(
        text='body',
        url='https://example.com/news',
        title='Headline',
        trigger='test',
        sentiment={'positive': 0.1},
        emotion={'joy': 0.8},
        propaganda={'severity': 'Low'},
        summarise='summary',
    )

    assert result.get('emotion_summary') == 'new'
    assert saved['url'].endswith('/database/ModelDataSummary/')
    assert saved['json']['url'] == 'https://example.com/news'
    assert saved['json']['data_summary'].get('emotion_summary') == 'new'


def test_get_data_summary_returns_empty_dict_for_malformed_service_response(monkeypatch):
    methods = load_methods_module()

    monkeypatch.setattr(methods.requests, 'post', lambda *args, **kwargs: SimpleNamespace(json=lambda: {'response': 'not-a-dict'}))
    assert methods.get_data_summary('body', 'https://example.com', 'Title') == {}
