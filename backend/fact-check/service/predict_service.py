import re
import json
import requests
from urllib.parse import urlparse

from config.config import Config
from models.datapayload import DataPayload, ModelDataPayload
from models.statementformat import StatementFormat
from models.predictformat import PredictFormat
from models.modeldataformat import ModelDataFormat


def normalize_url(url):
    """Normalize URL for comparison by removing protocol, www, and trailing slashes"""
    if not url:
        return ""
    parsed = urlparse(url.lower())
    domain_path = parsed.netloc + parsed.path
    domain_path = domain_path.replace('www.', '')
    domain_path = domain_path.rstrip('/')
    return domain_path


def filter_citations(citations, original_url):
    """Filter out citations that match the original article URL and deduplicate results"""
    if not citations or not original_url:
        return []

    def citation_to_url(citation):
        if isinstance(citation, str):
            return citation
        if isinstance(citation, dict):
            for key in ("url", "source", "link"):
                val = citation.get(key)
                if isinstance(val, str):
                    return val
        return ""

    normalized_original = normalize_url(original_url)
    filtered_urls = []

    for citation in citations:
        citation_url = citation_to_url(citation)
        if not citation_url:
            continue

        normalized_citation = normalize_url(citation_url)

        # Only include if it's NOT the same as the original article
        if normalized_citation != normalized_original:
            filtered_urls.append(citation_url)

    return filtered_urls


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
                    "content": "Please output JSON object(s) containing the following fields: sentiment_summary, emotion_summary, propaganda_summary, political_bias_summary. These summaries should be short paragraphs describing the data in layman terms to guide readers through understanding one data point then leading them to the next. Make use of summarise_result to understand what the data is about. Besides the specified format, do not mention anything else."
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


def clean_source_attributions(explanation: str) -> str:
    """
    Remove potentially inaccurate source attributions while keeping citation numbers.
    
    Examples:
    "According to AsiaOne, IMDA stated [1]" → "According to [1]"
    "CNA confirms [2]" → "[2]"
    "The IMDA verifies [3]" → "[3]"
    """
    if not explanation:
        return explanation
    
    # Remove "According to X," patterns
    explanation = re.sub(
        r'According to [^,\.\[]+?,\s*',
        '',
        explanation,
        flags=re.IGNORECASE
    )
    
    # Remove source names + verbs before citations
    sources = r'(?:the\s+)?(?:AsiaOne|CNA|Sky News|France24|BBC|Reuters|Bloomberg|ILTV|Times of Israel|IMDA|SPF|official|government)'
    verbs = r'(?:state[sd]?|confirm[s|ed]?|report[s|ed]?|verif(?:y|ies|ied)|note[s|d]?|mention[s|ed]?|impl(?:y|ies|ied)|announce[s|d]?|say[s]?|said)'
    
    explanation = re.sub(
        sources + r'\s+(?:and\s+\w+\s+)?' + verbs + r'\s+(?:that\s+)?',
        '',
        explanation,
        flags=re.IGNORECASE
    )
    
    # Remove institutional phrases
    explanation = re.sub(
        r'(?:the\s+)?(?:IMDA\'s\s+)?(?:official\s+)?(?:press\s+)?(?:release|statement|website)\s*[,:]?\s*',
        '',
        explanation,
        flags=re.IGNORECASE
    )
    
    # Add "According to" before orphaned citations
    explanation = re.sub(r'(?:^|(?<=\.\s))(\[)', r'According to \1', explanation)
    
    # Clean up spacing
    explanation = re.sub(r'\s+', ' ', explanation)
    explanation = re.sub(r'\s+([,\.\)])', r'\1', explanation)
    explanation = explanation.strip()
    
    # Fix duplicates
    explanation = re.sub(r'According to According to', 'According to', explanation)
    
    # Capitalize
    if explanation and explanation[0].islower():
        explanation = explanation[0].upper() + explanation[1:]
    
    return explanation


def reorder_citations_by_explanation(explanation: str, all_citations: list) -> tuple:
    """
    Extract citation numbers from explanation and reorder citations accordingly.
    Also removes duplicate citation numbers (e.g., [3][3] becomes [3])
    
    Returns: (updated_explanation, reordered_citations)
    """
    if not all_citations:
        return explanation, []
    
    pattern = r'\[(\d+)\]'
    matches = list(re.finditer(pattern, explanation))
    
    if not matches:
        return explanation, []
    
    mapping = {}
    reordered_citations = []
    
    for match in matches:
        old_idx = int(match.group(1))
        
        if old_idx not in mapping:
            if 1 <= old_idx <= len(all_citations):
                new_idx = len(reordered_citations) + 1
                mapping[old_idx] = new_idx
                reordered_citations.append(all_citations[old_idx - 1])
    
    updated_explanation = explanation
    for old_idx in sorted(mapping.keys(), reverse=True):
        new_idx = mapping[old_idx]
        updated_explanation = updated_explanation.replace(f'[{old_idx}]', f'[{new_idx}]')
    
    # *** NEW: Remove duplicate consecutive citation numbers ***
    # [1][1] or [3][3] becomes just [1] or [3]
    updated_explanation = re.sub(r'(\[\d+\])(\1)+', r'\1', updated_explanation)
    
    return updated_explanation, reordered_citations


