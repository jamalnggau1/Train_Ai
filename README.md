# 🧠 Self-Training Code Generation AI (Python Instruction → Script)

Proyek ini membangun sistem **self-training AI** untuk menghasilkan kode Python dari instruksi teks natural. Model akan:
- Menghasilkan skrip berdasarkan instruksi
- Mengevaluasi hasilnya
- Mencatat yang gagal dan memperbaikinya sendiri
- Menyaring hasil dengan seleksi semantik
- Mengulang proses secara otomatis

---

## 📁 Struktur Folder

```bash
Train_Ai/
├── data/
│   ├── dataset.jsonl            # Dataset utama (instruction, input, output="")
│   ├── generated.jsonl          # Output yang berhasil dijalankan
│   ├── final_dataset.jsonl      # Output yang lolos seleksi semantik (siap fine-tune)
│   ├── rejected_semantic.jsonl  # Output yang gagal seleksi semantik
│   ├── failed_outputs/
│   │   ├── errors.jsonl         # Output gagal saat dieksekusi
│   │   ├── non_python.jsonl     # Output JSON / bukan kode Python
│   │   └── too_short.jsonl      # Output terlalu pendek atau kosong
│   └── semantic_checker.py      # Seleksi semantik otomatis
├── model/                       # Model Hugging Face (tokenizer, config, weights)
├── scripts/
│   ├── loop.py                  # Main loop: generate → evaluasi → seleksi
│   ├── generator.py             # Modul: load_model, generate_script
│   ├── evaluator.py             # Modul: evaluasi runtime script Python
│   ├── extract_failed_to_dataset.py  # Ekstraksi ulang data gagal ke dataset
│   └── download_model.py        # (Opsional) Unduh model awal dari HuggingFace
📚 Format Dataset

```{
  "instruction": "Generate a POST request with custom headers.",
  "input": "Send request to https://api.example.com/data using the requests module",
  "output": ""
}```

---

✅ Prasyarat
Python 3.10+

Paket Python yang diperlukan:

```
pip install -r requirements.txt
requirements.txt
transformers
torch
accelerate
datasets

---

⬇️ Download Model Hugging Face
Model akan disimpan di folder model/. Contoh:

from huggingface_hub import snapshot_download
snapshot_download(repo_id="cahya/gpt2-small-indonesian-124M", local_dir="model")
🔁 Menjalankan Proses Self-Training

python scripts/loop.py
Fungsi:

Menghasilkan skrip dari dataset.jsonl

Menyimpan output valid ke generated.jsonl

Mengekstrak data gagal ke errors.jsonl

Menambahkan kembali ke dataset agar bisa dilatih ulang

Menyaring hasil semantik dengan semantic_checker.py

Menulis dataset siap latih ke final_dataset.jsonl

---

📊 Ringkasan Otomatis (Contoh Output)

📦 Memproses 100 item...
✅ Script berhasil dijalankan.
❌ Script gagal. Disimpan ke failed_outputs.
📊 Ringkasan:
✅ Berhasil: 60 script
❌ Gagal: 40 script
⚠️ JSON: 5 | Terlalu pendek: 3 | SyntaxError: 12 | Error lain: 20

---

🔎 Seleksi Semantik (Cek Kualitas Output)
File semantic_checker.py melakukan pengecekan apakah kode:

Sesuai dengan URL dan kata kunci dalam instruksi

Menggunakan modul yang tepat (requests, web3, dsb)

Memiliki fungsi atau class

Tidak hanya komentar atau JSON

---

🧠 Fine-Tuning
Setelah mendapatkan final_dataset.jsonl, kamu bisa melatih ulang model kamu:

from datasets import load_dataset
dataset = load_dataset("json", data_files="data/final_dataset.jsonl")
Gunakan Trainer, LoRA, atau metode fine-tuning pilihanmu.

---

🔄 Loop Tanpa Henti
Loop akan terus berjalan:

Data gagal masuk ke dataset kosong

Dilatih ulang lagi

Script membaik seiring waktu

Tidak perlu campur tangan manusia

---

💡 Credits
Dikembangkan oleh @jamalnggau1
Dengan bantuan ChatGPT

---

🛡️ Lisensi
MIT License – bebas digunakan dan dimodifikasi.
