from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse

from api_models import NewsItem, QuizItem, SubscriptionItem
import news_driver as news_methods
import quiz_driver as quiz_methods
import quiz_templates as quiz_templates

from typing import List

app = FastAPI(
    title="DB App API",
    description="API DB connector to Supabase.",
    version="1.0.0"
)


@app.get("/")
def health_check():
    # return 200
    return {"status": "ok"}


@app.get("/database")
def health_check2():
    # return 200
    return {"status": "ok"}


@app.post("/database/check_exists/", responses={
    200: {
        "description": "URL exists",
        "content": {
            "application/json": {
                "example": {
                    "exists": True
                }
            }
        }
    },
    404: {
        "description": "URL does not exist",
        "content": {
            "application/json": {
                "example": {
                    "exists": False
                }
            }
        }
    }
})
def check_url_exists(data: NewsItem):
    exists = news_methods.check_url_exists(data.url)
    if exists:
        return JSONResponse(status_code=200, content={"exists": True})
    return JSONResponse(status_code=404, content={"exists": False})


@app.post("/database/", responses={
    200: {
        "description": "News created successfully",
        "content": {
            "application/json": {
                "example": {
                    "news_id": "1234567890abcdef"
                }
            }
        }
    },
    201: {
        "description": "News already exists",
        "content": {
            "application/json": {
                "example": {
                    "url": "https://example.com/database1",
                    "title": "Sample News Title",
                    "content": "This is the content of the sample news article."
                }
            }
        }
    }
})

def create_news(data: NewsItem):
    # Check if URL already exists
    if news_methods.check_url_exists(data.url):
        news = news_methods.read_document_by_url(data.url)
        # If uploader now provided but wasn't saved before, update it
        if data.uploader and not news.get("uploader"):
            news_methods.update_uploader_by_url(data.url, data.uploader)
        return JSONResponse(status_code=201, content=news)

    news_data = {
        "url": data.url,
        "title": data.title,
        "content": data.content,
        "uploader": data.uploader or "",   # ← add this line
    }
    news_id = news_methods.create_document(news_data)
    return JSONResponse(status_code=200, content={"id": news_id})

@app.get("/database/getAll/", responses={
    200: {
        "description": "all news retrieved successfully",
        "content": {
            "application/json": {
                "example": [{
                    "url": "https://example.com/database1",
                    "title": "Sample News Title",
                    "content": "This is the content of the sample news article."
                }, {
                    "url": "https://example.com/database2",
                    "title": "Sample News Title",
                    "content": "This is the content of the sample news article."
                },
                ]
            }
        }
    }
})
def get_all_news():
    news = news_methods.read_all_documents()
    return JSONResponse(status_code=200, content={"news_id": news})


@app.post("/database/getByURL/", responses={
    200: {
        "description": "News retrieved successfully",
        "content": {
            "application/json": {
                "example": {
                    "url": "https://example.com/database1",
                    "title": "Sample News Title",
                    "content": "This is the content of the sample news article."
                }
            }
        }
    },
    404: {
        "detail": "News not found"
    }
})
def get_news_by_filter(data: NewsItem):
    news = news_methods.read_document_by_url(data.url)
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    return JSONResponse(status_code=200, content=news)


@app.get("/database/getByID/{news_id}", responses={
    200: {
        "description": "News retrieved successfully",
        "content": {
            "application/json": {
                "example": {
                    "url": "https://example.com/database1",
                    "title": "Sample News Title",
                    "content": "This is the content of the sample news article."
                }
            }
        }
    },
    404: {
        "detail": "News not found"
    }
})
def get_news_by_id(news_id: str):
    news = news_methods.read_document_by_id(news_id)
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    return JSONResponse(status_code=200, content=news)


@app.get("/database/stream_news")
async def stream_news(news_id: str):
    """
    Stream news data from the database.
    """
    return StreamingResponse(news_methods.stream_document_by_id(news_id), media_type="text/event-stream")


@app.put("/database/summarise/", responses={
    200: {
        "description": "Summary result updated successfully",
        "content": {
            "application/json": {
                "example": {
                    "message": "Summary result updated successfully"
                }
            }
        }
    }
})
def update_news_summary_by_url(data: NewsItem):
    news_methods.update_summary_by_url(data.url, data.summarise_result)
    return JSONResponse(status_code=200, content={"message": "Summary result updated successfully"})


