import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple

try:
    # Prefer SciPy for filters and peak finding if available
    from scipy.signal import butter, filtfilt, find_peaks
    from scipy.interpolate import interp1d
    SCIPY_AVAILABLE = True
except Exception:
    SCIPY_AVAILABLE = False


def _nan_safe(x: np.ndarray) -> np.ndarray:
    """Replace non-finite values with nearest finite (forward/back fill)."""
    x = np.asarray(x, dtype=float)
    if np.all(np.isfinite(x)):
        return x
    s = pd.Series(x)
    s = s.fillna(method="ffill").fillna(method="bfill")
    x2 = s.to_numpy()
    # In case of all-nan series, fall back to zeros
    if not np.any(np.isfinite(x2)):
        x2 = np.zeros_like(x)
    return x2


def butter_lowpass_filter(x: np.ndarray, fs: float, cutoff: float = 10.0, order: int = 4) -> np.ndarray:
    """Low-pass filters a signal. If SciPy unavailable, returns input."""
    x = _nan_safe(x)
    if not SCIPY_AVAILABLE or fs <= 0 or cutoff >= fs / 2.0:
        return x
    b, a = butter(order, cutoff / (fs / 2.0), btype="low")
    try:
        return filtfilt(b, a, x, method="gust")
    except Exception:
        return x


def interpolate_to_fs(x: np.ndarray, fs_in: float, fs_out: float = 50.0, kind: str = "cubic") -> Tuple[np.ndarray, float]:
    """Upsample/interpolate a 1D signal to a target sampling rate.

    Returns (y, fs_out). If SciPy unavailable, falls back to linear with numpy.
    """
    x = _nan_safe(x)
    if fs_in <= 0 or fs_out <= 0:
        return x, fs_in

    t_in = np.arange(len(x)) / fs_in
    duration = t_in[-1] if len(t_in) else 0.0
    if duration <= 0:
        return x, fs_in
    n_out = int(round(duration * fs_out)) + 1
    if n_out < 2:
        return x, fs_in
    t_out = np.linspace(0, duration, n_out)

    if SCIPY_AVAILABLE:
        try:
            f = interp1d(t_in, x, kind=kind, bounds_error=False, fill_value=(x[0], x[-1]))
            y = f(t_out)
            return y, fs_out
        except Exception:
            pass

    # Fallback: numpy linear interpolation
    y = np.interp(t_out, t_in, x)
    return y, fs_out


def hjorth_params(x: np.ndarray) -> Tuple[float, float, float]:
    """Hjorth parameters: activity, mobility, complexity."""
    x = _nan_safe(x)
    if len(x) < 2:
        return 0.0, 0.0, 0.0
    dx = np.diff(x)
    var_x = np.var(x)
    var_dx = np.var(dx)
    if var_x == 0:
        return 0.0, 0.0, 0.0
    mobility = np.sqrt(var_dx / (var_x + 1e-12))
    ddx = np.diff(dx)
    var_ddx = np.var(ddx)
    mobility_dx = np.sqrt(var_ddx / (var_dx + 1e-12)) if var_dx > 0 else 0.0
    complexity = mobility_dx / (mobility + 1e-12) if mobility > 0 else 0.0
    return var_x, mobility, complexity


def petrosian_fd(x: np.ndarray) -> float:
    """Petrosian fractal dimension (PFD)."""
    x = _nan_safe(x)
    if len(x) < 2:
        return 0.0
    sgn = np.sign(np.diff(x))
    N_delta = np.sum(np.diff(sgn) != 0)
    n = len(x)
    if n == 0:
        return 0.0
    return np.log(n) / (np.log(n) + np.log(n / (n + 0.4 * N_delta)))


def spectral_centroid_bandwidth(x: np.ndarray, fs: float) -> Tuple[float, float, float]:
    """Compute spectral centroid, bandwidth, and log-energy of magnitude spectrum."""
    x = _nan_safe(x)
    if len(x) < 2 or fs <= 0:
        return 0.0, 0.0, 0.0
    # Detrend simple
    x_d = x - np.mean(x)
    n = len(x_d)
    # Use rfft for real signal
    X = np.fft.rfft(x_d)
    freqs = np.fft.rfftfreq(n, d=1.0 / fs)
    mag = np.abs(X)
    power = mag**2
    total = np.sum(power) + 1e-12
    centroid = float(np.sum(freqs * power) / total)
    bw = float(np.sqrt(np.sum(((freqs - centroid) ** 2) * power) / total))
    log_energy = float(np.log(total + 1e-12))
    return centroid, bw, log_energy


