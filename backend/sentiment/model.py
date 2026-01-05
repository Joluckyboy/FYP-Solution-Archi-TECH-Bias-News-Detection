from transformers import AutoModelForSequenceClassification, AutoTokenizer, AutoConfig
import numpy as np
from scipy.special import softmax
import torch


class sentiment_model:
    def __init__(self):
        self.model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        self.config = AutoConfig.from_pretrained(self.model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
    
    def chunk_text(self, text, max_length=500):
        tokens = self.tokenizer(text, return_tensors="pt", truncation=False)
        input_ids = tokens['input_ids'][0]
        attention_mask = tokens['attention_mask'][0]

        chunks = []
        for i in range(0, len(input_ids), max_length):
            chunk = {
                'input_ids': input_ids[i:i+max_length].unsqueeze(0),
                'attention_mask': attention_mask[i:i+max_length].unsqueeze(0)
            }
            chunks.append(chunk)

        return chunks
    
    # def predict_sentiment(self, text_chunks):
    #     results = []

    #     for chunk in text_chunks:
    #         with torch.no_grad():
    #             output = self.model(**chunk)
    #             scores = output[0][0].detach().numpy()
    #             scores = softmax(scores)
    #             results.append(scores)

    #     return results

    def predict_sentiment(self, chunk):
        with torch.no_grad():
            output = self.model(**chunk)
            scores = output[0][0].detach().numpy()
            scores = softmax(scores)
            return scores
