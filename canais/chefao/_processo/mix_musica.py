"""Coloca a música de fundo no vídeo do Chefão: narração a 100%, música a 10%, música começando na batida.

uso:
  python3 mix_musica.py <video.mp4> <pasta_musicas> <saida.mp4> [--n N] [--faixa arquivo.mp3]

- <video.mp4>: vídeo já renderizado COM a narração (render_all.sh ... narracao_sync.wav).
- <pasta_musicas>: _processo/musicas/ (mp3/wav/m4a com batida eletrônica, livres de direitos).
- --n N: escolhe a faixa N (mod quantidade) da lista em ordem alfabética (PRODUÇÃO usa dia_do_ano*3 + k,
  k = 0/1/2 para v1/v2/v3, assim o mesmo dia não repete faixa). --faixa força uma faixa.
- Música: loudness igualado ao da narração e depois 10% do volume (−20 dB); começa num tempo forte
  logo depois da introdução calma (onde a música "entra"), então o 1º golpe cai junto com o gancho (0 s);
  repete a faixa se ela for curta; fade-in de 0,15 s e fade-out nos 1,5 s finais.
- Sem música na pasta: copia o vídeo como está e avisa (sai com código 0, imprime AVISO).
Imprime uma linha: MUSICA <nome> inicio=<s> bpm=<n>.
"""
import json, os, subprocess, sys
import numpy as np

SR = 22050
HOP = 512
VOL = 0.10          # música a 10% da narração
EXTS = (".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac")


def run(args):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("ERRO ffmpeg: " + r.stderr[-800:])
    return r


def dur(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                                capture_output=True, text=True).stdout.strip())


def mono(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def batidas(y):
    """tempo (bpm), instantes das batidas (s) e energia por quadro."""
    n = 2048
    frames = 1 + (len(y) - n) // HOP
    win = np.hanning(n).astype(np.float32)
    spec = np.abs(np.fft.rfft(np.stack([y[i * HOP:i * HOP + n] * win for i in range(frames)]), axis=1))
    spec = np.log1p(spec)
    flux = np.maximum(spec[1:] - spec[:-1], 0).sum(axis=1)
    flux = np.concatenate([[0], flux])
    flux = (flux - flux.mean()) / (flux.std() + 1e-9)
    rms = np.sqrt((np.stack([y[i * HOP:i * HOP + n] for i in range(frames)]) ** 2).mean(axis=1))
    fps = SR / HOP
    # tempo por autocorrelação, entre 85 e 160 bpm (música eletrônica)
    ac = np.correlate(flux, flux, mode="full")[len(flux) - 1:]
    lags = np.arange(len(ac))
    bpm_of = lambda lag: 60 * fps / lag
    ok = (lags > 0) & (bpm_of(np.maximum(lags, 1)) >= 85) & (bpm_of(np.maximum(lags, 1)) <= 160)
    lag = int(lags[ok][np.argmax(ac[ok])])
    bpm = bpm_of(lag)
    # fase: deslocamento que soma mais força de ataque nas batidas; depois cada batida é ajustada
    # ao ataque mais próximo (corrige a deriva do período arredondado)
    fase = int(np.argmax([flux[p::lag].sum() for p in range(lag)]))
    win_b = max(1, lag // 4)
    bq, q = [], fase
    while q < len(flux):
        a0, a1 = max(0, q - win_b), min(len(flux), q + win_b + 1)
        q = a0 + int(np.argmax(flux[a0:a1]))
        bq.append(q)
        q += lag
    beats = (np.array(bq) * HOP + n / 2) / SR + 0.025   # centro da janela + ajuste medido num metrônomo de teste
    beats = beats[beats >= 0]
    return bpm, beats, rms, fps


def inicio(beats, rms, fps, total, alvo=37.0):
    """1ª batida (múltipla de 4 = tempo forte do compasso) em que a música já está 'cheia'."""
    cheio = 0.6 * np.percentile(rms, 90)
    for i, b in enumerate(beats):
        if i % 4:
            continue
        q = int(max(0, b) * fps)
        if rms[q:q + int(2 * fps)].mean() >= cheio:
            if total - b >= 20 or b == beats[0]:
                return float(b)
    return float(beats[0])


def main():
    a = sys.argv[1:]
    if len(a) < 3:
        sys.exit(__doc__)
    video, pasta, saida = a[:3]
    n = int(a[a.index("--n") + 1]) if "--n" in a else 0
    faixas = sorted(f for f in os.listdir(pasta) if f.lower().endswith(EXTS)) if os.path.isdir(pasta) else []
    if "--faixa" in a:
        faixas = [a[a.index("--faixa") + 1]]
    if not faixas:
        run(["ffmpeg", "-y", "-v", "error", "-i", video, "-c", "copy", saida])
        print("AVISO: nenhuma música em", pasta, "- vídeo saiu só com a narração")
        return
    faixa = faixas[n % len(faixas)]
    mus = faixa if os.path.isabs(faixa) else os.path.join(pasta, faixa)
    D = dur(video)
    bpm, beats, rms, fps = batidas(mono(mus))
    # faixas geradas para o Chefão ("_sync" no nome) já começam alinhadas aos cortes de cena: usar do início
    t0 = 0.0 if "_sync" in os.path.basename(mus) else inicio(beats, rms, fps, dur(mus), D)
    # loudness da narração do vídeo e da música (LUFS integrado) para deixar a música em 10% da narração
    def lufs(path, extra=()):
        r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", *extra, "-i", path, "-af", "ebur128", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
        v = [l for l in r.splitlines() if l.strip().startswith("I:")]
        return float(v[-1].split()[1]) if v else -16.0
    l_nar = lufs(video)
    l_mus = lufs(mus, ["-ss", str(t0), "-t", str(D)])
    ganho_db = (l_nar - l_mus) + 20 * np.log10(VOL)
    fo = max(0.0, D - 1.5)
    filt = (f"[1:a]atrim=start={t0:.3f},asetpts=PTS-STARTPTS,atrim=0:{D:.3f},"
            f"volume={ganho_db:.2f}dB,afade=t=in:d=0.15,afade=t=out:st={fo:.2f}:d=1.5,"
            f"aresample=44100,aformat=channel_layouts=stereo[m];"
            f"[0:a]aresample=44100,aformat=channel_layouts=stereo[v];"
            f"[v][m]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.97[a]")
    tmp = saida + ".part.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-i", video, "-stream_loop", "-1", "-i", mus, "-filter_complex", filt,
         "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", f"{D:.3f}",
         "-movflags", "+faststart", tmp])
    os.replace(tmp, saida)
    print(f"MUSICA {os.path.basename(mus)} inicio={t0:.2f} bpm={bpm:.0f} ganho={ganho_db:.1f}dB")


if __name__ == "__main__":
    main()
