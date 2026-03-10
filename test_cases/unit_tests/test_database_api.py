import importlib
import json
import sys

import pytest


def load_db_app_module():
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    db_dir = str(root / 'backend' / 'database')
    if db_dir in sys.path:
        sys.path.remove(db_dir)
    sys.path.insert(0, db_dir)
    import types
    if 'openai' not in sys.modules:
        openai_stub = types.ModuleType('openai')
        class OpenAI:
            def __init__(self, *args, **kwargs):
                pass
        openai_stub.OpenAI = OpenAI
        sys.modules['openai'] = openai_stub
    for name in ['db_app', 'news_driver', 'quiz_driver', 'api_models', 'quiz_templates', 'vars']:
        sys.modules.pop(name, None)
    return importlib.import_module('db_app')


def decode_json_response(response):
    return json.loads(response.body.decode('utf-8'))


def test_database_health_endpoints():
    db_app = load_db_app_module()
    assert db_app.health_check() == {'status': 'ok'}
    assert db_app.health_check2() == {'status': 'ok'}


def test_create_news_returns_existing_document_with_201(monkeypatch):
    db_app = load_db_app_module()

    monkeypatch.setattr(db_app.news_methods, 'check_url_exists', lambda url: True)
    monkeypatch.setattr(db_app.news_methods, 'read_document_by_url', lambda url: {'url': url, 'title': 'Existing', 'content': 'Body'})

    payload = db_app.NewsItem(url='https://example.com', title='New', content='Body')
    response = db_app.create_news(payload)

    assert response.status_code == 201
    assert decode_json_response(response)['title'] == 'Existing'


def test_create_news_inserts_new_document_with_200(monkeypatch):
    db_app = load_db_app_module()

    monkeypatch.setattr(db_app.news_methods, 'check_url_exists', lambda url: False)
    monkeypatch.setattr(db_app.news_methods, 'create_document', lambda data: 'news-123')

    payload = db_app.NewsItem(url='https://example.com/new', title='Headline', content='Body')
    response = db_app.create_news(payload)

    assert response.status_code == 200
    assert decode_json_response(response) == {'id': 'news-123'}


def test_get_all_news_wraps_result_under_news_id_key(monkeypatch):
    db_app = load_db_app_module()
    monkeypatch.setattr(db_app.news_methods, 'read_all_documents', lambda: [{'url': 'u1'}, {'url': 'u2'}])
    response = db_app.get_all_news()
    assert response.status_code == 200
    assert decode_json_response(response) == {'news_id': [{'url': 'u1'}, {'url': 'u2'}]}


def test_get_news_by_filter_returns_404_when_missing(monkeypatch):
    db_app = load_db_app_module()

    monkeypatch.setattr(db_app.news_methods, 'read_document_by_url', lambda url: None)

    payload = db_app.NewsItem(url='https://example.com/missing')
    with pytest.raises(Exception) as exc:
        db_app.get_news_by_filter(payload)
    assert getattr(exc.value, 'status_code', None) == 404
    assert getattr(exc.value, 'detail', None) == 'News not found'


def test_get_news_by_id_returns_404_when_missing(monkeypatch):
    db_app = load_db_app_module()
    monkeypatch.setattr(db_app.news_methods, 'read_document_by_id', lambda news_id: None)
    with pytest.raises(Exception) as exc:
        db_app.get_news_by_id('missing-id')
    assert getattr(exc.value, 'status_code', None) == 404


def test_update_summary_and_model_data_summary_delegate_to_driver(monkeypatch):
    db_app = load_db_app_module()
    captured = {}

    monkeypatch.setattr(db_app.news_methods, 'update_summary_by_url', lambda url, summary: captured.update({'summary': (url, summary)}))
    monkeypatch.setattr(db_app.news_methods, 'update_model_data_summary_by_url', lambda url, data: captured.update({'data_summary': (url, data)}))

    summary_resp = db_app.update_news_summary_by_url(db_app.NewsItem(url='https://example.com', summarise_result='sum'))
    data_resp = db_app.update_news_data_summary_by_url(db_app.NewsItem(url='https://example.com', data_summary={'k': 'v'}))

    assert summary_resp.status_code == 200
    assert data_resp.status_code == 200
    assert captured['summary'] == ('https://example.com', 'sum')
    assert captured['data_summary'] == ('https://example.com', {'k': 'v'})


def test_update_factcheck_serializes_pydantic_items(monkeypatch):
    db_app = load_db_app_module()
    captured = {}

    def fake_update(url, payload):
        captured['url'] = url
        captured['payload'] = payload

    monkeypatch.setattr(db_app.news_methods, 'update_factcheck_by_url', fake_update)

    api_models = importlib.import_module('api_models')
    payload = db_app.NewsItem(
        url='https://example.com/story',
        factcheck_result=[
            api_models.FactCheckItem(
                statement='Claim',
                correctness='factual',
                explanation='Verified',
                citations=['https://source.test'],
            )
        ],
    )
    response = db_app.update_news_factcheck_by_url(payload)

    assert response.status_code == 200
    assert captured['url'] == 'https://example.com/story'
    assert captured['payload'][0]['statement'] == 'Claim'
    assert captured['payload'][0]['citations'] == ['https://source.test']


