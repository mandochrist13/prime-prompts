"""Alignement de la narration complète sur la voix de référence (DTW sur MFCC).
La narration n'est jamais découpée : on en déduit seulement l'heure de début de chaque fragment du storyboard."""
import json
import numpy as np, soundfile as sf, librosa
import storylib

def align(story, narration_wav, reference, out_json):
    P = storylib.pieces(story)
    g, sr = sf.read(narration_wav)
    if g.ndim > 1: g = g.mean(1)
    hop = sr // 100  # 10 ms
    ref, kb, pos = [], [], 0
    for key, _ in P:
        x, ksr = sf.read(reference[key]["file"])
        x = librosa.resample(x, orig_sr=ksr, target_sr=sr)
        gap = int(0.4 * sr)
        kb.append((pos, pos + len(x))); ref += [x, np.zeros(gap)]; pos += len(x) + gap
    ref = np.concatenate(ref)

    def feat(y):
        m = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20, hop_length=hop, n_fft=1024)[1:]
        m = (m - m.mean(1, keepdims=True)) / (m.std(1, keepdims=True) + 1e-6)
        e = librosa.feature.rms(y=y, hop_length=hop, frame_length=1024)[0]
        return np.vstack([m, ((e < 0.03 * e.max()).astype(float) * 4)[None]])

    _, wp = librosa.sequence.dtw(X=feat(ref), Y=feat(g), metric="euclidean")
    wp = wp[::-1]
    e = librosa.feature.rms(y=g, hop_length=hop, frame_length=1024)[0]; sil = e < 0.03 * e.max()

    def map_t(fr):
        i = min(np.searchsorted(wp[:, 0], fr), len(wp) - 1); return wp[i, 1]

    def snap(fr, rad=25):  # cale sur le silence le plus proche
        for d in range(rad):
            for c in (fr - d, fr + d):
                if 0 <= c < len(sil) and sil[c]: return c
        return fr

    keys = [k for k, _ in P]; out = {}
    for k, key in enumerate(keys):
        out[key] = [snap(map_t(kb[k][0] // hop)) * hop / sr, snap(map_t(kb[k][1] // hop)) * hop / sr]
    for k in range(1, len(keys)):
        out[keys[k]][0] = max(out[keys[k]][0], out[keys[k - 1]][0] + 0.3)
    ev = np.where(~sil)[0]; out[keys[-1]][1] = (ev[-1] + 1) * hop / sr

    report = []
    for k, (key, text) in enumerate(P):
        nxt = out[keys[k + 1]][0] if k + 1 < len(keys) else out[key][1]
        span = nxt - out[key][0]; ratio = span / reference[key]["dur"]
        flag = "  <-- À VÉRIFIER" if (ratio > 1.6 and span - reference[key]["dur"] > 1.5) or ratio < 0.5 else ""
        report.append(f"{key:5s} début {out[key][0]:6.2f}s  durée {span:5.2f}s  (réf {reference[key]['dur']:4.2f}s){flag}  {text}")
    json.dump({"full": narration_wav, "len": len(g) / sr, "pieces": out}, open(out_json, "w"), indent=1)
    return "\n".join(report)
