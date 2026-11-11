"""Testes do validador de pauta: quebra uma regra por vez na fixture íntegra."""
import json
import shutil
from pathlib import Path

import pytest

import validar_pauta

FIXTURE = Path(__file__).parent / "fixtures" / "pauta_valida"


@pytest.fixture
def pauta(tmp_path: Path) -> Path:
    """Cópia da fixture íntegra em pasta temporária."""
    destino = tmp_path / "pauta"
    shutil.copytree(FIXTURE, destino)
    return destino


def editar_json(caminho: Path, mudar) -> None:
    """Carrega, altera com a função dada e regrava o JSON."""
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    mudar(dados)
    caminho.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")


def mensagens(rel: validar_pauta.Relatorio, tipo: str = "erros") -> list[str]:
    """Junta 'arquivo: mensagem' de erros ou avisos."""
    return [f"{a}: {m}" for a, m in getattr(rel, tipo)]


def tem(rel: validar_pauta.Relatorio, trecho: str, tipo: str = "erros") -> bool:
    """Diz se algum erro/aviso contém o trecho."""
    return any(trecho in m for m in mensagens(rel, tipo))


def test_fixture_integra_passa(pauta: Path) -> None:
    rel = validar_pauta.validar_pasta(pauta)
    assert rel.erros == [] and rel.avisos == []
    assert validar_pauta.main([str(pauta)]) == 0


def test_captions_com_10_itens(pauta: Path) -> None:
    editar_json(pauta / "v1/episode.json", lambda d: d["captions"].pop())
    rel = validar_pauta.validar_pasta(pauta)
    assert tem(rel, "v1/episode.json: 'captions' deve ter exatamente 11")
    assert validar_pauta.main([str(pauta)]) == 1


def test_cor_de_caption_invalida(pauta: Path) -> None:
    editar_json(pauta / "v1/episode.json", lambda d: d["captions"][0][0].__setitem__(1, "x"))
    assert tem(validar_pauta.validar_pasta(pauta), "captions[1]: cor 'x'")


def test_caption_longa_e_aviso(pauta: Path) -> None:
    editar_json(pauta / "v1/episode.json",
                lambda d: d["captions"][0].__setitem__(0, ["A" * 30, ""]))
    rel = validar_pauta.validar_pasta(pauta)
    assert rel.erros == [] and tem(rel, "30 caracteres", "avisos")


def test_fala_com_digito(pauta: Path) -> None:
    editar_json(pauta / "v2/narration.json", lambda d: d["lines"].__setitem__(2, "Faça isso 3 vezes."))
    assert tem(validar_pauta.validar_pasta(pauta), "v2/narration.json: fala 3: contém dígito")


def test_fala_longa_e_sem_pontuacao(pauta: Path) -> None:
    def mudar(d: dict) -> None:
        d["lines"][2] = "x" * 46 + "."
        d["lines"][3] = "Sem pontuação final"
        d["lines"][1] = "y" * 55 + "."  # 56 chars, passa do limite das falas 2 e 10
    editar_json(pauta / "v3/narration.json", mudar)
    rel = validar_pauta.validar_pasta(pauta)
    assert tem(rel, "fala 3: 47 caracteres (máximo 45)")
    assert tem(rel, "fala 4: deve terminar")
    assert tem(rel, "fala 2: 56 caracteres (máximo 55)")


def test_legenda_com_alerta(pauta: Path) -> None:
    legenda = pauta / "v1/legenda.txt"
    legenda.write_text("⚠️ revisar antes\n" + legenda.read_text(encoding="utf-8"), encoding="utf-8")
    assert tem(validar_pauta.validar_pasta(pauta), "v1/legenda.txt: linha 1 não pode ir ao ar")


def test_legenda_com_postar_as_e_vazia(pauta: Path) -> None:
    (pauta / "c1/legenda.txt").write_text("Postar às 09:00\n#a #b #c #d #e #f\n", encoding="utf-8")
    (pauta / "c2/legenda.txt").write_text("  \n", encoding="utf-8")
    rel = validar_pauta.validar_pasta(pauta)
    assert tem(rel, "c1/legenda.txt: linha 1")
    assert tem(rel, "c2/legenda.txt: legenda vazia")


def test_hashtags_fora_da_faixa_e_aviso(pauta: Path) -> None:
    (pauta / "v1/legenda.txt").write_text("Texto #um #dois\n", encoding="utf-8")
    rel = validar_pauta.validar_pasta(pauta)
    assert rel.erros == [] and tem(rel, "2 hashtags", "avisos")


