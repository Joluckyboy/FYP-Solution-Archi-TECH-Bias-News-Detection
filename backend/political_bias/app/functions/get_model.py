import boto3
import filelock  # pip install filelock
import os
import torch
from transformers import BertTokenizer
from ..models.bertclass import BERTClass

def get_model():
    model_local_dir = os.getenv("BIAS_MODEL_DIR", "/app/bias_model")
    model_local_path = os.path.join(model_local_dir, "best_model_ba_12_wd.pt")
    lock_path = model_local_path + ".lock"

    os.makedirs(model_local_dir, exist_ok=True)

    # File lock ensures only 1 worker downloads, others wait
    with filelock.FileLock(lock_path):
        if not os.path.exists(model_local_path):
            bucket = os.getenv("S3_MODEL_BUCKET")
            key = os.getenv("S3_MODEL_KEY", "bias_model/best_model_ba_12_wd.pt")
            print(f"[bias_model] Downloading from s3://{bucket}/{key}")
            s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION", "ap-southeast-1"))
            s3.download_file(bucket, key, model_local_path)
            print(f"[bias_model] Downloaded to {model_local_path}")
        else:
            print(f"[bias_model] Using cached model at {model_local_path}")

    # Load model
    model = BERTClass()
    model_weights = torch.load(model_local_path, map_location=torch.device('cpu'))['state_dict']
    model.load_state_dict(model_weights)
    device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
    model.to(device)
    model.eval()
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

    return {"device": device, "model": model, "tokenizer": tokenizer}