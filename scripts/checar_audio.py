#!/usr/bin/env python3
"""Confere as narrações geradas fala por fala (duração, voz, ritmo, transcrição)."""
from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any

LIMIAR_SEM_VOZ_DB = -45.0
CPS_MIN = 8.0
CPS_MAX = 25.0
LIMIAR_SIMILARIDADE = 0.8
MODELO_PADRAO = "small"
EXTENSOES = (".mp3", ".wav")


# ---------------------------------------------------------------- lógica pura

def normalizar(texto: str) -> str:
    """Minúsculas, sem acentos nem pontuação, espaços únicos."""
    sem_acento = unicodedata.normalize("NFD", texto.lower())
    sem_acento = "".join(c for c in sem_acento if unicodedata.category(c) != "Mn")
    so_texto = re.sub(r"[^\w\s]|_", " ", sem_acento)
    return " ".join(so_texto.split())


def similaridade(roteiro: str, ouvido: str) -> float:
    """Razão de similaridade (0 a 1) entre roteiro e transcrição normalizados."""
    return difflib.SequenceMatcher(None, normalizar(roteiro), normalizar(ouvido)).ratio()


def calcular_cps(roteiro: str, duracao: float) -> float:
    """Caracteres por segundo do roteiro sobre a duração do áudio."""
    return len(roteiro.strip()) / duracao if duracao > 0 else 0.0


def classificar_ritmo(cps: float) -> str | None:
    """Devolve 'longa demais' ou 'curta demais' se o ritmo sair da faixa."""
    if cps < CPS_MIN:
        return "longa demais"
    if cps > CPS_MAX:
        return "curta demais"
    return None


def classificar_fala(duracao: float, volume_medio: float | None, roteiro: str,
                     ouvido: str | None, limiar: float = LIMIAR_SIMILARIDADE) -> list[str]:
    """Lista os motivos para refazer a fala (vazia se estiver OK)."""
    motivos: list[str] = []
    if volume_medio is not None and volume_medio < LIMIAR_SEM_VOZ_DB:
        motivos.append("sem voz")
    ritmo = classificar_ritmo(calcular_cps(roteiro, duracao))
    if ritmo:
        motivos.append(ritmo)
    if ouvido is not None:
        sim = similaridade(roteiro, ouvido)
        if sim < limiar:
            motivos.append(f"falou diferente ({sim:.2f})")
    return motivos


def parse_volume_medio(saida_ffmpeg: str) -> float | None:
    """Extrai o mean_volume (dB) da saída do volumedetect."""
    achado = re.search(r"mean_volume:\s*(-?inf|-?[\d.]+)\s*dB", saida_ffmpeg)
    if not achado:
        return None
    return float("-inf") if "inf" in achado.group(1) else float(achado.group(1))


# ---------------------------------------------------------------- ffmpeg e whisper

def duracao_ffprobe(arquivo: Path) -> float:
    """Duração em segundos via ffprobe; levanta RuntimeError se não abrir."""
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
           "-of", "default=nw=1:nk=1", str(arquivo)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return float(r.stdout.strip())
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise RuntimeError(f"ffprobe não abriu o arquivo: {exc}") from exc


def volume_medio(arquivo: Path) -> float | None:
    """Volume médio (dB) via ffmpeg volumedetect; None se não medir."""
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", str(arquivo),
           "-af", "volumedetect", "-f", "null", "-"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.SubprocessError):
        return None
    return parse_volume_medio(r.stderr)


def carregar_whisper(modelo: str) -> Any | None:
    """Carrega o faster-whisper de forma preguiçosa; None se não estiver instalado."""
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except ImportError:
        return None
    try:
        return WhisperModel(modelo, device="cpu", compute_type="int8")
    except Exception as exc:  # modelo indisponível (ex.: sem rede para baixar)
        print(f"AVISO: não foi possível carregar o modelo '{modelo}': {exc}", file=sys.stderr)
        return None


