#!/usr/bin/env python3
"""Valida a pasta de pauta diária do canal Chefão dos Treinos."""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

ARQ_REGRAS = Path(__file__).resolve().parent / "regras_conteudo.json"

STATUS_PAUTA = {"proposta", "aprovada", "padrao", "produzida"}
SLOTS = {"manha", "almoco", "noite"}
ESTADO_PAUTA = {"proposta", "em_ajuste", "aprovada", "padrao"}
ESTADO_AUDIO = {"pendente", "em_andamento", "pronto", "pronto_com_avisos", "falhou"}
ESTADO_PRODUCAO = {"pendente", "em_andamento", "produzida"}
CORES_CAPTION = {"", "r", "g"}
CORES_CARROSSEL = {"r", "y", "g"}
CORES_TAG = {"r", "g", "y"}
VIEWS = {
    "front", "front_low", "high_front", "top_front", "threequarter", "side",
    "side_left", "low_side", "back", "top", "side_under",
}
PREFIXOS_VIEW = ("under_", "split")
EIXOS = {"x", "y", "z"}

N_CAPTIONS = 11
MAX_PARES_CAPTION = 4
MAX_CHARS_CAPTION = 24
N_FALAS = 10
MAX_FALA = 45
MAX_FALA_LONGA = 55
FALAS_LONGAS = {2, 10}
MAX_CHECK = 20
MAX_LINHA_NOME_CARD = 12
MAX_LINHA_TITULO_CARROSSEL = 22
MAX_NOME_SLIDE = 14
MAX_ERRADO_CERTO = 28
MAX_LINHA_TITULO_INFO = 18
MAX_TEXTO_INFO = 140
HASHTAGS_VIDEO = (6, 8)
HASHTAGS_CARROSSEL = (6, 10)
LINHAS_PROIBIDAS = ("postar às", "gerado por ia", "título:")


class Relatorio:
    """Acumula erros e avisos por arquivo."""

    def __init__(self) -> None:
        self.erros: list[tuple[str, str]] = []
        self.avisos: list[tuple[str, str]] = []

    def erro(self, arquivo: str, msg: str) -> None:
        """Registra um erro que reprova a pauta."""
        self.erros.append((arquivo, msg))

    def aviso(self, arquivo: str, msg: str) -> None:
        """Registra um aviso que apenas é reportado."""
        self.avisos.append((arquivo, msg))


Textos = list[tuple[str, str]]


# ---------------------------------------------------------------- utilitários

def carregar_json(raiz: Path, nome: str, rel: Relatorio, ausente_e_erro: bool = True) -> Any:
    """Lê um JSON da pauta; registra problema e devolve None se não der."""
    caminho = raiz / nome
    if not caminho.is_file():
        (rel.erro if ausente_e_erro else rel.aviso)(nome, "arquivo ausente")
        return None
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        rel.erro(nome, f"JSON inválido: {exc}")
        return None


def eh_numero(valor: Any) -> bool:
    """Diz se o valor é int ou float (booleano não conta)."""
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def exigir(obj: dict, campos: list[str], arq: str, rel: Relatorio, ctx: str = "") -> None:
    """Registra erro para cada campo ausente ou vazio."""
    for campo in campos:
        if obj.get(campo) in (None, "", []):
            rel.erro(arq, f"{ctx}campo '{campo}' ausente ou vazio")


def exigir_dict(valor: Any, arq: str, rel: Relatorio, ctx: str) -> bool:
    """Confere que o valor é objeto JSON; registra erro se não for."""
    if isinstance(valor, dict):
        return True
    rel.erro(arq, f"{ctx}deveria ser um objeto")
    return False


def view_valida(view: Any) -> bool:
    """Confere se a vista de câmera é uma das aceitas."""
    return isinstance(view, str) and (view in VIEWS or view.startswith(PREFIXOS_VIEW))


def em_maiusculas(texto: str) -> bool:
    """Diz se o texto não tem letra minúscula."""
    return texto == texto.upper()


def avisar_minusculas(textos: list[str], arq: str, rel: Relatorio, ctx: str) -> None:
    """Avisa para cada texto de tela que não esteja em maiúsculas."""
    for texto in textos:
        if isinstance(texto, str) and not em_maiusculas(texto):
            rel.aviso(arq, f"{ctx}texto de tela deveria estar em MAIÚSCULAS: '{texto}'")