@app.put("/database/ModelDataSummary/", responses={
    200: {
        "description": "Model data summary result updated successfully",
        "content": {
            "application/json": {
                "example": {
                    "message": "Model data summary result updated successfully"
                }
            }
        }
    }
})
def update_news_data_summary_by_url(data: NewsItem):
    news_methods.update_model_data_summary_by_url(data.url, data.data_summary)
    return JSONResponse(status_code=200, content={"message": "Model data summary result updated successfully"})


@app.put("/database/factcheck/", responses={
    200: {
        "description": "Sentiment result updated successfully",
        "content": {
            "application/json": {
                "example": {
                    "message": "Sentiment result updated successfully"
                }
            }
        }
    }
})
def update_news_factcheck_by_url(data: NewsItem):
    factcheck_result_dicts = [
        fact.model_dump() for fact in data.factcheck_result] if data.factcheck_result else []

    news_methods.update_factcheck_by_url(data.url, factcheck_result_dicts)
    return JSONResponse(status_code=200, content={"message": "Fact-check result updated successfully"})


@app.put("/database/sentiment/", responses={
    200: {
        "description": "Sentiment result updated successfully",
        "content": {
            "application/json": {
                "example": {
                    "message": "Sentiment result updated successfully"
                }
            }
        }
    }
})
def update_news_sentiment_by_url(data: NewsItem):
    news_methods.update_sentiment_by_url(data.url, data.sentiment_result)
    return JSONResponse(status_code=200, content={"message": "Sentiment result updated successfully"})


@app.put("/database/emotion/", responses={
    200: {
        "description": "Emotion result updated successfully",
        "content": {
            "application/json": {
                "example": {
                    "message": "Emotion result updated successfully"
                }
            }
        }
    }
})
def update_news_emotion_by_url(data: NewsItem):
    news_methods.update_emotion_by_url(data.url, data.emotion_result)
    return JSONResponse(status_code=200, content={"message": "Emotion result updated successfully"})


@app.put("/database/propaganda/", responses={
    200: {
        "description": "Propaganda result updated successfully",
        "content": {
            "application/json": {
                "example": {
                    "message": "Propaganda result updated successfully"
                }
            }
        }
    }
})
def update_news_propaganda_by_url(data: NewsItem):
    news_methods.update_propaganda_by_url(data.url, data.propaganda_result)
    return JSONResponse(status_code=200, content={"message": "Propaganda result updated successfully"})


@app.put("/database/political_bias/", responses={
    200: {
        "description": "Political bias result updated successfully",
        "content": {
            "application/json": {
                "example": {
                    "message": "Political bias result updated successfully"
                }
            }
        }
    }
})
def update_news_political_bias_by_url(data: NewsItem):
    news_methods.update_political_bias_by_url(data.url, data.political_bias_result)
    return JSONResponse(status_code=200, content={"message": "Political bias result updated successfully"})


@app.put("/database/{news_id}/sentiment/", responses={
    200: {
        "description": "Sentiment result updated successfully",
        "content": {
            "application/json": {
                "example": {
                    "message": "Sentiment result updated successfully"
                }
            }
        }
    }
})
def update_news_sentiment(news_id: str, data: NewsItem):
    news_methods.update_sentiment_result(news_id, data.sentiment_result)
    return JSONResponse(status_code=200, content={"message": "Sentiment result updated successfully"})


@app.put("/database/{news_id}/emotion/", responses={
    200: {
        "description": "Emotion result updated successfully",
        "content": {
            "application/json": {
                "example": {
                    "message": "Emotion result updated successfully"
                }
            }
        }
    }
})
def update_news_emotion(news_id: str, data: NewsItem):
    news_methods.update_emotion_result(news_id, data.emotion_result)
    return JSONResponse(status_code=200, content={"message": "Emotion result updated successfully"})


@app.put("/database/{news_id}/propaganda/", responses={
    200: {
        "description": "Propaganda result updated successfully",
        "content": {
            "application/json": {
                "example": {
                    "message": "Propaganda result updated successfully"
                }
            }
        }
    }
})
def update_news_propaganda(news_id: str, data: NewsItem):
    news_methods.update_propaganda_result(news_id, data.propaganda_result)
    return JSONResponse(status_code=200, content={"message": "Propaganda result updated successfully"})


@app.get("/database/getByDomain/{domain}", responses={
    200: {
        "description": "Articles for domain retrieved successfully",
    }
})
def get_news_by_domain(domain: str):
    articles = news_methods.read_documents_by_domain(domain)
    return JSONResponse(status_code=200, content={"articles": articles})


