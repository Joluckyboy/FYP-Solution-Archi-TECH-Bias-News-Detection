import re
import json
import requests

from config.config import Config
from models.datapayload import DataPayload
from models.datapayload import ModelDataPayload
from models.statementformat import StatementFormat
from models.predictformat import PredictFormat
from models.modeldataformat import ModelDataFormat


def processStatement(content):
    cleaned_content = re.sub(r"```json|```", "", content).strip()
    statements_json = json.loads(cleaned_content)
    statements_list = [item["statement"] for item in statements_json]
    return statements_list

async def summarise(text: str) -> str:
    try:
        MODEL = "llama-3.3-70b-versatile"
        payload = {
            "model": f"{MODEL}",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a summariser and will only assist with tasks related to summarising. You are to take inputs and summarise the contents and return the result."
                },
                {
                    "role": "user",
                    "content": f"Summarise the following content: {text}"
                },
            ]
        }
        
        response = requests.post(Config.DEEPSEEK_URL, headers=Config.HEADERS_DS, json=payload)
        print(f"Summarise API status: {response.status_code}")
        if response.status_code != 200:
            print(f"Summarise API error response: {response.text}")
            raise Exception(f"API returned status {response.status_code}: {response.text}")
        
        response_data = response.json()
        content = response_data['choices'][0]['message']['content']
        return content.strip()
    except Exception as e:
        print(f"⚠️ Summarise exception: {str(e)}")
        raise Exception(f"Failed to summarise article: {str(e)}")


async def summarise_data(json_payload: ModelDataPayload):
    try:
        MODEL = "llama-3.3-70b-versatile"
        payload = {
            "model": f"{MODEL}",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert at summarising information and drawing inferences from a set of data. You will perform such a summary only and nothing else. Your role is to take a look at JSON data and draw inferences from the data so that a reader can easily interpret the all the data holistically and not in silo."
                },
                {
                    "role": "user",
                    "content": f"The data is: {json_payload}"
                },
                {
                    "role": "user",
                    "content": "Please output JSON object(s) containing the following fields: sentiment_summary, emotion_summary, propaganda_summary. These summaries should be short paragraphs describing the data in layman terms to guide readers through understanding one data point then leading them to the next. Make use of summarise_result to understand what the data is about. Besides the specified format, do not mention anything else."
                }
            ],
            "response_format": {
                "type": "json_object"
            }
        }

        response = requests.post(Config.DEEPSEEK_URL, headers=Config.HEADERS_DS, json=payload)
        print(f"Summarise data API status: {response.status_code}")
        if response.status_code != 200:
            print(f"Summarise data API error response: {response.text}")
            raise Exception(f"API returned status {response.status_code}: {response.text}")
        
        response_data = response.json()
        content = response_data['choices'][0]['message']['content']
        return content.strip()
    except Exception as e:
        raise Exception(f"Failed to summarise data: {str(e)}")


async def getStatement(json_payload: DataPayload):
    try:
        content = json_payload.content
        model = "llama-3.3-70b-versatile"
        if Config.MODEL == "deepseek":
            model = "llama-3.3-70b-versatile"
        
        if model == "sonar":
            payload = {
                "model": f"{model}",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a content auditor and will only assist with tasks related to this. Your role is to analyze articles and identify statements that may be factually incorrect or require further investigation."
                    },
                    {
                        "role": "user",
                        "content": f"The article content to audit is: {content}. Please output JSON object(s) containing the following fields: statement. Besides the specified format, do not mention anything else."
                    },
                ],
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {"schema": StatementFormat.model_json_schema()},
                },
            }
        else:
            payload = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a content auditor and will only assist with tasks related to this. Your role is to analyze articles and identify statements that may be factually incorrect or require further investigation.\n"
                                   f"The JSON object must use the schema: [{json.dumps(StatementFormat.model_json_schema(), indent=2)}]",
                    },
                    {
                        "role": "user",
                        "content": f"The article content to audit is: {content}. Please output a JSON array of objects, each containing the following field: statement. Besides the specified format, do not mention anything else."
                    },
                ],
                "model": f"{model}",
                "temperature": 0,
                "stream": False
            }
        
        CHATURL = Config.PERPLEXITY_URL if model == "sonar" else Config.DEEPSEEK_URL
        HEADER = Config.HEADERS if model == "sonar" else Config.HEADERS_DS
        
        response = requests.post(CHATURL, headers=HEADER, json=payload)
        print(f"GetStatement API status: {response.status_code}")
        if response.status_code != 200:
            print(f"GetStatement API error response: {response.text}")
            raise Exception(f"API returned status {response.status_code}: {response.text}")
            
        response_data = response.json()
        if model == "sonar":
            raw_content = response_data["choices"][0]["message"]["content"]
            statements_list = processStatement(raw_content)
            return statements_list
        else:
            content = response_data['choices'][0]['message']['content']
            statements_list = processStatement(content.strip())
            return statements_list
            
    except Exception as e:
        print(f"⚠️ GetStatement exception: {str(e)}")
        raise Exception(f"Failed to retrieve statements while processing article: {str(e)}")


