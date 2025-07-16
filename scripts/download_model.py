from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL_ID = "deepseek-ai/deepseek-coder-1.3b-instruct"
SAVE_DIR = "model"

print("⬇️  Mengunduh model:", MODEL_ID)
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(MODEL_ID, device_map="auto", torch_dtype="auto")
print("💾 Menyimpan ke:", SAVE_DIR)
tokenizer.save_pretrained(SAVE_DIR)
model.save_pretrained(SAVE_DIR)
print("✅ Selesai.")
