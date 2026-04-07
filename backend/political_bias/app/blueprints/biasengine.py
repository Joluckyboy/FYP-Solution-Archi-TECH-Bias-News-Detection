import json
import logging
import re
from typing import Optional

import torch
from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from .prompts import prompts

logger = logging.getLogger(__name__)

# Replaces Flask Blueprint — same url_prefix, same routes
biasengine = APIRouter(prefix="/biasengine")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_json_safely(raw_text: str):
    cleaned = re.sub(r"```json|```", "", (raw_text or "")).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        pass
    start_candidates = [i for i in (cleaned.find("{"), cleaned.find("[")) if i != -1]
    if not start_candidates:
        raise ValueError("Model response does not contain JSON")
    start = min(start_candidates)
    end = max(cleaned.rfind("}"), cleaned.rfind("]"))
    candidate = cleaned[start: end + 1] if end > start else cleaned[start:]
    try:
        return json.loads(candidate)
    except Exception:
        return json.loads(candidate, strict=False)


async def _extract_fields(
    request: Request,
    site: Optional[str],
    title: Optional[str],
    page_text: Optional[str],
):
    """Support both GET query params and POST JSON body — mirrors original Flask helper."""
    if request.method == "POST":
        try:
            payload = await request.json()
        except Exception:
            payload = {}
        site = payload.get("site") or site
        title = payload.get("title") or title
        page_text = payload.get("page_text") or page_text
    return site, title, page_text


def _run_bert(model_state: dict, site: str, title: str, page_text: str) -> list:
    """Run BERT tokenisation + forward pass. Returns raw sigmoid output list."""
    tokenizer = model_state["tokenizer"]
    model = model_state["model"]
    device = model_state["device"]

    example = str(site) + str(title) + str(page_text)
    encodings = tokenizer.encode_plus(
        example,
        None,
        add_special_tokens=True,
        max_length=256,
        padding="max_length",
        return_token_type_ids=True,
        truncation=True,
        return_attention_mask=True,
        return_tensors="pt",
    )
    with torch.no_grad():
        input_ids = encodings["input_ids"].to(device, dtype=torch.long)
        attention_mask = encodings["attention_mask"].to(device, dtype=torch.long)
        token_type_ids = encodings["token_type_ids"].to(device, dtype=torch.long)
        output = model(input_ids, attention_mask, token_type_ids)
        return torch.sigmoid(output).cpu().detach().numpy().tolist()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@biasengine.get("/hello")
def hello():
    return "Hello"


@biasengine.get("/rate_bias")
@biasengine.post("/rate_bias")
async def rate_bias(
    request: Request,
    site: Optional[str] = Query(default=None),
    title: Optional[str] = Query(default=None),
    page_text: Optional[str] = Query(default=None),
):
    try:
        from main import model_state  # model loaded in main.py lifespan

        site, title, page_text = await _extract_fields(request, site, title, page_text)

        if not site or not title or not page_text:
            return JSONResponse(
                {"status": 400, "message": "Missing required fields: site, title, page_text"},
                status_code=400,
            )

        final_output = _run_bert(model_state, site, title, page_text)

        pkey = model_state.get("pkey")
        if pkey:
            try:
                from perplexity import Perplexity

                user_prompt = (
                    prompts.user_prompt
                    + "<article>"
                    + str(site) + " | " + str(title) + " | " + str(page_text)
                    + "</article>"
                )
                client = Perplexity(api_key=pkey)
                completion = client.chat.completions.create(
                    model="sonar",
                    messages=[
                        {"role": "system", "content": prompts.sys_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                target_dict = {"left": 0, "leaning-left": 1, "center": 2, "leaning-right": 3, "right": 4}
                bias = json.loads(completion.choices[0].message.content)["bias"]
                final_output[int(target_dict[bias])] = final_output[int(target_dict[bias])] * 1.2
            except Exception:
                pass  # non-fatal

        scores = final_output[0]
        label = ["left", "leaning-left", "center", "leaning-right", "right"][scores.index(max(scores))]
        return {"status": 200, "rating": label}

    except Exception as e:
        logger.exception("rate_bias failed")
        return JSONResponse({"status": 500, "message": str(e)}, status_code=500)


@biasengine.get("/rate_bias_no_perplexity")
@biasengine.post("/rate_bias_no_perplexity")
async def rate_bias_no_perplexity(
    request: Request,
    site: Optional[str] = Query(default=None),
    title: Optional[str] = Query(default=None),
    page_text: Optional[str] = Query(default=None),
):
    try:
        from main import model_state

        site, title, page_text = await _extract_fields(request, site, title, page_text)

        if not site or not title or not page_text:
            return JSONResponse(
                {"status": 400, "message": "Missing required fields: site, title, page_text"},
                status_code=400,
            )

        final_output = _run_bert(model_state, site, title, page_text)
        scores = final_output[0]
        label = ["left", "leaning-left", "center", "leaning-right", "right"][scores.index(max(scores))]
        return {"status": 200, "rating": label}

    except Exception as e:
        logger.exception("rate_bias_no_perplexity failed")
        return JSONResponse({"status": 500, "message": str(e)}, status_code=500)


@biasengine.get("/get_topics")
@biasengine.post("/get_topics")
async def get_topics(
    request: Request,
    site: Optional[str] = Query(default=None),
    title: Optional[str] = Query(default=None),
    page_text: Optional[str] = Query(default=None),
):
    try:
        from main import model_state

        site, title, page_text = await _extract_fields(request, site, title, page_text)

        if not site or not title or not page_text:
            return JSONResponse(
                {"status": 400, "message": "Missing required fields: site, title, page_text"},
                status_code=400,
            )

        pkey = model_state.get("pkey")
        if not pkey:
            return JSONResponse({"status": 500, "message": "API_KEY not set"}, status_code=500)

        output = ""
        counter = 0
        last_error = None

        while output == "" and counter < 3:
            try:
                from perplexity import Perplexity

                user_prompt = (
                    prompts.topics_user_prompt
                    + "<article>"
                    + str(site) + " | " + str(title) + " | " + str(page_text)
                    + "</article>"
                )
                client = Perplexity(api_key=pkey)
                completion = client.chat.completions.create(
                    model="sonar",
                    messages=[
                        {"role": "system", "content": prompts.topics_sys_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                raw_content = completion.choices[0].message.content
                temp_output = _parse_json_safely(raw_content)

                if not isinstance(temp_output, dict):
                    raise ValueError("Model response is not a JSON object")
                if "covered" not in temp_output or "omitted" not in temp_output:
                    raise ValueError("Missing required keys: covered, omitted")

                output = temp_output
                counter += 1

            except Exception as e:
                last_error = str(e)
                logger.warning("get_topics attempt %s failed: %s", counter + 1, last_error)
                counter += 1
                continue

        if not output or not isinstance(output, dict):
            logger.warning("get_topics fallback. last_error=%s", last_error)
            return {
                "status": 200,
                "topics": {"covered": [], "omitted": []},
                "warning": f"Topics analysis unavailable: {last_error or 'model output format invalid'}",
            }

        return {"status": 200, "topics": output}

    except Exception as e:
        logger.exception("get_topics failed")
        return JSONResponse({"status": 500, "message": str(e)}, status_code=500)