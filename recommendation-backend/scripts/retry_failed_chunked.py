"""Retries a list of previously-failed trailer filenames through
batch_process_trailers.py in small chunks, each run as a *fresh subprocess*.

Why chunked subprocesses: the first full run loaded ML models once and reused
that process for all 74 videos. Partway through, one video (#4) stalled for
~37 minutes then every subsequent video failed identically with a CUBLAS
"CUDA_STATUS_NOT_INITIALIZED" error — the GPU/CUDA context had been reset
(most likely a Windows driver TDR from the stall) and onnxruntime's CUDA
provider never recovers within the same process. A fresh process gets a
fresh CUDA context, so re-running in small chunks bounds the blast radius:
if one chunk's process degrades, only that chunk needs a retry, not all 68.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BATCH_SCRIPT = SCRIPT_DIR / "batch_process_trailers.py"


def chunked(items: list[str], size: int) -> list[list[str]]:
    return [items[i:i + size] for i in range(0, len(items), size)]


def run(filenames_path: str, chunk_size: int, pause_seconds: float) -> None:
    all_filenames = [line.strip() for line in Path(filenames_path).read_text(encoding="utf-8").splitlines() if line.strip()]
    chunks = chunked(all_filenames, chunk_size)

    print("=" * 80)
    print(f"CHUNKED RETRY: {len(all_filenames)} filename(s) in {len(chunks)} chunk(s) of up to {chunk_size}")
    print("=" * 80)

    tmp_dir = SCRIPT_DIR.parent / "storage" / "_retry_chunks"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    chunk_results = []
    for idx, chunk in enumerate(chunks, 1):
        chunk_file = tmp_dir / f"chunk_{idx:02d}.txt"
        chunk_file.write_text("\n".join(chunk), encoding="utf-8")

        print(f"\n{'-' * 80}\nCHUNK {idx}/{len(chunks)} ({len(chunk)} files) — starting fresh process\n{'-' * 80}")
        t0 = time.time()
        result = subprocess.run(
            [sys.executable, str(BATCH_SCRIPT), "--filenames-file", str(chunk_file)],
        )
        elapsed = time.time() - t0
        chunk_results.append({"chunk": idx, "files": len(chunk), "exit_code": result.returncode, "elapsed_sec": round(elapsed, 1)})
        print(f"CHUNK {idx}/{len(chunks)} finished: exit_code={result.returncode}, elapsed={elapsed:.1f}s")

        if idx < len(chunks) and pause_seconds > 0:
            print(f"Pausing {pause_seconds:.0f}s before next chunk (let GPU/driver settle)...")
            time.sleep(pause_seconds)

    print("\n" + "=" * 80)
    print("CHUNKED RETRY COMPLETE")
    print("=" * 80)
    for r in chunk_results:
        print(f"  Chunk {r['chunk']:02d}: {r['files']} files, exit_code={r['exit_code']}, {r['elapsed_sec']}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--filenames-file", type=str, required=True, help="Newline-delimited text file of raw filenames to retry.")
    parser.add_argument("--chunk-size", type=int, default=10, help="Number of videos per subprocess run.")
    parser.add_argument("--pause-seconds", type=float, default=10.0, help="Seconds to pause between chunks.")
    args = parser.parse_args()
    run(args.filenames_file, args.chunk_size, args.pause_seconds)