def test_update_sentiment_emotion_and_propaganda_by_url_delegate_to_driver(monkeypatch):
    db_app = load_db_app_module()
    captured = {}

    monkeypatch.setattr(db_app.news_methods, 'update_sentiment_by_url', lambda url, payload: captured.update({'sentiment': (url, payload)}))
    monkeypatch.setattr(db_app.news_methods, 'update_emotion_by_url', lambda url, payload: captured.update({'emotion': (url, payload)}))
    monkeypatch.setattr(db_app.news_methods, 'update_propaganda_by_url', lambda url, payload: captured.update({'propaganda': (url, payload)}))

    db_app.update_news_sentiment_by_url(db_app.NewsItem(url='https://example.com', sentiment_result={'p': 1}))
    db_app.update_news_emotion_by_url(db_app.NewsItem(url='https://example.com', emotion_result={'joy': 1}))
    db_app.update_news_propaganda_by_url(db_app.NewsItem(url='https://example.com', propaganda_result={'sev': 'Low'}))

    assert captured['sentiment'] == ('https://example.com', {'p': 1})
    assert captured['emotion'] == ('https://example.com', {'joy': 1})
    assert captured['propaganda'] == ('https://example.com', {'sev': 'Low'})


def test_update_by_news_id_and_delete_endpoints_delegate_to_driver(monkeypatch):
    db_app = load_db_app_module()
    captured = {}

    monkeypatch.setattr(db_app.news_methods, 'update_sentiment_result', lambda news_id, payload: captured.update({'sentiment': (news_id, payload)}))
    monkeypatch.setattr(db_app.news_methods, 'update_emotion_result', lambda news_id, payload: captured.update({'emotion': (news_id, payload)}))
    monkeypatch.setattr(db_app.news_methods, 'update_propaganda_result', lambda news_id, payload: captured.update({'propaganda': (news_id, payload)}))
    monkeypatch.setattr(db_app.news_methods, 'delete_documents', lambda filter_data: 2)
    monkeypatch.setattr(db_app.news_methods, 'delete_document_by_id', lambda news_id: 1)

    db_app.update_news_sentiment('news-1', db_app.NewsItem(sentiment_result={'p': 1}))
    db_app.update_news_emotion('news-1', db_app.NewsItem(emotion_result={'joy': 1}))
    db_app.update_news_propaganda('news-1', db_app.NewsItem(propaganda_result={'sev': 'High'}))
    resp1 = db_app.delete_news(db_app.NewsItem(url='https://example.com'))
    resp2 = db_app.delete_news_by_id('news-1')

    assert captured['sentiment'] == ('news-1', {'p': 1})
    assert captured['emotion'] == ('news-1', {'joy': 1})
    assert captured['propaganda'] == ('news-1', {'sev': 'High'})
    assert decode_json_response(resp1) == {'deleted_count': 2}
    assert decode_json_response(resp2) == {'deleted_count': 1}


def test_add_quiz_returns_400_when_driver_fails(monkeypatch):
    db_app = load_db_app_module()
    monkeypatch.setattr(db_app.quiz_methods, 'add_quiz_data', lambda payload: None)
    with pytest.raises(Exception) as exc:
        db_app.add_quiz(db_app.QuizItem(question='Q', options=['A'], answer=[0], question_type='bias'))
    assert getattr(exc.value, 'status_code', None) == 400


def test_add_multiple_quiz_collects_all_ids(monkeypatch):
    db_app = load_db_app_module()
    counter = {'i': 0}

    def fake_add(payload):
        counter['i'] += 1
        return f"quiz-{counter['i']}"

    monkeypatch.setattr(db_app.quiz_methods, 'add_quiz_data', fake_add)
    items = [
        db_app.QuizItem(question='Q1', options=['A'], answer=[0], question_type='bias'),
        db_app.QuizItem(question='Q2', options=['B'], answer=[0], question_type='bias'),
    ]
    response = db_app.add_multiple_quiz(items)
    assert decode_json_response(response) == {'quiz_id': ['quiz-1', 'quiz-2']}


def test_get_all_quiz_returns_400_when_no_quiz_found(monkeypatch):
    db_app = load_db_app_module()
    monkeypatch.setattr(db_app.quiz_methods, 'get_all_quiz_data', lambda *args, **kwargs: None)
    with pytest.raises(Exception) as exc:
        db_app.get_all_quiz(question_type='bias')
    assert getattr(exc.value, 'status_code', None) == 400


def test_get_random_quiz_passes_number_and_question_type(monkeypatch):
    db_app = load_db_app_module()

    monkeypatch.setattr(
        db_app.quiz_methods,
        'get_random_quiz_data',
        lambda number, question_type=None: [{'id': '1', 'question_type': question_type, 'question': 'Q'}],
    )

    response = db_app.get_random_quiz(number=5, question_type='bias')

    assert response.status_code == 200
    assert decode_json_response(response)['quiz'][0]['question_type'] == 'bias'


def test_generate_and_save_quiz_maps_correct_answer_to_index(monkeypatch):
    db_app = load_db_app_module()
    saved = []

    monkeypatch.setattr(db_app.quiz_templates, 'generate_quiz_from_analysis', lambda question_type='bias': [
        {
            'question': 'Which is neutral?',
            'options': ['A', 'B', 'C'],
            'correct_answer': 'B',
            'explanation': 'Because B is neutral',
        }
    ])
    monkeypatch.setattr(db_app.quiz_methods, 'add_quiz_data', lambda payload: saved.append(payload) or 'quiz-1')

    response = db_app.generate_and_save_quiz(question_type='bias')
    body = decode_json_response(response)

    assert body['quiz_ids'] == ['quiz-1']
    assert saved[0]['answer'] == [1]
    assert saved[0]['debrief'] == 'Because B is neutral'
