from fastapi import FastAPI, Request
import torch
import torch.nn.functional as F
from transformers import BertTokenizerFast

from api_models  import TextInput, PropagandaResponse
from model import BertForTokenAndSequenceJointClassification

app = FastAPI(
    title="Propaganda Analysis API",
    description="API for analyzing propaganda techniques in text using a pre-trained model.",
    version="1.0.0"
)

tokenizer = BertTokenizerFast.from_pretrained('bert-base-cased')
model = BertForTokenAndSequenceJointClassification.from_pretrained(
    "QCRI/PropagandaTechniquesAnalysis-en-BERT",
    revision="v0.1.0"
)

@app.get("/")
async def health_check():
    # return 200
    return {"status": "ok"}

@app.get("/propaganda")
def health_check2():
    # return 200
    return {"status": "ok"}

@app.post("/propaganda/analyze_propaganda", 
          summary= "Analyze Propaganda", 
          description="Analyze the propaganda techniques in the provided text.",
          response_model= PropagandaResponse
          )
async def analyze_text(input: TextInput):
    with torch.inference_mode():
        # Tokenize text and get token IDs
        tokenized_text = tokenizer.encode_plus(input.text, return_tensors="pt", truncation=False)
        input_ids = tokenized_text.input_ids[0]  # Get token IDs (without truncation)
        
        max_chunk_size = 510  # BERT max token limit (512) - CLS/SEP tokens
        chunks = [input_ids[i : i + max_chunk_size] for i in range(0, len(input_ids), max_chunk_size)]
        
        results = []
        overall_probs = []
        formatted_results = []
        
        for chunk in chunks:
            # Add [CLS] and [SEP] tokens
            chunk = torch.cat([torch.tensor([tokenizer.cls_token_id]), chunk, torch.tensor([tokenizer.sep_token_id])])
            chunk = chunk.unsqueeze(0)  # Add batch dimension
            
            # Pass chunk to model
            outputs = model(input_ids=chunk)
            
            # Get sequence-level classification
            sequence_class_index = torch.argmax(outputs.sequence_logits, dim=-1)
            sequence_class = model.sequence_tags[sequence_class_index[0]]
            
            # Get token-level classification
            token_class_index = torch.argmax(outputs.token_logits, dim=-1)
            tokens = tokenizer.convert_ids_to_tokens(chunk[0][1:-1])  # Skip CLS/SEP
            tags = [model.token_tags[i] for i in token_class_index[0].tolist()[1:-1]]


            # Store sequence probabilities
            sequence_probs = F.softmax(outputs.sequence_logits, dim=-1)
            overall_probs.append(sequence_probs[0].tolist())

            # Format output
            formatted_tokens = []
            current_token_combination = []
            current_tag = None
            tolerance = 4
            non_o_count = 0

            for token, tag in zip(tokens, tags):

                if tag != "O":
                    if current_tag is None:
                        current_tag = tag
                        current_token_combination.append(token)
                        non_o_count = 0
                    
                    elif (current_tag == tag) & (non_o_count < tolerance):
                        if token.startswith("##") & len(current_token_combination) > 0:
                                current_token_combination[-1] += token[2:]
                        else: current_token_combination.append(token.replace("##", ""))  

                else:

                    if current_tag is not None:
                        if non_o_count > tolerance:
                            formatted_results.append([current_tag , " ".join(current_token_combination)])
                            current_token_combination = []
                            current_tag = None
                        else:
                            non_o_count += 1
                            if token.startswith("##") & len(current_token_combination) > 0:
                                current_token_combination[-1] += token[2:]
                            else: current_token_combination.append(token.replace("##", ""))  

            results.append(" ".join(formatted_tokens))

        # Average probabilities across chunks
        non_propaganda_prob = sum(p[0] for p in overall_probs) / len(overall_probs)
        propaganda_prob = sum(p[1] for p in overall_probs) / len(overall_probs)

        # print(formatted_results)
    return { 
        "propaganda_result": {
            "non_propaganda_probability": non_propaganda_prob,
            "propaganda_probability": propaganda_prob,
            "formatted_result": formatted_results
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)