@app.delete("/database/", responses={
    200: {
        "description": "News deleted successfully",
        "content": {
            "application/json": {
                "example": {
                    "deleted_count": 1
                }
            }
        }
    }
})
def delete_news(filter_data: NewsItem):
    deleted_count = news_methods.delete_documents(filter_data)
    return JSONResponse(status_code=200, content={"deleted_count": deleted_count})


@app.delete("/database/{news_id}", responses={
    200: {
        "description": "News deleted successfully",
        "content": {
            "application/json": {
                "example": {
                    "deleted_count": 1
                }
            }
        }
    }
})
def delete_news_by_id(news_id: str):
    deleted_count = news_methods.delete_document_by_id(news_id)
    return JSONResponse(status_code=200, content={"deleted_count": deleted_count})


# Quiz API
@app.post("/database/quiz/addMultiple", responses={
    200: {
        "description": "Quiz created successfully",
        "content": {
            "application/json": {
                "example": {
                    "quiz_id": "1234567890abcdef"
                }
            }
        }
    }
})
def add_multiple_quiz(data: List[QuizItem]):
    quiz_ids = []
    for item in data:
        quiz_data = {
            "question": item.question,
            "options": item.options,
            "answer": item.answer,
            "question_type": item.question_type,
            "debrief": item.debrief
        }
        quiz_id = quiz_methods.add_quiz_data(quiz_data)
        quiz_ids.append(quiz_id)
    return JSONResponse(status_code=200, content={"quiz_id": quiz_ids})


@app.post("/database/quiz/add", responses={
    200: {
        "description": "Quiz created successfully",
        "content": {
            "application/json": {
                "example": {
                    "quiz_id": "1234567890abcdef"
                }
            }
        }
    }
})
def add_quiz(data: QuizItem):
    quiz_data = {
        "question": data.question,
        "options": data.options,
        "answer": data.answer,
        "question_type": data.question_type,
        "debrief": data.debrief
    }
    quiz_id = quiz_methods.add_quiz_data(quiz_data)
    if not quiz_id:
        raise HTTPException(status_code=400, detail="add quiz failed")
    return JSONResponse(status_code=200, content={"quiz_id": quiz_id})


@app.get("/database/quiz/getAll", responses={
    200: {
        "description": "all quiz data retrieved successfully",
        "content": {
            "application/json": {
                "example": [{
                    "question": "Which headline is biased? \\n A: 'Candidate X Crushes Opponent in Fiery Debate, Exposing Lies and Weak Policies.' \\n B: 'Candidate X and Y Debate Economic Policies in Heated Exchange.'",
                    "options": ["A", "B", "Both"],
                    "answer": [0]
                }, {
                    "question": "'If you love your country, you must support this new policy. Only true patriots stand with us!' Which propaganda technique is being used?",
                    "options": ["Bandwagon Effect", "Fear Appeal", "Appeal to Patriotism", "Name-Calling"],
                    "answer": [2]
                },
                ]
            }
        }
    }
})
def get_all_quiz(question_type: str = Query(None, description="Type of quiz question to retrieve")):
    quiz = None
    if question_type:
        quiz = quiz_methods.get_all_quiz_data(question_type)
    else:
        quiz = quiz_methods.get_all_quiz_data()
    if not quiz:
        raise HTTPException(status_code=400, detail="get all quiz failed")
    return JSONResponse(status_code=200, content={"quiz": quiz})


@app.get("/database/quiz/getRandom", responses={
    200: {
        "description": "random quiz data retrieved successfully",
        "content": {
            "application/json": {
                "example": [{
                    "question": "Which headline is biased? \\n A: 'Candidate X Crushes Opponent in Fiery Debate, Exposing Lies and Weak Policies.' \\n B: 'Candidate X and Y Debate Economic Policies in Heated Exchange.'",
                    "options": ["A", "B", "Both"],
                    "answer": [0]
                }, {
                    "question": "'If you love your country, you must support this new policy. Only true patriots stand with us!' Which propaganda technique is being used?",
                    "options": ["Bandwagon Effect", "Fear Appeal", "Appeal to Patriotism", "Name-Calling"],
                    "answer": [2]
                },
                ]
            }
        }
    }
})
def get_random_quiz(number: int = Query(..., description="Number of random quiz questions to retrieve"), question_type: str = Query(None, description="Type of quiz question to retrieve")):
    quiz = None
    if question_type:
        quiz = quiz_methods.get_random_quiz_data(number, question_type)
    else:
        quiz = quiz_methods.get_random_quiz_data(number)

    if not quiz:
        raise HTTPException(status_code=400, detail="get random quiz failed")
    return JSONResponse(status_code=200, content={"quiz": quiz})