def transcrever(whisper: Any, arquivo: Path) -> str:
    """Transcreve o áudio em português e junta os segmentos."""
    segmentos, _ = whisper.transcribe(str(arquivo), language="pt")
    return " ".join(s.text.strip() for s in segmentos).strip()


# ---------------------------------------------------------------- orquestração

def achar_arquivo(pasta: Path, n: int) -> Path | None:
    """Procura NN.mp3 ou NN.wav na pasta."""
    for ext in EXTENSOES:
        candidato = pasta / f"{n:02d}{ext}"
        if candidato.is_file():
            return candidato
    return None


def checar_fala(arquivo: Path | None, roteiro: str, whisper: Any | None,
                limiar: float) -> dict[str, Any]:
    """Confere uma fala e devolve a entrada do qa.json."""
    base: dict[str, Any] = {"ok": False, "duracao": None, "cps": None, "volume_db": None,
                            "roteiro": roteiro, "ouvido": None, "transcricao": None,
                            "similaridade": None, "motivos": [], "erro": None}
    if arquivo is None:
        base["erro"] = "arquivo de áudio ausente"
        return base
    try:
        duracao = duracao_ffprobe(arquivo)
    except RuntimeError as exc:
        base["erro"] = str(exc)
        return base
    volume = volume_medio(arquivo)
    ouvido = transcrever(whisper, arquivo) if whisper is not None else None
    base.update(duracao=round(duracao, 2), cps=round(calcular_cps(roteiro, duracao), 1),
                volume_db=volume if volume is None or volume != float("-inf") else -120.0,
                ouvido=ouvido, transcricao=ouvido)
    if ouvido is not None:
        base["similaridade"] = round(similaridade(roteiro, ouvido), 2)
    base["motivos"] = classificar_fala(duracao, volume, roteiro, ouvido, limiar)
    base["ok"] = not base["motivos"]
    return base


def resumo_linha(chave: str, e: dict[str, Any]) -> str:
    """Formata a linha de resumo de uma fala."""
    if e["erro"]:
        return f"{chave} ERRO: {e['erro']}"
    if e["ok"]:
        return f"{chave} OK {e['duracao']:.1f}s"
    return f"{chave} REFAZER: {'; '.join(e['motivos'])}"


def ler_falas(narration: Path) -> list[str]:
    """Lê as falas ('lines') do narration.json."""
    dados = json.loads(narration.read_text(encoding="utf-8"))
    falas = dados.get("lines") if isinstance(dados, dict) else None
    if not (isinstance(falas, list) and all(isinstance(f, str) for f in falas)):
        raise ValueError("narration.json sem lista 'lines' de textos")
    return falas


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada: confere as falas, grava o qa.json e devolve o exit code."""
    ap = argparse.ArgumentParser(description="Confere narrações fala por fala.")
    ap.add_argument("pasta_falas", type=Path)
    ap.add_argument("narration", type=Path)
    ap.add_argument("--saida", type=Path, default=None, help="qa.json (padrão: <pasta_falas>/qa.json)")
    ap.add_argument("--modelo", default=MODELO_PADRAO)
    ap.add_argument("--limiar", type=float, default=LIMIAR_SIMILARIDADE)
    ap.add_argument("--sem-whisper", action="store_true")
    args = ap.parse_args(argv)
    try:
        falas = ler_falas(args.narration)
    except (OSError, ValueError) as exc:
        print(f"ERRO ao ler {args.narration}: {exc}", file=sys.stderr)
        return 2
    whisper = None if args.sem_whisper else carregar_whisper(args.modelo)
    if whisper is None and not args.sem_whisper:
        print("AVISO: transcrição pulada (whisper indisponível).", file=sys.stderr)
    qa: dict[str, dict[str, Any]] = {}
    for n, roteiro in enumerate(falas, 1):
        chave = f"{n:02d}"
        qa[chave] = checar_fala(achar_arquivo(args.pasta_falas, n), roteiro, whisper, args.limiar)
        print(resumo_linha(chave, qa[chave]))
    saida = args.saida or args.pasta_falas / "qa.json"
    saida.write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if all(e["ok"] for e in qa.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
