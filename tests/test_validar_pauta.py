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


def test_caption_longa_e_erro(pauta: Path) -> None:
    editar_json(pauta / "v1/episode.json",
                lambda d: d["captions"][0].__setitem__(0, ["A" * 30, ""]))
    rel = validar_pauta.validar_pasta(pauta)
    assert tem(rel, "captions[1]: 30 caracteres (máximo 24)")


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
    "Faça dez repetições.",
    "Hipertrofia garantida.",
    "Queime gordura.",
    "Perca peso.",
    "Pode te lesionar.",
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


@pytest.mark.parametrize("fala", [
    "Quem procura postura acerta.",
    "Isso se trata de postura.",
    "Quem perde dois segundos perde o controle.",
    "Sua postura garantida.",
    "Sem remédio, só técnica.",
])
def test_palavra_comum_nao_e_falso_positivo(pauta: Path, fala: str) -> None:
    editar_json(pauta / "v1/narration.json", lambda d: d["lines"].__setitem__(2, fala))
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
        d["errors"][2]["view"] = "under_foot"  # válida só em piscina
        d["ambiente"] = "piscina"
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


# ------------------------------------------------------------ contagens e limites

def test_contagem_de_videos_e_carrosseis(pauta: Path) -> None:
    def mudar(d: dict) -> None:
        d["videos"].pop()
        d["carrosseis"].append(d["carrosseis"][0])
    editar_json(pauta / "pauta.json", mudar)
    rel = validar_pauta.validar_pasta(pauta)
    assert tem(rel, "'videos' deve ter exatamente 3")
    assert tem(rel, "'carrosseis' deve ter exatamente 3")


def test_errors_diferente_de_3(pauta: Path) -> None:
    editar_json(pauta / "v1/episode.json", lambda d: d["errors"].pop())
    assert tem(validar_pauta.validar_pasta(pauta), "'errors' deve ter exatamente 3")


def test_limites_de_slide_sao_erro(pauta: Path) -> None:
    def mudar(d: dict) -> None:
        d["slides"][0]["nome"] = "N" * 15
        d["slides"][0]["errado"] = "E" * 29
        d["slides"][1]["certo"] = "C" * 29
    editar_json(pauta / "c1/carrossel.json", mudar)
    rel = validar_pauta.validar_pasta(pauta)
    assert tem(rel, "'nome' com 15 caracteres (máximo 14)")
    assert tem(rel, "'errado' com 29 caracteres (máximo 28)")
    assert tem(rel, "slides[2]: 'certo' com 29")
    editar_json(pauta / "c1/carrossel.json", lambda d: d["slides"][0].update(nome="N" * 14, errado="E" * 28))
    assert not tem(validar_pauta.validar_pasta(pauta), "'nome' com")


def test_card_name_longo_e_erro(pauta: Path) -> None:
    editar_json(pauta / "v1/episode.json", lambda d: d["card"].__setitem__("name", ["A" * 13]))
    assert tem(validar_pauta.validar_pasta(pauta), "card.name deve ter 1-2 linhas de até 12")


def test_caption_com_5_blocos_e_erro(pauta: Path) -> None:
    editar_json(pauta / "v1/episode.json",
                lambda d: d["captions"].__setitem__(0, [["A", ""]] * 5))
    assert tem(validar_pauta.validar_pasta(pauta), "captions[1]: 5 pares (máximo 4)")


def test_cores_invalidas(pauta: Path) -> None:
    editar_json(pauta / "c1/carrossel.json", lambda d: d.__setitem__("cor", "z"))
    editar_json(pauta / "c3/carrossel.json", lambda d: d["slides"][0].__setitem__("tagcor", "q"))
    rel = validar_pauta.validar_pasta(pauta)
    assert tem(rel, "c1/carrossel.json: cor 'z'")
    assert tem(rel, "c3/carrossel.json: slides[1]: tagcor 'q'")


def test_tipo_de_slide_slot_e_arquivo_invalidos(pauta: Path) -> None:
    editar_json(pauta / "c1/carrossel.json", lambda d: d["slides"][0].__setitem__("tipo", "foto"))
    def mudar(d: dict) -> None:
        d["videos"][0]["slot"] = "tarde"
        d["videos"][1]["arquivo"] = "pushup.glb"
    editar_json(pauta / "pauta.json", mudar)
    rel = validar_pauta.validar_pasta(pauta)
    assert tem(rel, "slides[1]: tipo 'foto'")
    assert tem(rel, "videos[1]: slot 'tarde'")
    assert tem(rel, "videos[2]: arquivo 'pushup.glb' deve terminar em .fbx")