def bandpower(x: np.ndarray, fs: float, fmin: float, fmax: float) -> float:
    """Compute band power using FFT integration."""
    x = _nan_safe(x)
    if len(x) < 2 or fs <= 0:
        return 0.0
    X = np.fft.rfft(x - np.mean(x))
    freqs = np.fft.rfftfreq(len(x), d=1.0 / fs)
    mask = (freqs >= fmin) & (freqs < fmax)
    power = np.abs(X) ** 2
    return float(np.sum(power[mask]) / (len(x) ** 2))


def iqr(x: np.ndarray) -> float:
    x = np.asarray(x, dtype=float)
    if x.size == 0:
        return 0.0
    return float(np.nanpercentile(x, 75) - np.nanpercentile(x, 25))


def detect_peaks(signal: np.ndarray, fs: float, hr_hint: Optional[float] = None) -> np.ndarray:
    """Detect systolic peaks with a distance based on HR. Returns peak indices.

    Works with SciPy if available; otherwise a simple local-max fallback.
    """
    x = _nan_safe(signal)
    n = len(x)
    if n < 3:
        return np.array([], dtype=int)

    # Expected distance between peaks
    if hr_hint and hr_hint > 0:
        period = 60.0 / hr_hint
        min_dist = max(1, int(0.5 * period * fs))  # allow some variability
    else:
        # Assume HR in [45, 160] bpm
        min_dist = max(1, int(0.3 * fs))

    # Dynamic prominence based on robust amplitude
    amp = np.nanpercentile(x, 95) - np.nanpercentile(x, 5)
    prom = max(amp * 0.1, 1e-6)

    if SCIPY_AVAILABLE:
        try:
            peaks, _ = find_peaks(x, distance=min_dist, prominence=prom)
            return peaks.astype(int)
        except Exception:
            pass

    # Fallback: simple local maxima with distance pruning
    cand = np.where((x[1:-1] > x[:-2]) & (x[1:-1] >= x[2:]))[0] + 1
    if cand.size == 0:
        return np.array([], dtype=int)
    selected = [int(cand[0])]
    for c in cand[1:]:
        if c - selected[-1] >= min_dist and x[c] - x[selected[-1]] > 0:
            selected.append(int(c))
    return np.array(selected, dtype=int)


def _find_foot(x: np.ndarray, peak_idx: int, search_left: int) -> int:
    """Approximate foot (onset) as minimum in a window before peak."""
    left = max(0, peak_idx - search_left)
    if left >= peak_idx:
        return max(0, peak_idx - 1)
    seg = x[left:peak_idx]
    if seg.size == 0:
        return max(0, peak_idx - 1)
    return int(left + np.argmin(seg))


def _crossing_width(x: np.ndarray, baseline: float, level: float, fs: float) -> float:
    """Pulse width at a given level (absolute level), in seconds. Returns 0 if not found."""
    y = x - baseline
    thr = level - baseline
    above = y >= thr
    idx = np.where(above)[0]
    if idx.size == 0:
        return 0.0
    # continuous block around the peak assumed
    start = idx[0]
    end = idx[-1]
    return float((end - start) / fs)