@app.post("/database/quiz/generate-and-save")
def generate_and_save_quiz(question_type: str = "bias"):
    """Generate a batch of general-knowledge quiz questions and persist to DB."""
    print(f"Generating questions for category: {question_type}")
    try:
        questions = quiz_templates.generate_quiz_from_analysis(question_type=question_type)
        print(f"Generated {len(questions)} questions")
    except Exception as e:
        print(f"Error generating questions: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"generation failed: {str(e)}")

    quiz_ids = []
    for q in questions:
        try:
            question_text = q.get("question")
            options = q.get("options") or []

            # Determine answer indices; prefer provided indices, else map from correct_answer
            answer = q.get("answer")
            if not answer:
                correct = q.get("correct_answer")
                if correct in options:
                    answer = [options.index(correct)]
                else:
                    # fallback to first option if mapping fails
                    answer = [0] if options else []

            payload = {
                "question": question_text,
                "options": options,
                "answer": answer,
                "question_type": question_type,
                "debrief": q.get("debrief") or q.get("explanation")
            }

            quiz_id = quiz_methods.add_quiz_data(payload)
            if quiz_id:
                quiz_ids.append(quiz_id)
        except Exception as e:
            # Skip problematic question, continue with the rest
            print(f"Error saving question: {e}")
            continue

    if not quiz_ids:
        raise HTTPException(status_code=500, detail="no questions saved")

    return JSONResponse(status_code=200, content={"quiz_ids": quiz_ids, "count": len(quiz_ids)})


@app.post("/database/quiz/seed/{category}", responses={
    200: {
        "description": "Seeded quiz questions for category",
        "content": {
            "application/json": {
                "example": {
                    "quiz_ids": ["uuid-1", "uuid-2"],
                    "category": "emotion"
                }
            }
        }
    }
})
def seed_quiz_category(category: str):
    """Generate AI questions for any category."""
    category = category.lower()
    # All categories now use AI generation with explicit category parameter
    questions = quiz_templates.generate_ai_quiz_questions(num_questions=20, question_type=category)

    quiz_ids = []
    for q in questions:
        question_text = q.get("question")
        options = q.get("options") or []
        answer = q.get("answer") or []
        payload = {
            "question": question_text,
            "options": options,
            "answer": answer,
            "question_type": category,
            "debrief": q.get("debrief")
        }
        quiz_id = quiz_methods.add_quiz_data(payload)
        if quiz_id:
            quiz_ids.append(quiz_id)

    return JSONResponse(status_code=200, content={"quiz_ids": quiz_ids, "category": category})


# ── Digest Subscriptions ─────────────────────────────────────────────────────

@app.post("/database/subscriptions/")
def create_subscription(item: SubscriptionItem):
    """Subscribe a Telegram user to the daily bias digest."""
    result = news_methods.create_subscription(item.telegram_user_id, item.chat_id)
    if result:
        return JSONResponse(status_code=200, content={"message": "Subscribed successfully", "data": result})
    raise HTTPException(status_code=500, detail="Failed to create subscription")


@app.delete("/database/subscriptions/{telegram_user_id}")
def remove_subscription(telegram_user_id: int):
    """Unsubscribe a Telegram user from the daily bias digest."""
    success = news_methods.remove_subscription(telegram_user_id)
    if success:
        return JSONResponse(status_code=200, content={"message": "Unsubscribed successfully"})
    raise HTTPException(status_code=404, detail="Subscription not found")


@app.get("/database/subscriptions/active")
def get_active_subscriptions():
    """Get all active digest subscriptions."""
    subs = news_methods.get_active_subscriptions()
    return JSONResponse(status_code=200, content={"subscriptions": subs})


@app.get("/database/articles/recent-biased")
def get_recent_biased_articles(hours: int = 24):
    """Get recently analyzed articles with non-center political bias."""
    articles = news_methods.get_recent_biased_articles(hours=hours)
    return JSONResponse(status_code=200, content={"articles": articles})
