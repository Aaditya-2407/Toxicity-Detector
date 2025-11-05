from transformers import AutoTokenizer, AutoModelForSequenceClassification
import os

MODEL_NAME = "unitary/toxic-bert"
MODEL_DIR = os.path.join("app", "toxic_bert", "model_files")

print(f"Downloading model and tokenizer for '{MODEL_NAME}'...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

print(f"Saving to '{MODEL_DIR}'...")
tokenizer.save_pretrained(MODEL_DIR)
model.save_pretrained(MODEL_DIR)

print("✅ Model download complete!")