def _beat_features(x: np.ndarray, fs: float, peak_idx: int, next_foot_idx: Optional[int]) -> Dict[str, float]:
    """Compute per-beat morphology features around a peak.

    Uses foot (onset) before peak and next foot (end). If next_foot_idx is None, uses end of signal.
    """
    n = len(x)
    search_left = int(0.5 * fs)  # 0.5 s search window for foot
    foot_idx = _find_foot(x, peak_idx, search_left)
    end_idx = next_foot_idx if next_foot_idx is not None else min(n - 1, peak_idx + search_left)
    if end_idx <= foot_idx:
        end_idx = min(n - 1, foot_idx + 1)

    seg = x[foot_idx:end_idx + 1]
    if seg.size < 2:
        return {k: np.nan for k in (
            "amp", "rise_time", "fall_time", "width50", "width75", "area",
            "max_rise_slope", "min_fall_slope", "slope_ratio", "t_to_peak_frac",
            "aix", "notch_time_frac", "pi", "period")}

    baseline = seg[0]
    # Local peak within segment for safety
    local_peak = np.argmax(seg)
    peak_val = seg[local_peak]
    amp = float(max(peak_val - baseline, 1e-12))

    # Rise/fall times
    t_peak = local_peak / fs
    t_total = max((len(seg) - 1) / fs, 1e-6)
    rise_time = t_peak
    fall_time = max(t_total - t_peak, 0.0)

    # Widths at 50% and 75% of amplitude above baseline
    width50 = _crossing_width(seg, baseline, baseline + 0.5 * amp, fs)
    width75 = _crossing_width(seg, baseline, baseline + 0.75 * amp, fs)

    # Area under curve above baseline
    area = float(np.trapz(np.maximum(seg - baseline, 0.0), dx=1.0 / fs))

    # Slopes (first difference)
    dseg = np.diff(seg) * fs
    max_rise_slope = float(np.max(dseg[:max(1, local_peak)])) if local_peak > 0 else 0.0
    min_fall_slope = float(np.min(dseg[local_peak:])) if local_peak < len(dseg) else 0.0
    slope_ratio = float(max_rise_slope / (abs(min_fall_slope) + 1e-12))

    t_to_peak_frac = float(t_peak / t_total) if t_total > 0 else np.nan

    # Augmentation index approximation via second peak/inflection after systolic peak
    # Use second local maximum within the falling limb if present
    aix = np.nan
    notch_time_frac = np.nan
    if local_peak + 2 < len(seg):
        # Simple search for a secondary bump
        post = seg[local_peak:]
        # Find next local maximum excluding the main peak
        locs = np.where((post[1:-1] > post[:-2]) & (post[1:-1] >= post[2:]))[0] + 1
        if locs.size > 1:
            sec_peak_val = float(post[locs[1]])
            aix = float((sec_peak_val - baseline) / amp)
            notch_time_frac = float(locs[1] / len(post))

    # Perfusion Index (approx): AC/DC
    pi = float(amp / (abs(baseline) + 1e-12))

    return {
        "amp": float(amp),
        "rise_time": float(rise_time),
        "fall_time": float(fall_time),
        "width50": float(width50),
        "width75": float(width75),
        "area": float(area),
        "max_rise_slope": float(max_rise_slope),
        "min_fall_slope": float(min_fall_slope),
        "slope_ratio": float(slope_ratio),
        "t_to_peak_frac": float(t_to_peak_frac),
        "aix": float(aix) if np.isfinite(aix) else np.nan,
        "notch_time_frac": float(notch_time_frac) if np.isfinite(notch_time_frac) else np.nan,
        "pi": float(pi),
        "period": float(t_total),
    }


def aggregate_beats(beat_list: List[Dict[str, float]]) -> Dict[str, float]:
    """Aggregate per-beat feature dicts to window-level statistics."""
    if not beat_list:
        return {}
    keys = sorted(beat_list[0].keys())
    out: Dict[str, float] = {}
    for k in keys:
        vals = np.array([b.get(k, np.nan) for b in beat_list], dtype=float)
        out[f"{k}_mean"] = float(np.nanmean(vals))
        out[f"{k}_std"] = float(np.nanstd(vals))
        out[f"{k}_iqr"] = float(iqr(vals))
        out[f"{k}_median"] = float(np.nanmedian(vals))
    out["n_beats"] = len(beat_list)
    return out


def window_features(signal: np.ndarray, fs: float, hr_hint: Optional[float] = None) -> Dict[str, float]:
    """Compute robust window-level features from a PPG-like signal.

    Steps:
      - Denoise (low-pass ~10 Hz)
      - Peak detection guided by HR if provided
      - Per-beat morphology features + aggregation
      - Global Hjorth, fractal, spectral features, bandpowers
    """
    if signal is None or len(signal) < 8 or fs <= 0:
        return {}

    x = _nan_safe(signal)
    x_f = butter_lowpass_filter(x, fs, cutoff=10.0, order=4)

    # Beat detection
    peaks = detect_peaks(x_f, fs, hr_hint=hr_hint)

    # Build per-beat features
    beat_feats: List[Dict[str, float]] = []
    if peaks.size > 0:
        # Approximate next foot via minimum between peaks
        for i, p in enumerate(peaks):
            next_foot = None
            if i + 1 < len(peaks):
                # Search min between current peak and next peak as beat end
                start = p
                stop = peaks[i + 1]
                if stop > start + 1:
                    next_foot = int(start + np.argmin(x_f[start:stop + 1]))
            bf = _beat_features(x_f, fs, int(p), next_foot)
            beat_feats.append(bf)

    agg = aggregate_beats(beat_feats)

    # Global descriptors
    act, mob, comp = hjorth_params(x_f)
    centroid, bw, log_e = spectral_centroid_bandwidth(x_f, fs)
    pfd = petrosian_fd(x_f)

    # Bandpowers in plausible pulse band (0.5–8 Hz). Handle low-fs by guards.
    bp_low = bandpower(x_f, fs, 0.5, min(1.5, fs / 2.0 - 1e-3))
    bp_mid = bandpower(x_f, fs, 1.5, min(3.0, fs / 2.0 - 1e-3))
    bp_high = bandpower(x_f, fs, 3.0, min(8.0, fs / 2.0 - 1e-3))
    total_power = bp_low + bp_mid + bp_high + 1e-12
    sqi_power_ratio = (bp_low + bp_mid) / total_power

    # dPPG slopes overall
    dx = np.diff(x_f) * fs
    d2x = np.diff(dx) * fs if dx.size > 1 else np.array([0.0])

    out = {
        **{f"morph_{k}": v for k, v in agg.items()},
        "hjorth_activity": float(act),
        "hjorth_mobility": float(mob),
        "hjorth_complexity": float(comp),
        "spec_centroid": float(centroid),
        "spec_bandwidth": float(bw),
        "spec_log_energy": float(log_e),
        "bp_0p5_1p5": float(bp_low),
        "bp_1p5_3": float(bp_mid),
        "bp_3_8": float(bp_high),
        "sqi_power_ratio": float(sqi_power_ratio),
        "dppg_max": float(np.nanmax(dx) if dx.size else 0.0),
        "dppg_min": float(np.nanmin(dx) if dx.size else 0.0),
        "dppg_mean": float(np.nanmean(dx) if dx.size else 0.0),
        "d2ppg_max": float(np.nanmax(d2x) if d2x.size else 0.0),
        "d2ppg_min": float(np.nanmin(d2x) if d2x.size else 0.0),
        "pfd": float(pfd),
    }

    return out


