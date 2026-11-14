"""Synthesize a light, upbeat corporate background track + whooshes (royalty-free, generated)."""
import numpy as np, sys, json, wave

SR = 44100
dur = float(sys.argv[1])
whoosh_times = json.loads(sys.argv[2]) if len(sys.argv) > 2 else []
out = sys.argv[3] if len(sys.argv) > 3 else "music.wav"
N = int(SR * dur)
t = np.arange(N) / SR
COLD = len(sys.argv) > 4 and sys.argv[4] == "cold"
bpm = 126 if COLD else 104
beat = 60 / bpm
mix = np.zeros(N)

def note(f):
    return 440 * 2 ** ((f - 69) / 12)

# I - V - vi - IV in C major (midi)
chords = [[48, 55, 60, 64, 67], [43, 50, 55, 59, 62], [45, 52, 57, 60, 64], [41, 48, 53, 57, 60]]
if COLD:
    chords = [[45, 52, 57, 60, 64], [41, 48, 53, 57, 60], [48, 55, 60, 64, 67], [43, 50, 55, 59, 62]]
bar = beat * 4

def env_adsr(n, a, r):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    na = min(na, n); nr = min(nr, n - na)
    e[:na] = np.linspace(0, 1, na)
    if nr > 0:
        e[-nr:] = np.linspace(1, 0, nr)
    return e

# pads
nb = int(np.ceil(dur / bar))
for b in range(nb):
    ch = chords[b % 4]
    s = int(b * bar * SR); n = min(int(bar * SR) + int(0.3 * SR), N - s)
    if n <= 0: break
    tt = np.arange(n) / SR
    e = env_adsr(n, 0.4, 0.6)
    sig = sum(np.sin(2 * np.pi * note(m) * tt) + 0.3 * np.sin(2 * np.pi * note(m) * 2.003 * tt) for m in ch[1:])
    mix[s:s + n] += 0.035 * sig * e
    # bass on beats 1 & 3
    for k in (0, 2):
        bs = s + int(k * beat * SR); bn = min(int(beat * 1.8 * SR), N - bs)
        if bn <= 0: continue
        bt = np.arange(bn) / SR
        mix[bs:bs + bn] += 0.16 * np.sin(2 * np.pi * note(ch[0] - 12) * bt) * np.exp(-bt * 2.5)

# pluck arpeggio on 8th notes
step = beat / 2
nsteps = int(dur / step)
pattern = [0, 2, 3, 4, 3, 2, 4, 3]
for i in range(nsteps):
    ch = chords[int(i * step / bar) % 4]
    m = ch[1:][pattern[i % 8] % 4] + 12
    s = int(i * step * SR); n = min(int(0.5 * SR), N - s)
    if n <= 0: break
    tt = np.arange(n) / SR
    sig = np.sin(2 * np.pi * note(m) * tt) * np.exp(-tt * 9) + 0.25 * np.sin(4 * np.pi * note(m) * tt) * np.exp(-tt * 14)
    mix[s:s + n] += 0.06 * sig

# soft kick + hat
for i in range(int(dur / beat)):
    s = int(i * beat * SR); n = min(int(0.25 * SR), N - s)
    tt = np.arange(n) / SR
    f = 110 * np.exp(-tt * 25) + 45
    mix[s:s + n] += 0.22 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 14)
    hs = s + int(beat / 2 * SR); hn = min(int(0.05 * SR), N - hs)
    if hn > 0:
        noise = np.random.randn(hn)
        noise = np.diff(np.concatenate([[0], noise]))
        mix[hs:hs + hn] += 0.025 * noise * np.exp(-np.arange(hn) / SR * 80)

if COLD:
    for i in range(int(dur / beat)):
        s = int(i * beat * SR)
        if i % 2 == 1:  # clap
            n = min(int(0.18 * SR), N - s)
            if n > 0:
                nz = np.random.randn(n); nz = nz - np.convolve(nz, np.ones(6) / 6, mode="same")
                mix[s:s + n] += 0.10 * nz * np.exp(-np.arange(n) / SR * 22)
        for q in (1, 3):  # 16th hats
            hs = s + int(q * beat / 4 * SR); hn = min(int(0.03 * SR), N - hs)
            if hn > 0:
                nz = np.diff(np.concatenate([[0], np.random.randn(hn)]))
                mix[hs:hs + hn] += 0.018 * nz * np.exp(-np.arange(hn) / SR * 120)
        n = min(int(0.3 * SR), N - s)  # extra kick weight
        if n > 0:
            tt = np.arange(n) / SR; f = 90 * np.exp(-tt * 30) + 42
            mix[s:s + n] += 0.15 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 10)

# whooshes
for wt in whoosh_times:
    s = int((wt - 0.25) * SR); n = int(0.5 * SR)
    if s < 0 or s + n > N: continue
    noise = np.random.randn(n)
    # simple moving-average low-pass sweep
    k = np.convolve(noise, np.ones(12) / 12, mode="same")
    e = np.sin(np.linspace(0, np.pi, n)) ** 2
    mix[s:s + n] += 0.12 * k * e

# fade in/out, normalize
fi, fo = int(0.5 * SR), int(2.0 * SR)
mix[:fi] *= np.linspace(0, 1, fi)
mix[-fo:] *= np.linspace(1, 0, fo)
mix = mix / np.max(np.abs(mix)) * 0.85
st = np.stack([mix, np.roll(mix, 300)], axis=1)
data = (st * 32767).astype(np.int16)
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data.tobytes())
print("ok", out)
