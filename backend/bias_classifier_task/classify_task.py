# classify_task.py
import boto3, csv, os, json, torch, logging
from io import StringIO
from transformers import BertTokenizer, BertModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── S3 config from environment variables ──────────────────────
BUCKET       = os.environ["S3_BUCKET"]
CSV_KEY      = "scraped_articles/scraped_articles.csv"
MODEL_KEY    = "bias_model/best_model_ba_12_wd.pt"
MODEL_PATH   = "/tmp/best_model_ba_12_wd.pt"

# ── BERT model definition (same as your existing code) ────────
class BERTClass(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.bert_model = BertModel.from_pretrained(
            'bert-base-uncased', return_dict=True)
        self.dropout = torch.nn.Dropout(0.3)
        self.linear  = torch.nn.Linear(768, 5)

    def forward(self, input_ids, attn_mask, token_type_ids):
        out = self.bert_model(input_ids,
                              attention_mask=attn_mask,
                              token_type_ids=token_type_ids)
        return self.linear(self.dropout(out.pooler_output))

def load_model():
    logger.info("Loading BERT model from /tmp ...")
    model = BERTClass()
    weights = torch.load(MODEL_PATH, map_location="cpu")["state_dict"]
    model.load_state_dict(weights)
    model.eval()
    tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
    logger.info("Model loaded ✓")
    return model, tokenizer

def classify_article(text, model, tokenizer):
    enc = tokenizer(
        text,
        add_special_tokens=True,
        max_length=256,
        padding="max_length",
        truncation=True,
        return_attention_mask=True,
        return_tensors="pt"
    )
    with torch.no_grad():
        out = model(enc["input_ids"],
                    enc["attention_mask"],
                    enc["token_type_ids"])
        probs = torch.sigmoid(out).cpu().numpy().tolist()[0]
    labels = ["left","leaning-left","center","leaning-right","right"]
    return labels[probs.index(max(probs))]

def main():
    s3 = boto3.client("s3", region_name=os.environ.get("AWS_REGION","us-east-1"))

    # 1. Download model
    logger.info(f"Downloading model from s3://{BUCKET}/{MODEL_KEY}")
    s3.download_file(BUCKET, MODEL_KEY, MODEL_PATH)

    # 2. Download CSV
    logger.info(f"Downloading CSV from s3://{BUCKET}/{CSV_KEY}")
    obj     = s3.get_object(Bucket=BUCKET, Key=CSV_KEY)
    content = obj["Body"].read().decode("utf-8")
    reader  = csv.DictReader(StringIO(content))
    articles = list(reader)
    headers  = reader.fieldnames or []
    logger.info(f"Loaded {len(articles)} articles")

    # 3. Load model ONCE (big saving vs calling API per article)
    model, tokenizer = load_model()

    # 4. Classify only unlabeled articles
    labeled = 0
    for article in articles:
        if not article.get("political_bias"):
            text  = f"{article.get('title','')} {article.get('summary','')}"
            label = classify_article(text, model, tokenizer)
            article["political_bias"] = label
            labeled += 1

    logger.info(f"Classified {labeled} articles ✓")

    # 5. Write labeled CSV back to S3
    out = StringIO()
    writer = csv.DictWriter(out, fieldnames=headers)
    writer.writeheader()
    writer.writerows(articles)

    s3.put_object(
        Bucket=BUCKET, Key=CSV_KEY,
        Body=out.getvalue().encode("utf-8"),
        ContentType="text/csv"
    )
    logger.info("Uploaded labeled CSV to S3 ✓")
    logger.info("Done!")

if __name__ == "__main__":
    main()