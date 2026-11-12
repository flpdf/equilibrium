#!/usr/bin/env python3
"""Baixa arquivos do Google Drive por id, a partir de um manifesto DRIVE.md ou de pares id=destino.

Uso:
  python3 scripts/drive_baixar.py manifesto canais/chefao/DRIVE.md --destino run/chefao [--filtro REGEX] [--secao TEXTO]
  python3 scripts/drive_baixar.py ids 1abc...=run/template.html 1def...=run/x.mp3

Exige que o arquivo esteja compartilhado "qualquer pessoa com o link" (a pasta Videos-Claude inteira resolve).
Confere o tamanho quando o manifesto informa; detecta a página de login do Google (arquivo não compartilhado).
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

URL = "https://drive.usercontent.google.com/download?id={id}&export=download&confirm=t"
ID_RE = re.compile(r"^[A-Za-z0-9_-]{20,}$")
TRACO = re.compile(r"^\|?\s*:?-{2,}")


@dataclass
class Item:
    caminho: str
    id: str
    tamanho: int | None
    destino: str | None = None


def _celulas(linha: str) -> list[str]:
    """Divide uma linha de tabela markdown em células sem crases nem espaços."""
    partes = [c.strip().strip("`").strip() for c in linha.strip().strip("|").split("|")]
    return partes


def ler_manifesto(texto: str, secao: str | None = None) -> list[Item]:
    """Extrai de todas as tabelas as linhas `| caminho | id | tamanho [| destino] |`."""
    itens: list[Item] = []
    dentro = secao is None
    for linha in texto.splitlines():
        if linha.startswith("## "):
            dentro = secao is None or secao.lower() in linha.lower()
            continue
        if not dentro or not linha.lstrip().startswith("|") or TRACO.match(linha):
            continue
        cel = _celulas(linha)
        if len(cel) < 3 or not ID_RE.match(cel[1]):
            continue
        tamanho = int(cel[2]) if cel[2].isdigit() else None
        if tamanho is None:
            continue  # tabelas de pastas têm "Itens", não tamanho
        destino = cel[3] if len(cel) > 3 and cel[3] and "/" in cel[3] else None
        itens.append(Item(cel[0], cel[1], tamanho, destino))
    return itens


def baixar(item: Item, destino: Path) -> str:
    """Baixa um item para `destino`; devolve "OK", ou a razão da falha."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(URL.format(id=item.id), headers={"User-Agent": "curl/8"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            tipo = r.headers.get("Content-Type", "")
            dados = r.read()
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}"
    except urllib.error.URLError as e:
        return f"rede: {e.reason}"
    if tipo.startswith("text/html") and b"accounts.google.com" in dados[:4096]:
        return "não compartilhado (página de login)"
    if item.tamanho is not None and len(dados) != item.tamanho:
        return f"tamanho {len(dados)} != esperado {item.tamanho}"
    destino.write_bytes(dados)
    return "OK"


def main(argv: list[str] | None = None) -> int:
    """Linha de comando."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="modo", required=True)
    m = sub.add_parser("manifesto")
    m.add_argument("arquivo")
    m.add_argument("--destino", required=True)
    m.add_argument("--filtro", default=None, help="regex sobre o caminho")
    m.add_argument("--secao", default=None, help="só tabelas cujo título ## contenha este texto")
    i = sub.add_parser("ids")
    i.add_argument("pares", nargs="+", help="id=destino")
    args = ap.parse_args(argv)

    if args.modo == "manifesto":
        itens = ler_manifesto(Path(args.arquivo).read_text(encoding="utf-8"), args.secao)
        if args.filtro:
            itens = [x for x in itens if re.search(args.filtro, x.caminho)]
        base = Path(args.destino)
        pares = [(x, base / (x.destino or x.caminho)) for x in itens]
    else:
        pares = []
        for p in args.pares:
            fid, _, dest = p.partition("=")
            pares.append((Item(dest, fid, None), Path(dest)))

    if not pares:
        print("nada a baixar", file=sys.stderr)
        return 2
    falhas = 0
    for item, dest in pares:
        res = baixar(item, dest)
        print(f"{'OK ' if res == 'OK' else 'ERRO'} {dest}  {res if res != 'OK' else ''}".rstrip())
        falhas += res != "OK"
    print(f"{len(pares) - falhas} baixados, {falhas} falhas")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
