from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import os

MODEL_DIR = os.path.join("app", "toxic_bert", "model_files")

print("Loading local Toxic-BERT model...")
# These must be at the top level to load only once
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
print("✅ Model loaded successfully.")

def score_comment(text: str) -> float:
    """
    Scores a single comment for toxicity.
    Returns the toxicity score as a float between 0 and 1.
    """
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)

    with torch.no_grad():
        outputs = model(**inputs)

    # Use sigmoid to get independent probabilities for all 6 labels
    predictions = torch.nn.functional.sigmoid(outputs.logits)
    
    # Take the MAXIMUM score from ANY of the 6 categories
    # (toxic, severe_toxic, obscene, threat, insult, identity_hate)
    toxicity_score = torch.max(predictions[0]).item()
    
    return toxicity_score