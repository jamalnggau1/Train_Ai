import json
import os

GENERATED_PATH = "data/generated.jsonl"

def remove_duplicates_from_generated():
    if not os.path.exists(GENERATED_PATH):
        print("❌ File generated.jsonl tidak ditemukan.")
        return

    seen = set()
    unique_samples = []
    total = 0
    duplicate_count = 0

    with open(GENERATED_PATH, "r", encoding="utf-8") as f:
        for line in f:
            total += 1
            try:
                sample = json.loads(line)
                key = sample.get("instruction", "") + sample.get("input", "") + sample.get("output", "")
                if key not in seen:
                    seen.add(key)
                    unique_samples.append(sample)
                else:
                    duplicate_count += 1
            except Exception as e:
                print(f"⚠️ Gagal parse JSONL: {e}")

    # Tulis ulang hanya yang unik ke file yang sama
    with open(GENERATED_PATH, "w", encoding="utf-8") as f:
        for sample in unique_samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")

    print("✅ Duplikasi dibersihkan.")
    print(f"   - Total entri dibaca  : {total}")
    print(f"   - Tersisa unik        : {len(unique_samples)}")
    print(f"   - Duplikat dibuang    : {duplicate_count}")

if __name__ == "__main__":
    remove_duplicates_from_generated()