# ---------------------------------------------------------------- pauta e estado

def validar_pauta_json(dados: Any, rel: Relatorio) -> None:
    """Valida pauta.json: campos, 3 vídeos, 3 carrosséis, sem exercício repetido."""
    arq = "pauta.json"
    if not exigir_dict(dados, arq, rel, ""):
        return
    exigir(dados, ["data", "dia", "tema", "status"], arq, rel)
    _validar_data(dados.get("data"), arq, rel)
    if dados.get("status") not in STATUS_PAUTA:
        rel.erro(arq, f"status '{dados.get('status')}' fora de {sorted(STATUS_PAUTA)}")
    _validar_videos_pauta(dados.get("videos"), arq, rel)
    _validar_carrosseis_pauta(dados.get("carrosseis"), arq, rel)


def _validar_data(data: Any, arq: str, rel: Relatorio) -> None:
    """Confere que data é AAAA-MM-DD válida."""
    if data in (None, ""):
        return
    try:
        if not (isinstance(data, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", data)):
            raise ValueError
        date.fromisoformat(data)
    except ValueError:
        rel.erro(arq, f"data '{data}' não está no formato AAAA-MM-DD")


def _hora_valida(hora: Any) -> bool:
    """Confere se é um horário HH:MM."""
    return isinstance(hora, str) and re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", hora) is not None


def _validar_videos_pauta(videos: Any, arq: str, rel: Relatorio) -> None:
    """Valida a lista de 3 vídeos da pauta e a repetição de exercícios."""
    if not isinstance(videos, list) or len(videos) != 3:
        rel.erro(arq, "'videos' deve ter exatamente 3 itens")
        return
    exercicios: list[str] = []
    for i, video in enumerate(videos, 1):
        ctx = f"videos[{i}]: "
        if not exigir_dict(video, arq, rel, ctx):
            continue
        exigir(video, ["id", "slot", "postar", "nivel", "exercicio", "arquivo", "pasta", "gancho"],
               arq, rel, ctx)
        if video.get("id") != f"v{i}":
            rel.erro(arq, f"{ctx}id deve ser 'v{i}', veio '{video.get('id')}'")
        if video.get("slot") not in SLOTS:
            rel.erro(arq, f"{ctx}slot '{video.get('slot')}' fora de {sorted(SLOTS)}")
        if video.get("postar") and not _hora_valida(video.get("postar")):
            rel.erro(arq, f"{ctx}postar '{video.get('postar')}' não é HH:MM")
        arquivo = video.get("arquivo")
        if arquivo and not (isinstance(arquivo, str) and arquivo.endswith(".fbx")):
            rel.erro(arq, f"{ctx}arquivo '{arquivo}' deve terminar em .fbx")
        erros = video.get("erros")
        if not (isinstance(erros, list) and len(erros) == 3 and all(isinstance(e, str) for e in erros)):
            rel.erro(arq, f"{ctx}'erros' deve ter exatamente 3 textos")
        if isinstance(video.get("exercicio"), str):
            exercicios.append(video["exercicio"].strip().casefold())
    repetidos = sorted({e for e in exercicios if exercicios.count(e) > 1})
    for exercicio in repetidos:
        rel.erro(arq, f"exercício repetido no mesmo dia: '{exercicio}'")


def _validar_carrosseis_pauta(carrosseis: Any, arq: str, rel: Relatorio) -> None:
    """Valida a lista de 3 carrosséis da pauta."""
    if not isinstance(carrosseis, list) or len(carrosseis) != 3:
        rel.erro(arq, "'carrosseis' deve ter exatamente 3 itens")
        return
    for i, carrossel in enumerate(carrosseis, 1):
        ctx = f"carrosseis[{i}]: "
        if not exigir_dict(carrossel, arq, rel, ctx):
            continue
        exigir(carrossel, ["id", "postar", "tipo", "titulo", "itens"], arq, rel, ctx)
        if carrossel.get("id") != f"c{i}":
            rel.erro(arq, f"{ctx}id deve ser 'c{i}', veio '{carrossel.get('id')}'")
        if carrossel.get("postar") and not _hora_valida(carrossel.get("postar")):
            rel.erro(arq, f"{ctx}postar '{carrossel.get('postar')}' não é HH:MM")
        if "itens" in carrossel and not isinstance(carrossel["itens"], list):
            rel.erro(arq, f"{ctx}'itens' deve ser uma lista")


def validar_estado_json(dados: Any, rel: Relatorio) -> None:
    """Valida estado.json: valores de pauta, audio e producao."""
    arq = "estado.json"
    if not exigir_dict(dados, arq, rel, ""):
        return
    for campo, validos in (("pauta", ESTADO_PAUTA), ("audio", ESTADO_AUDIO),
                           ("producao", ESTADO_PRODUCAO)):
        if dados.get(campo) not in validos:
            rel.erro(arq, f"'{campo}' = '{dados.get(campo)}' fora de {sorted(validos)}")


# ---------------------------------------------------------------- visual compartilhado

def _validar_zone(zone: Any, arq: str, rel: Relatorio, ctx: str) -> None:
    """Valida zone (string ou lista) e avisa sobre prefixo mixamorig."""
    if isinstance(zone, str):
        nomes = [zone]
    elif isinstance(zone, list) and all(isinstance(z, str) for z in zone) and zone:
        nomes = zone
    else:
        rel.erro(arq, f"{ctx}'zone' deve ser string ou lista de strings")
        return
    for nome in nomes:
        if nome.startswith("mixamorig"):
            rel.aviso(arq, f"{ctx}zone '{nome}' não deve levar o prefixo 'mixamorig'")


def _validar_deform(deform: Any, arq: str, rel: Relatorio, ctx: str) -> None:
    """Valida deform (objeto ou lista de objetos com bone, axis e angle)."""
    itens = deform if isinstance(deform, list) else [deform]
    if not itens:
        rel.erro(arq, f"{ctx}'deform' vazio")
    for i, item in enumerate(itens):
        rotulo = f"{ctx}deform[{i}]: " if isinstance(deform, list) else f"{ctx}deform: "
        if not exigir_dict(item, arq, rel, rotulo):
            continue
        if not (isinstance(item.get("bone"), str) and item["bone"]):
            rel.erro(arq, f"{rotulo}'bone' ausente")
        if item.get("axis") not in EIXOS:
            rel.erro(arq, f"{rotulo}'axis' '{item.get('axis')}' fora de x, y, z")
        if not eh_numero(item.get("angle")):
            rel.erro(arq, f"{rotulo}'angle' deve ser número")


def _validar_visual(obj: dict, arq: str, rel: Relatorio, ctx: str) -> None:
    """Valida view, zone e deform de um erro (episódio ou slide de carrossel)."""
    if not view_valida(obj.get("view")):
        rel.erro(arq, f"{ctx}view '{obj.get('view')}' inválida")
    if obj.get("zone") in (None, "", []):
        rel.erro(arq, f"{ctx}campo 'zone' ausente")
    else:
        _validar_zone(obj["zone"], arq, rel, ctx)
    if obj.get("deform") in (None, "", []):
        rel.erro(arq, f"{ctx}campo 'deform' ausente")
    else:
        _validar_deform(obj["deform"], arq, rel, ctx)


# ---------------------------------------------------------------- episode.json

def validar_episode(dados: Any, nome: str, rel: Relatorio, textos: Textos) -> None:
    """Valida vN/episode.json e coleta os textos de tela."""
    if not exigir_dict(dados, nome, rel, ""):
        return
    _validar_captions(dados.get("captions"), nome, rel, textos)
    _validar_errors(dados.get("errors"), nome, rel, textos)
    _validar_card(dados.get("card"), nome, rel, textos)
    outro = dados.get("outro")
    if isinstance(outro, dict) and "percent" in outro:
        pct = outro["percent"]
        if not (eh_numero(pct) and 20 <= pct <= 80):
            rel.erro(nome, f"outro.percent '{pct}' deve estar entre 20 e 80")
    cta = dados.get("cta")
    if isinstance(cta, dict) and "cards" in cta:
        if not (isinstance(cta["cards"], list) and len(cta["cards"]) == 3):
            rel.aviso(nome, "cta.cards deveria ter 3 itens")


def _validar_captions(captions: Any, nome: str, rel: Relatorio, textos: Textos) -> None:
    """Valida as 11 captions: pares [texto, cor], limites e maiúsculas."""
    if not isinstance(captions, list) or len(captions) != N_CAPTIONS:
        total = len(captions) if isinstance(captions, list) else "inválido"
        rel.erro(nome, f"'captions' deve ter exatamente {N_CAPTIONS} itens (tem {total})")
        if not isinstance(captions, list):
            return
    for i, item in enumerate(captions, 1):
        ctx = f"captions[{i}]: "
        if not isinstance(item, list) or not all(
                isinstance(p, list) and len(p) == 2 and isinstance(p[0], str) for p in item):
            rel.erro(nome, f"{ctx}deve ser lista de pares [texto, cor]")
            continue
        for par in item:
            if par[1] not in CORES_CAPTION:
                rel.erro(nome, f"{ctx}cor '{par[1]}' fora de \"\", \"r\", \"g\"")
            textos.append((nome, par[0]))
        if len(item) > MAX_PARES_CAPTION:
            rel.aviso(nome, f"{ctx}{len(item)} pares (máximo {MAX_PARES_CAPTION})")
        soma = sum(len(par[0]) for par in item)
        if soma > MAX_CHARS_CAPTION:
            rel.aviso(nome, f"{ctx}{soma} caracteres (máximo {MAX_CHARS_CAPTION})")
        avisar_minusculas([par[0] for par in item], nome, rel, ctx)


def _validar_errors(erros: Any, nome: str, rel: Relatorio, textos: Textos) -> None:
    """Valida os 3 erros do episódio: label, check, view, zone e deform."""
    if not isinstance(erros, list) or len(erros) != 3:
        rel.erro(nome, "'errors' deve ter exatamente 3 itens")
        return
    for i, erro in enumerate(erros, 1):
        ctx = f"errors[{i}]: "
        if not exigir_dict(erro, nome, rel, ctx):
            continue
        exigir(erro, ["label", "check"], nome, rel, ctx)
        for campo in ("label", "check"):
            if isinstance(erro.get(campo), str):
                textos.append((nome, erro[campo]))
                avisar_minusculas([erro[campo]], nome, rel, ctx)
        check = erro.get("check")
        if isinstance(check, str) and len(check) > MAX_CHECK:
            rel.erro(nome, f"{ctx}check com {len(check)} caracteres (máximo {MAX_CHECK})")
        _validar_visual(erro, nome, rel, ctx)


def _validar_card(card: Any, nome: str, rel: Relatorio, textos: Textos) -> None:
    """Valida card.name (1-2 linhas de até 12) e card.rows (3 linhas)."""
    if not isinstance(card, dict):
        rel.aviso(nome, "'card' ausente")
        return
    linhas = card.get("name")
    if not (isinstance(linhas, list) and 1 <= len(linhas) <= 2
            and all(isinstance(x, str) and len(x) <= MAX_LINHA_NOME_CARD for x in linhas)):
        rel.aviso(nome, f"card.name deve ter 1-2 linhas de até {MAX_LINHA_NOME_CARD} caracteres")
    if isinstance(linhas, list):
        textos.extend((nome, x) for x in linhas if isinstance(x, str))
        avisar_minusculas(linhas, nome, rel, "card.name: ")
    if not (isinstance(card.get("rows"), list) and len(card["rows"]) == 3):
        rel.aviso(nome, "card.rows deveria ter 3 linhas")


# ---------------------------------------------------------------- narration.json

def validar_narration(dados: Any, nome: str, rel: Relatorio, textos: Textos) -> None:
    """Valida vN/narration.json: 10 falas, tamanho, pontuação, sem dígitos."""
    if not exigir_dict(dados, nome, rel, ""):
        return
    falas = dados.get("lines")
    if not (isinstance(falas, list) and len(falas) == N_FALAS
            and all(isinstance(f, str) for f in falas)):
        rel.erro(nome, f"'lines' deve ter exatamente {N_FALAS} textos")
        return
    for i, fala in enumerate(falas, 1):
        ctx = f"fala {i}: "
        textos.append((nome, fala))
        limite = MAX_FALA_LONGA if i in FALAS_LONGAS else MAX_FALA
        if len(fala) > limite:
            rel.erro(nome, f"{ctx}{len(fala)} caracteres (máximo {limite})")
        if not fala.rstrip().endswith((".", "!", "?")):
            rel.erro(nome, f"{ctx}deve terminar com '.', '!' ou '?'")
        if re.search(r"\d", fala):
            rel.erro(nome, f"{ctx}contém dígito; escreva o número por extenso")
    if "desbloqueado" not in falas[8].casefold():
        rel.aviso(nome, "fala 9 deveria conter 'desbloqueado'")


# ---------------------------------------------------------------- legenda.txt

def validar_legenda(raiz: Path, nome: str, faixa: tuple[int, int], rel: Relatorio,
                    textos: Textos) -> None:
    """Valida legenda.txt: não vazia, sem linhas internas, contagem de hashtags."""
    caminho = raiz / nome
    if not caminho.is_file():
        rel.erro(nome, "arquivo ausente")
        return
    texto = caminho.read_text(encoding="utf-8")
    if not texto.strip():
        rel.erro(nome, "legenda vazia")
        return
    textos.append((nome, texto))
    for n, linha in enumerate(texto.splitlines(), 1):
        baixa = linha.strip().casefold()
        if baixa.startswith("⚠") or any(p in baixa for p in LINHAS_PROIBIDAS):
            rel.erro(nome, f"linha {n} não pode ir ao ar: '{linha.strip()}'")
    total = len(re.findall(r"#\w+", texto))
    if not faixa[0] <= total <= faixa[1]:
        rel.aviso(nome, f"{total} hashtags (esperado de {faixa[0]} a {faixa[1]})")


# ---------------------------------------------------------------- carrossel.json

def validar_carrossel(dados: Any, nome: str, id_esperado: str, rel: Relatorio,
                      textos: Textos) -> None:
    """Valida cN/carrossel.json e coleta os textos."""
    if not exigir_dict(dados, nome, rel, ""):
        return
    if dados.get("id") != id_esperado:
        rel.erro(nome, f"id deve ser '{id_esperado}', veio '{dados.get('id')}'")
    if dados.get("cor") not in CORES_CARROSSEL:
        rel.erro(nome, f"cor '{dados.get('cor')}' fora de {sorted(CORES_CARROSSEL)}")
    _validar_titulo_carrossel(dados.get("titulo"), nome, rel, textos)
    slides = dados.get("slides")
    if not isinstance(slides, list) or len(slides) != 4:
        rel.erro(nome, "'slides' deve ter exatamente 4 itens")
        return
    for i, slide in enumerate(slides, 1):
        ctx = f"slides[{i}]: "
        if not exigir_dict(slide, nome, rel, ctx):
            continue
        if slide.get("tipo") == "erro":
            _validar_slide_erro(slide, nome, rel, ctx, textos)
        elif slide.get("tipo") == "info":
            _validar_slide_info(slide, nome, rel, ctx, textos)
        else:
            rel.erro(nome, f"{ctx}tipo '{slide.get('tipo')}' fora de erro, info")


def _linhas_titulo(titulo: Any, nome: str, rel: Relatorio, ctx: str) -> list[str] | None:
    """Extrai as linhas de um título (string ou [texto, cor]); erro se o formato falhar."""
    if not isinstance(titulo, list) or not titulo:
        rel.erro(nome, f"{ctx}'titulo' deve ser uma lista de linhas")
        return None
    linhas: list[str] = []
    for item in titulo:
        if isinstance(item, str):
            linhas.append(item)
        elif isinstance(item, list) and len(item) == 2 and isinstance(item[0], str):
            linhas.append(item[0])
        else:
            rel.erro(nome, f"{ctx}linha de título deve ser texto ou [texto, cor]")
            return None
    return linhas


def _validar_titulo_carrossel(titulo: Any, nome: str, rel: Relatorio, textos: Textos) -> None:
    """Valida o título do carrossel (até 2 linhas de 22)."""
    linhas = _linhas_titulo(titulo, nome, rel, "")
    if linhas is None:
        return
    textos.extend((nome, x) for x in linhas)
    if len(linhas) > 2:
        rel.aviso(nome, f"titulo com {len(linhas)} linhas (máximo 2)")
    for linha in linhas:
        if len(linha) > MAX_LINHA_TITULO_CARROSSEL:
            rel.aviso(nome, f"linha de titulo '{linha}' passa de {MAX_LINHA_TITULO_CARROSSEL} caracteres")


def _limite_aviso(slide: dict, campo: str, limite: int, nome: str, rel: Relatorio, ctx: str) -> None:
    """Avisa se o campo de texto passa do limite."""
    valor = slide.get(campo)
    if isinstance(valor, str) and len(valor) > limite:
        rel.aviso(nome, f"{ctx}'{campo}' com {len(valor)} caracteres (máximo {limite})")


def _coletar(slide: dict, campos: list[str], nome: str, textos: Textos) -> None:
    """Adiciona os campos de texto do slide à lista de textos."""
    textos.extend((nome, slide[c]) for c in campos if isinstance(slide.get(c), str))


def _validar_slide_erro(slide: dict, nome: str, rel: Relatorio, ctx: str, textos: Textos) -> None:
    """Valida um slide do tipo erro."""
    exigir(slide, ["kicker", "nome", "anim", "errado", "certo", "erro"], nome, rel, ctx)
    _limite_aviso(slide, "nome", MAX_NOME_SLIDE, nome, rel, ctx)
    _limite_aviso(slide, "errado", MAX_ERRADO_CERTO, nome, rel, ctx)
    _limite_aviso(slide, "certo", MAX_ERRADO_CERTO, nome, rel, ctx)
    if isinstance(slide.get("anim"), str) and not slide["anim"].endswith(".fbx"):
        rel.erro(nome, f"{ctx}anim '{slide['anim']}' deve terminar em .fbx")
    _coletar(slide, ["kicker", "nome", "errado", "certo"], nome, textos)
    if isinstance(slide.get("erro"), dict):
        _validar_visual(slide["erro"], nome, rel, ctx + "erro: ")
    elif "erro" in slide and slide["erro"] not in (None, "", []):
        rel.erro(nome, f"{ctx}'erro' deve ser um objeto")


def _validar_slide_info(slide: dict, nome: str, rel: Relatorio, ctx: str, textos: Textos) -> None:
    """Valida um slide do tipo info."""
    exigir(slide, ["tag", "titulo", "anim", "view", "texto"], nome, rel, ctx)
    if "tagcor" in slide and slide["tagcor"] not in CORES_TAG:
        rel.erro(nome, f"{ctx}tagcor '{slide['tagcor']}' fora de {sorted(CORES_TAG)}")
    if slide.get("titulo") not in (None, "", []):
        linhas = _linhas_titulo(slide["titulo"], nome, rel, ctx)
        if linhas is not None:
            textos.extend((nome, x) for x in linhas)
            if len(linhas) > 2 or any(len(x) > MAX_LINHA_TITULO_INFO for x in linhas):
                rel.aviso(nome, f"{ctx}titulo deve ter até 2 linhas de {MAX_LINHA_TITULO_INFO} caracteres")
    texto = slide.get("texto")
    if isinstance(texto, str) and len(texto) > MAX_TEXTO_INFO:
        rel.erro(nome, f"{ctx}texto com {len(texto)} caracteres (máximo {MAX_TEXTO_INFO})")
    _coletar(slide, ["tag", "texto"], nome, textos)


# ---------------------------------------------------------------- regras de conteúdo

def carregar_regras(rel: Relatorio) -> list[tuple[re.Pattern[str], str]]:
    """Carrega os padrões proibidos de regras_conteudo.json."""
    try:
        bruto = json.loads(ARQ_REGRAS.read_text(encoding="utf-8"))
        return [(re.compile(r["padrao"], re.IGNORECASE), r["motivo"]) for r in bruto]
    except (OSError, ValueError, KeyError, TypeError, re.error) as exc:
        rel.erro("regras_conteudo.json", f"não foi possível carregar as regras: {exc}")
        return []


def checar_conteudo(textos: Textos, regras: list[tuple[re.Pattern[str], str]],
                    rel: Relatorio) -> None:
    """Aplica as regras de conteúdo a todos os textos coletados."""
    vistos: set[tuple[str, str, str]] = set()
    for arquivo, texto in textos:
        for padrao, motivo in regras:
            achado = padrao.search(texto)
            chave = (arquivo, padrao.pattern, achado.group(0) if achado else "")
            if achado and chave not in vistos:
                vistos.add(chave)
                rel.erro(arquivo, f"conteúdo proibido '{achado.group(0)}': {motivo}")


# ---------------------------------------------------------------- orquestração

def validar_pasta(raiz: Path) -> Relatorio:
    """Roda todas as validações na pasta de pauta e devolve o relatório."""
    rel = Relatorio()
    textos: Textos = []
    if not raiz.is_dir():
        rel.erro(str(raiz), "pasta não encontrada")
        return rel
    pauta = carregar_json(raiz, "pauta.json", rel)
    if pauta is not None:
        validar_pauta_json(pauta, rel)
    estado = carregar_json(raiz, "estado.json", rel, ausente_e_erro=False)
    if estado is not None:
        validar_estado_json(estado, rel)
    for i in range(1, 4):
        _validar_video(raiz, f"v{i}", rel, textos)
    for i in range(1, 4):
        _validar_pasta_carrossel(raiz, f"c{i}", rel, textos)
    checar_conteudo(textos, carregar_regras(rel), rel)
    return rel


def _validar_video(raiz: Path, pasta: str, rel: Relatorio, textos: Textos) -> None:
    """Valida a pasta de um vídeo (episode, narration, legenda)."""
    if not (raiz / pasta).is_dir():
        rel.erro(pasta, "pasta ausente")
        return
    episode = carregar_json(raiz, f"{pasta}/episode.json", rel)
    if episode is not None:
        validar_episode(episode, f"{pasta}/episode.json", rel, textos)
    narracao = carregar_json(raiz, f"{pasta}/narration.json", rel)
    if narracao is not None:
        validar_narration(narracao, f"{pasta}/narration.json", rel, textos)
    validar_legenda(raiz, f"{pasta}/legenda.txt", HASHTAGS_VIDEO, rel, textos)


def _validar_pasta_carrossel(raiz: Path, pasta: str, rel: Relatorio, textos: Textos) -> None:
    """Valida a pasta de um carrossel (carrossel.json, legenda)."""
    if not (raiz / pasta).is_dir():
        rel.erro(pasta, "pasta ausente")
        return
    carrossel = carregar_json(raiz, f"{pasta}/carrossel.json", rel)
    if carrossel is not None:
        validar_carrossel(carrossel, f"{pasta}/carrossel.json", pasta, rel, textos)
    validar_legenda(raiz, f"{pasta}/legenda.txt", HASHTAGS_CARROSSEL, rel, textos)


def formatar_relatorio(rel: Relatorio) -> str:
    """Monta o relatório legível, agrupado por arquivo, com o resumo final."""
    por_arquivo: dict[str, list[str]] = {}
    for arquivo, msg in rel.erros:
        por_arquivo.setdefault(arquivo, []).append(f"  ERRO  {msg}")
    for arquivo, msg in rel.avisos:
        por_arquivo.setdefault(arquivo, []).append(f"  AVISO {msg}")
    linhas: list[str] = []
    for arquivo in sorted(por_arquivo):
        linhas.append(arquivo)
        linhas.extend(sorted(por_arquivo[arquivo], key=lambda x: not x.startswith("  ERRO")))
    linhas.append(f"{len(rel.erros)} erros, {len(rel.avisos)} avisos")
    return "\n".join(linhas)


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada: imprime o relatório e devolve o exit code."""
    ap = argparse.ArgumentParser(description="Valida a pasta de pauta diária.")
    ap.add_argument("pasta", type=Path, help="pasta da pauta")
    ap.add_argument("--json", action="store_true", help="saída em JSON")
    args = ap.parse_args(argv)
    rel = validar_pasta(args.pasta)
    if args.json:
        print(json.dumps({
            "erros": [{"arquivo": a, "mensagem": m} for a, m in rel.erros],
            "avisos": [{"arquivo": a, "mensagem": m} for a, m in rel.avisos],
        }, ensure_ascii=False, indent=2))
    else:
        print(formatar_relatorio(rel))
    return 1 if rel.erros else 0


if __name__ == "__main__":
    sys.exit(main())
