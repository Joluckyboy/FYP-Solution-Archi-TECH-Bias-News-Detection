from ..models.bertclass import BERTClass
import os
import torch
import boto3
from transformers import BertTokenizer

def get_model():
    model_local_dir = os.getenv("BIAS_MODEL_DIR", "/app/bias_model")
    model_local_path = os.path.join(model_local_dir, "best_model_ba_12_wd.pt")

    # Download from S3 if not already present
    if not os.path.exists(model_local_path):
        bucket = os.getenv("S3_MODEL_BUCKET")
        key = os.getenv("S3_MODEL_KEY", "bias_model/best_model_ba_12_wd.pt")
        os.makedirs(model_local_dir, exist_ok=True)
        print(f"[bias_model] Downloading from s3://{bucket}/{key}")
        s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION", "ap-southeast-1"))
        s3.download_file(bucket, key, model_local_path)
        print(f"[bias_model] Downloaded to {model_local_path}")

    # Load model
    if not os.path.exists(model_local_path):
        raise FileNotFoundError(f"Model not found at {model_local_path}")

    model = BERTClass()
    model_weights = torch.load(model_local_path, map_location=torch.device('cpu'))['state_dict']
    model.load_state_dict(model_weights)
    device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
    model.to(device)
    model.eval()
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

    return {"device": device, "model": model, "tokenizer": tokenizer}