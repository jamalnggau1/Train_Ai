import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import uuid
from scripts.score_checker import run_score_checker
from data.semantic_checker import run_semantic_checker
from scripts import extract_failed_to_dataset
from generator import load_model, load_dataset, generate_script
from evaluator import evaluate_script
from scripts.semantic_checker_automation import run_semantic_checker_automation


# Path dataset
DATA_PATH = "data/dataset.jsonl"
GENERATED_PATH = "data/generated.jsonl"
FAILED_DIR = "data/failed_outputs"
os.makedirs(FAILED_DIR, exist_ok=True)


def save_jsonl_line(path, item):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")


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


def main_loop():
    print("🔁 Memulai loop self-training...")

    model, tokenizer = load_model()

    existing_ids = load_existing_ids(GENERATED_PATH)

    # Statistik
    success_count = fail_count = 0
    json_count = short_count = syntax_error_count = other_error_count = 0

    data = []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        for line in f:
            sample = json.loads(line)
            if "id" not in sample:
                sample["id"] = str(uuid.uuid4())
            data.append(sample)

    print(f"📦 Memproses {len(data)} item...")

    for sample in data:
        print(f"\n🎯 Memproses ID: {sample['id'][:8]}")

        if sample["id"] in existing_ids:
            print("⚠️ Sudah ada di generated.jsonl, lewati.")
            continue

        try:
            script_code = generate_script(model, tokenizer, sample).strip()

            sample["output"] = script_code

            # Filter 1: Output seperti JSON
            if script_code.startswith("{") or script_code.startswith("["):
                print("⚠️ Output tampaknya JSON, bukan Python.")
                json_count += 1
                save_jsonl_line(f"{FAILED_DIR}/non_python.jsonl", sample)
                continue

            # Filter 2: Terlalu pendek
            if len(script_code.splitlines()) < 2:
                print("⚠️ Output terlalu pendek.")
                short_count += 1
                save_jsonl_line(f"{FAILED_DIR}/too_short.jsonl", sample)
                continue

            # Evaluasi eksekusi script
            eval_result = evaluate_script(script_code)

            if eval_result["success"]:
                print("✅ Script berhasil dijalankan.")
                success_count += 1
                save_jsonl_line(GENERATED_PATH, sample)
            else:
                print("❌ Script gagal.")
                print("🪲 Error:", eval_result["stderr"])
                stderr = eval_result["stderr"]

                if "SyntaxError" in stderr:
                    syntax_error_count += 1
                else:
                    other_error_count += 1

                fail_count += 1
                save_jsonl_line(f"{FAILED_DIR}/errors.jsonl", {
                    "instruction": sample["instruction"],
                    "input": sample["input"],
                    "generated": script_code,
                    "error": stderr
                })

        except Exception as e:
            print("🚨 Error tak terduga:", e)
            other_error_count += 1
            fail_count += 1

    # Ringkasan akhir
    print("\n📊 Ringkasan:")
    print(f"✅ Berhasil: {success_count}")
    print(f"❌ Gagal: {fail_count}")
    print(f"⚠️ JSON: {json_count} | Terlalu pendek: {short_count} | Syntax: {syntax_error_count} | Lain: {other_error_count}")


if __name__ == "__main__":
    main_loop()
    print("\n🔁 Menambahkan error ke dataset...")
    extract_failed_to_dataset.extract_failed_to_dataset()

    run_semantic_checker_automation()
    print("soft cheker")
    print("\n🧠 Menjalankan semantic checker...")
    run_semantic_checker()

    print("\n📐 Menjalankan score checker...")
    run_score_checker()
