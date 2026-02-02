from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F

# TODO: Using LLM for sentiments, If WE can spare time on it [local LLM] [Qwen 3 8B]

# Maximum number of tokens per BERT chunk (BERT models have a 512-token limit)
MAX_TOKENS = 512

# Labels used by FinBERT for classification
LABELS = ["negative", "neutral", "positive"]

# FinBERT tokenizer converts text into tokens that the model can understand
tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")

# FinBERT model for sequence classification (predicts sentiment)
model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")

# Use GPU if available, otherwise fall back to CPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

def finbert_sentiment(text):
    """
    Compute sentiment of a text using FinBERT.
    Handles long texts by chunking them into <= 512 tokens.
    Returns a dictionary with sentiment probabilities and a custom score.
    """

    # Tokenize text without truncation to preserve all tokens
    encoding = tokenizer(
        text,
        return_tensors="pt",
        truncation=False
    )
    
    # Extract the token IDs from the encoding (single sequence)
    input_ids = encoding["input_ids"][0]

    # Split the tokens into chunks of MAX_TOKENS to avoid BERT overflow
    chunks = input_ids.split(MAX_TOKENS)

    # List to store probability tensors for each chunk
    probs_list = []

    # Disable gradient calculation for inference (saves memory) (We dont need it since we are not training)
    with torch.no_grad():
        for chunk in chunks:
            # Add batch dimension and move chunk to device
            chunk = chunk.unsqueeze(0).to(device) # .to(device) moves the tensor to either GPU or CPU depending on what device we selected
            
            # Create an attention mask of ones (all tokens are valid)
            attention_mask = torch.ones_like(chunk)

            # Forward pass through the model
            outputs = model(
                input_ids=chunk,
                attention_mask=attention_mask
            )

            # Convert logits to probabilities using softmax
            probs = F.softmax(outputs.logits, dim=-1)[0]
            probs_list.append(probs)

    # Average probabilities across all chunks
    avg_probs = torch.mean(torch.stack(probs_list), dim=0)

    # Map probabilities to their corresponding labels
    sentiment = dict(zip(LABELS, avg_probs.tolist()))

    # Custom sentiment score: positive minus negative probability
    score = sentiment["positive"] - sentiment["negative"]

    return {
        "score": score,
        "positive": sentiment["positive"],
        "neutral": sentiment["neutral"],
        "negative": sentiment["negative"]
    }

if __name__ == "__main__":
    result = finbert_sentiment("Alphabet Becomes Newest $4 Trillion Company, Joining Nvidia")
    print(result)