"""Narração do Chefão gerada FALA POR FALA (10 arquivos curtos), conferida, TRATADA e montada nas cenas.

uso:
  python3 audio_falas.py checar <pasta_falas> narration.json [transcricoes.json]
      -> grava <pasta_falas>/qa.json; uma linha por fala: OK ou REFAZER (motivo).
         Além de duração/volume/texto, confere CONSISTÊNCIA DE VOZ entre as 10 falas
         (tom, timbre, ruído de fundo e brilho) — fala que "parece outra pessoa" sai REFAZER.
  python3 audio_falas.py tratar <pasta_falas> <pasta_tratadas> [perfil_voz.json]
      -> limpa e EQUALIZA as falas entre si: tira ruído, corta grave sujo, iguala a curva de
         frequências de todas as falas ao perfil de referência (voz brasileira aprovada),
         de-esser, compressão leve e mesmo volume (-18 LUFS) em todas. Grava tratamento.json.
  python3 audio_falas.py perfil <pasta_ref> perfil_voz.json
      -> mede a curva de frequências de uma narração APROVADA (o alvo da equalização).
  python3 audio_falas.py dividir narracao_inteira.wav <pasta_falas>
      -> corta a narração gerada numa chamada só (10 linhas no mesmo texto = mesma voz do início ao fim)
         em 01..10.wav, nas 9 maiores pausas.
  python3 audio_falas.py montar <pasta_tratadas> narration.json saida.wav
      -> narracao_sync.wav de 37 s, cada fala no início da sua cena, -14 LUFS sem "bombear".

Ordem: [dividir] -> checar -> (refazer só as reprovadas) -> tratar -> montar.
Dependências: ffmpeg, numpy, scipy, librosa, pyloudnorm, noisereduce
  (pip install librosa pyloudnorm noisereduce --break-system-packages).
"""
import json, os, re, subprocess, sys, unicodedata
from difflib import SequenceMatcher

SCENES = [0.0, 3.4, 7.2, 10.4, 13.6, 16.8, 20.0, 23.2, 26.4, 29.6, 33.0]
MAX_TEMPO = 1.15          # acima disso a aceleração soa mecânica: melhor regerar com speed maior
SIM_MIN = 0.70            # semelhança mínima roteiro x ouvido
SIL_DB = -45
SR = 44100
# consistência de voz (entre as falas do MESMO vídeo)
TOM_MAX = 0.25            # tom (F0 mediano) até ±25% da mediana do vídeo (fala 09 "desbloqueado" até +40%)
TOM_MAX_EXCL = 0.40
TIMBRE_MAX = 2.2          # distância de timbre (MFCC) até 2,2x a distância típica do vídeo
CHAO_MAX = -40.0          # ruído de fundo (dB RMS nas pausas, 30 dB abaixo da voz) acima disso = chiado/ambiente
BRILHO_MIN = 0.012        # energia acima de 4 kHz: abaixo disso a fala está abafada/telefone

# alvo padrão da equalização (curva média de narração brasileira aprovada, dB relativos por banda de 1/3 de oitava)
BANDAS = [80, 100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3150,
          4000, 5000, 6300, 8000, 10000]


def ff(args, **kw):
    return subprocess.run(["ffmpeg", "-hide_banner", "-nostats", *args], capture_output=True, text=True, timeout=180, **kw)


def carregar(p, sr=SR):
    import librosa
    y, _ = librosa.load(p, sr=sr, mono=True)
    return y


def aparar(y, sr=SR, db=-40):
    import librosa
    yt, idx = librosa.effects.trim(y, top_db=-db if db < 0 else db, frame_length=1024, hop_length=256)
    a = max(0, idx[0] - int(0.03 * sr)); b = min(len(y), idx[1] + int(0.06 * sr))
    return y[a:b]


def curva(y, sr=SR):
    """energia por banda de 1/3 de oitava (dB), normalizada pela média (só a FORMA da curva)."""
    import numpy as np, librosa
    S = np.abs(librosa.stft(y, n_fft=4096, hop_length=1024)) ** 2
    rms = S.sum(0); ativo = rms > np.percentile(rms, 40)          # só os quadros com voz
    P = S[:, ativo].mean(1) if ativo.any() else S.mean(1)
    f = librosa.fft_frequencies(sr=sr, n_fft=4096); out = []
    for fc in BANDAS:
        lo, hi = fc / 2 ** (1 / 6), fc * 2 ** (1 / 6)
        m = (f >= lo) & (f < hi)
        out.append(10 * np.log10(P[m].mean() + 1e-12))
    out = np.array(out)
    return out - out.mean()


