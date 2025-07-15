import sys
import os
import json
import uuid
import time
from datetime import datetime

# Pastikan direktori utama bisa diakses
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from generator import load_model, generate_script
from evaluator import evaluate_script
from data.semantic_checker import check_semantic_compatibility
from scripts.score_checker import compute_score

DATA_PATH = "data/dataset.jsonl"
GEN_PATH = "data/generated.jsonl"
FINAL_PATH = "data/final_datasets.jsonl"
LOG_PATH = "logs/auto_loop.log"

RETRY_LIMIT = 3
SCORE_THRESHOLD = 0.7  # minimal syntax score
SLEEP_BETWEEN_BATCH = 3  # detik

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

def process_sample(pipe, sample, retry_count=0):
    if retry_count >= RETRY_LIMIT:
        log(f"⛔ Gagal permanen ID: {sample['id'][:8]} setelah {RETRY_LIMIT} percobaan.")
        return False

    try:
        script = generate_script(pipe, sample).strip()
        sample["output"] = script

        # Evaluasi sintaks & eksekusi
        result = evaluate_script(script)
        if not result["success"]:
            log(f"⚠️ Runtime error ID: {sample['id'][:8]}")
            return process_sample(pipe, sample, retry_count + 1)

        # Evaluasi semantik
        sem_ok, reason = check_semantic_compatibility(sample)
        if not sem_ok:
            log(f"❌ Gagal semantik ID: {sample['id'][:8]} | {reason}")
            return process_sample(pipe, sample, retry_count + 1)

        # Evaluasi skor sintaks
        score = compute_score(script)
        if score["syntax_valid_percent"] < SCORE_THRESHOLD * 100:
            log(f"❌ Skor rendah ID: {sample['id'][:8]} | Syntax: {score['syntax_valid_percent']:.2f}")
            return process_sample(pipe, sample, retry_count + 1)

        # Filter tambahan
        if score["line_count"] > 100:
            log(f"🗑️ Terlalu panjang ID: {sample['id'][:8]} | Line: {score['line_count']}")
            return process_sample(pipe, sample, retry_count + 1)
        if score["line_count"] < 3 or score["function_count"] < 1:
            log(f"🗑️ Terlalu pendek ID: {sample['id'][:8]}")
            return process_sample(pipe, sample, retry_count + 1)
        if script.count("#") > 20:
            log(f"🗑️ Terlalu banyak komentar ID: {sample['id'][:8]}")
            return process_sample(pipe, sample, retry_count + 1)

        # ✅ Simpan hasil sukses
        log(f"✅ OK ID: {sample['id'][:8]} | Line: {score['line_count']} | Func: {score['function_count']} | Syntax: {score['syntax_valid_percent']:.2f}%")
        save_jsonl_line(GEN_PATH, sample)
        save_jsonl_line(FINAL_PATH, sample)
        return True

    except Exception as e:
        log(f"🚨 ERROR ID: {sample['id'][:8]} | {str(e)}")
        return process_sample(pipe, sample, retry_count + 1)

def main():
    pipe = load_model()

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
        log(f"🔁 Proses ID: {sample['id'][:8]}")
        if process_sample(pipe, sample):
            success += 1
        time.sleep(SLEEP_BETWEEN_BATCH)

    log(f"🏁 Selesai. Total: {total} | Berhasil: {success} | Gagal: {total - success}")

if __name__ == "__main__":
    main()
