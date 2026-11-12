"""Narração do Chefão gerada FALA POR FALA (10 arquivos curtos), conferida e montada nas cenas.

uso:
  python3 audio_falas.py checar <pasta_falas> narration.json [transcricoes.json]
      -> grava <pasta_falas>/qa.json e imprime uma linha por fala: OK ou REFAZER (motivo)
  python3 audio_falas.py montar <pasta_falas> narration.json saida.wav
      -> narracao_sync.wav de 37 s com cada fala no início da sua cena

<pasta_falas> tem 01.wav (ou .mp3) ... 10.wav (uma fala cada, na ordem do narration.json).
transcricoes.json (opcional, recomendado) = {"01": "texto que o Scribe ouviu", ...}.
"""
import json, os, re, subprocess, sys, unicodedata
from difflib import SequenceMatcher

SCENES = [0.0, 3.4, 7.2, 10.4, 13.6, 16.8, 20.0, 23.2, 26.4, 29.6, 33.0]
MAX_TEMPO = 1.25          # aceleração máxima que ainda soa natural
SIM_MIN = 0.70            # semelhança mínima entre o roteiro e o que foi falado (o Whisper erra números e sussurros: 0,8 reprovava falas boas)
SIL_DB = -45              # abaixo disso a fala é considerada silêncio


def ff(args, **kw):
    return subprocess.run(["ffmpeg", "-hide_banner", "-nostats", *args], capture_output=True, text=True, timeout=120, **kw)


def info(path):
    """duração útil (sem silêncio no começo/fim), volume médio e pico."""
    trim = "silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.05," \
           "areverse,silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.05,areverse"
    r = ff(["-i", path, "-af", trim + ",volumedetect,astats=metadata=0", "-f", "null", "-"])
    err = r.stderr
    if r.returncode != 0:
        return None
    mean = re.search(r"mean_volume: (-?[\d.]+|-inf) dB", err)
    peak = re.search(r"max_volume: (-?[\d.]+|-inf) dB", err)
    # duração depois do corte de silêncio
    def probe(f):
        v = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f],
                           capture_output=True, text=True).stdout.strip()
        try:
            return float(v)
        except ValueError:      # arquivo vazio (fala só de silêncio)
            return 0.0
    tmp = path + ".trim.wav"
    ff(["-y", "-v", "error", "-i", path, "-af", trim, tmp])
    dur_total = probe(path)
    dur = probe(tmp) if os.path.exists(tmp) else dur_total
    if os.path.exists(tmp):
        os.remove(tmp)
    f = lambda x: -120.0 if (not x or x.group(1) == "-inf") else float(x.group(1))
    return {"dur": round(dur, 2), "dur_arquivo": round(dur_total, 2), "media_db": f(mean), "pico_db": f(peak)}


def norm(s):
    s = re.sub(r"\[[^\]]*\]", " ", s.lower())
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9 ]+", " ", s).split()


def arq(pasta, k):
    for ext in (".wav", ".mp3"):
        if os.path.exists(os.path.join(pasta, k + ext)): return os.path.join(pasta, k + ext)
    return os.path.join(pasta, k + ".wav")


def checar(pasta, narr, transc=None):
    lines = json.load(open(narr, encoding="utf-8"))["lines"]
    tr = json.load(open(transc, encoding="utf-8")) if transc else {}
    res, ok_all = {}, True
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
                r["motivos"].append(f"longa demais ({a['dur']}s para {slot:.1f}s; precisaria acelerar {r['tempo']}x)")
            if a["dur"] < 0.35 * slot and len(norm(txt)) > 3:
                r["motivos"].append("curta demais (pode ter cortado palavras)")
        if tr.get(k):
            sim = SequenceMatcher(None, norm(txt), norm(tr[k])).ratio()
            r["ouvido"] = tr[k]; r["semelhanca"] = round(sim, 2)
            if sim < SIM_MIN:
                r["motivos"].append(f"falou diferente do roteiro (semelhança {sim:.2f})")
        r["ok"] = not r["motivos"]; ok_all &= r["ok"]; res[k] = r
        print(f"{k} {'OK     ' if r['ok'] else 'REFAZER'} {r.get('dur', '-')}s/{slot:.1f}s  {'; '.join(r['motivos'])}")
    json.dump({"ok": ok_all, "falas": res}, open(os.path.join(pasta, "qa.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("TUDO OK" if ok_all else "HÁ FALAS PARA REFAZER")
    return ok_all


def montar(pasta, narr, out):
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
            print(f"AVISO fala {k}: {a['dur']}s não cabe em {slot:.1f}s nem a {MAX_TEMPO}x; será cortada")
        tempo = min(tempo, MAX_TEMPO)
        n = len(ins) // 2; ins += ["-i", p]
        d = int((SCENES[i] + (0.05 if i else 0)) * 1000); L = min(a["dur"] / tempo, slot)
        f = (f"[{n}:a]silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.05,"
             f"areverse,silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.05,areverse,"
             f"aresample=44100,aformat=channel_layouts=stereo")
        if tempo > 1.0:
            f += f",atempo={tempo:.3f}"
        f += f",atrim=0:{L:.3f},afade=t=in:d=0.01,afade=t=out:st={max(0, L - 0.04):.3f}:d=0.04,adelay={d}|{d}[s{n}]"
        parts.append(f); lab += f"[s{n}]"
        print(f"fala {k}: {a['dur']:.2f}s na cena de {slot:.1f}s" + (f" (acelerada {tempo:.2f}x)" if tempo > 1 else ""))
    fc = ";".join(parts) + ";" + lab + f"amix=inputs={len(parts)}:normalize=0:duration=longest," \
         "apad=whole_dur=37,loudnorm=I=-14:TP=-1.5:LRA=11[o]"
    r = ff(["-y", "-v", "error", *ins, "-filter_complex", fc, "-map", "[o]", "-ar", "44100", "-ac", "2", "-t", "37", out])
    if r.returncode:
        sys.exit(r.stderr)
    print("ok", out)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "checar":
        sys.exit(0 if checar(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None) else 2)
    elif cmd == "montar":
        montar(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        sys.exit(__doc__)
