import json
import os
import re

INPUT_PATH = "data/generated.jsonl"
SCORE_LOG = "data/score_log.jsonl"
SUMMARY_PATH = "data/score_summary.json"

def analyze_code(code):
    lines = code.strip().splitlines()
    line_count = len(lines)

    function_count = len(re.findall(r"^\s*def\s+\w+", code, re.MULTILINE))
    class_count = len(re.findall(r"^\s*class\s+\w+", code, re.MULTILINE))
    comment_count = len(re.findall(r"^\s*#.*", code, re.MULTILINE))
    variable_count = len(re.findall(r"\b\w+\s*=", code))

    hardcoded_values = len(re.findall(r"[^a-zA-Z](\"[^\"]*\"|'[^']*'|\d+)", code))

    try:
        compile(code, "<string>", "exec")
        syntax_valid = True
    except Exception:
        syntax_valid = False

    return {
        "line_count": line_count,
        "function_count": function_count,
        "class_count": class_count,
        "comment_count": comment_count,
        "variable_count": variable_count,
        "hardcoded_values": hardcoded_values,
        "syntax_valid": syntax_valid,
    }

def run_score_checker():
    if not os.path.exists(INPUT_PATH):
        print(f"❌ File tidak ditemukan: {INPUT_PATH}")
        return

    all_scores = []
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            sample = json.loads(line)
            code = sample.get("output", "").strip()
            if not code:
                continue
            score = analyze_code(code)
            all_scores.append(score)

            # Simpan log per sample (opsional)
            log_item = {
                "id": sample.get("id"),
                "instruction": sample["instruction"],
                "score": score,
            }
            with open(SCORE_LOG, "a", encoding="utf-8") as log_f:
                log_f.write(json.dumps(log_item, ensure_ascii=False) + "\n")

    if not all_scores:
        print("⚠️ Tidak ada script yang bisa dinilai.")
        return

    # Ringkasan statistik
    summary = {
        "total": len(all_scores),
        "avg_line_count": round(sum(s["line_count"] for s in all_scores) / len(all_scores), 2),
        "avg_function_count": round(sum(s["function_count"] for s in all_scores) / len(all_scores), 2),
        "avg_comment_count": round(sum(s["comment_count"] for s in all_scores) / len(all_scores), 2),
        "avg_variable_count": round(sum(s["variable_count"] for s in all_scores) / len(all_scores), 2),
        "syntax_valid_percent": round(
            sum(1 for s in all_scores if s["syntax_valid"]) / len(all_scores) * 100, 2
        ),
    }

    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("📊 Ringkasan Skor Kode:")
    for key, val in summary.items():
        print(f"   - {key}: {val}")

if __name__ == "__main__":
    run_score_checker()
