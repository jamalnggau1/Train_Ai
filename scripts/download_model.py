from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL_ID = "Salesforce/codegen-350M-mono"
SAVE_DIR = "model"

print("⬇️  Mengunduh model:", MODEL_ID)
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(MODEL_ID)
print("💾 Menyimpan ke:", SAVE_DIR)
tokenizer.save_pretrained(SAVE_DIR)
model.save_pretrained(SAVE_DIR)
print("✅ Selesai.")
