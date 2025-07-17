# generator.py
import json
import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL_PATH = "model"  # Ubah jika direktori model berbeda

def load_model():
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_PATH, trust_remote_code=True, local_files_only=True
    )
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        trust_remote_code=True,
        local_files_only=True,
        torch_dtype=torch.float16
    ).cuda()
    return model, tokenizer


def load_dataset(jsonl_path="data/dataset.jsonl"):
    with open(jsonl_path, "r", encoding="utf-8") as f:
        dataset = []
        for line in f:
            try:
                item = json.loads(line)
                if item.get("output", "") == "":
                    dataset.append(item)
            except json.JSONDecodeError:
                continue  # Lewati jika format JSON salah
        return dataset


def save_outputs(data, output_path="data/generated.jsonl"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "a", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

def generate_script(model, tokenizer, sample, max_tokens=300):
    prompt = (
        f"Generate a complete runnable Python script based on the instruction and HAR data below.\n"
        f"Include all necessary `import` statements.\n"
        f"Only return code. Do not add any explanations or comments.\n\n"
        f"Instruction: {sample['instruction']}\n\n"
        f"Gunakan string pendek untuk key, jangan masukkan data asli jika terlalu panjang.\n"
        f"HAR:\n{sample['input']}\n\n"
        f"Python Code:\n"
    )

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(
        **inputs,
        max_new_tokens=max_tokens,
        do_sample=True,
        temperature=0.5,
        pad_token_id=tokenizer.eos_token_id
    )
    generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
    cleaned = generated[len(prompt):].strip()

    # 🔍 Bersihkan blok markdown ```python
    if "```" in cleaned:
        parts = cleaned.split("```")
        for part in parts:
            if "import" in part or "def " in part or "requests" in part:
                cleaned = part.replace("python", "", 1).strip()
                break

    # 🧹 Hapus baris dengan kutip tidak seimbang atau dict tidak tertutup
    cleaned_lines = []
    open_brace = 0
    for line in cleaned.splitlines():
        if line.count('"') % 2 != 0 or line.count("'") % 2 != 0:
            continue  # lewati jika kutip tidak seimbang

        open_brace += line.count("{") - line.count("}")
        if open_brace < 0:
            open_brace = 0
            continue  # lewati jika brace ditutup berlebih

        cleaned_lines.append(line)

    # Potong bagian akhir jika masih ada kurung kurawal terbuka
    if open_brace != 0:
        for i in range(len(cleaned_lines) - 1, -1, -1):
            if "{" in cleaned_lines[i]:
                cleaned_lines = cleaned_lines[:i]
                break

    cleaned = "\n".join(cleaned_lines)

    return cleaned



if __name__ == "__main__":
    model, tokenizer = load_model()
    data = load_dataset()
    output_data = []

    for sample in data:
        print(f"🛠️  Generating for input ID: {sample['id'][:8]}...")
        output = generate_script(model, tokenizer, sample)
        sample["output"] = output
        output_data.append(sample)

    save_outputs(output_data)
    print(f"✅ {len(output_data)} script selesai dibuat dan disimpan di generated.jsonl")
