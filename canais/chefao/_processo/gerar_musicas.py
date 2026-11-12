"""Gera faixas eletrônicas/chiptune originais (sem direitos de terceiros) para o fundo dos vídeos do Chefão.

150 BPM: 2 compassos = 3,2 s = intervalo entre as cenas dos erros. A faixa começa com meio compasso
de "pickup", então os tempos fortes caem em 0,8 + 1,6·k s → 7,2 / 10,4 / 13,6 / … (cortes de cena).
uso: python3 gerar_musicas.py <pasta_saida>
"""
import os, subprocess, sys
import numpy as np

SR = 44100
BPM = 150
BEAT = 60 / BPM
DUR = 40.0
N = int(SR * DUR)
PICKUP = 2 * BEAT  # meio compasso


def env(n, a=0.002, d=0.15):
    t = np.arange(n) / SR
    e = np.minimum(1, t / a) * np.exp(-t / d)
    return e


def kick(n=int(0.25 * SR)):
    t = np.arange(n) / SR
    f = 50 + 110 * np.exp(-t * 35)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)


def hat(rng, n=int(0.05 * SR)):
    x = rng.standard_normal(n)
    x = np.diff(np.concatenate([[0], x]))  # brilho
    return x * env(n, 0.0005, 0.012) * 0.35


def snare(rng, n=int(0.18 * SR)):
    t = np.arange(n) / SR
    return (rng.standard_normal(n) * 0.6 + np.sin(2 * np.pi * 190 * t) * 0.5) * np.exp(-t * 22)


def square(freq, n, duty=0.5):
    t = np.arange(n) / SR
    ph = (t * freq) % 1
    return np.where(ph < duty, 1.0, -1.0)


def saw(freq, n):
    t = np.arange(n) / SR
    return 2 * ((t * freq) % 1) - 1


def nota(m):
    return 440 * 2 ** ((m - 69) / 12)


def add(buf, x, t):
    i = int(t * SR)
    if i >= len(buf):
        return
    x = x[:len(buf) - i]
    buf[i:i + len(x)] += x


# (nota MIDI da raiz, 3 = menor / 4 = maior)
PROGS = {
    "a": [(57, 3), (53, 4), (48, 4), (55, 4)],   # Am F C G
    "d": [(50, 3), (46, 4), (53, 4), (48, 4)],   # Dm Bb F C
    "e": [(52, 3), (48, 4), (55, 4), (50, 4)],   # Em C G D
    "f": [(53, 3), (49, 4), (56, 4), (51, 4)],   # Fm Db Ab Eb
    "c": [(48, 4), (45, 3), (41, 4), (43, 4)],   # C Am F G
    "g": [(55, 3), (51, 4), (58, 4), (53, 4)],   # Gm Eb Bb F
}


def faixa(nome, raiz, estilo, seed):
    rng = np.random.default_rng(seed)
    mix = np.zeros(N)
    prog = PROGS[raiz]
    beats = int((DUR - PICKUP) / BEAT) + 1
    # pickup: rufada de caixa crescente
    for k in range(4):
        add(mix, snare(rng) * (0.25 + 0.15 * k), k * BEAT / 2)
    for b in range(beats):
        t = PICKUP + b * BEAT
        bar = b // 4
        pos = b % 4
        intro = bar < 2
        acorde, terc = prog[bar % 4]
        triade = [acorde, acorde + terc, acorde + 7]
        add(mix, kick() * 0.9, t)
        if not intro:
            if pos in (1, 3):
                add(mix, snare(rng) * 0.45, t)
            for h in (0.5,) if estilo == "chip" else (0.5, 0.25, 0.75):
                add(mix, hat(rng), t + h * BEAT)
        # baixo em colcheias (off-beat no estilo "house")
        for e in (0, 0.5):
            if estilo == "house" and e == 0:
                continue
            n = int(BEAT / 2 * SR)
            f = nota(acorde - 12)
            x = (square(f, n, 0.5) * 0.5 + saw(f, n) * 0.5) * env(n, 0.003, 0.12) * 0.32
            add(mix, x, t + e * BEAT)
        # arpejo (chiptune) em semicolcheias, a partir do 3º compasso
        if not intro:
            for s in range(4):
                m = triade[(b * 4 + s) % 3] + 12 + (12 if (bar % 8) >= 4 and estilo != "house" else 0)
                n = int(BEAT / 4 * SR)
                duty = 0.25 if estilo == "chip" else 0.5
                add(mix, square(nota(m), n, duty) * env(n, 0.002, 0.08) * 0.12, t + s * BEAT / 4)
        # pad no 1º tempo de cada compasso
        if pos == 0:
            n = int(4 * BEAT * SR)
            x = sum(saw(nota(m) * (1 + d), n) for m in triade for d in (-0.003, 0.003))
            x = x * np.minimum(1, np.arange(n) / (0.3 * SR)) * np.exp(-np.arange(n) / SR / 3) * 0.035
            add(mix, x, t)
    # leve compressão + normalização
    mix = np.tanh(mix * 1.4)
    mix /= np.max(np.abs(mix)) + 1e-9
    mix *= 0.89
    est = np.stack([mix, np.roll(mix, int(0.008 * SR)) * 0.9 + mix * 0.1], axis=1)
    raw = (est * 32767).astype("<i2").tobytes()
    out = os.path.join(sys.argv[1], nome)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-af", "highpass=f=30,lowpass=f=15000", "-b:a", "192k", out], input=raw, check=True)
    print(out)


if __name__ == "__main__":
    os.makedirs(sys.argv[1], exist_ok=True)
    for i, (r, e) in enumerate([("a", "chip"), ("d", "electro"), ("e", "house"), ("f", "chip"), ("c", "electro"), ("g", "house")]):
        faixa(f"chefao_{i + 1:02d}_{e}_{BPM}bpm_sync.mp3", r, e, 100 + i)
