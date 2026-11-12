"""audio_mix.py episodio.json som.json saida.wav
som.json: {"music":[{"file":"m_tapis","at":0,"from":0,"to":78.4,"gain":-14,"fadein":1,"fadeout":3}],
           "beds":[{"file":"rain_heavy","key":"rain","gain":-12}, {"file":"city_morning","beats":[1,18],"gain":-20}],
           "sfx":[{"file":"thunder_close","at":11.9,"gain":-6}], "thunder":{"files":[...],"gain":-7,"delay":0.25}}
Leitos ("beds") seguem a intensidade da chuva de cada cena (env.rain) quando key="rain"."""
import json, subprocess, sys, numpy as np
SR = 48000
ep = json.load(open(sys.argv[1])); spec = json.load(open(sys.argv[2])); out = sys.argv[3]
DUR = ep["dur"]; N = int(DUR * SR)
A = "assets/audio/"
def load(name):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", A + name + ".mp3", "-f", "s16le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32).reshape(-1, 2) / 32768
db = lambda g: 10 ** (g / 20)
mix = np.zeros((N, 2), np.float32)
def place(x, at, gain, fadein=0.02, fadeout=0.05, length=None):
    s = int(at * SR)
    if length is not None: x = x[:int(length * SR)]
    if s >= N: return
    x = x[:N - s].copy()
    fi = int(fadein * SR); fo = int(fadeout * SR)
    if fi > 0: x[:fi] *= np.linspace(0, 1, min(fi, len(x)))[:, None][:len(x[:fi])]
    if fo > 0 and len(x) > fo: x[-fo:] *= np.linspace(1, 0, fo)[:, None]
    mix[s:s + len(x)] += x * db(gain)
# envelope de chuva por amostra (a partir das cenas)
def ease(u): return 0.5 - 0.5 * np.cos(np.pi * np.clip(u, 0, 1))
t = np.arange(N) / SR
rain = np.zeros(N, np.float32); indoor = np.zeros(N, np.float32); sunny = np.zeros(N, np.float32)
for i, b in enumerate(ep["beats"]):
    a, z = b["t"]; m = (t >= a) & (t < z); u = (t[m] - a) / (z - a)
    r0 = b["env"].get("rain", 0); r1 = (b.get("env2") or {}).get("rain", r0)
    rain[m] = r0 + (r1 - r0) * ease(u)
    if b.get("fx", {}).get("overlay") in ("phone", "board"): rain[m] *= 0.75
    if "fill" in b.get("fx", {}): indoor[m] = 1
    if b["env"].get("storm", 0) < 0.3 and r0 == 0: sunny[m] = 1
def smooth(x, sec=0.4):
    k = int(sec * SR); c = np.cumsum(np.concatenate([[0], x])); y = (c[k:] - c[:-k]) / k
    return np.concatenate([y, np.full(len(x) - len(y), y[-1])]).astype(np.float32)
rain = smooth(rain); indoor = smooth(indoor); sunny = smooth(sunny, 0.8)
for bd in spec.get("beds", []):
    x = load(bd["file"]); reps = int(np.ceil(N / len(x))) + 1; x = np.tile(x, (reps, 1))[:N]
    env = {"rain": rain, "sunny": sunny, "indoor": indoor}.get(bd.get("key"), np.ones(N, np.float32))
    if bd.get("key") == "rain": env = env * (1 - 0.6 * indoor)
    mix += x * env[:, None] * db(bd["gain"])
for m in spec.get("music", []):
    x = load(m["file"])[int(m.get("from", 0) * SR):]
    place(x, m["at"], m["gain"], m.get("fadein", 1), m.get("fadeout", 2), m["to"] - m["at"])
th = spec.get("thunder")
if th:
    k = 0
    for b in ep["beats"]:
        for f in b.get("fx", {}).get("flash", []):
            x = load(th["files"][k % len(th["files"])]); k += 1
            place(x, b["t"][0] + f + th.get("delay", 0.25), th["gain"], 0.01, 1.0, th.get("max", 6))
for s in spec.get("sfx", []):
    place(load(s["file"]), s["at"], s.get("gain", -8), s.get("fadein", 0.02), s.get("fadeout", 0.3), s.get("len"))
# limitador suave + fade final
mix *= np.minimum(1, (N - np.arange(N)) / (0.8 * SR))[:, None]
peak = np.max(np.abs(mix)); mix = np.tanh(mix / max(peak, 1e-6) * 1.4) * 0.9
pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ac", "2", "-ar", str(SR), "-i", "-", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", str(SR), out], input=pcm.tobytes(), check=True)
print("ok", out)
