import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
import uuid
import os
from data.semantic_checker import run_semantic_checker
import extract_failed_to_dataset
from generator import load_model, load_dataset, generate_script
from evaluator import evaluate_script

os.makedirs("data/failed_outputs", exist_ok=True)
DATA_PATH = "data/dataset.jsonl"


def save_jsonl_line(path, item):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(item) + "\n")

def main_loop():
    print("🔁 Memulai loop self-training...")

    pipe = load_model()

    # Hitung performa
    success_count = 0
    fail_count = 0
    json_count = 0
    short_count = 0
    syntax_error_count = 0
    other_error_count = 0

    # Baca .jsonl dan tambahkan ID kalau belum ada
    data = []
    with open(DATA_PATH, "r") as f:
        for line in f:
            sample = json.loads(line)
            if "id" not in sample:
                sample["id"] = str(uuid.uuid4())
            data.append(sample)

    print(f"📦 Memproses {len(data)} item...")

    for sample in data:
        print(f"\n🎯 Memproses ID: {sample['id'][:8]}")

        try:
            script_code = generate_script(pipe, sample).strip()
            sample["output"] = script_code

            # Deteksi jika output berupa JSON atau string non-kode
            if script_code.startswith("{") or script_code.startswith("["):
                print("⚠️ Output tampaknya JSON, bukan script Python. Diskip.")
                json_count += 1
                save_jsonl_line("data/failed_outputs/non_python.jsonl", {
                    "instruction": sample["instruction"],
                    "input": sample["input"],
                    "output": script_code
                })
                continue

            # Jika terlalu pendek atau kosong
            if len(script_code.splitlines()) < 2:
                print("⚠️ Output terlalu pendek, kemungkinan tidak valid. Diskip.")
                short_count += 1
                save_jsonl_line("data/failed_outputs/too_short.jsonl", {
                    "instruction": sample["instruction"],
                    "input": sample["input"],
                    "output": script_code
                })
                continue

            # Evaluasi kode Python
            eval_result = evaluate_script(script_code)

            if eval_result["success"]:
                print("✅ Script berhasil dijalankan.")
                success_count += 1
                save_jsonl_line("data/generated.jsonl", sample)
            else:
                print("❌ Script gagal. Disimpan ke failed_outputs.")
                print("📝 Script yang dihasilkan:")
                print(script_code)
                print("🪲 Error saat evaluasi:")
                print(eval_result["stderr"])
                
                stderr = eval_result["stderr"]
                if "SyntaxError" in stderr:
                    syntax_error_count += 1
                else:
                    other_error_count += 1

                fail_count += 1
                error_sample = {
                    "instruction": sample["instruction"],
                    "input": sample["input"],
                    "generated": script_code,
                    "error": stderr
                }
                save_jsonl_line("data/failed_outputs/errors.jsonl", error_sample)

        except Exception as e:
            print("🚨 Error tak terduga:", e)
            other_error_count += 1
            fail_count += 1

    # Tampilkan ringkasan
    print("\n📊 Ringkasan:")
    print(f"✅ Berhasil: {success_count} script")
    print(f"❌ Gagal: {fail_count} script")
    print(f"⚠️ JSON: {json_count} | Terlalu pendek: {short_count} | SyntaxError: {syntax_error_count} | Error lain: {other_error_count}")
    # Di akhir loop.py


if __name__ == "__main__":
    main_loop() 
    extract_failed_to_dataset.extract_failed_to_dataset()
    run_semantic_checker()

