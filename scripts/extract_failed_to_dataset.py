import json
import os

FAILED_PATH = "data/failed_outputs/errors.jsonl"
DATASET_PATH = "data/dataset.jsonl"

def extract_failed_to_dataset():
    if not os.path.exists(FAILED_PATH):
        print(f"❌ File tidak ditemukan: {FAILED_PATH}")
        return

    # Muat entri yang sudah ada agar tidak duplikat
    existing_keys = set()
    if os.path.exists(DATASET_PATH):
        with open(DATASET_PATH, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    item = json.loads(line)
                    key = item["instruction"] + item["input"]
                    existing_keys.add(key)
                except:
                    continue

    count = 0
    new_data = []

    with open(FAILED_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                item = json.loads(line)
                key = item["instruction"] + item["input"]
                if key in existing_keys:
                    continue  # Lewati jika sudah ada
                dataset_item = {
                    "instruction": item["instruction"],
                    "input": item["input"],
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

    with open(DATASET_PATH, "a", encoding="utf-8") as f:
        for item in new_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"✅ {count} data baru dari errors.jsonl berhasil dimasukkan ke dataset.jsonl")

if __name__ == "__main__":
    extract_failed_to_dataset()
