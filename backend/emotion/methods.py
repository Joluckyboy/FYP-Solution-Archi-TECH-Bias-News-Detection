from collections import Counter, defaultdict

def predict(token_chunks, tokenizer, classifier):
    results = []
    for chunk in token_chunks:
        # Detokenize the chunk back into text
        chunk_text = tokenizer.decode(chunk, skip_special_tokens=True)
        
        # Perform emotion classification on the chunk
        model_output = classifier(chunk_text)
        
        # Store the results in sequence
        results.append(model_output)
    return results

def aggregate_emotions_weighted(emotion_results, chunk_lengths):
    # Calculate proportional weights based on chunk lengths
    total_length = sum(chunk_lengths)
    weights = [length / total_length for length in chunk_lengths]
    
    aggregated = defaultdict(float)
    for i, chunk in enumerate(emotion_results):
        for emotion in chunk[0]:
            aggregated[emotion['label']] += emotion['score'] * weights[i]
    
    # No need to normalize by total weight, as weights already sum to 1
    return dict(sorted(aggregated.items(), key=lambda x: x[1], reverse=True))


def aggregate_emotions_majority_vote(emotion_results):
    top_emotions = [max(chunk[0], key=lambda x: x['score'])['label'] for chunk in emotion_results]
    emotion_counts = Counter(top_emotions)
    return emotion_counts.most_common()

def hybrid_aggregation(emotion_results, weights):
    # Weighted Averaging
    weighted_aggregate = aggregate_emotions_weighted(emotion_results, weights)
    
    # Majority Vote
    majority_vote = aggregate_emotions_majority_vote(emotion_results)
    
    return weighted_aggregate, majority_vote

