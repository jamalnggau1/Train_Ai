import sys
import os
import json
import uuid
import time
from datetime import datetime

# Tambah path agar bisa mengimpor modul lokal
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from generator import load_model, generate_script
from evaluator import evaluate_script
from data.semantic_checker import check_semantic_compatibility
from scripts.score_checker import compute_score

DATA_PATH = "data/dataset.jsonl"
GEN_PATH = "data/generated.jsonl"
FINAL_PATH = "data/final_datasets.jsonl"
LOG_PATH = "logs/auto_loop.log"
FAILED_DIR = "data/failed_outputs"

RETRY_LIMIT = 3
SCORE_THRESHOLD = 0.7
SLEEP_BETWEEN_BATCH = 3

os.makedirs(FAILED_DIR, exist_ok=True)

def save_jsonl_line(path, item):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

def log(text):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {text}"
    print(line)
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def load_existing_ids(path):
    ids = set()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    ids.add(json.loads(line)["id"])
                except:
                    continue
    return ids

def process_sample(pipe, sample, retry_count=0):
    if retry_count >= RETRY_LIMIT:
        log(f"⛔ Gagal permanen ID: {sample['id'][:8]} setelah {RETRY_LIMIT} percobaan.")
        return False

    try:
        model, tokenizer = pipe
        script = generate_script(model, tokenizer, sample).strip()
        sample["output"] = script

        # ❌ Output bukan Python (misal JSON)
        if script.startswith("{") or script.startswith("["):
            log(f"⚠️ Output JSON ID: {sample['id'][:8]}")
            save_jsonl_line(f"{FAILED_DIR}/non_python.jsonl", sample)
            return False

        # ❌ Terlalu pendek
        if len(script.splitlines()) < 3:
            log(f"⚠️ Terlalu pendek ID: {sample['id'][:8]}")
            save_jsonl_line(f"{FAILED_DIR}/too_short.jsonl", sample)
            return False

        # 🧪 Evaluasi runtime
        result = evaluate_script(script)
        if not result["success"]:
            log(f"⚠️ Runtime error ID: {sample['id'][:8]}")
            save_jsonl_line(f"{FAILED_DIR}/errors.jsonl", {
                "instruction": sample["instruction"],
                "input": sample["input"],
                "generated": script,
                "error": result["stderr"]
            })
            return process_sample(pipe, sample, retry_count + 1)

        # ✅ Evaluasi semantik
        sem_ok, reason = check_semantic_compatibility(sample)
        if not sem_ok:
            log(f"❌ Gagal semantik ID: {sample['id'][:8]} | {reason}")
            return process_sample(pipe, sample, retry_count + 1)

        # ✅ Evaluasi skor sintaks
        score = compute_score(script)
        if score["syntax_valid_percent"] < SCORE_THRESHOLD * 100:
            log(f"❌ Skor rendah ID: {sample['id'][:8]} | Syntax: {score['syntax_valid_percent']:.2f}")
            return process_sample(pipe, sample, retry_count + 1)

        if score["line_count"] > 100:
            log(f"🗑️ Terlalu panjang ID: {sample['id'][:8]} | Line: {score['line_count']}")
            return process_sample(pipe, sample, retry_count + 1)
        if score["function_count"] < 1:
            log(f"🗑️ Tidak ada fungsi ID: {sample['id'][:8]}")
            return process_sample(pipe, sample, retry_count + 1)
        if script.count("#") > 20:
            log(f"🗑️ Terlalu banyak komentar ID: {sample['id'][:8]}")
            return process_sample(pipe, sample, retry_count + 1)

        # ✅ Lolos semua filter
        log(f"✅ OK ID: {sample['id'][:8]} | Line: {score['line_count']} | Func: {score['function_count']} | Syntax: {score['syntax_valid_percent']:.2f}%")
        save_jsonl_line(GEN_PATH, sample)
        save_jsonl_line(FINAL_PATH, sample)
        return True

    except Exception as e:
        log(f"🚨 ERROR ID: {sample['id'][:8]} | {str(e)}")
        return process_sample(pipe, sample, retry_count + 1)

def main():
    model, tokenizer = load_model()
    existing_ids = load_existing_ids(GEN_PATH)

    if not os.path.exists(DATA_PATH):
        log(f"❌ Tidak ada file {DATA_PATH}!")
        return

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = [json.loads(line) for line in f]

    total = len(data)
    success = 0
    for sample in data:
        if "id" not in sample:
            sample["id"] = str(uuid.uuid4())

        if sample["id"] in existing_ids:
            log(f"⚠️ Lewati duplikat ID: {sample['id'][:8]}")
            continue

        log(f"🔁 Proses ID: {sample['id'][:8]}")
        if process_sample((model, tokenizer), sample):
            success += 1
        time.sleep(SLEEP_BETWEEN_BATCH)

    log(f"🏁 Selesai. Total: {total} | Berhasil: {success} | Gagal: {total - success}")

if __name__ == "__main__":
    main()