def test_slide_a_mais(pauta: Path) -> None:
    editar_json(pauta / "c1/carrossel.json", lambda d: d["slides"].append(d["slides"][0]))
    assert tem(validar_pauta.validar_pasta(pauta), "c1/carrossel.json: 'slides' deve ter exatamente 4")


def test_texto_info_longo(pauta: Path) -> None:
    editar_json(pauta / "c1/carrossel.json", lambda d: d["slides"][3].__setitem__("texto", "a" * 141))
    assert tem(validar_pauta.validar_pasta(pauta), "texto com 141 caracteres")


@pytest.mark.parametrize("fala", [
    "Use 20 kg na barra.",
    "Você vai emagrecer rápido.",
    "Isso é um tratamento de verdade.",
    "Tome creatina antes.",
])
def test_palavra_proibida_na_fala(pauta: Path, fala: str) -> None:
    editar_json(pauta / "v1/narration.json", lambda d: d["lines"].__setitem__(2, fala))
    rel = validar_pauta.validar_pasta(pauta)
    assert tem(rel, "conteúdo proibido")


def test_palavra_proibida_em_legenda_e_carrossel(pauta: Path) -> None:
    legenda = pauta / "v2/legenda.txt"
    legenda.write_text(legenda.read_text(encoding="utf-8") + "\nResultado garantido!\n", encoding="utf-8")
    editar_json(pauta / "c3/carrossel.json", lambda d: d["slides"][0].__setitem__("texto", "Tome whey."))
    rel = validar_pauta.validar_pasta(pauta)
    assert tem(rel, "v2/legenda.txt: conteúdo proibido")
    assert tem(rel, "c3/carrossel.json: conteúdo proibido")


def test_palavra_comum_nao_e_falso_positivo(pauta: Path) -> None:
    editar_json(pauta / "v1/narration.json",
                lambda d: d["lines"].__setitem__(2, "Quem procura postura acerta."))
    assert validar_pauta.validar_pasta(pauta).erros == []


def test_json_invalido(pauta: Path) -> None:
    (pauta / "v1/episode.json").write_text("{quebrado", encoding="utf-8")
    assert tem(validar_pauta.validar_pasta(pauta), "v1/episode.json: JSON inválido")


def test_arquivos_ausentes(pauta: Path) -> None:
    (pauta / "estado.json").unlink()
    shutil.rmtree(pauta / "c2")
    rel = validar_pauta.validar_pasta(pauta)
    assert tem(rel, "estado.json: arquivo ausente", "avisos")
    assert tem(rel, "c2: pasta ausente")
    (pauta / "pauta.json").unlink()
    assert tem(validar_pauta.validar_pasta(pauta), "pauta.json: arquivo ausente")


def test_exercicio_repetido(pauta: Path) -> None:
    editar_json(pauta / "pauta.json", lambda d: d["videos"][1].__setitem__("exercicio", "agachamento"))
    assert tem(validar_pauta.validar_pasta(pauta), "exercício repetido")


def test_estado_invalido(pauta: Path) -> None:
    editar_json(pauta / "estado.json", lambda d: d.__setitem__("audio", "quase"))
    assert tem(validar_pauta.validar_pasta(pauta), "estado.json: 'audio'")


def test_check_longo_e_view_invalida(pauta: Path) -> None:
    def mudar(d: dict) -> None:
        d["errors"][0]["check"] = "A" * 21
        d["errors"][1]["view"] = "lateral"
        d["errors"][2]["view"] = "under_foot"  # válida pelo prefixo
    editar_json(pauta / "v1/episode.json", mudar)
    rel = validar_pauta.validar_pasta(pauta)
    assert tem(rel, "errors[1]: check com 21")
    assert tem(rel, "errors[2]: view 'lateral'")
    assert not tem(rel, "under_foot")


def test_avisos_de_zone_minusculas_e_outro(pauta: Path) -> None:
    def mudar(d: dict) -> None:
        d["errors"][0]["zone"] = "mixamorigHips"
        d["errors"][1]["label"] = "minúsculo"
        d["outro"]["percent"] = 90
    editar_json(pauta / "v1/episode.json", mudar)
    rel = validar_pauta.validar_pasta(pauta)
    assert tem(rel, "mixamorig", "avisos")
    assert tem(rel, "MAIÚSCULAS", "avisos")
    assert tem(rel, "outro.percent '90'")


def test_json_cli(pauta: Path, capsys: pytest.CaptureFixture[str]) -> None:
    editar_json(pauta / "v1/episode.json", lambda d: d["captions"].pop())
    assert validar_pauta.main([str(pauta), "--json"]) == 1
    saida = json.loads(capsys.readouterr().out)
    assert set(saida) == {"erros", "avisos"}
    assert saida["erros"][0].keys() == {"arquivo", "mensagem"}
