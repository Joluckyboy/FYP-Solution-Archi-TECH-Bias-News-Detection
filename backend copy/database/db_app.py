from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse

from api_models import NewsItem, QuizItem
import news_driver as news_methods
import quiz_driver as quiz_methods

from typing import List

app = FastAPI(
    title="DB App API",
    description="API DB connector to MongoDB.",
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
        ## return 201 and the existing document 
        news = news_methods.read_document_by_url(data.url)
        return JSONResponse(status_code=201, content=news)

    news_data = {
        "url": data.url,
        "title": data.title,
        "content": data.content
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
                    },{
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
    factcheck_result_dicts = [fact.dict() for fact in data.factcheck_result] if data.factcheck_result else []
    
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
        item = {
            "question": item.question,
            "options": item.options,
            "answer": item.answer,
            "question_type": item.question_type,
            "debrief": item.debrief
        }
        quiz_id = quiz_methods.add_quiz_data(item)
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
    data = {
        "question": data.question,
        "options": data.options,
        "answer": data.answer,
        "question_type": data.question_type,
        "debrief": data.debrief
    }
    quiz_id = quiz_methods.add_quiz_data(data)
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
                    },{
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
                    },{
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

