# Re-run the semantic checker after code execution environment reset
import re
import json
import os

INPUT_PATH = "data/generated.jsonl"
FINAL_PATH = "data/final_dataset.jsonl"
REJECTED_PATH = "data/failed_outputs/errors.jsonl"

def check_semantic_compatibility(sample):
    instruction = sample["instruction"].lower()
    input_text = sample["input"].lower()
    code = sample["output"]

    # 1. Basic checks
    if not code.strip().startswith("import"):
        return False, "Script tidak mengimpor modul apa pun"

    if "http" in input_text:
        if "requests" not in code:
            return False, "Permintaan HTTP tapi modul 'requests' tidak digunakan"
        if "requests.get" not in code and "requests.post" not in code:
            return False, "Permintaan HTTP tapi tidak ada metode GET/POST"

    if "web3" in input_text or "swap" in instruction:
        if "web3" not in code.lower():
            return False, "Instruksi menyebut 'Web3' atau 'swap' tapi tidak ditemukan penggunaan Web3"

    if "input(" in input_text:
        if "input(" not in code:
            return False, "Instruksi menyebut input, tapi tidak ditemukan penggunaan input()"

    # 2. Logical structure
    if "def " not in code and "class " not in code:
        return False, "Tidak ada fungsi atau kelas yang didefinisikan"

    # 3. Keyword enforcement
    keywords = re.findall(r"https?://[^\s]+", input_text)
    for url in keywords:
        if url not in code:
            return False, f"URL '{url}' tidak ditemukan di script"

    return True, None

def run_semantic_checker():
    if not os.path.exists(INPUT_PATH):
        print("❌ File generated.jsonl tidak ditemukan.")
        return

    final_data = []
    rejected_data = []
    total = 0

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            total += 1
            item = json.loads(line)
            passed, reason = check_semantic_compatibility(item)
            if passed:
                final_data.append(item)
            else:
                item["rejected_reason"] = reason
                rejected_data.append(item)

    with open(FINAL_PATH, "w", encoding="utf-8") as f:
        for item in final_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    with open(REJECTED_PATH, "w", encoding="utf-8") as f:
        for item in rejected_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"✅ Seleksi selesai. Total: {total}")
    print(f"   - Lolos  : {len(final_data)} ke {FINAL_PATH}")
    print(f"   - Ditolak: {len(rejected_data)} ke {REJECTED_PATH}")

run_semantic_checker()