def medir(y, sr=SR):
    import numpy as np, librosa
    f0, vf, _ = librosa.pyin(y, fmin=60, fmax=400, sr=sr, frame_length=2048)
    f0v = f0[vf]
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
    db = 20 * np.log10(rms + 1e-9); topo = np.percentile(db, 95); sil = db[db < topo - 30]
    chao = float(np.median(sil)) if sil.size >= 8 else None   # sem pausa suficiente: não dá para medir
    S = np.abs(librosa.stft(y, n_fft=2048)) ** 2; f = librosa.fft_frequencies(sr=sr, n_fft=2048)
    mf = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)[1:].mean(1)
    return {"tom_hz": float(np.nanmedian(f0v)) if f0v.size else None,
            "chao_db": chao,
            "brilho": float(S[f > 4000].sum() / (S.sum() + 1e-12)),
            "mfcc": mf.tolist()}


def info(path):
    trim = "silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.05," \
           "areverse,silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.05,areverse"
    r = ff(["-i", path, "-af", trim + ",volumedetect", "-f", "null", "-"])
    if r.returncode != 0:
        return None
    err = r.stderr
    mean = re.search(r"mean_volume: (-?[\d.]+|-inf) dB", err)
    peak = re.search(r"max_volume: (-?[\d.]+|-inf) dB", err)

    def probe(f):
        v = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f],
                           capture_output=True, text=True).stdout.strip()
        try:
            return float(v)
        except ValueError:
            return 0.0
    tmp = path + ".trim.wav"
    ff(["-y", "-v", "error", "-i", path, "-af", trim, tmp])
    dur_total = probe(path); dur = probe(tmp) if os.path.exists(tmp) else dur_total
    if os.path.exists(tmp):
        os.remove(tmp)
    g = lambda x: -120.0 if (not x or x.group(1) == "-inf") else float(x.group(1))
    return {"dur": round(dur, 2), "dur_arquivo": round(dur_total, 2), "media_db": g(mean), "pico_db": g(peak)}


def norm(s):
    s = re.sub(r"\[[^\]]*\]", " ", s.lower())
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9 ]+", " ", s).split()


def arq(pasta, k):
    for ext in (".wav", ".mp3"):
        if os.path.exists(os.path.join(pasta, k + ext)):
            return os.path.join(pasta, k + ext)
    return os.path.join(pasta, k + ".wav")


