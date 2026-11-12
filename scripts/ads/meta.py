"""Adaptador Meta (Instagram) para a Marketing API v21.0, só com urllib.

Fluxo: campanha -> conjunto de anúncios -> criativo (reel existente) -> anúncio.
Sem `confirmar`, nada é enviado: imprime os payloads exatos e não toca a rede.
Variáveis: META_ACCESS_TOKEN, META_AD_ACCOUNT_ID (act_123). Página e Instagram de cada canal vêm de
config/ads.json → meta_contas; META_PAGE_ID e META_IG_USER_ID só como reserva.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import urllib.parse
from datetime import datetime, timedelta
from typing import Any

from ads.comum import AdsError, chamar, mostrar, variaveis

VERSAO = "v21.0"
BASE = f"https://graph.facebook.com/{VERSAO}"
VARS = ["META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID"]
CONFIG = Path(__file__).resolve().parents[2] / "config" / "ads.json"


def conta_do_canal(canal: str, config: Path = CONFIG) -> dict[str, str]:
    """Página e Instagram do canal pelo config; reserva nas variáveis META_PAGE_ID/META_IG_USER_ID."""
    try:
        contas = json.loads(config.read_text(encoding="utf-8")).get("meta_contas", {})
    except (OSError, ValueError):
        contas = {}
    conta = contas.get(canal, {})
    return {
        "page_id": conta.get("page_id") or os.environ.get("META_PAGE_ID") or "<META_PAGE_ID>",
        "instagram_user_id": conta.get("instagram_user_id") or os.environ.get("META_IG_USER_ID") or "<META_IG_USER_ID>",
    }

# objetivo da plataforma (config) -> (objective, optimization_goal)
OBJETIVOS = {
    "seguidores": ("OUTCOME_ENGAGEMENT", "PROFILE_VISIT"),
    "visualizacoes": ("OUTCOME_AWARENESS", "THRUPLAY"),
}


def _nome(d: dict[str, Any]) -> str:
    return f"eq-{d['canal']}-{d['post_id']}"


def payload_campanha(d: dict[str, Any], objetivo: str) -> dict[str, Any]:
    obj, _ = OBJETIVOS[objetivo]
    return {
        "name": _nome(d),
        "objective": obj,
        "status": "PAUSED",  # nasce pausada; ativar é decisão manual no Ads Manager
        "special_ad_categories": [],
        "is_adset_budget_sharing_enabled": False,
    }


def payload_conjunto(d: dict[str, Any], objetivo: str, campanha_id: str, agora: datetime) -> dict[str, Any]:
    _, meta = OBJETIVOS[objetivo]
    dias = d["duracao_dias"]
    return {
        "name": _nome(d),
        "campaign_id": campanha_id,
        "daily_budget": round(d["orcamento"] / dias * 100),  # centavos
        "billing_event": "IMPRESSIONS",
        "optimization_goal": meta,
        "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
        "targeting": {
            "geo_locations": {"countries": ["BR"]},
            "age_min": 18,
            "age_max": 45,
            "publisher_platforms": ["instagram"],
            "instagram_positions": ["stream", "reels"],
        },
        "start_time": agora.isoformat(),
        "end_time": (agora + timedelta(days=dias)).isoformat(),
        "status": "PAUSED",
    }


def payload_criativo(d: dict[str, Any], env: dict[str, str]) -> dict[str, Any]:
    midia = d.get("extra", {}).get("midia_id") or "<midia_id do reel>"
    return {
        "name": _nome(d),
        "object_story_spec": conta_do_canal(d.get("canal", "")),
        "source_instagram_media_id": midia,
    }


def payload_anuncio(d: dict[str, Any], conjunto_id: str, criativo_id: str) -> dict[str, Any]:
    return {
        "name": _nome(d),
        "adset_id": conjunto_id,
        "creative": {"creative_id": criativo_id},
        "status": "PAUSED",
    }


def _post(caminho: str, payload: dict[str, Any], token: str) -> dict[str, Any]:
    campos = {k: v if isinstance(v, str) else json.dumps(v) for k, v in payload.items()}
    campos["access_token"] = token
    corpo = urllib.parse.urlencode(campos).encode()
    return chamar(f"{BASE}/{caminho}", corpo, {"Content-Type": "application/x-www-form-urlencoded"})


def _id(resp: dict[str, Any], etapa: str) -> str:
    if "id" not in resp:
        raise AdsError(f"Meta/{etapa}: resposta sem id: {json.dumps(resp)[:200]}")
    return str(resp["id"])


def criar(d: dict[str, Any], objetivo: str, agora: datetime, confirmar: bool) -> dict[str, Any]:
    """Cria (ou simula) o anúncio. Devolve o registro para o historico_ads.json."""
    env = variaveis(VARS, exigir=confirmar)
    conta = env["META_AD_ACCOUNT_ID"]
    ph = lambda n: f"<{n}>"  # noqa: E731
    etapas = [
        ("campanha", f"{conta}/campaigns", payload_campanha(d, objetivo)),
        ("conjunto", f"{conta}/adsets", None),
        ("criativo", f"{conta}/adcreatives", payload_criativo(d, env)),
        ("anuncio", f"{conta}/ads", None),
    ]
    ids: dict[str, str] = {}
    for etapa, caminho, payload in etapas:
        if etapa == "conjunto":
            payload = payload_conjunto(d, objetivo, ids.get("campanha", ph("campanha_id")), agora)
        elif etapa == "anuncio":
            payload = payload_anuncio(d, ids.get("conjunto", ph("conjunto_id")), ids.get("criativo", ph("criativo_id")))
        if not confirmar:
            mostrar(f"Meta {etapa}", f"/{VERSAO}/{caminho}", payload)
            continue
        ids[etapa] = _id(_post(caminho, payload, env["META_ACCESS_TOKEN"]), etapa)
    return {
        "post_id": d["post_id"], "plataforma": "instagram", "canal": d["canal"],
        "orcamento": d["orcamento"], "duracao_dias": d["duracao_dias"],
        "criado_em": agora.isoformat(), "dry_run": not confirmar, "ids": ids,
    }
