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


async def fact_check_hybrid(statements, original_article):
    """
    HYBRID APPROACH: Balances speed, cost, and citation accuracy
    
    Strategy:
    1. First pass: 1 API call to fact-check all statements (fast, cheap)
    2. Parse response to extract statement-specific citation references
    3. Return results with proper citation mapping
    
    This maintains 1 API call while improving citation accuracy through
    better prompt engineering.
    """
    try:
        model = "sonar-pro"
        
        # Strip existing numbering from statements
        cleaned_statements = [re.sub(r"^\d+\.\s*", "", stmt) for stmt in statements]
        
        # Combine all statements with clear numbering
        statements_text = "\n".join([f"{i+1}. {stmt}" for i, stmt in enumerate(cleaned_statements)])
        
        print(f"🔍 Fact-checking {len(cleaned_statements)} statements with citation tracking...")
        
        payload = {
            "model": f"{model}",
            "messages": [
                {
                    "role": "system",
                    "content": f"You are a fact-checker for Singapore media outlets (Straits Times, CNA). Analyze each statement independently and provide factual/unfactual/cannot be determined verdicts. CRITICAL: In your explanation, reference which specific sources verify EACH statement. Do not use the original article titled: {original_article} in your citations."
                },
                {
                    "role": "user",
                    "content": f"""Fact-check these numbered statements:

{statements_text}

For EACH statement, provide:
1. The statement number and text
2. Correctness verdict (factual/unfactual/cannot be determined)
3. Explanation that EXPLICITLY mentions which sources verify THIS specific statement (e.g., "According to [source 1], this claim is verified..." or "Sources [2] and [3] confirm...")

Output as JSON array with fields: statement, correctness, explanation."""
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
        
        # Handle error scenarios
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
        
        # Get all citations from the response
        all_citations = response_data.get("citations", [])
        
        # Strip numbering from statement field
        for result in results:
            if "statement" in result:
                result["statement"] = re.sub(r"^\d+\.\s*", "", result["statement"])
        
        # IMPROVED: Parse explanation to map statement-specific citations
        for idx, result in enumerate(results):
            explanation = result.get("explanation", "")
            statement_citations = extract_statement_citations(explanation, all_citations)
            
            # If we couldn't parse specific citations, fall back to all citations
            # but flag this for the frontend
            if statement_citations:
                result["citations"] = statement_citations
                result["citation_confidence"] = "high"  # We found specific refs
            else:
                result["citations"] = all_citations
                result["citation_confidence"] = "low"   # Fallback to all
        
        print(f"✓ Fact-checked {len(results)} statements with citation mapping (1 API call)")
        return results
        
    except Exception as e:
        print(f"⚠️ Fact-check exception: {str(e)}")
        raise Exception(f"Failed to fact-check statements: {str(e)}")


def extract_statement_citations(explanation: str, all_citations: list) -> list:
    """
    Parse the explanation to find which citations are referenced for this specific statement.
    
    Looks for patterns like:
    - "According to [source 1]"
    - "Source [2] confirms"
    - "[1] and [3] verify"
    - Direct URL mentions
    
    Returns: List of citation objects that are referenced in the explanation
    """
    if not all_citations:
        return []
    
    statement_citations = []
    explanation_lower = explanation.lower()
    
    # Method 1: Look for citation index references [1], [2], etc.
    citation_indices = re.findall(r'\[(\d+)\]', explanation)
    for idx_str in citation_indices:
        idx = int(idx_str) - 1  # Convert to 0-indexed
        if 0 <= idx < len(all_citations):
            citation = all_citations[idx]
            if citation not in statement_citations:
                statement_citations.append(citation)
    
    # Method 2: Look for direct URL mentions in explanation
    for citation in all_citations:
        citation_url = citation.lower() if isinstance(citation, str) else ""
        # Check if the domain or significant part of URL is mentioned
        if citation_url:
            domain = extract_domain(citation_url)
            if domain and domain in explanation_lower:
                if citation not in statement_citations:
                    statement_citations.append(citation)
    
    # Method 3: Look for source references like "source 1", "according to source 2"
    source_refs = re.findall(r'source[s]?\s+(\d+)', explanation_lower)
    for idx_str in source_refs:
        idx = int(idx_str) - 1
        if 0 <= idx < len(all_citations):
            citation = all_citations[idx]
            if citation not in statement_citations:
                statement_citations.append(citation)
    
    return statement_citations


def extract_domain(url: str) -> str:
    """Extract domain from URL for matching"""
    try:
        # Simple domain extraction
        match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        if match:
            return match.group(1).lower()
    except:
        pass
    return ""


# ALTERNATIVE: If you need perfect citation accuracy and can afford it
async def fact_check_sequential_accurate(statements, original_article):
    """
    FALLBACK OPTION: Sequential fact-checking for maximum accuracy
    
    Use this ONLY if:
    - You have higher API budget
    - Citation accuracy is critical for your use case
    - You can tolerate 30-40s processing time
    
    Cost: N API calls (1 per statement)
    Speed: Slow (30-40s for 10 statements)
    Accuracy: Perfect citation mapping
    """
    processed_results = []
    model = "sonar-pro"
    
    print(f"🔍 Sequential fact-checking {len(statements)} statements (HIGH ACCURACY MODE)...")
    
    for idx, statement in enumerate(statements, 1):
        try:
            payload = {
                "model": f"{model}",
                "messages": [
                    {
                        "role": "system",
                        "content": f"You are a fact-checker for Singapore media outlets (Straits Times, CNA). Analyze if the statement is factual/unfactual/cannot be determined. Do not use the original article titled: {original_article} in your citations."
                    },
                    {
                        "role": "user",
                        "content": f"Fact-check this statement: {statement}. Output JSON with fields: statement, correctness, explanation."
                    },
                ],
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {"schema": PredictFormat.model_json_schema()},
                },
            }
            
            response = requests.post(Config.PERPLEXITY_URL, headers=Config.HEADERS, json=payload)
            
            if response.status_code != 200:
                print(f"⚠️ Skipping statement {idx} due to API error (status {response.status_code})")
                continue
                
            response_data = response.json()
            raw_content = response_data["choices"][0]["message"]["content"]
            cleaned_content = re.sub(r"```json|```", "", raw_content).strip()
            statement_json = json.loads(cleaned_content)
            
            # Perfect citation mapping - each statement has its own citations
            statement_json["citations"] = response_data.get("citations", [])
            statement_json["citation_confidence"] = "perfect"
            
            processed_results.append(statement_json)
            print(f"✓ Checked statement {idx}/{len(statements)}")
            
        except Exception as e:
            print(f"⚠️ Error with statement {idx}: {str(e)}")
    
    print(f"✓ Sequential fact-checking complete: {len(processed_results)}/{len(statements)} verified")
    return processed_results


# UPDATE YOUR ORIGINAL fact_check FUNCTION TO USE HYBRID
async def fact_check(statements, original_article):
    """
    Main fact-check function - uses hybrid approach by default
    
    Switch between approaches based on your needs:
    - fact_check_hybrid: Fast + Good accuracy (RECOMMENDED)
    - fact_check_sequential_accurate: Slow + Perfect accuracy (if budget allows)
    """
    # Use hybrid approach for best balance
    return await fact_check_hybrid(statements, original_article)
    
    # OR uncomment this for perfect accuracy (if you can afford it):
    # return await fact_check_sequential_accurate(statements, original_article)