def extract_row_features(row: pd.Series,
                         ir_prefix: str = "ir_",
                         fs_raw: float = 5.63,
                         fs_target: float = 50.0) -> Dict[str, float]:
    """Extract features from a single row with columns like ir_0..ir_N.

    If a column `heartRate` exists, it is used as a hint for beat spacing.
    """
    ir_cols = [c for c in row.index if c.startswith(ir_prefix)]
    if not ir_cols:
        return {}
    x = row[ir_cols].to_numpy(dtype=float)
    x = _nan_safe(x)
    # Interpolate to target fs and filter
    y, fs_eff = interpolate_to_fs(x, fs_raw, fs_out=fs_target)
    feats = window_features(y, fs_eff, hr_hint=float(row.get("heartRate", np.nan)))
    # Attach simple stats of raw window too (redundant but helps robustness)
    base = {
        "raw_mean": float(np.nanmean(x)),
        "raw_std": float(np.nanstd(x)),
        "raw_skew": float(pd.Series(x).skew() if len(x) > 2 else 0.0),
        "raw_kurt": float(pd.Series(x).kurt() if len(x) > 3 else 0.0),
        "fs_eff": float(fs_eff),
    }
    return {**base, **feats}


def extract_features_df(df: pd.DataFrame,
                        ir_prefix: str = "ir_",
                        fs_raw: float = 5.63,
                        fs_target: float = 50.0,
                        extra_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """Vectorize feature extraction for a DataFrame of windows.

    - Looks for columns matching `ir_prefix` (e.g., ir_0..ir_N)
    - Returns a DataFrame of engineered features, optionally including `extra_cols`.
    """
    feats: List[Dict[str, float]] = []
    for _, row in df.iterrows():
        f = extract_row_features(row, ir_prefix=ir_prefix, fs_raw=fs_raw, fs_target=fs_target)
        if extra_cols:
            for c in extra_cols:
                f[c] = row.get(c, np.nan)
        feats.append(f)
    out = pd.DataFrame(feats)
    return out


def from_csv_to_features(csv_path: str,
                         ir_prefix: str = "ir_",
                         fs_raw: float = 5.63,
                         fs_target: float = 50.0,
                         include_demo: bool = True) -> pd.DataFrame:
    """Convenience: read a CSV like bp_dataset_upsampled_50Hz_filtered.csv and return features.

    If present, carries over demographic columns and targets for later modeling:
      - Demographics: spo2, heartRate, userAge, userGender, userHeight, userWeight, userBmi
      - Targets: systolic_BP, diastolic_BP
    """
    df = pd.read_csv(csv_path)
    demo_cols = [
        "spo2", "heartRate", "userAge", "userGender", "userHeight", "userWeight", "userBmi"
    ] if include_demo else []
    target_cols = [c for c in ("systolic_BP", "diastolic_BP") if c in df.columns]

    feats = extract_features_df(df, ir_prefix=ir_prefix, fs_raw=fs_raw, fs_target=fs_target, extra_cols=demo_cols)
    # Optionally attach targets for training use
    for t in target_cols:
        feats[t] = df[t].values
    return feats


if __name__ == "__main__":
    # Example CLI usage (safe no-op if file not present)
    import os
    default_csv = "bp_dataset_upsampled_50Hz_filtered.csv"
    if os.path.exists(default_csv):
        out_df = from_csv_to_features(default_csv)
        out_path = "ppg_features_extracted_advanced.csv"
        out_df.to_csv(out_path, index=False)
        print(f"Saved features -> {out_path} ({len(out_df)} rows, {out_df.shape[1]} cols)")
    else:
        print("No default CSV found. Import this module and call from_csv_to_features().")
