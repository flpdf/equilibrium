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


def test_classificar_fala_janela() -> None:
    roteiro = "a" * 40
    assert ca.classificar_fala(4.0, -20.0, roteiro, None, janela=4.25) == []
    motivos = ca.classificar_fala(5.0, -20.0, roteiro, None, janela=4.25)
    assert "longa demais para a cena (5.00 s > 4.25 s)" in motivos
    assert ca.JANELAS_PADRAO == {1: 3.4 * 1.25, 2: 3.8 * 1.25}


@pytest.fixture
def ffmpeg() -> list[str]:
    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg ausente")
    return ["ffmpeg", "-y", "-loglevel", "error"]


def narracao(tmp_path: Path, n: int = 10) -> Path:
    """Escreve um narration.json com n falas de 24 caracteres."""
    caminho = tmp_path / "narration.json"
    caminho.write_text(json.dumps({"lines": ["Bora treinar, guerreiro!"] * n}))
    return caminho


def rodar(*args: object) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                          capture_output=True, text=True)


def tom(base: list[str], destino: Path, segundos: float) -> None:
    subprocess.run(base + ["-f", "lavfi", "-i", f"sine=frequency=440:duration={segundos}",
                           str(destino)], check=True)


def test_integracao_sem_voz(tmp_path: Path, ffmpeg: list[str]) -> None:
    falas = tmp_path / "falas"
    falas.mkdir()
    subprocess.run(ffmpeg + ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "2",
                             str(falas / "01.mp3")], check=True)
    tom(ffmpeg, falas / "02.mp3", 2)
    qa_path = tmp_path / "sub" / "qa.json"  # a pasta de saída é criada
    r = rodar(falas, narracao(tmp_path), "--saida", qa_path, "--sem-whisper")
    qa = json.loads(qa_path.read_text())
    assert r.returncode == 1
    assert "01 REFAZER: sem voz" in r.stdout
    assert qa["transcricao_pulada"] is True
    assert "sem voz" in qa["falas"]["01"]["motivos"] and qa["falas"]["01"]["ok"] is False
    assert qa["falas"]["02"]["ok"] is True  # fala 2: 2 s cabe na janela
    assert qa["falas"]["01"]["transcricao"] is None and qa["falas"]["02"]["ouvido"] is None
    assert abs(qa["falas"]["02"]["duracao"] - 2.0) < 0.2


def test_pasta_inexistente(tmp_path: Path) -> None:
    r = rodar(tmp_path / "nao_existe", narracao(tmp_path))
    assert r.returncode == 2 and "pasta de falas não encontrada" in r.stderr
    assert not (tmp_path / "nao_existe").exists()


def test_arquivo_ausente_vira_refazer(tmp_path: Path) -> None:
    falas = tmp_path / "falas"
    falas.mkdir()
    qa_path = tmp_path / "qa.json"
    r = rodar(falas, narracao(tmp_path), "--saida", qa_path, "--sem-whisper")
    qa = json.loads(qa_path.read_text())
    assert r.returncode == 1
    assert "01 REFAZER: arquivo ausente" in r.stdout and "ERRO" not in r.stdout
    assert qa["falas"]["01"]["motivos"] == ["arquivo ausente"] and qa["falas"]["01"]["erro"] is None


def test_arquivo_corrompido_vira_refazer(tmp_path: Path) -> None:
    if shutil.which("ffprobe") is None:
        pytest.skip("ffprobe ausente")
    falas = tmp_path / "falas"
    falas.mkdir()
    (falas / "01.mp3").write_text("isto não é áudio")
    qa_path = tmp_path / "qa.json"
    r = rodar(falas, narracao(tmp_path), "--saida", qa_path, "--sem-whisper")
    assert "01 REFAZER: arquivo inválido (" in r.stdout
    motivos = json.loads(qa_path.read_text())["falas"]["01"]["motivos"]
    assert motivos[0].startswith("arquivo inválido (") and len(motivos) == 1


def test_sem_whisper_marca_transcricao_pulada(tmp_path: Path) -> None:
    falas = tmp_path / "falas"
    falas.mkdir()
    qa_path = tmp_path / "qa.json"
    rodar(falas, narracao(tmp_path), "--saida", qa_path, "--sem-whisper")
    qa = json.loads(qa_path.read_text())
    assert qa["transcricao_pulada"] is True and set(qa["falas"]) == {f"{n:02d}" for n in range(1, 11)}


def test_janela_da_fala_1_estourada(tmp_path: Path, ffmpeg: list[str]) -> None:
    falas = tmp_path / "falas"
    falas.mkdir()
    tom(ffmpeg, falas / "01.mp3", 5)
    r = rodar(falas, narracao(tmp_path), "--sem-whisper")
    assert r.returncode == 1
    assert "01 REFAZER:" in r.stdout and "longa demais para a cena (5." in r.stdout
    qa = json.loads((falas / "qa.json").read_text())
    assert any(m.startswith("longa demais para a cena") for m in qa["falas"]["01"]["motivos"])


def test_janelas_customizadas(tmp_path: Path, ffmpeg: list[str]) -> None:
    falas = tmp_path / "falas"
    falas.mkdir()
    tom(ffmpeg, falas / "03.mp3", 2)
    janelas = tmp_path / "janelas.json"
    janelas.write_text(json.dumps([None, None, 1.0] + [None] * 7))
    r = rodar(falas, narracao(tmp_path), "--sem-whisper", "--janelas", janelas)
    assert "03 REFAZER:" in r.stdout and "(2.0" in r.stdout
    janelas.write_text(json.dumps([1, 2]))
    assert rodar(falas, narracao(tmp_path), "--janelas", janelas).returncode == 2


def test_narracao_com_9_linhas(tmp_path: Path) -> None:
    falas = tmp_path / "falas"
    falas.mkdir()
    r = rodar(falas, narracao(tmp_path, 9))
    assert r.returncode == 2 and "9 falas" in r.stderr
    assert not (falas / "qa.json").exists()


def test_checar_fala_volumedetect_falhou(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ca, "duracao_ffprobe", lambda a: 2.0)
    monkeypatch.setattr(ca, "volume_medio", lambda a: None)
    e = ca.checar_fala(tmp_path / "01.mp3", "a" * 28, None, 0.8)
    assert e["ok"] is False and e["erro"] == "volumedetect falhou"
    assert ca.resumo_linha("01", e) == "01 ERRO: volumedetect falhou"


def test_checar_fala_transcricao_falhou_nao_reprova(tmp_path: Path,
                                                    monkeypatch: pytest.MonkeyPatch) -> None:
    def quebra(whisper, arquivo):
        raise ValueError("modelo corrompido")
    monkeypatch.setattr(ca, "duracao_ffprobe", lambda a: 2.0)
    monkeypatch.setattr(ca, "volume_medio", lambda a: -20.0)
    monkeypatch.setattr(ca, "transcrever", quebra)
    e = ca.checar_fala(tmp_path / "01.mp3", "a" * 28, object(), 0.8)
    assert e["ok"] is True and e["ouvido"] is None
    assert e["motivos"] == ["transcrição falhou: modelo corrompido"]


def test_duracao_zero_e_arquivo_invalido(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class R:
        returncode, stdout, stderr = 0, "0.0\n", ""
    monkeypatch.setattr(ca.subprocess, "run", lambda *a, **k: R())
    with pytest.raises(ca.ArquivoInvalido, match="arquivo inválido"):
        ca.duracao_ffprobe(tmp_path / "x.mp3")
