import json
from fastapi import FastAPI, HTTPException

from models.datapayload import DataPayload, SummarisePayload, ModelDataPayload

from service.predict_service import getStatement, fact_check, summarise, summarise_data

# logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/")
def health_check():
    # return 200
    return {"status": "ok"}

@app.get("/factcheck")
def health_check2():
    # return 200
    return {"status": "ok"}

@app.post("/factcheck/predict/statements")
async def getStatements(json_payload: DataPayload):
    statements = await getStatement(json_payload)
    return {"response": statements}

@app.post("/factcheck/summarise")
async def summary(json_payload: SummarisePayload):
    text = json_payload.content
    try:
        summary_content = await summarise(text)
        return {"response": summary_content}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    
@app.post("/factcheck/summarise/model-data")
async def summarise_model_data(json_payload: ModelDataPayload):
    try:
        summary_content = await summarise_data(json_payload)
        response_json = json.loads(summary_content)
        return {"response": response_json}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.post("/factcheck/predict/fact-check")
async def predict(json_payload: DataPayload):
    original_article_title = json_payload.title
    try:
        logger.info(f"[Factcheck Service] Received payload: {json_payload}")
        statement_list = await getStatement(json_payload)
        logger.info(f"[Factcheck Service] Statements extracted: {statement_list}")
        if not statement_list:
            raise HTTPException(status_code=400, detail="No statements found in the payload.")
        
        facts = await fact_check(statement_list, original_article_title)
        logger.info(f"[Factcheck Service] Facts extracted: {facts}")
        if not facts:
            raise HTTPException(status_code=400, detail="No facts found in the payload.")
        
        return {"response": facts}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8005, reload=True)
    