async def fact_check_hybrid(statements, original_article_title, original_article_url):
    """
    HYBRID APPROACH: Fast, cost-effective fact-checking with citation filtering
    
    Features:
    1. Filters out original article URL from citations
    2. Reorders citations to match explanation references
    3. Cleans up false source attributions
    """
    try:
        model = "sonar-pro"
        
        cleaned_statements = [re.sub(r"^\d+\.\s*", "", stmt) for stmt in statements]
        statements_text = "\n".join([f"{i+1}. {stmt}" for i, stmt in enumerate(cleaned_statements)])
        
        print(f"Fact-checking {len(cleaned_statements)} statements...")
        print(f"Original article: {original_article_title}")
        print(f"Excluding citations from: {original_article_url}")
        
        payload = {
            "model": f"{model}",
            "messages": [
                {
                    "role": "system",
                    "content": f"You are a fact-checker for Singapore media outlets. Analyze if the statement is factual/unfactual/cannot be determined. CRITICAL: Do NOT cite or reference the article titled '{original_article_title}' (URL: {original_article_url}). Find independent verification from OTHER sources."
                },
                {
                    "role": "user",
                    "content": f"""Fact-check these numbered statements from an article titled "{original_article_title}":

{statements_text}

IMPORTANT: Do NOT use the original article ({original_article_url}) as a source. Find independent verification from OTHER reliable sources.

For EACH statement, provide:
1. The statement number and text
2. Correctness verdict (factual/unfactual/cannot be determined)
3. Explanation with citation numbers [1], [2], etc.

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
        
        if response.status_code == 402:
            raise Exception("⚠️ Perplexity credit limit exceeded!")
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
        
        # *** CRITICAL: Filter out original article citations ***
        all_citations = response_data.get("citations", [])
        filtered_citations = filter_citations(all_citations, original_article_url)
        
        print(f"Total citations: {len(all_citations)}")
        print(f"Filtered citations (excluding original): {len(filtered_citations)}")
        
        # Strip numbering from statements
        for result in results:
            if "statement" in result:
                result["statement"] = re.sub(r"^\d+\.\s*", "", result["statement"])
        
        # Process each result
        for idx, result in enumerate(results):
            explanation = result.get("explanation", "")
            
            # Reorder citations based on explanation
            updated_explanation, reordered_citations = reorder_citations_by_explanation(
                explanation, filtered_citations
            )
            
            # Clean up false source attributions
            cleaned_explanation = clean_source_attributions(updated_explanation)
            result["explanation"] = cleaned_explanation
            
            if reordered_citations:
                result["citations"] = reordered_citations
                result["citation_confidence"] = "high"
            else:
                result["citations"] = []
                result["citation_confidence"] = "low"
        
        print(f"✓ Fact-checked {len(results)} statements (1 API call)")
        return results
        
    except Exception as e:
        print(f"⚠️ Fact-check exception: {str(e)}")
        raise Exception(f"Failed to fact-check statements: {str(e)}")


async def fact_check_sequential_accurate(statements, original_article_title, original_article_url):
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
    
    print(f"Sequential fact-checking {len(statements)} statements (HIGH ACCURACY MODE)...")
    print(f"Excluding citations from: {original_article_url}")
    
    for idx, statement in enumerate(statements, 1):
        try:
            payload = {
                "model": f"{model}",
                "messages": [
                    {
                        "role": "system",
                        "content": f"You are a fact-checker for Singapore media outlets. Analyze if the statement is factual/unfactual/cannot be determined. CRITICAL: Do NOT cite or reference the article titled '{original_article_title}' (URL: {original_article_url}). Find independent verification from OTHER sources."
                    },
                    {
                        "role": "user",
                        "content": f"Fact-check this statement: {statement}. Do NOT use {original_article_url} as a source. Find alternative verification. Output JSON with fields: statement, correctness, explanation."
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
            
            # Filter citations to exclude original article
            all_citations = response_data.get("citations", [])
            filtered_citations = filter_citations(all_citations, original_article_url)

            statement_json["citations"] = filtered_citations
            statement_json["citation_confidence"] = "perfect"
            
            processed_results.append(statement_json)
            print(f"✓ Checked statement {idx}/{len(statements)} (Citations: {len(filtered_citations)})")
            
        except Exception as e:
            print(f"⚠️ Error with statement {idx}: {str(e)}")
    
    print(f"✓ Sequential fact-checking complete: {len(processed_results)}/{len(statements)} verified")
    return processed_results


async def fact_check(statements, original_article_title, original_article_url):
    """
    Main fact-check function - uses hybrid approach by default
    
    Switch between approaches based on your needs:
    - fact_check_hybrid: Fast + Good accuracy (RECOMMENDED)
    - fact_check_sequential_accurate: Slow + Perfect accuracy (if budget allows)
    """
    return await fact_check_hybrid(statements, original_article_title, original_article_url)
    
    # OR uncomment this for perfect accuracy (if budget allows):
    # return await fact_check_sequential_accurate(statements, original_article_title, original_article_url)