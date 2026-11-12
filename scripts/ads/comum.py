"""Utilitários comuns dos adaptadores: erro claro e chamada HTTP só com urllib."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


class AdsError(Exception):
    """Erro de rede ou de API, com mensagem legível (sem traceback na CLI)."""


def variaveis(nomes: list[str], exigir: bool) -> dict[str, str]:
    """Lê variáveis de ambiente. Se `exigir`, falta = AdsError; senão usa placeholder."""
    valores = {n: os.environ.get(n, "") for n in nomes}
    faltando = [n for n, v in valores.items() if not v]
    if faltando and exigir:
        raise AdsError("Variáveis de ambiente ausentes: " + ", ".join(faltando))
    return {n: v or f"<{n}>" for n, v in valores.items()}


def _mensagem_erro(corpo: bytes) -> str:
    try:
        dados = json.loads(corpo)
    except ValueError:
        return corpo.decode("utf-8", "replace")[:300]
    if isinstance(dados, dict):
        erro = dados.get("error")
        if isinstance(erro, dict) and erro.get("message"):
            return str(erro["message"])
        if dados.get("message"):
            return str(dados["message"])
    return str(dados)[:300]


def chamar(url: str, corpo: bytes, cabecalhos: dict[str, str], timeout: int = 30) -> dict[str, Any]:
    """POST via urllib; devolve o JSON ou levanta AdsError com o error.message."""
    req = urllib.request.Request(url, data=corpo, headers=cabecalhos, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            dados = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise AdsError(f"{url.split('?')[0]} -> HTTP {e.code}: {_mensagem_erro(e.read())}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise AdsError(f"Falha de rede em {url.split('?')[0]}: {getattr(e, 'reason', e)}") from None
    except ValueError:
        raise AdsError(f"Resposta não é JSON em {url.split('?')[0]}") from None
    return dados


def mostrar(titulo: str, caminho: str, payload: dict[str, Any]) -> None:
    print(f"[dry-run] {titulo}: POST {caminho}")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
