from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import os

MODEL_DIR = os.path.join("app", "toxic_bert", "model_files")

# Loaded once at startup; subsequent imports reuse these objects
print("Loading Toxic-BERT model…")
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
model.eval()
print("✅ Toxic-BERT ready.")

# --- Scoring labels (Jigsaw Toxic Comment Classification order) ---
LABELS = ["toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate"]

# --- Per-category weights (sum = 1.0) ---
# Severity reasoning: direct threats and severe toxicity are weighted highest;
# generic obscenity carries the least weight in isolation.
WEIGHTS = {
    "toxic":          0.20,
    "severe_toxic":   0.30,
    "obscene":        0.05,
    "threat":         0.25,
    "insult":         0.08,
    "identity_hate":  0.12,
}


def score_comment(text: str) -> dict:
    """
    Score a single comment with Toxic-BERT.

    Returns a dict with:
      - ``composite``  float [0, 1]  — weighted aggregate toxicity score
      - ``scores``     dict          — raw sigmoid probability for each of the
                                       6 Jigsaw categories (keys = LABELS)

    The composite is a weighted sum (not the max) so that isolated obscenity
    does not inflate the final score the same way a credible threat would.
    """
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)

    with torch.no_grad():
        outputs = model(**inputs)

    # sigmoid gives independent P(label) for each of the 6 classes
    probs = torch.nn.functional.sigmoid(outputs.logits)[0]

    scores = {label: probs[i].item() for i, label in enumerate(LABELS)}
    composite = sum(scores[label] * WEIGHTS[label] for label in LABELS)

    return {"composite": composite, "scores": scores}
