# extract_failed_to_dataset.py

import json
import os

FAILED_PATH = "data/failed_outputs/errors.jsonl"
RAW_DATASET_PATH = "data/dataset.jsonl"  # dataset mentah (tanpa output)

def extract_failed_to_dataset():
    if not os.path.exists(FAILED_PATH):
        print(f"❌ File tidak ditemukan: {FAILED_PATH}")
        return

    # Muat entri yang sudah ada untuk mencegah duplikat
    existing_keys = set()
    if os.path.exists(RAW_DATASET_PATH):
        with open(RAW_DATASET_PATH, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    item = json.loads(line)
                    key = item.get("instruction", "") + item.get("input", "")
                    existing_keys.add(key)
                except:
                    continue

    count = 0
    new_data = []

    with open(FAILED_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                item = json.loads(line)
                instruction = item.get("instruction", "")
                input_text = item.get("input", "")
                key = instruction + input_text

                if not instruction or not input_text:
                    continue  # skip jika tidak lengkap

                if key in existing_keys:
                    continue  # skip jika sudah ada di dataset mentah

                # Reset output
                dataset_item = {
                    "instruction": instruction,
                    "input": input_text,
                    "output": ""
                }
                new_data.append(dataset_item)
                existing_keys.add(key)
                count += 1
            except Exception as e:
                print("⚠️ Gagal parsing satu baris:", e)

    if not new_data:
        print("⚠️ Tidak ada data baru yang bisa ditambahkan.")
        return

    # Simpan ke dataset mentah
    with open(RAW_DATASET_PATH, "a", encoding="utf-8") as f:
        for item in new_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"✅ {count} entri error berhasil dikembalikan ke dataset mentah.")

if __name__ == "__main__":
    extract_failed_to_dataset()
