"""Testes do checador de áudio: funções puras e integração com ffmpeg."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import checar_audio as ca

SCRIPT = Path(__file__).parent.parent / "scripts" / "checar_audio.py"


def test_normalizar() -> None:
    assert ca.normalizar("  Olá,   MUNDO!  Ação… ") == "ola mundo acao"
    assert ca.normalizar("Já é bom?") == "ja e bom"


def test_similaridade() -> None:
    assert ca.similaridade("Bora treinar!", "bora treinar") == 1.0
    assert ca.similaridade("Joelho para dentro.", "Cotovelo aberto demais") < 0.8
    assert 0.8 < ca.similaridade("Empurre o joelho para fora.", "Empurre o joelho pra fora") < 1.0


@pytest.mark.parametrize("cps,esperado", [
    (7.9, "longa demais"), (8.0, None), (14.0, None), (25.0, None), (25.1, "curta demais"),
])
def test_classificar_ritmo(cps: float, esperado: str | None) -> None:
    assert ca.classificar_ritmo(cps) == esperado


def test_calcular_cps() -> None:
    assert ca.calcular_cps("a" * 28, 2.0) == 14.0
    assert ca.calcular_cps("abc", 0) == 0.0


def test_classificar_fala_ok_e_motivos() -> None:
    roteiro = "a" * 28
    assert ca.classificar_fala(2.0, -20.0, roteiro, None) == []
    assert ca.classificar_fala(2.0, -50.0, roteiro, None) == ["sem voz"]
    assert ca.classificar_fala(10.0, -20.0, roteiro, None) == ["longa demais"]
    assert ca.classificar_fala(0.5, -20.0, roteiro, None) == ["curta demais"]
    motivos = ca.classificar_fala(2.0, -20.0, "bora treinar agora", "outra coisa totalmente", 0.8)
    assert motivos and motivos[0].startswith("falou diferente (")


def test_parse_volume_medio() -> None:
    assert ca.parse_volume_medio("x\n[Parsed_volumedetect_0] mean_volume: -23.4 dB\n") == -23.4
    assert ca.parse_volume_medio("mean_volume: -inf dB") == float("-inf")
    assert ca.parse_volume_medio("sem nada") is None


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg ausente")
def test_integracao_sem_voz(tmp_path: Path) -> None:
    falas = tmp_path / "falas"
    falas.mkdir()
    base = ["ffmpeg", "-y", "-loglevel", "error"]
    subprocess.run(base + ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "2",
                           str(falas / "01.mp3")], check=True)
    subprocess.run(base + ["-f", "lavfi", "-i", "sine=frequency=440:duration=2",
                           str(falas / "02.mp3")], check=True)
    roteiro = tmp_path / "narration.json"
    roteiro.write_text(json.dumps({"lines": ["Bora treinar, guerreiro!", "Foco no movimento certo."]}))
    qa_path = tmp_path / "qa.json"
    r = subprocess.run([sys.executable, str(SCRIPT), str(falas), str(roteiro),
                        "--saida", str(qa_path), "--sem-whisper"], capture_output=True, text=True)
    qa = json.loads(qa_path.read_text())
    assert r.returncode == 1
    assert "01 REFAZER: sem voz" in r.stdout
    assert "sem voz" in qa["01"]["motivos"] and qa["01"]["ok"] is False
    assert "sem voz" not in qa["02"]["motivos"]
    assert qa["01"]["transcricao"] is None and qa["02"]["ouvido"] is None
    assert abs(qa["02"]["duracao"] - 2.0) < 0.2
