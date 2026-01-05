
from transformers import pipeline, AutoTokenizer
import torch

class emotion_model:
    def __init__(self):
        self.model_name = "SamLowe/roberta-base-go_emotions"
        self.classifier = pipeline(
            task="text-classification", 
            model=self.model_name, tokenizer=self.model_name, 
            top_k=None
            )
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
    
    def chunk_text(self, text, max_length=500):
        ### returns a list of tokenized chunks of the text

        tokens = self.tokenizer(text, return_tensors="pt", truncation=False)
        token_chunks = [tokens['input_ids'][0][i:i+max_length] for i in range(0, len(tokens['input_ids'][0]), max_length)]
        return token_chunks
    
    def predict_emotion(self, text):
        text_chunks = self.chunk_text(text)
        emotion_results = self.predict(text_chunks)
        return emotion_results
    
