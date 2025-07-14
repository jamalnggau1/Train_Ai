# generator.py
import json
import os
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

MODEL_PATH = "model"  # Ubah jika direktori model berbeda

def load_model():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        local_files_only=True,
        trust_remote_code=True
    )
    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        pad_token_id=tokenizer.eos_token_id  # penting agar tidak error pada model causal
    )
    return pipe

def load_dataset(jsonl_path="data/dataset.jsonl"):
    with open(jsonl_path, "r", encoding="utf-8") as f:
        return [
            json.loads(line)
            for line in f
            if '"output": ""' in line  # hanya yang belum memiliki output
        ]

def save_outputs(data, output_path="data/generated.jsonl"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "a", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

def generate_script(pipe, sample, max_tokens=300):
    prompt = (
        "# Instruction: Write a Python script using the requests module.\n"
        f"# Task: {sample['instruction']}\n"
        f"# Details: {sample['input']}\n\n"
    )
    result = pipe(prompt, max_new_tokens=max_tokens, do_sample=True, temperature=0.7)
    generated = result[0]["generated_text"]

    cleaned = generated[len(prompt):].strip()

    # Optional: jika model menghasilkan markdown block
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")  # hapus karakter `
        cleaned = cleaned.replace("python", "", 1).strip()
    return cleaned


if __name__ == "__main__":
    pipe = load_model()
    data = load_dataset()
    output_data = []

    for sample in data:
        print(f"🛠️  Generating for input ID: {sample['id'][:8]}...")
        output = generate_script(pipe, sample)
        sample["output"] = output
        output_data.append(sample)

    save_outputs(output_data)
    print(f"✅ {len(output_data)} script selesai dibuat dan disimpan di generated.jsonl")
