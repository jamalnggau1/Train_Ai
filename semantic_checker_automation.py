import re
import json
import os

INPUT_PATH = "data/generated.jsonl"
FINAL_PATH = "data/final_dataset_soft.jsonl"
REJECTED_PATH = "data/failed_outputs/errors.jsonl"

automation_keywords = [
    "requests", "aiohttp", "httpx", "selenium", "web3", "pyautogui", "pyppeteer", "undetected_chromedriver",
    "sign", "claim", "swap", "trigger", "button", "submit", "task", "schedule"
]

def check_semantic_for_automation(sample):
    instruction = sample["instruction"].lower()
    input_text = sample["input"].lower()
    code = sample["output"].strip()

    # 🚫 1. Jangan kosong atau dummy
    if not code or len(code.splitlines()) < 2:
        return False, "Output terlalu pendek atau kosong"

    if "pass" in code and "def" in code and len(code.splitlines()) <= 5:
        return False, "Fungsi kosong dengan pass"

    # ✅ 2. Harus ada aktivitas automation / script logic
    automation_detected = any(lib in code.lower() for lib in automation_keywords)
    if not automation_detected:
        return False, "Tidak ditemukan aktivitas automation dalam kode"

    # ✅ 3. Harus ada struktur fungsional
    if not any(k in code for k in ["def ", "class ", "requests.", "async def", "await", "web3.", "selenium."]):
        return False, "Tidak ada struktur logis seperti fungsi, kelas, atau action"

    # ✅ 4. Jika menyebut http, harus akses URL valid
    if "http" in input_text:
        urls = re.findall(r"https?://[^\s\"']+", input_text)
        for url in urls:
            if url not in code:
                return False, f"URL {url} disebut tapi tidak digunakan dalam kode"

    # ✅ 5. Keyword checker (contoh swap harus pakai web3)
    if "swap" in instruction or "web3" in input_text:
        if "web3" not in code.lower():
            return False, "Instruksi menyebut 'swap' atau 'Web3' tapi tidak ada penggunaan Web3"

    return True, None

def run_semantic_checker_automation():
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
            passed, reason = check_semantic_for_automation(item)
            if passed:
                final_data.append(item)
            else:
                item["rejected_reason"] = reason
                rejected_data.append(item)

    os.makedirs(os.path.dirname(FINAL_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(REJECTED_PATH), exist_ok=True)

    with open(FINAL_PATH, "w", encoding="utf-8") as f:
        for item in final_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    with open(REJECTED_PATH, "w", encoding="utf-8") as f:
        for item in rejected_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"✅ Selesai menyaring automation dataset")
    print(f"   - Total   : {total}")
    print(f"   - Diterima: {len(final_data)} → {FINAL_PATH}")
    print(f"   - Ditolak : {len(rejected_data)} → {REJECTED_PATH}")

# Jalankan
run_semantic_checker_automation()
