"""Per-genre trailer norms learned from real professional trailers.

The idea this replaces: the existing anomaly detector fits on a single
trailer's own scenes, so it can only answer "which scene is unusual *within
this trailer*". A trailer whose pacing is uniformly wrong contains no internal
outlier and is reported as clean; a well-made trailer with one deliberate
quiet beat gets that beat flagged.

What this does instead: learn, per genre, the *shape* of a professionally cut
trailer -- how shot length, energy, motion and tempo move across the running
time -- from a corpus of real trailers of that genre. A new trailer is then
measured against its genre's shape, so "too slow here" means slow relative to
what the genre actually does, not relative to itself.

No manual labelling is involved. The supervision is the corpus: these are
released, professionally edited trailers, so their aggregate shape defines the
target. That also means the genre conventions currently hand-written in
cinematic_recommendation_engine.py (Horror holds suspense, Comedy pauses for
timing) stop being typed rules -- they emerge as measured facts, or they do
not appear at all, which is itself an honest finding.

The stored norm is plain JSON on purpose: every number can be inspected,
plotted, and defended, which matters more for a dissertation than a model
whose behaviour can only be demonstrated empirically.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# Curve dimensions sampled across normalised running time.
#
# The first five are pacing/energy, read from final_system_output.csv. They
# identify Action well but cannot tell Horror, Romance and Comedy apart --
# measured at chance in validate_genre_norms.py, because all three can be
# slow and moderate-energy.
#
# The last four are colour grading, read from colour_features.csv (written by
# scripts/extract_colour_features.py). They were added precisely to close that
# gap: horror grades dark and desaturated, romance warm, comedy bright.
STRUCTURE_DIMS = ("shot_duration", "ei", "audio_energy", "motion", "tempo_bpm")
COLOUR_CURVE_DIMS = ("brightness", "saturation", "warmth", "contrast")
CURVE_DIMS = STRUCTURE_DIMS + COLOUR_CURVE_DIMS
DEFAULT_BINS = 20
# A norm is only meaningful once enough trailers agree on a shape. Below this,
# per-bin spread is dominated by which particular films happened to be picked.
MIN_TRAILERS_FOR_NORM = 8


def parse_timeframe(text: str) -> tuple[float, float]:
    """'00:05.34-00:10.01' -> (5.34, 10.01) seconds."""
    try:
        left, right = str(text).split("-")

        def to_sec(t: str) -> float:
            total = 0.0
            for part in t.strip().split(":"):
                total = total * 60 + float(part)
            return total

        return to_sec(left), to_sec(right)
    except Exception:
        return 0.0, 0.0


def trailer_profile(final_csv: Path, bins: int = DEFAULT_BINS) -> dict[str, np.ndarray] | None:
    """Resample one trailer onto a fixed number of normalised-time bins.

    Trailers differ in length and shot count, so raw per-scene arrays are not
    comparable across films. Sampling each dimension at the midpoint of every
    bin puts every trailer on the same axis, which is what makes averaging
    across a genre meaningful.
    """
    try:
        df = pd.read_csv(final_csv)
    except Exception:
        return None
    if df.empty or "time" not in df.columns:
        return None

    spans = [parse_timeframe(t) for t in df["time"]]
    starts = np.array([s for s, _ in spans], dtype=float)
    ends = np.array([e for _, e in spans], dtype=float)
    total = float(ends.max()) if len(ends) else 0.0
    if total <= 0:
        return None

    durations = np.maximum(ends - starts, 1e-3)
    series = {
        "shot_duration": durations,
        "ei": pd.to_numeric(df.get("EI"), errors="coerce").to_numpy(dtype=float),
        "audio_energy": pd.to_numeric(df.get("A"), errors="coerce").to_numpy(dtype=float),
        "motion": pd.to_numeric(df.get("M"), errors="coerce").to_numpy(dtype=float),
        "tempo_bpm": pd.to_numeric(df.get("tempo_bpm"), errors="coerce").to_numpy(dtype=float),
    }

    # Colour lives in a sibling file because it is measured from the saved
    # frames, not from the analysis CSV. A trailer processed before colour
    # extraction existed simply has flat zeros here rather than failing --
    # but a norm must never be built from a mix of measured and zero-filled
    # colour, so build_norm() drops such trailers instead of averaging them in.
    colour_path = final_csv.parent / "colour_features.csv"
    if colour_path.exists():
        try:
            cdf = pd.read_csv(colour_path)
            for dim in COLOUR_CURVE_DIMS:
                series[dim] = pd.to_numeric(cdf.get(dim), errors="coerce").to_numpy(dtype=float)
        except Exception:
            pass
    for dim in COLOUR_CURVE_DIMS:
        if dim not in series or series[dim] is None or len(series[dim]) != len(df):
            series[dim] = np.zeros(len(df), dtype=float)

    # Sample the scene that is on screen at each bin midpoint (step-function
    # sampling): a trailer is a sequence of held shots, not a continuous
    # signal, so interpolating between scenes would invent values.
    mids = (np.arange(bins) + 0.5) / bins * total
    idxs = np.searchsorted(ends, mids, side="left")
    idxs = np.clip(idxs, 0, len(df) - 1)

    profile: dict[str, np.ndarray] = {}
    for dim, values in series.items():
        if values is None or len(values) != len(df):
            return None
        vals = np.nan_to_num(values, nan=0.0)
        profile[dim] = vals[idxs]

    energy = np.nan_to_num(series["ei"], nan=0.0)
    positions = (starts + ends) / 2 / total
    profile["_scalar"] = np.array([
        total,
        float(positions[int(np.argmax(energy))]) if len(energy) else 0.5,   # climax position
        float(np.polyfit(positions, energy, 1)[0]) if len(energy) > 2 else 0.0,  # escalation slope
        float(len(df)),                                                      # shot count
    ])
    # Flag so callers can tell a genuinely dark trailer from one whose colour
    # was never measured — both look like low brightness otherwise.
    profile["_has_colour"] = np.array([1.0 if colour_path.exists() else 0.0])
    return profile


def profile_from_scene_rows(
    scene_rows: list[dict[str, Any]],
    colour_series: dict[str, list[float]] | None = None,
    bins: int = DEFAULT_BINS,
) -> dict[str, np.ndarray] | None:
    """Same measurement as trailer_profile(), but from scenes already in memory.

    The live API receives scene data as JSON, not as a file on disk, so the
    engine cannot re-read a CSV. This builds the identical profile shape from
    the parsed scene rows, which keeps live requests and offline corpus builds
    measuring the same thing -- if these two drifted apart, a trailer would be
    judged against a norm built by different rules.
    """
    if not scene_rows:
        return None

    starts, ends, durations = [], [], []
    ei, audio, motion, tempo = [], [], [], []
    for row in scene_rows:
        s, e = parse_timeframe(row.get("timeframe", ""))
        ev = row["evidence"]
        starts.append(s)
        ends.append(e)
        durations.append(max(e - s, 1e-3) if e > s else max(getattr(ev, "shot_duration", 1.0), 1e-3))
        ei.append(getattr(ev, "ei", 0.0))
        audio.append(getattr(ev, "audio_energy", 0.0))
        motion.append(getattr(ev, "motion", 0.0))
        tempo.append(getattr(ev, "tempo_bpm", 0.0))

    starts_a, ends_a = np.array(starts, dtype=float), np.array(ends, dtype=float)
    total = float(ends_a.max()) if len(ends_a) and ends_a.max() > 0 else float(sum(durations))
    if total <= 0:
        return None

    series: dict[str, np.ndarray] = {
        "shot_duration": np.array(durations, dtype=float),
        "ei": np.array(ei, dtype=float),
        "audio_energy": np.array(audio, dtype=float),
        "motion": np.array(motion, dtype=float),
        "tempo_bpm": np.array(tempo, dtype=float),
    }
    has_colour = False
    if colour_series:
        ok = all(
            dim in colour_series and len(colour_series[dim]) == len(scene_rows)
            for dim in COLOUR_CURVE_DIMS
        )
        if ok:
            has_colour = True
            for dim in COLOUR_CURVE_DIMS:
                series[dim] = np.array(colour_series[dim], dtype=float)
    for dim in COLOUR_CURVE_DIMS:
        series.setdefault(dim, np.zeros(len(scene_rows), dtype=float))

    mids = (np.arange(bins) + 0.5) / bins * total
    idxs = np.clip(np.searchsorted(ends_a, mids, side="left"), 0, len(scene_rows) - 1)

    profile = {dim: np.nan_to_num(vals, nan=0.0)[idxs] for dim, vals in series.items()}
    energy = np.nan_to_num(series["ei"], nan=0.0)
    positions = (starts_a + ends_a) / 2 / total
    profile["_scalar"] = np.array([
        total,
        float(positions[int(np.argmax(energy))]) if len(energy) else 0.5,
        float(np.polyfit(positions, energy, 1)[0]) if len(energy) > 2 else 0.0,
        float(len(scene_rows)),
    ])
    profile["_has_colour"] = np.array([1.0 if has_colour else 0.0])
    return profile


@dataclass
class GenreNorm:
    genre: str
    n_trailers: int
    bins: int
    curves: dict[str, dict[str, list[float]]] = field(default_factory=dict)
    scalars: dict[str, dict[str, float]] = field(default_factory=dict)
    films: list[str] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        return {
            "genre": self.genre, "n_trailers": self.n_trailers, "bins": self.bins,
            "curves": self.curves, "scalars": self.scalars, "films": self.films,
            "reliable": self.n_trailers >= MIN_TRAILERS_FOR_NORM,
            "min_trailers_for_norm": MIN_TRAILERS_FOR_NORM,
        }

    @staticmethod
    def from_json(payload: dict[str, Any]) -> "GenreNorm":
        return GenreNorm(
            genre=payload["genre"], n_trailers=payload["n_trailers"], bins=payload["bins"],
            curves=payload["curves"], scalars=payload["scalars"], films=payload.get("films", []),
        )

    @property
    def reliable(self) -> bool:
        return self.n_trailers >= MIN_TRAILERS_FOR_NORM


def build_norm(genre: str, final_csvs: list[Path], films: list[str], bins: int = DEFAULT_BINS) -> GenreNorm | None:
    """THE TRAINING STEP. Learn what one genre's trailers typically look like.

    Plain English: take 25 real Action trailers, line them all up on the same
    timeline, and for each point on that timeline work out the average value
    and how much real trailers vary around it. The result is a description of
    "a typical Action trailer" that a new trailer can be compared against.

    This is a trained model in the real sense -- every number below is
    estimated from data, none is written by hand -- it is just a simple kind
    (per-position density estimation) rather than a neural network. With only
    25 examples per genre, a simple model is the correct choice: a deep model
    would memorise these particular films instead of learning the genre.
    """
    # Convert each trailer into a comparable, fixed-length profile. Any
    # trailer whose CSV is unreadable is skipped rather than faked.
    profiles, used = [], []
    skipped_no_colour = 0
    for csv_path, film in zip(final_csvs, films):
        prof = trailer_profile(csv_path, bins)
        if prof is None:
            continue
        # A trailer with no measured colour would contribute zeros and drag
        # the genre's colour average toward black, inventing a difference
        # that does not exist. Leave it out rather than corrupt the norm.
        if float(prof["_has_colour"][0]) < 1.0:
            skipped_no_colour += 1
            continue
        profiles.append(prof)
        used.append(film)
    if skipped_no_colour:
        print(f"    (skipped {skipped_no_colour} trailer(s) with no colour data)")
    if not profiles:
        return None

    norm = GenreNorm(genre=genre, n_trailers=len(profiles), bins=bins, films=used)

    # For each measurement, stack all the trailers into one grid --
    # rows = trailers, columns = points in time -- then average down each
    # column. Column 3's mean is "what real trailers of this genre are
    # typically doing 15% of the way in".
    for dim in CURVE_DIMS:
        stack = np.vstack([p[dim] for p in profiles])
        norm.curves[dim] = {
            "mean": np.mean(stack, axis=0).round(5).tolist(),
            # Floor the spread: a bin where the corpus happens to agree almost
            # exactly would otherwise divide by ~0 and turn a trivial
            # difference into an enormous z-score.
            "std": np.maximum(np.std(stack, axis=0), 1e-3).round(5).tolist(),
        }

    scal = np.vstack([p["_scalar"] for p in profiles])
    for i, name in enumerate(("total_duration", "climax_position", "escalation_gradient", "shot_count")):
        norm.scalars[name] = {
            "mean": float(np.mean(scal[:, i]).round(5)),
            "std": float(max(np.std(scal[:, i]), 1e-3).__round__(5)),
        }
    return norm


@dataclass
class Deviation:
    dimension: str
    bin_index: int
    start_time: float
    end_time: float
    observed: float
    expected: float
    expected_std: float
    z: float

    @property
    def direction(self) -> str:
        return "above" if self.z > 0 else "below"


def score_against_norm(
    final_csv: Path, norm: GenreNorm, z_threshold: float = 2.0
) -> tuple[list[Deviation], dict[str, Any]]:
    """Measure one trailer (read from its CSV) against its genre norm."""
    profile = trailer_profile(final_csv, norm.bins)
    if profile is None:
        return [], {}
    return score_profile(profile, norm, z_threshold)


def score_profile(
    profile: dict[str, np.ndarray], norm: GenreNorm, z_threshold: float = 2.0
) -> tuple[list[Deviation], dict[str, Any]]:
    """Measure an already-built profile against its genre norm.

    Returns deviations exceeding `z_threshold`, each carrying the real
    timeframe in the trailer where it occurs, plus the scalar comparisons.

    Colour dimensions are skipped when the trailer has no measured colour --
    otherwise its zero-filled colour would read as "impossibly dark" and
    produce a page of confident, entirely fictional findings.
    """
    if profile is None:
        return [], {}
    has_colour = float(profile.get("_has_colour", np.array([0.0]))[0]) >= 1.0
    dims = CURVE_DIMS if has_colour else STRUCTURE_DIMS

    # Each bin covers this many real seconds, which is how a deviation gets
    # turned back into a timestamp an editor can actually jump to.
    total = float(profile["_scalar"][0])
    bin_sec = total / norm.bins
    deviations: list[Deviation] = []

    for dim in dims:
        if dim not in norm.curves:
            continue
        mean = np.array(norm.curves[dim]["mean"], dtype=float)
        std = np.array(norm.curves[dim]["std"], dtype=float)
        observed = profile[dim]

        # The z-score: how many "typical spreads" away from the genre average
        # this trailer sits at each moment. Dividing by std is what makes the
        # comparison fair -- if real trailers vary wildly at this point then a
        # big difference is unremarkable, but if they all agree closely then
        # even a small difference is meaningful.
        z = (observed - mean) / std

        # Only report a deviation once it passes the sensitivity threshold
        # (default 2 spreads). This is the one tunable dial in the method,
        # and it is deliberately explicit rather than buried.
        for i, zi in enumerate(z):
            if abs(zi) >= z_threshold:
                deviations.append(Deviation(
                    dimension=dim, bin_index=i,
                    start_time=round(i * bin_sec, 2), end_time=round((i + 1) * bin_sec, 2),
                    observed=round(float(observed[i]), 4),
                    expected=round(float(mean[i]), 4), expected_std=round(float(std[i]), 4),
                    z=round(float(zi), 2),
                ))

    scalar_report: dict[str, Any] = {}
    obs_scalars = {
        "total_duration": profile["_scalar"][0], "climax_position": profile["_scalar"][1],
        "escalation_gradient": profile["_scalar"][2], "shot_count": profile["_scalar"][3],
    }
    for name, obs in obs_scalars.items():
        ref = norm.scalars.get(name)
        if not ref:
            continue
        z = (float(obs) - ref["mean"]) / max(ref["std"], 1e-3)
        scalar_report[name] = {
            "observed": round(float(obs), 4), "expected": round(ref["mean"], 4),
            "expected_std": round(ref["std"], 4), "z": round(float(z), 2),
        }

    deviations = _merge_adjacent(deviations)
    deviations.sort(key=lambda d: abs(d.z), reverse=True)
    return deviations, scalar_report


def _merge_adjacent(deviations: list[Deviation]) -> list[Deviation]:
    """Collapse consecutive bins that flag the same dimension the same way.

    A single held shot spanning two normalised bins previously surfaced as two
    separate findings with identical measurements and adjacent timeframes --
    the same note twice. Merging reports it once, over the full stretch it
    actually covers, which is also the more honest timeframe: the problem is
    the run, not one arbitrary slice of it.

    The merged deviation keeps the peak bin's numbers, so the reported z-score
    and observed value stay real measurements rather than averages of a span.
    """
    by_dim: dict[str, list[Deviation]] = {}
    for dev in deviations:
        by_dim.setdefault(dev.dimension, []).append(dev)

    merged: list[Deviation] = []
    for devs in by_dim.values():
        devs.sort(key=lambda d: d.bin_index)
        run: list[Deviation] = []
        for dev in devs:
            contiguous = (
                run
                and dev.bin_index == run[-1].bin_index + 1
                and dev.direction == run[-1].direction
            )
            if contiguous:
                run.append(dev)
                continue
            if run:
                merged.append(_collapse_run(run))
            run = [dev]
        if run:
            merged.append(_collapse_run(run))
    return merged


def _collapse_run(run: list[Deviation]) -> Deviation:
    """One deviation covering a run of bins, carrying the peak bin's values."""
    if len(run) == 1:
        return run[0]
    peak = max(run, key=lambda d: abs(d.z))
    return Deviation(
        dimension=peak.dimension,
        bin_index=peak.bin_index,
        start_time=min(d.start_time for d in run),
        end_time=max(d.end_time for d in run),
        observed=peak.observed,
        expected=peak.expected,
        expected_std=peak.expected_std,
        z=peak.z,
    )


def load_norms(norms_dir: Path) -> dict[str, GenreNorm]:
    norms: dict[str, GenreNorm] = {}
    if not norms_dir.exists():
        return norms
    for path in norms_dir.glob("*.json"):
        try:
            norms[path.stem.title()] = GenreNorm.from_json(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            continue
    return norms