# ------------------------------------------------------------ legenda e narração

def test_legenda_gerado_por_ia_e_titulo(pauta: Path) -> None:
    legenda = pauta / "c1/legenda.txt"
    base = legenda.read_text(encoding="utf-8")
    legenda.write_text("Conteúdo gerado por IA\n" + base, encoding="utf-8")
    (pauta / "c2/legenda.txt").write_text("TÍTULO: algo\n" + (pauta / "c2/legenda.txt").read_text(encoding="utf-8"),
                                          encoding="utf-8")
    rel = validar_pauta.validar_pasta(pauta)
    assert tem(rel, "c1/legenda.txt: linha 1 não pode ir ao ar")
    assert tem(rel, "c2/legenda.txt: linha 1 não pode ir ao ar")


def test_legenda_subtitulo_e_alerta_no_meio_da_linha(pauta: Path) -> None:
    legenda = pauta / "c1/legenda.txt"
    base = legenda.read_text(encoding="utf-8")
    legenda.write_text("Subtítulo: x\n" + base, encoding="utf-8")
    assert validar_pauta.validar_pasta(pauta).erros == []
    legenda.write_text("Cuidado ⚠ aqui\n" + base, encoding="utf-8")
    assert tem(validar_pauta.validar_pasta(pauta), "c1/legenda.txt: linha 1")


def test_fala_10_limite_de_55(pauta: Path) -> None:
    editar_json(pauta / "v1/narration.json", lambda d: d["lines"].__setitem__(9, "x" * 54 + "."))
    assert validar_pauta.validar_pasta(pauta).erros == []
    editar_json(pauta / "v1/narration.json", lambda d: d["lines"].__setitem__(9, "x" * 55 + "."))
    assert tem(validar_pauta.validar_pasta(pauta), "fala 10: 56 caracteres (máximo 55)")


def test_hashtags_acima_do_maximo_e_aviso(pauta: Path) -> None:
    (pauta / "v1/legenda.txt").write_text("Texto " + " ".join(f"#t{i}" for i in range(9)) + "\n",
                                          encoding="utf-8")
    rel = validar_pauta.validar_pasta(pauta)
    assert rel.erros == [] and tem(rel, "9 hashtags", "avisos")


def test_legenda_latin1_sem_traceback(pauta: Path) -> None:
    (pauta / "v1/legenda.txt").write_bytes("Ação #a #b #c #d #e #f\n".encode("latin-1"))
    assert tem(validar_pauta.validar_pasta(pauta), "v1/legenda.txt: arquivo não está em UTF-8")


# ------------------------------------------------------------ episode.json

def test_outro_percent_10(pauta: Path) -> None:
    editar_json(pauta / "v1/episode.json", lambda d: d["outro"].__setitem__("percent", 10))
    assert tem(validar_pauta.validar_pasta(pauta), "outro.percent '10'")


