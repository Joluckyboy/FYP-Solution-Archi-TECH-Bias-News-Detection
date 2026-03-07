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
    
    def predict_sentiment_batch(self, chunks):
        """Process multiple chunks in a single batch for faster inference"""
        if not chunks:
            return []
        
        # Pad all chunks to same length for batching
        max_len = max(chunk['input_ids'].shape[1] for chunk in chunks)
        
        batch_input_ids = []
        batch_attention_mask = []
        
        for chunk in chunks:
            input_ids = chunk['input_ids'][0]
            attention_mask = chunk['attention_mask'][0]
            
            # Pad to max_len
            padding_len = max_len - len(input_ids)
            if padding_len > 0:
                input_ids = torch.cat([input_ids, torch.zeros(padding_len, dtype=torch.long)])
                attention_mask = torch.cat([attention_mask, torch.zeros(padding_len, dtype=torch.long)])
            
            batch_input_ids.append(input_ids)
            batch_attention_mask.append(attention_mask)
        
        # Stack into batch tensors
        batch_input_ids = torch.stack(batch_input_ids)
        batch_attention_mask = torch.stack(batch_attention_mask)
        
        # Run model on entire batch
        with torch.no_grad():
            output = self.model(input_ids=batch_input_ids, attention_mask=batch_attention_mask)
            scores = output[0].detach().numpy()
            scores = softmax(scores, axis=1)
        
        return scores
