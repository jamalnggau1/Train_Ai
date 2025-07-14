import json
import os
import uuid

def parse_har_file(har_path):
    with open(har_path, "r", encoding="utf-8") as f:
        har_data = json.load(f)

    entries = har_data.get("log", {}).get("entries", [])
    parsed = []

    for entry in entries:
        req = entry.get("request", {})
        method = req.get("method", "GET")
        url = req.get("url", "")
        headers = {h["name"]: h["value"] for h in req.get("headers", [])}
        post_data = req.get("postData", {}).get("text", "")

        # Buat input untuk AI
        input_text = f"[{method}] {url}\nHeaders:\n"
        input_text += "\n".join([f"{k}: {v}" for k, v in headers.items()])
        if post_data:
            input_text += f"\n\nBody:\n{post_data}"

        data = {
            "id": str(uuid.uuid4()),
            "instruction": "Buatkan script Python menggunakan modul requests berdasarkan permintaan HTTP berikut.",
            "input": input_text,
            "output": ""  # nanti diisi AI
        }
        parsed.append(data)

    return parsed

def save_dataset(parsed_data, output_file="data/dataset.jsonl"):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "a", encoding="utf-8") as f:
        for item in parsed_data:
            f.write(json.dumps(item) + "\n")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python parse_har.py yourfile.har")
        exit(1)

    har_file = sys.argv[1]
    dataset = parse_har_file(har_file)
    save_dataset(dataset)
    print(f"✅ {len(dataset)} request disimpan ke dataset.jsonl")
