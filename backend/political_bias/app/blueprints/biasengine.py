from flask import current_app, Blueprint, render_template, request
import torch
import numpy as np
from .prompts import prompts
from perplexity import Perplexity
import json

biasengine = Blueprint('biasengine', __name__, url_prefix='/biasengine')

@biasengine.get("/")
def health_check():
    # return 200
    return {"status": "ok"}

@biasengine.route('/hello')
def hello():
    return "Hello"

def _rate_bias(use_perplexity: bool):
    try:
        site = request.args.get("site")
        title = request.args.get("title")
        page_text = request.args.get("page_text")

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
                    model="sonar",
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

        return json.dumps({"status": 200, "rating": label})

    except Exception as e:
        return json.dumps({"status": 500, "message": str(e)})


@biasengine.route('/rate_bias', methods=["GET"])
def rate_bias():
    return _rate_bias(use_perplexity=True)


@biasengine.route('/rate_bias_no_perplexity', methods=["GET"])
def rate_bias_no_perplexity():
    return _rate_bias(use_perplexity=False)

@biasengine.route('/get_topics', methods=["GET"])
def get_topics():

    try:
        output = ""
        counter = 0
        site = request.args.get("site")
        title = request.args.get("title")
        page_text = request.args.get("page_text")

        while output == "" and counter < 3:
            try:
                # get prompts
                sys_prompt = prompts.topics_sys_prompt
                user_prompt = prompts.topics_user_prompt + "<article>" + str(site) + " | " + str(title) + " | " + str(page_text) + "</article>"

                # Initialize the client (uses PERPLEXITY_API_KEY environment variable)
                client = Perplexity(api_key=current_app.pkey)

                # Make the API call with a preset
                completion = client.chat.completions.create(
                    model="sonar",
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
                temp_output = json.loads(completion.choices[0].message.content)
                keys = list(temp_output.keys())
                if "covered" in keys and "omitted" in keys:
                    output = temp_output
                else:
                    raise(Exception)
                
                # increment counter
                counter += 1
            except:
                # increment counter
                counter += 1
                pass
    
        resp = json.dumps({'status': 200, 'topics': output})
        return resp
    
    except Exception as e:
        return json.dumps({'status':500, 'message':str(e)})