# ---------------------------------------------------------------- checar
def checar(pasta, narr, transc=None):
    import numpy as np
    lines = json.load(open(narr, encoding="utf-8"))["lines"]
    tr = json.load(open(transc, encoding="utf-8")) if transc else {}
    res, med = {}, {}
    for i, txt in enumerate(lines):
        k = f"{i + 1:02d}"; p = arq(pasta, k); slot = SCENES[i + 1] - SCENES[i] - 0.1
        r = {"fala": txt, "slot": round(slot, 2), "motivos": []}
        a = info(p) if os.path.exists(p) else None
        if not a:
            r["motivos"].append("arquivo faltando ou corrompido")
        else:
            r.update(a)
            r["tempo"] = round(max(1.0, a["dur"] / slot), 2)
            if a["media_db"] < SIL_DB or a["dur"] < 0.4:
                r["motivos"].append("sem voz / silêncio")
            if r["tempo"] > MAX_TEMPO:
                r["motivos"].append(f"longa demais ({a['dur']}s para {slot:.1f}s; regerar com speed {min(1.3, r['tempo']):.2f})")
            if a["dur"] < 0.35 * slot and len(norm(txt)) > 3:
                r["motivos"].append("curta demais (pode ter cortado palavras)")
            if a["media_db"] >= SIL_DB:
                m = medir(carregar(p)); med[k] = m
                r.update({x: (round(v, 3) if isinstance(v, float) else v) for x, v in m.items() if x != "mfcc"})
                if m["chao_db"] is not None and m["chao_db"] > CHAO_MAX:
                    r["motivos"].append(f"ruído de fundo alto ({m['chao_db']:.0f} dB)")
                if m["brilho"] < BRILHO_MIN:
                    r["motivos"].append("voz abafada (sem agudos)")
        if tr.get(k):
            sim = SequenceMatcher(None, norm(txt), norm(tr[k])).ratio()
            r["ouvido"] = tr[k]; r["semelhanca"] = round(sim, 2)
            if sim < SIM_MIN:
                r["motivos"].append(f"falou diferente do roteiro (semelhança {sim:.2f})")
        res[k] = r
    # consistência entre falas (mesma pessoa?)
    tons = {k: m["tom_hz"] for k, m in med.items() if m["tom_hz"]}
    if len(tons) >= 4:
        ref_tom = float(np.median([v for k, v in tons.items() if k != "09"] or list(tons.values())))
        M = np.array([med[k]["mfcc"] for k in med]); c = np.median(M, 0)
        dist = {k: float(np.linalg.norm(np.array(med[k]["mfcc"]) - c)) for k in med}
        tip = float(np.median(list(dist.values()))) or 1.0
        for k in med:
            r = res[k]
            if k in tons:
                desv = tons[k] / ref_tom - 1; r["tom_desvio"] = round(desv, 2)
                lim = TOM_MAX_EXCL if k == "09" else TOM_MAX
                if abs(desv) > lim:
                    r["motivos"].append(f"tom destoa ({tons[k]:.0f} Hz x {ref_tom:.0f} Hz do vídeo): parece outra voz")
            r["timbre_dist"] = round(dist[k] / tip, 2)
            if dist[k] / tip > TIMBRE_MAX:
                r["motivos"].append(f"timbre destoa das outras falas ({dist[k] / tip:.1f}x)")
    ok_all = True
    for k, r in res.items():
        r["ok"] = not r["motivos"]; ok_all &= r["ok"]
        print(f"{k} {'OK     ' if r['ok'] else 'REFAZER'} {r.get('dur', '-')}s/{r['slot']:.1f}s  {'; '.join(r['motivos'])}")
    json.dump({"ok": ok_all, "falas": res}, open(os.path.join(pasta, "qa.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("TUDO OK" if ok_all else "HÁ FALAS PARA REFAZER")
    return ok_all


# ---------------------------------------------------------------- perfil (alvo da equalização)
def perfil(pasta_ref, saida):
    import numpy as np, glob
    cs = [curva(aparar(carregar(p))) for p in sorted(glob.glob(os.path.join(pasta_ref, "*.mp3")) + glob.glob(os.path.join(pasta_ref, "*.wav")))]
    alvo = np.median(np.array(cs), 0)
    json.dump({"bandas": BANDAS, "alvo_db": [round(float(x), 2) for x in alvo], "fonte": pasta_ref},
              open(saida, "w", encoding="utf-8"), indent=1)
    print("perfil gravado:", saida, f"({len(cs)} falas)")


# ---------------------------------------------------------------- tratar (limpeza + equalização entre as vozes)
def _eq_fir(gains_db, sr=SR, taps=2047):
    import numpy as np
    from scipy.signal import firwin2
    f = [0.0] + [b for b in BANDAS] + [sr / 2]
    g = [gains_db[0]] + list(gains_db) + [gains_db[-1]]
    return firwin2(taps, [x / (sr / 2) for x in f], [10 ** (x / 20) for x in g])


def tratar(pasta, saida, perfil_json=None):
    import numpy as np, noisereduce as nr, pyloudnorm as pyln, soundfile as sf
    from scipy.signal import fftconvolve, butter, sosfiltfilt
    os.makedirs(saida, exist_ok=True)
    ks = [f"{i:02d}" for i in range(1, 11)]
    ys = {}
    for k in ks:
        p = arq(pasta, k)
        if os.path.exists(p):
            ys[k] = carregar(p)
    if not ys:
        sys.exit("nenhuma fala encontrada")
    sos = butter(4, 75, btype="highpass", fs=SR, output="sos")
    limp, ruido = {}, {}
    for k, y in ys.items():
        y = sosfiltfilt(sos, y)
        # ruído: perfil estacionário tirado dos trechos mais baixos; redução moderada (forte demais = voz robótica)
        chao = medir(y)["chao_db"]
        if chao is not None and chao > -50:          # só limpa se houver ruído de verdade; limpar voz limpa deixa ela robótica
            y = nr.reduce_noise(y=y, sr=SR, stationary=True, prop_decrease=0.6 if chao < -42 else 0.8, n_fft=2048,
                                freq_mask_smooth_hz=300, time_mask_smooth_ms=80)
        limp[k] = aparar(y); ruido[k] = None if chao is None else round(chao, 1)
    curvas = {k: curva(y) for k, y in limp.items()}
    if perfil_json and os.path.exists(perfil_json):
        alvo = np.array(json.load(open(perfil_json, encoding="utf-8"))["alvo_db"])
        fonte = "perfil " + os.path.basename(perfil_json)
    else:
        alvo = np.median(np.array(list(curvas.values())), 0); fonte = "mediana das falas do vídeo"
    meter = pyln.Meter(SR); rel = {"alvo": fonte, "falas": {}}
    for k, y in limp.items():
        corr = np.clip(alvo - curvas[k], -9, 9)
        corr = np.convolve(np.pad(corr, 1, mode="edge"), [0.25, 0.5, 0.25], mode="valid")   # suaviza a correção
        corr[BANDAS.index(10000)] = min(corr[BANDAS.index(10000)], 4)    # não inventa agudo que não existe (só ruído)
        y = fftconvolve(y, _eq_fir(corr), mode="same")
        tmp_in, tmp_out = os.path.join(saida, f".{k}_in.wav"), os.path.join(saida, f"{k}.wav")
        sf.write(tmp_in, y.astype("float32"), SR)
        # de-esser + compressão leve (voz "na cara", sem bombear) + limitador
        r = ff(["-y", "-v", "error", "-i", tmp_in, "-af",
                "deesser=i=0.4:m=0.5:f=0.5,",
                "acompressor=threshold=-22dB:ratio=2.5:attack=8:release=120:makeup=1,"
                "alimiter=limit=0.89:attack=3:release=60:level=disabled", "-ar", str(SR), tmp_out])
        os.remove(tmp_in)
        if r.returncode:
            sys.exit(r.stderr)
        z = carregar(tmp_out)
        lu = meter.integrated_loudness(z) if len(z) > SR * 0.4 else -18
        z = z * 10 ** ((-18 - lu) / 20)
        pk = np.max(np.abs(z)) or 1
        if pk > 0.89:
            z = z * 0.89 / pk
        sf.write(tmp_out, z.astype("float32"), SR, subtype="PCM_16")
        rel["falas"][k] = {"eq_db": [round(float(x), 1) for x in corr], "ruido_db": ruido[k], "lufs_antes": round(float(lu), 1)}
        print(f"fala {k}: limpa, equalizada (correção máx {np.max(np.abs(corr)):.1f} dB), -18 LUFS")
    json.dump(rel, open(os.path.join(saida, "tratamento.json"), "w", encoding="utf-8"), indent=1)
    print("ok", saida)


# ---------------------------------------------------------------- dividir (gravação única -> 10 falas)
def dividir(wav, pasta, n=10):
    """A narração gerada NUMA chamada só (as 10 falas no mesmo texto, uma por linha) mantém a MESMA voz
    do começo ao fim. Aqui ela é cortada nas n-1 maiores pausas e vira 01..10.wav."""
    import numpy as np, librosa, soundfile as sf
    y = carregar(wav); hop = 256
    rms = librosa.feature.rms(y=y, frame_length=1024, hop_length=hop)[0]
    db = 20 * np.log10(rms + 1e-9); voz = db > (np.percentile(db, 95) - 35)
    trechos, i = [], 0                       # pausas = sequências de quadros sem voz
    while i < len(voz):
        if not voz[i]:
            j = i
            while j < len(voz) and not voz[j]:
                j += 1
            trechos.append((i, j)); i = j
        else:
            i += 1
    internas = [t for t in trechos if t[0] > 0 and t[1] < len(voz)]
    if len(internas) < n - 1:
        sys.exit(f"só achei {len(internas) + 1} trechos de fala (esperava {n}): gere de novo com pausa maior entre as linhas")
    cortes = sorted(sorted(internas, key=lambda t: t[1] - t[0], reverse=True)[:n - 1])
    menor = min(t[1] - t[0] for t in cortes) * hop / SR
    os.makedirs(pasta, exist_ok=True); ini = 0
    for k, (a, b) in enumerate(cortes + [(len(voz), len(voz))]):
        meio = (a + b) // 2 * hop if b < len(voz) else len(y)
        seg = aparar(y[ini:meio]); sf.write(os.path.join(pasta, f"{k + 1:02d}.wav"), seg, SR, subtype="PCM_16")
        print(f"fala {k + 1:02d}: {len(seg) / SR:.2f}s"); ini = meio
    print(f"ok ({n} falas; menor pausa usada {menor:.2f}s)")


# ---------------------------------------------------------------- montar
def montar(pasta, narr, out):
    import numpy as np, pyloudnorm as pyln, soundfile as sf
    lines = json.load(open(narr, encoding="utf-8"))["lines"]
    ins, parts, lab = [], [], ""
    for i in range(len(lines)):
        k = f"{i + 1:02d}"; p = arq(pasta, k)
        if not os.path.exists(p):
            print(f"fala {k} faltando: fica em silêncio"); continue
        a = info(p); slot = SCENES[i + 1] - SCENES[i] - 0.1
        if not a or a["dur"] < 0.2:
            print(f"fala {k} sem voz: fica em silêncio"); continue
        tempo = max(1.0, a["dur"] / slot)
        if tempo > MAX_TEMPO:
            print(f"AVISO fala {k}: {a['dur']}s não cabe em {slot:.1f}s a {MAX_TEMPO}x; será cortada (regerar com speed maior)")
        tempo = min(tempo, MAX_TEMPO)
        n = len(ins) // 2; ins += ["-i", p]
        d = int((SCENES[i] + (0.05 if i else 0)) * 1000); L = min(a["dur"] / tempo, slot)
        f = (f"[{n}:a]silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.05,"
             f"areverse,silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.05,areverse,"
             f"aresample={SR},aformat=channel_layouts=stereo")
        if tempo > 1.0:
            f += f",atempo={tempo:.3f}"
        f += f",atrim=0:{L:.3f},afade=t=in:d=0.015,afade=t=out:st={max(0, L - 0.06):.3f}:d=0.06,adelay={d}|{d}[s{n}]"
        parts.append(f); lab += f"[s{n}]"
        print(f"fala {k}: {a['dur']:.2f}s na cena de {slot:.1f}s" + (f" (acelerada {tempo:.2f}x)" if tempo > 1 else ""))
    tmp = out + ".tmp.wav"
    fc = ";".join(parts) + ";" + lab + f"amix=inputs={len(parts)}:normalize=0:duration=longest,apad=whole_dur=37[o]"
    r = ff(["-y", "-v", "error", *ins, "-filter_complex", fc, "-map", "[o]", "-ar", str(SR), "-ac", "2", "-t", "37", tmp])
    if r.returncode:
        sys.exit(r.stderr)
    # volume final: ganho LINEAR para -14 LUFS (não usa loudnorm dinâmico, que "bombeia" e deixa a voz artificial)
    y, sr = sf.read(tmp); os.remove(tmp)
    lu = pyln.Meter(sr).integrated_loudness(y); y = y * 10 ** ((-14 - lu) / 20)
    pk = np.max(np.abs(y))
    if pk > 0.84:                        # ~ -1,5 dBTP
        tmp2 = out + ".lim.wav"; sf.write(tmp2, y.astype("float32"), sr)
        r = ff(["-y", "-v", "error", "-i", tmp2, "-af", "alimiter=limit=0.84:attack=2:release=50:level=disabled",
                "-ar", str(SR), "-c:a", "pcm_s16le", out]); os.remove(tmp2)
        if r.returncode:
            sys.exit(r.stderr)
    else:
        sf.write(out, y, sr, subtype="PCM_16")
    print("ok", out)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "checar":
        sys.exit(0 if checar(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None) else 2)
    elif cmd == "tratar":
        tratar(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
    elif cmd == "perfil":
        perfil(sys.argv[2], sys.argv[3])
    elif cmd == "dividir":
        dividir(sys.argv[2], sys.argv[3])
    elif cmd == "montar":
        montar(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        sys.exit(__doc__)
