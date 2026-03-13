from fastapi import FastAPI
import re
import torch
import torch.nn.functional as F
from transformers import BertTokenizerFast

from api_models import TextInput, PropagandaResponse
from model import BertForTokenAndSequenceJointClassification

app = FastAPI(
    title="Propaganda Analysis API",
    description="API for analyzing propaganda techniques in text using a pre-trained model.",
    version="2.2.0"
)

tokenizer = BertTokenizerFast.from_pretrained('bert-base-cased')
model = BertForTokenAndSequenceJointClassification.from_pretrained(
    "QCRI/PropagandaTechniquesAnalysis-en-BERT",
    revision="v0.1.0"
)

TECHNIQUE_DESCRIPTIONS = {
    "Name_Calling,Labeling":                       {"description": "Attaches a negative or positive label to a person or idea to provoke an emotional reaction without logical argument."},
    "Repetition":                                  {"description": "Repeats a message or slogan many times to make it stick in the reader's mind, bypassing critical thinking."},
    "Slogans":                                     {"description": "Uses catchy phrases that are easy to remember but oversimplify complex issues."},
    "Appeal_to_fear-prejudice":                    {"description": "Exploits fear or existing prejudices to push an agenda, making the audience act out of emotion rather than reason."},
    "Doubt":                                       {"description": "Questions the credibility of someone or something to undermine trust without providing evidence."},
    "Exaggeration,Minimisation":                   {"description": "Overstates or understates facts to distort reality and steer opinion."},
    "Flag-Waving":                                 {"description": "Appeals to national pride or group identity to justify actions or policies."},
    "Loaded_Language":                             {"description": "Uses emotionally charged words to influence the audience's feelings toward a subject."},
    "Reductio_ad_hitlerum":                        {"description": "Discredits an idea by associating it with an extreme negative figure or group."},
    "Bandwagon":                                   {"description": "Implies everyone agrees with a position to pressure others into conforming."},
    "Causal_Oversimplification":                   {"description": "Reduces a complex issue to a single cause, ignoring nuance."},
    "Obfuscation,Intentional_Vagueness,Confusion": {"description": "Uses unclear or confusing language to hide the true intent of a message."},
    "Appeal_to_Authority":                         {"description": "Cites an authority figure to validate a claim, even if they are not an expert on the topic."},
    "Black-and-White_Fallacy":                     {"description": "Presents only two extreme options when other possibilities exist."},
    "Thought-terminating_Cliches":                 {"description": "Uses familiar phrases to shut down debate and discourage critical thinking."},
    "Red_Herring":                                 {"description": "Introduces irrelevant information to distract from the real issue."},
    "Straw_Men":                                   {"description": "Misrepresents an opponent's argument to make it easier to attack."},
    "Whataboutism":                                {"description": "Deflects criticism by pointing to a different issue, avoiding the original argument."},
}

# Trailing stopwords = phrase was cut off mid-thought
_TRAILING_STOPWORD = re.compile(
    r'\s+(?:the|a|an|and|or|but|of|in|on|at|to|for|with|by|from|as|that|this|its|their|our|your)\s*$',
    re.IGNORECASE
)

# "said X" sentence fragments dragged in by the tolerance buffer
_SAID_FRAGMENT = re.compile(
    r',\s+(?:the\s+)?(?:official|he|she|they|trump|mamdani|officials?|sources?|spokespeople?|spokesman?)\s+said.*$',
    re.IGNORECASE
)

# All quote types including curly/smart quotes
_ALL_QUOTES = '\u201c\u201d\u2018\u2019"\'\u0060'
_BOUNDARY   = r'[\s' + re.escape(_ALL_QUOTES) + r'.,;:!?()\[\]{}\u2014\u2013]+'


def _clean_phrase(phrase: str) -> str:
    """Remove BERT tokenization artifacts and boundary noise."""
    # 1. Strip "said X" fragments at end
    phrase = _SAID_FRAGMENT.sub("", phrase)
    # 2. Fix spaced apostrophes: "who ' s" → "who's"
    phrase = re.sub(r"\s'\s(\w)", r"'\1", phrase)
    # 3. Fix spaced hyphens
    phrase = re.sub(r"\s-\s", r"-", phrase)
    # 4. Fix spaced slashes
    phrase = re.sub(r"\s/\s", r"/", phrase)
    # 5. Strip leading boundary chars (incl. curly quotes)
    phrase = re.sub(r'^' + _BOUNDARY, "", phrase)
    # 6. Strip trailing boundary chars
    phrase = re.sub(_BOUNDARY + r'$', "", phrase)
    # 7. Strip trailing stopwords (truncated phrases)
    phrase = _TRAILING_STOPWORD.sub("", phrase)
    # 8. Collapse multiple spaces
    phrase = re.sub(r"\s{2,}", " ", phrase)
    return phrase.strip()