async def fact_check(statements, original_article):
    """
    Optimized fact-checking: 1 API call per article instead of 1 per statement
    """
    try:
        model = "sonar-pro"
        
        # Strip existing numbering from statements to avoid duplication
        cleaned_statements = [re.sub(r"^\d+\.\s*", "", stmt) for stmt in statements]
        
        # Combine all statements into one prompt
        statements_text = "\n".join([f"{i+1}. {stmt}" for i, stmt in enumerate(cleaned_statements)])
        
        payload = {
            "model": f"{model}",
            "messages": [
                {
                    "role": "system",
                    "content": f"You are a fact-checker and will only assist with fact-checking tasks in Singapore for popular media outlet straitstimes and channel news asia (CNA). You are to analyse if statements provided are factual/unfactual/cannot be determined. Utilise citations relevant to Singapore to derive this. Provide an explanation with reference to quotes from the cited sources for your answer but do not use the original article titled: {original_article} in your citations."
                },
                {
                    "role": "user",
                    "content": f"The statement to fact-check is: {statements_text}. Please output JSON object(s) containing the following fields: statement, correctness (factual/unfactual/cannot be determined), and explanation. Besides the specified format, do not mention anything else."
                },
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "schema": {
                        "type": "array",
                        "items": PredictFormat.model_json_schema()
                    }
                },
            },
        }
        
        response = requests.post(Config.PERPLEXITY_URL, headers=Config.HEADERS, json=payload)
        print(f"Fact-check API status: {response.status_code}")
        
        # Handle various error scenarios
        if response.status_code == 402:
            raise Exception("⚠️ Perplexity credit limit exceeded! Wait for monthly reset or upgrade your plan.")
        elif response.status_code == 429:
            raise Exception("⚠️ Rate limit exceeded. Please try again later.")
        elif response.status_code == 401:
            raise Exception("⚠️ Authentication failed. Check your Perplexity API key.")
        elif response.status_code != 200:
            print(f"Fact-check API error response: {response.text}")
            raise Exception(f"API returned status {response.status_code}: {response.text}")
        
        response_data = response.json()
        raw_content = response_data["choices"][0]["message"]["content"]
        cleaned_content = re.sub(r"```json|```", "", raw_content).strip()
        results = json.loads(cleaned_content)
        
        # Strip numbering from statement field in LLM response
        for result in results:
            if "statement" in result:
                result["statement"] = re.sub(r"^\d+\.\s*", "", result["statement"])
        
        # Add citations to all results
        citations = response_data.get("citations", [])
        for result in results:
            result["citations"] = citations
        
        print(f"Successfully fact-checked {len(results)} statements in 1 API call")
        return results
        
    except Exception as e:
        print(f"⚠️ Fact-check exception: {str(e)}")
        raise Exception(f"Failed to fact-check statements: {str(e)}")
    

# Previous code to fact-check each statement individually
# async def fact_check(statements, original_article):
#     processed_results = []
    
#     model = "sonar-pro"     
#     for statement in statements:
#         try:
#             payload = {
#                 "model": f"{model}",
#                 "messages": [
#                     {
#                         "role": "system",
#                         "content": f"You are a fact-checker and will only assist with fact-checking tasks in Singapore for popular media outlet straitstimes and channel news asia (CNA). You are to analyse if statements provided are factual/unfactual/cannot be determined. Utilise citations relevant to Singapore to derive this. Provide an explanation with reference to quotes from the cited sources for your answer but do not use the original article titled: {original_article} in your citations."
#                     },
#                     {
#                         "role": "user",
#                         "content": f"The statement to fact-check is: {statement}. Please output JSON object(s) containing the following fields: statement, correctness (factual/unfactual/cannot be determined), and explanation. Besides the specified format, do not mention anything else."
#                     },
#                 ],
#                 "response_format": {
#                     "type": "json_schema",
#                     "json_schema": {"schema": PredictFormat.model_json_schema()},
#                 },
#             }
#             response = requests.post(Config.PERPLEXITY_URL, headers=Config.HEADERS, json=payload)
#             print(f"Fact-check API status for statement '{statement[:50]}...': {response.status_code}")
#             if response.status_code != 200:
#                 print(f"Fact-check API error response: {response.text}")
#                 print(f"⚠️ Skipping statement due to API error")
#                 continue
                
#             response_data = response.json() 
#             raw_content = response_data["choices"][0]["message"]["content"]
#             cleaned_content = re.sub(r"```json|```", "", raw_content).strip()
#             statement_json = json.loads(cleaned_content)
#             citations = response_data["citations"]
#             statement_json["citations"] = citations
            
#             processed_results.append(statement_json)
#         except Exception as e:
#             print(f"Error encountered with statement: {statement}")
#             print("⚠️ **Exception:**", str(e)) 
    
#     return processed_results