#!/usr/bin/env python3
"""Gerenciador de impulsionamento (ads) dos vídeos curtos no Instagram e TikTok.

Uso:
  python3 impulsionar.py decidir metricas.json historico_ads.json [--config config/ads.json] [--agora ISO]
  python3 impulsionar.py avaliar historico_ads.json [--config config/ads.json]
  python3 impulsionar.py executar decisoes.json [--plataforma instagram|tiktok] [--dry-run | --executar --confirmo]

`decidir` e `avaliar_ativos` são funções puras (sem rede, sem relógio). `executar` é dry-run
por padrão; só cria algo com `--executar --confirmo`. Ver docs/impulsionamento.md.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

FUSO = timezone(timedelta(hours=-3))  # "dia" de gasto = dia de Brasília
PASSO = 5.0  # múltiplo de R$
CONFIG_PADRAO = Path(__file__).resolve().parent.parent / "config" / "ads.json"


@dataclass
class Decisao:
    post_id: str
    plataforma: str
    canal: str
    orcamento: float
    duracao_dias: int
    motivo: str
    pontuacao: float
    extra: dict[str, Any] = field(default_factory=dict)  # url, midia_id, auth_code (para a execução)


@dataclass
class Parada:
    post_id: str
    plataforma: str
    motivo: str
    valor: float
    limite: float


def _dt(texto: str) -> datetime:
    dt = datetime.fromisoformat(texto)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _dia(dt: datetime) -> str:
    return dt.astimezone(FUSO).date().isoformat()


def taxa_engajamento(p: dict[str, Any]) -> float:
    views = p.get("views", 0) or 0
    if views <= 0:
        return 0.0
    soma = sum(p.get(k, 0) or 0 for k in ("likes", "comentarios", "compartilhamentos", "salvos"))
    return soma / views


def _quantil(valores: list[float], q: float) -> float:
    v = sorted(valores)
    pos = q * (len(v) - 1)
    i, f = math.floor(pos), pos - math.floor(pos)
    return v[i] if f == 0 else v[i] + (v[i + 1] - v[i]) * f


def _ja_impulsionados(historico: dict[str, Any]) -> set[str]:
    ids = {a["post_id"] for a in historico.get("ativos", [])}
    ids |= {a["post_id"] for a in historico.get("criados", [])}
    ids |= set(historico.get("gasto_por_post", {}))
    return ids


def _orcamento_restante(historico: dict[str, Any], config: dict[str, Any], agora: datetime) -> float:
    por_dia = historico.get("gasto_por_dia", {})
    hoje = _dia(agora)
    gasto_hoje = float(por_dia.get(hoje, 0.0))
    inicio = (agora.astimezone(FUSO) - timedelta(days=6)).date().isoformat()
    gasto_semana = sum(float(v) for k, v in por_dia.items() if inicio <= k <= hoje)
    return min(config["orcamento_diario_total"] - gasto_hoje, config["orcamento_semanal_total"] - gasto_semana)


def _distribuir(candidatos: list[Decisao], pool: float, config: dict[str, Any]) -> list[Decisao]:
    """Divide `pool` proporcionalmente à pontuação, em múltiplos de R$ 5, respeitando min/max.
    Se alguém ficar abaixo do mínimo, sai o de menor pontuação e refaz a conta."""
    mn = config["orcamento_por_post"]["min"]
    mx = math.floor(config["orcamento_por_post"]["max"] / PASSO) * PASSO
    sel = list(candidatos)  # já ordenada por pontuação desc
    while sel:
        pesos = [max(c.pontuacao, 0.1) for c in sel]
        total = sum(pesos)
        valores = [min(mx, math.floor(pool * w / total / PASSO) * PASSO) for w in pesos]
        if min(valores) >= mn:
            for c, v in zip(sel, valores):
                c.orcamento = float(v)
            return sel
        sel.pop()
    return []


def decidir(metricas: list[dict[str, Any]], historico: dict[str, Any],
            config: dict[str, Any], agora: datetime) -> list[Decisao]:
    crit = config["criterios"]
    janela = timedelta(hours=config["janela_horas"])
    proibidas = {t.lower() for t in config.get("nunca_impulsionar", [])}
    usados = _ja_impulsionados(historico)

    na_janela = []
    for p in metricas:
        idade = agora - _dt(p["publicado_em"])
        if timedelta(0) <= idade <= janela:
            na_janela.append(p)

    grupos: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for p in na_janela:
        grupos.setdefault((p["canal"], p["plataforma"]), []).append(p)

    candidatos: list[Decisao] = []
    for p in na_janela:
        plat = config["plataformas"].get(p["plataforma"], {})
        canal = config["canais"].get(p["canal"], {})
        if not plat.get("ativo") or not canal.get("ativo"):
            continue
        if p["id"] in usados or proibidas & {t.lower() for t in p.get("tags", [])}:
            continue
        views, taxa = p.get("views", 0) or 0, taxa_engajamento(p)
        if views < crit["views_min"] or taxa < crit["taxa_engajamento_min"]:
            continue
        if crit.get("retencao_min") is not None and (p.get("retencao") or 0) < crit["retencao_min"]:
            continue
        grupo = grupos[(p["canal"], p["plataforma"])]
        vs = [g.get("views", 0) or 0 for g in grupo]
        z = 0.0
        if len(grupo) >= 3:
            if views < _quantil(vs, crit["percentil_views_canal"]):
                continue
            sd = statistics.pstdev(vs)
            z = (views - statistics.fmean(vs)) / sd if sd > 0 else 0.0
        nota = z * canal.get("peso", 1.0) + taxa * 10
        motivo = (f"views {views}, engajamento {taxa:.1%}"
                  + (f", z-views {z:+.2f}" if len(grupo) >= 3 else ", poucos posts no canal (só mínimos)")
                  + f", objetivo {plat.get('objetivo', '?')}")
        candidatos.append(Decisao(
            post_id=p["id"], plataforma=p["plataforma"], canal=p["canal"], orcamento=0.0,
            duracao_dias=config["duracao_dias"], motivo=motivo, pontuacao=round(nota, 4),
            extra={k: p[k] for k in ("url", "midia_id", "auth_code") if p.get(k)}))

    candidatos.sort(key=lambda c: c.pontuacao, reverse=True)
    hoje = _dia(agora)
    ja_hoje = len({a["post_id"] for a in historico.get("criados", []) + historico.get("ativos", [])
                   if str(a.get("criado_em", ""))[:10] == hoje})
    vagas = max(0, config["max_posts_por_dia"] - ja_hoje)
    pool = _orcamento_restante(historico, config, agora)
    if vagas == 0 or pool < config["orcamento_por_post"]["min"]:
        return []
    return _distribuir(candidatos[:vagas], pool, config)


def avaliar_ativos(ativos: list[dict[str, Any]], config: dict[str, Any]) -> list[Parada]:
    lim = config["parar_se"]
    paradas = []
    for a in ativos:
        gasto = float(a.get("gasto", 0) or 0)
        imp = a.get("impressoes", 0) or 0
        seg = a.get("seguidores_ganhos", 0) or 0
        if imp > 0 and lim.get("cpm_max") is not None:
            cpm = gasto / imp * 1000
            if cpm > lim["cpm_max"]:
                paradas.append(Parada(a["post_id"], a["plataforma"], "cpm acima do limite", round(cpm, 2), lim["cpm_max"]))
                continue
        objetivo = config["plataformas"].get(a["plataforma"], {}).get("objetivo")
        cmax = lim.get("custo_por_seguidor_max")
        if objetivo == "seguidores" and cmax is not None:
            custo = gasto / seg if seg > 0 else (math.inf if gasto > cmax else None)
            if custo is not None and custo > cmax:
                valor = round(custo, 2) if seg > 0 else round(gasto, 2)
                paradas.append(Parada(a["post_id"], a["plataforma"],
                                      "custo por seguidor acima do limite" if seg > 0 else "gasto sem nenhum seguidor",
                                      valor, cmax))
    return paradas


# ---------------------------------------------------------------- CLI

def _ler(caminho: str) -> Any:
    try:
        return json.loads(Path(caminho).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise SystemExit(f"Erro ao ler {caminho}: {e}")


def _tabela(decisoes: list[Decisao]) -> str:
    if not decisoes:
        return "Nenhum post para impulsionar."
    linhas = [f"{'post':<14}{'plataforma':<11}{'canal':<16}{'R$':>6}{'dias':>5}{'nota':>8}  motivo"]
    for d in decisoes:
        linhas.append(f"{d.post_id:<14}{d.plataforma:<11}{d.canal:<16}{d.orcamento:>6.0f}{d.duracao_dias:>5}"
                      f"{d.pontuacao:>8.2f}  {d.motivo}")
    return "\n".join(linhas)


def cmd_decidir(a: argparse.Namespace) -> int:
    agora = _dt(a.agora) if a.agora else datetime.now(timezone.utc)
    decisoes = decidir(_ler(a.metricas), _ler(a.historico), _ler(a.config), agora)
    print(_tabela(decisoes))
    Path(a.saida).write_text(json.dumps([asdict(d) for d in decisoes], ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGravado em {a.saida}")
    return 0


def cmd_avaliar(a: argparse.Namespace) -> int:
    paradas = avaliar_ativos(_ler(a.historico).get("ativos", []), _ler(a.config))
    for p in paradas:
        print(f"PARAR {p.post_id} ({p.plataforma}): {p.motivo}: {p.valor} > {p.limite}")
    if not paradas:
        print("Nenhum impulsionamento para parar.")
    return 0


def cmd_executar(a: argparse.Namespace) -> int:
    from ads import meta, tiktok
    from ads.comum import AdsError

    confirmar = bool(a.executar and a.confirmo)
    if a.executar and not a.confirmo:
        print("Erro: --executar exige --confirmo. Nada foi criado.", file=sys.stderr)
        return 2
    config = _ler(a.config)
    decisoes = [d for d in _ler(a.decisoes) if not a.plataforma or d["plataforma"] == a.plataforma]
    agora = datetime.now(timezone.utc)
    adaptadores = {"instagram": meta, "tiktok": tiktok}
    registros = []
    try:
        for d in decisoes:
            objetivo = config["plataformas"][d["plataforma"]]["objetivo"]
            print(f"== {d['post_id']} ({d['plataforma']}) R$ {d['orcamento']:.0f} por {d['duracao_dias']} dias")
            registros.append(adaptadores[d["plataforma"]].criar(d, objetivo, agora, confirmar))
    except AdsError as e:
        print(f"Erro: {e}", file=sys.stderr)
        _gravar_historico(a.historico, registros, agora, confirmar)
        return 1
    _gravar_historico(a.historico, registros, agora, confirmar)
    print("\nDry-run: nada foi criado." if not confirmar else f"\n{len(registros)} impulsionamento(s) criado(s), em pausa.")
    return 0


def _gravar_historico(caminho: str, registros: list[dict[str, Any]], agora: datetime, confirmar: bool) -> None:
    """Só grava no modo real. `criados` é o diário de criação; `ativos` é o que `avaliar` vigia."""
    reais = [r for r in registros if not r.get("dry_run")]
    if not confirmar or not reais:
        return
    p = Path(caminho)
    h = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    for r in reais:
        h.setdefault("criados", []).append(r)
        h.setdefault("ativos", []).append({**r, "gasto": 0.0, "impressoes": 0, "seguidores_ganhos": 0})
        dia = _dia(agora)
        h.setdefault("gasto_por_dia", {})[dia] = h.get("gasto_por_dia", {}).get(dia, 0.0) + r["orcamento"]
        h.setdefault("gasto_por_post", {})[r["post_id"]] = r["orcamento"]
    p.write_text(json.dumps(h, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Histórico atualizado em {caminho}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("decidir")
    d.add_argument("metricas"); d.add_argument("historico")
    d.add_argument("--config", default=str(CONFIG_PADRAO)); d.add_argument("--agora")
    d.add_argument("--saida", default="decisoes.json")
    d.set_defaults(fn=cmd_decidir)
    v = sub.add_parser("avaliar")
    v.add_argument("historico"); v.add_argument("--config", default=str(CONFIG_PADRAO))
    v.set_defaults(fn=cmd_avaliar)
    e = sub.add_parser("executar")
    e.add_argument("decisoes"); e.add_argument("--plataforma", choices=["instagram", "tiktok"])
    e.add_argument("--config", default=str(CONFIG_PADRAO)); e.add_argument("--historico", default="historico_ads.json")
    e.add_argument("--dry-run", action="store_true", help="padrão; imprime payloads sem chamar a rede")
    e.add_argument("--executar", action="store_true", help="cria de verdade (exige --confirmo)")
    e.add_argument("--confirmo", action="store_true")
    e.set_defaults(fn=cmd_executar)
    a = ap.parse_args(argv)
    if a.cmd == "executar" and a.dry_run and a.executar:
        ap.error("--dry-run e --executar são excludentes")
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