def _is_valid_phrase(phrase: str) -> bool:
    """Only keep phrases with ≥ 3 meaningful words and ≥ 10 chars."""
    if len(phrase.split()) < 3:
        return False
    if len(phrase.strip()) < 10:
        return False
    if not re.search(r"[a-zA-Z]", phrase):
        return False
    return True


def get_severity_from_probability(prob: float) -> str:
    if prob < 0.35:   return "Low"
    if prob < 0.65:   return "Moderate"
    return "High"


@app.get("/")
async def health_check():
    return {"status": "ok"}

@app.get("/propaganda")
def health_check2():
    return {"status": "ok"}


@app.post(
    "/propaganda/analyze_propaganda",
    response_model=PropagandaResponse
)
async def analyze_text(input: TextInput):

    with torch.inference_mode():
        tokenized_text = tokenizer(input.text, return_tensors="pt", truncation=False)
        input_ids      = tokenized_text.input_ids[0]

        max_chunk_size = 510
        chunks = [input_ids[i: i + max_chunk_size] for i in range(0, len(input_ids), max_chunk_size)]

        results           = []
        overall_probs     = []
        formatted_results = []

        for chunk in chunks:
            chunk = torch.cat([
                torch.tensor([tokenizer.cls_token_id]),
                chunk,
                torch.tensor([tokenizer.sep_token_id])
            ]).unsqueeze(0)

            outputs        = model(input_ids=chunk)
            seq_probs      = F.softmax(outputs.sequence_logits, dim=-1)
            overall_probs.append(seq_probs[0].tolist())

            token_class_index = torch.argmax(outputs.token_logits, dim=-1)
            tokens = tokenizer.convert_ids_to_tokens(chunk[0][1:-1])
            tags   = [model.token_tags[i] for i in token_class_index[0].tolist()[1:-1]]

            current_tokens  = []
            current_tag     = None
            tolerance       = 4
            non_o_count     = 0

            def _flush(tokens_list, tag):
                if not tokens_list or not tag:
                    return
                raw   = " ".join(tokens_list)
                clean = _clean_phrase(raw)
                if _is_valid_phrase(clean):
                    formatted_results.append([tag, clean])

            for token, tag in zip(tokens, tags):
                if tag != "O":
                    if current_tag is None:
                        current_tag = tag
                        current_tokens = [token]
                        non_o_count = 0
                    elif current_tag == tag and non_o_count < tolerance:
                        if token.startswith("##") and current_tokens:
                            current_tokens[-1] += token[2:]
                        else:
                            current_tokens.append(token.replace("##", ""))
                else:
                    if current_tag is not None:
                        if non_o_count > tolerance:
                            _flush(current_tokens, current_tag)
                            current_tokens = []
                            current_tag    = None
                            non_o_count    = 0
                        else:
                            non_o_count += 1
                            if token.startswith("##") and current_tokens:
                                current_tokens[-1] += token[2:]
                            else:
                                current_tokens.append(token.replace("##", ""))

            _flush(current_tokens, current_tag)  # flush at end of chunk
            results.append("")

        non_propaganda_prob = sum(p[0] for p in overall_probs) / len(overall_probs)
        propaganda_prob     = sum(p[1] for p in overall_probs) / len(overall_probs)

    # Group by technique
    grouped: dict = {}
    for tag, phrase in formatted_results:
        info = TECHNIQUE_DESCRIPTIONS.get(tag, {"description": "An influence technique was detected."})
        if tag not in grouped:
            grouped[tag] = {"technique": tag, "description": info["description"], "phrases": []}
        grouped[tag]["phrases"].append(phrase)

    total_tokens    = sum(len(c) for c in chunks)
    detected_tokens = sum(len(p.split()) for _, p in formatted_results)
    coverage_pct    = round(min(detected_tokens / max(total_tokens, 1) * 100, 100), 1)

    return {
        "propaganda_result": {
            "non_propaganda_probability": non_propaganda_prob,
            "propaganda_probability":     propaganda_prob,
            "formatted_result":           formatted_results,
            "techniques":                 list(grouped.values()),
            "coverage_pct":               coverage_pct,
            "severity":                   get_severity_from_probability(propaganda_prob),
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8014)