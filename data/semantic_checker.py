# Re-run the semantic checker after code execution environment reset
import re
import json
import os
from urllib.parse import urlparse

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
        if not any(m in code for m in ("requests.get", "requests.post", "requests.put", "requests.delete", "requests.patch")):
            return False, "Permintaan HTTP tapi tidak ada metode GET/POST/PUT/DELETE/PATCH"

    if "web3" in input_text or "swap" in instruction or "contract" in instruction:
        if "web3" not in code.lower():
            return False, "Instruksi menyebut 'Web3/swap/contract' tapi tidak ditemukan penggunaan Web3"

    if "input(" in input_text or "masukkan" in instruction:
        if "input(" not in code:
            return False, "Instruksi menyebut input, tapi tidak ditemukan penggunaan input()"

    # 2. Logical structure
    if "def " not in code and "class " not in code and "requests." not in code and "web3." not in code:
        return False, "Tidak ada fungsi, class, atau pemanggilan API (requests/web3)"

    # 3. Keyword enforcement
    urls = re.findall(r"https?://[^\s\"']+", input_text)
    for url in urls:
        domain = urlparse(url).netloc
        if domain not in code:
            return False, f"Domain URL '{domain}' tidak ditemukan dalam kode"

    # 4. Header enforcement if mentioned
    if "content-type" in input_text or "headers:" in input_text:
        if not ("headers" in code.lower() and ("application/json" in code.lower() or "content-type" in code.lower())):
            return False, "Header 'Content-Type' disebutkan tapi tidak ditemukan dalam kode"

    # 5. Body/data presence if 'body:' or 'json' mentioned
    if "body:" in input_text or "json" in instruction:
        if not any(k in code.lower() for k in ["data=", "json="]):
            return False, "Body disebutkan tapi tidak ditemukan dalam kode request"

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
