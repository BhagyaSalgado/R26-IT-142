"""Measures colour grading for every processed trailer and writes it beside
the existing per-scene data as colour_features.csv.

Run once after new trailers are processed. Safe to re-run: trailers that
already have the file are skipped unless --force is passed.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.colour_features import COLOUR_DIMS, scene_colour_series

REPO = Path(__file__).resolve().parent.parent


def trailer_dirs(root: Path) -> list[Path]:
    """Any folder holding a final_system_output.csv is one processed trailer."""
    return sorted({p.parent for p in root.rglob("final_system_output.csv")})


def run(roots: list[Path], force: bool) -> None:
    done = skipped = no_frames = failed = 0

    for root in roots:
        if not root.exists():
            continue
        dirs = trailer_dirs(root)
        print(f"\n{root.relative_to(REPO)}: {len(dirs)} trailer(s)")

        for d in dirs:
            out = d / "colour_features.csv"
            if out.exists() and not force:
                skipped += 1
                continue

            frames = d / "frames"
            if not frames.exists():
                no_frames += 1
                continue

            try:
                df = pd.read_csv(d / "final_system_output.csv")
                scene_ids = [int(s) for s in df["scene"].tolist()]
                series = scene_colour_series(frames, scene_ids)
                if series is None:
                    no_frames += 1
                    continue
                pd.DataFrame({"scene": scene_ids, **series}).to_csv(out, index=False)
                done += 1
                if done % 20 == 0:
                    print(f"  ...{done} done")
            except Exception as exc:
                print(f"  FAILED {d.name}: {type(exc).__name__}: {str(exc)[:90]}")
                failed += 1

    print("\n" + "=" * 66)
    print(f"colour_features.csv written : {done}")
    print(f"already had one (skipped)   : {skipped}")
    print(f"no frames available         : {no_frames}")
    print(f"failed                      : {failed}")
    print("=" * 66)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--force", action="store_true", help="Recompute even if colour_features.csv exists.")
    args = p.parse_args()
    run([REPO / "storage" / "genre_corpus", REPO / "storage" / "outputs"], args.force)
