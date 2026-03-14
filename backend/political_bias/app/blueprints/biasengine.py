from flask import current_app, Blueprint, render_template, request, jsonify
import torch
import numpy as np
from .prompts import prompts
from perplexity import Perplexity
import json
import re

biasengine = Blueprint('biasengine', __name__, url_prefix='/biasengine')


def _extract_article_fields():
    payload = request.get_json(silent=True) if request.method == "POST" else None
    payload = payload or {}

    site = payload.get("site") or request.args.get("site")
    title = payload.get("title") or request.args.get("title")
    page_text = payload.get("page_text") or request.args.get("page_text")

    return site, title, page_text


def _parse_json_safely(raw_text: str):
    cleaned = re.sub(r"```json|```", "", (raw_text or "")).strip()

    try:
        return json.loads(cleaned)
    except Exception:
        pass

    start_candidates = [idx for idx in (cleaned.find("{"), cleaned.find("[")) if idx != -1]
    if not start_candidates:
        raise ValueError("Model response does not contain JSON")

    start = min(start_candidates)
    end = max(cleaned.rfind("}"), cleaned.rfind("]"))
    candidate = cleaned[start:end + 1] if end > start else cleaned[start:]

    try:
        return json.loads(candidate)
    except Exception:
        return json.loads(candidate, strict=False)

@biasengine.get("/")
def health_check():
    # return 200
    return {"status": "ok"}

@biasengine.route('/hello')
def hello():
    return "Hello"

def _rate_bias(use_perplexity: bool):
    try:
        site, title, page_text = _extract_article_fields()

        if not site or not title or not page_text:
            return jsonify({"status": 400, "message": "Missing required fields: site, title, page_text"}), 400

        example = str(site) + str(title) + str(page_text)

        encodings = current_app.tokenizer.encode_plus(
            example,
            None,
            add_special_tokens=True,
            max_length=256,
            padding='max_length',
            return_token_type_ids=True,
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt'
        )

        with torch.no_grad():
            input_ids = encodings['input_ids'].to(current_app.device, dtype=torch.long)
            attention_mask = encodings['attention_mask'].to(current_app.device, dtype=torch.long)
            token_type_ids = encodings['token_type_ids'].to(current_app.device, dtype=torch.long)
            output = current_app.model(input_ids, attention_mask, token_type_ids)
            final_output = torch.sigmoid(output).cpu().detach().numpy().tolist()

        if use_perplexity and getattr(current_app, "pkey", None):
            try:
                # get prompts
                sys_prompt = prompts.sys_prompt
                user_prompt = prompts.user_prompt + "<article>" + str(site) + " | " + str(title) + " | " + str(page_text) + "</article>"

                # Initialize the client (uses PERPLEXITY_API_KEY environment variable)
                client = Perplexity(api_key=current_app.pkey)

                # Make the API call with a preset
                completion = client.chat.completions.create(
                    model="sonar-pro",
                    messages=[
                        {
                            "role": "system",
                            "content": sys_prompt
                        },
                        {
                            "role": "user",
                            "content": user_prompt
                        }
                    ]
                )

                # adjust sigmoid weights
                target_dict = {'left': 0, 'leaning-left': 1, 'center': 2, 'leaning-right': 3, 'right': 4}
                bias = json.loads(completion.choices[0].message.content)["bias"]

                index_to_adjust = target_dict[bias]
                final_output[int(index_to_adjust)] = final_output[int(index_to_adjust)] * 1.2

            except:
                pass

        # translate into text
        final_output = final_output[0]
        max_prob = max(final_output)
        max_index = final_output.index(max_prob)
        target_list = ['left', 'leaning-left', 'center', 'leaning-right', 'right']
        label = target_list[max_index]

        return jsonify({"status": 200, "rating": label})

    except Exception as e:
        current_app.logger.exception("rate_bias failed")
        return jsonify({"status": 500, "message": str(e)}), 500


@biasengine.route('/rate_bias', methods=["GET", "POST"])
def rate_bias():
    return _rate_bias(use_perplexity=True)


@biasengine.route('/rate_bias_no_perplexity', methods=["GET", "POST"])
def rate_bias_no_perplexity():
    return _rate_bias(use_perplexity=False)

@biasengine.route('/get_topics', methods=["GET", "POST"])
def get_topics():

    try:
        output = ""
        counter = 0
        last_error = None
        site, title, page_text = _extract_article_fields()

        if not site or not title or not page_text:
            return jsonify({"status": 400, "message": "Missing required fields: site, title, page_text"}), 400

        while output == "" and counter < 3:
            try:
                # get prompts
                sys_prompt = prompts.topics_sys_prompt
                user_prompt = prompts.topics_user_prompt + "<article>" + str(site) + " | " + str(title) + " | " + str(page_text) + "</article>"

                # Initialize the client (uses PERPLEXITY_API_KEY environment variable)
                client = Perplexity(api_key=current_app.pkey)

                # Make the API call with a preset
                completion = client.chat.completions.create(
                    model="sonar-pro",
                    messages=[
                        {
                            "role": "system",
                            "content": sys_prompt
                        },
                        {
                            "role": "user",
                            "content": user_prompt
                        }
                    ]
                )
                
                #check output format
                raw_content = completion.choices[0].message.content
                temp_output = _parse_json_safely(raw_content)
                if not isinstance(temp_output, dict):
                    raise ValueError("Model response is not a JSON object")

                keys = list(temp_output.keys())
                if "covered" in keys and "omitted" in keys:
                    output = temp_output
                else:
                    raise ValueError("Missing required keys: covered, omitted")
                
                # increment counter
                counter += 1
            except Exception as e:
                last_error = str(e)
                current_app.logger.warning("get_topics parse attempt %s failed: %s", counter + 1, last_error)
                # increment counter
                counter += 1
                continue
    
        if not output or not isinstance(output, dict):
            current_app.logger.warning("get_topics fallback applied after retries. last_error=%s", last_error)
            return jsonify({
                'status': 200,
                'topics': {'covered': [], 'omitted': []},
                'warning': f"Topics analysis unavailable: {last_error or 'model output format invalid'}"
            })

        return jsonify({'status': 200, 'topics': output})
    
    except Exception as e:
        current_app.logger.exception("get_topics failed")
        return jsonify({'status': 500, 'message': str(e)}), 500