def test_pasta_inexistente(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert validar_pauta.main([str(tmp_path / "nada")]) == 2
    assert "pasta da pauta não encontrada" in capsys.readouterr().err


def test_json_cli_com_aviso(pauta: Path, capsys: pytest.CaptureFixture[str]) -> None:
    editar_json(pauta / "v1/episode.json", lambda d: d["errors"][0].__setitem__("zone", "mixamorigHips"))
    assert validar_pauta.main([str(pauta), "--json"]) == 0
    saida = json.loads(capsys.readouterr().out)
    assert saida["erros"] == [] and saida["avisos"][0].keys() == {"arquivo", "mensagem"}


def test_vistas_de_natacao_so_em_piscina(pauta: Path) -> None:
    caminho = pauta / "v1/episode.json"
    editar_json(caminho, lambda d: d["errors"][0].__setitem__("view", "side_under"))
    assert tem(validar_pauta.validar_pasta(pauta), "errors[1]: view 'side_under'")
    editar_json(caminho, lambda d: d.__setitem__("ambiente", "piscina"))
    editar_json(caminho, lambda d: d["errors"][1].__setitem__("view", "split_front"))
    assert validar_pauta.validar_pasta(pauta).erros == []


def test_vistas_de_natacao_em_carrossel_e_slide_info(pauta: Path) -> None:
    editar_json(pauta / "c1/carrossel.json", lambda d: d["slides"][0]["erro"].__setitem__("view", "top"))
    editar_json(pauta / "c1/carrossel.json", lambda d: d["slides"][3].__setitem__("view", "under_foot"))
    rel = validar_pauta.validar_pasta(pauta)
    assert tem(rel, "slides[1]: erro: view 'top'")
    assert tem(rel, "slides[4]: view 'under_foot'")


def test_pose_do_slide_info(pauta: Path) -> None:
    editar_json(pauta / "c1/carrossel.json", lambda d: d["slides"][3].__setitem__("pose", "pico"))
    assert validar_pauta.validar_pasta(pauta).erros == []
    editar_json(pauta / "c1/carrossel.json", lambda d: d["slides"][3].__setitem__("pose", "meio"))
    assert tem(validar_pauta.validar_pasta(pauta), "slides[4]: pose 'meio'")


def test_angle_em_graus_e_aviso(pauta: Path) -> None:
    editar_json(pauta / "v1/episode.json", lambda d: d["errors"][0]["deform"].__setitem__("angle", 20))
    rel = validar_pauta.validar_pasta(pauta)
    assert rel.erros == [] and tem(rel, "parece graus; o campo é em radianos", "avisos")


def test_anim_e_peak_obrigatorios(pauta: Path) -> None:
    def mudar(d: dict) -> None:
        del d["anim"]
        d["peak"] = {"bone": "Hips"}
    editar_json(pauta / "v1/episode.json", mudar)
    rel = validar_pauta.validar_pasta(pauta)
    assert tem(rel, "v1/episode.json: campo 'anim' ausente")
    assert tem(rel, "'peak' deve ser objeto com 'bone' e 'metric'")
    editar_json(pauta / "v2/episode.json", lambda d: d.update(anim="x.glb"))
    assert tem(validar_pauta.validar_pasta(pauta), "v2/episode.json: anim 'x.glb'")


def test_card_rows_e_cta_cards_formato(pauta: Path) -> None:
    def mudar(d: dict) -> None:
        d["card"]["rows"] = [["A"], ["B", "C", "x"], ["D", "E"]]
        d["cta"]["cards"] = [["A", "B"], "C", ["D", "E"]]
    editar_json(pauta / "v1/episode.json", mudar)
    rel = validar_pauta.validar_pasta(pauta)
    assert rel.erros == []
    assert tem(rel, "card.rows[1]: deveria ser lista de 2 ou 3", "avisos")
    assert tem(rel, 'card.rows[2]: terceiro item deve ser "r"', "avisos")
    assert tem(rel, "cta.cards[2]: deveria ser lista de 2 textos", "avisos")
    editar_json(pauta / "v1/episode.json", lambda d: d["card"].__setitem__("rows", [["A", "B"]]))
    assert tem(validar_pauta.validar_pasta(pauta), "card.rows deveria ter 3 linhas", "avisos")


# ------------------------------------------------------------ robustez de tipos

@pytest.mark.parametrize("arquivo,mudar", [
    ("pauta.json", lambda d: d.__setitem__("status", ["aprovada"])),
    ("pauta.json", lambda d: d["videos"][0].__setitem__("slot", {"a": 1})),
    ("estado.json", lambda d: d.__setitem__("audio", ["pronto"])),
    ("v1/episode.json", lambda d: d["captions"][0][0].__setitem__(1, ["r"])),
    ("v1/episode.json", lambda d: d["errors"][0]["deform"].__setitem__("axis", ["x"])),
    ("v1/episode.json", lambda d: d["errors"][0].__setitem__("view", ["front"])),
    ("c1/carrossel.json", lambda d: d.__setitem__("cor", ["r"])),
    ("c1/carrossel.json", lambda d: d["slides"][3].__setitem__("tagcor", {"x": 1})),
    ("c1/carrossel.json", lambda d: d["slides"][3].__setitem__("pose", ["pico"])),
    ("c1/carrossel.json", lambda d: d["slides"][0].__setitem__("tipo", ["erro"])),
])
def test_campo_string_como_lista_nao_quebra(pauta: Path, arquivo: str, mudar) -> None:
    editar_json(pauta / arquivo, mudar)
    rel = validar_pauta.validar_pasta(pauta)  # sem traceback
    assert tem(rel, "tipo inválido") or tem(rel, "inválida") or tem(rel, "fora de")


# ------------------------------------------------------------ regras de conteúdo novas

def test_regras_cobrem_pauta_json(pauta: Path) -> None:
    def mudar(d: dict) -> None:
        d["tema"] = "Perca peso rápido"
        d["videos"][0]["gancho"] = "Tome whey hoje"
        d["carrosseis"][0]["titulo"] = "Queime gordura"
        d["carrosseis"][1]["itens"] = ["Vinte quilos na barra", "ok", "ok"]
    editar_json(pauta / "pauta.json", mudar)
    rel = validar_pauta.validar_pasta(pauta)
    assert sum(1 for a, _ in rel.erros if a == "pauta.json") >= 4


@pytest.mark.parametrize("arquivo,mudar", [
    ("v1/episode.json", lambda d: d["topbar"].__setitem__("left", "VOCÊ · QUEIME GORDURA")),
    ("v1/episode.json", lambda d: d["topbar"].__setitem__("right", "TOME WHEY")),
    ("v1/episode.json", lambda d: d["card"].__setitem__("rows", [["RISCO", "PODE LESIONAR"], ["A", "B"], ["C", "D"]])),
    ("v1/episode.json", lambda d: d["outro"].__setitem__("next", "Emagrecer")),
    ("v1/episode.json", lambda d: d["cta"]["cards"].__setitem__(0, ["PRANCHA", "30 REPS"])),
    ("c1/carrossel.json", lambda d: d.__setitem__("cta", {"pergunta": ["VOCÊ TOMA", "CREATINA?"], "sub": "OK"})),
    ("c1/carrossel.json", lambda d: d.__setitem__("arrasta", "RESULTADO GARANTIDO")),
])
def test_regras_cobrem_campos_novos(pauta: Path, arquivo: str, mudar) -> None:
    editar_json(pauta / arquivo, mudar)
    rel = validar_pauta.validar_pasta(pauta)
    assert any(a == arquivo and "conteúdo proibido" in m for a, m in rel.erros)


@pytest.mark.parametrize("fala", [
    "Faça 3x10 hoje.", "Corra a 10 km/h.", "Use vinte quilos.", "Faça três séries.",
    "Faça 3 x 12.",
])
def test_regras_de_carga_e_velocidade(pauta: Path, fala: str) -> None:
    caminho = pauta / "v3/episode.json"
    editar_json(caminho, lambda d: d["errors"][0].__setitem__("label", fala.upper()))
    assert tem(validar_pauta.validar_pasta(pauta), "conteúdo proibido")


def test_fbx_proibidos(pauta: Path) -> None:
    editar_json(pauta / "pauta.json",
                lambda d: d["videos"][0].__setitem__("arquivo", "Pike Walk.fbx"))
    editar_json(pauta / "v2/episode.json", lambda d: d.__setitem__("anim", "Swimming Breaststroke.fbx"))
    editar_json(pauta / "v3/episode.json", lambda d: d.__setitem__("anim", "Pike Walk.fbx"))
    rel = validar_pauta.validar_pasta(pauta)
    assert tem(rel, "pauta.json: animação proibida 'Pike Walk.fbx' em vídeo")
    assert tem(rel, "v2/episode.json: animação proibida 'Swimming Breaststroke.fbx'")
    assert tem(rel, "v3/episode.json: animação proibida 'Pike Walk.fbx' em vídeo")


def test_fbx_em_carrossel(pauta: Path) -> None:
    editar_json(pauta / "c1/carrossel.json", lambda d: d["slides"][0].__setitem__("anim", "Pike Walk.fbx"))
    assert validar_pauta.validar_pasta(pauta).erros == []
    editar_json(pauta / "c2/carrossel.json",
                lambda d: d["slides"][0].__setitem__("anim", "Swimming Breaststroke.fbx"))
    assert tem(validar_pauta.validar_pasta(pauta), "c2/carrossel.json: animação proibida")
