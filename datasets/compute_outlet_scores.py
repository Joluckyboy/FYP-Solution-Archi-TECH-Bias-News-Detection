import json
import pandas as pd

INPUT_CSV  = "news_with_model_scores.csv"
OUTPUT_CSV = "outlet_scores.csv"

def main():
    df = pd.read_csv(INPUT_CSV)

    df["sentiment"] = df["sentiment_result_json"].apply(
        lambda s: json.loads(s) if isinstance(s, str) and s.strip() else {}
    )
    df["emotion"] = df["emotion_weighted_json"].apply(
        lambda s: json.loads(s) if isinstance(s, str) and s.strip() else {}
    )

    # Extract numeric features per article
    df["sent_neutral"] = df["sentiment"].apply(lambda d: d.get("neutral", 0.0))
    df["emo_neutral"]  = df["emotion"].apply(lambda d: d.get("neutral", 0.0))

    # Group by outlet (site)
    grouped = df.groupby("site").agg(
        sent_neutral_avg=("sent_neutral", "mean"),
        emo_neutral_avg=("emo_neutral", "mean"),
        article_count=("url", "count"),
    ).reset_index()

    # Derive 0–1 scores for chart
    grouped["reliability"]  = grouped["sent_neutral_avg"].clip(0, 1)
    grouped["emotionality"] = (1 - grouped["emo_neutral_avg"]).clip(0, 1)

    grouped.to_csv(OUTPUT_CSV, index=False)
    print("Saved outlet scores to", OUTPUT_CSV)

if __name__ == "__main__":
    main()
