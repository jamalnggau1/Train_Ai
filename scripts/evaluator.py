# evaluator.py
import subprocess
import tempfile
import uuid
import os

def evaluate_script(script_code: str, timeout=10) -> dict:
    result = {
        "success": False,
        "stdout": "",
        "stderr": "",
    }

    # Simpan script sementara ke file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
        tmp.write(script_code)
        tmp_path = tmp.name

    try:
        # Jalankan script Python
        proc = subprocess.run(
            ["python", tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        result["success"] = proc.returncode == 0
        result["stdout"] = proc.stdout
        result["stderr"] = proc.stderr
    except subprocess.TimeoutExpired:
        result["stderr"] = "Script execution timed out."
    except Exception as e:
        result["stderr"] = f"Unexpected error: {str(e)}"
    finally:
        # Hapus file sementara
        os.remove(tmp_path)

    return result
